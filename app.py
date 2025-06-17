#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态聊天机器人 Web 应用
集成SiliconFlow文本处理和Groq图片处理的Flask后端服务
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import json
import base64
import os
from typing import List, Dict, Optional
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# API配置
SILICONFLOW_API_KEY = os.environ.get("SILICONFLOW_API_KEY", "sk-icupqsqwcgsfnqbwpcgfertxbdlkksapxtacxlupjzanguyv")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# 可用模型列表
AVAILABLE_MODELS = [
    {
        "id": "deepseek-ai/DeepSeek-V2.5",
        "name": "DeepSeek-V2.5 (文本)",
        "provider": "siliconflow",
        "default": True,
        "supports_image": False,
        "type": "text"
    },
    {
        "id": "Qwen/Qwen2.5-7B-Instruct",
        "name": "Qwen2.5-7B (文本)",
        "provider": "siliconflow",
        "default": False,
        "supports_image": False,
        "type": "text"
    },
    {
        "id": "meta-llama/llama-4-scout-17b-16e-instruct",
        "name": "Llama 4 Scout (多模态)",
        "provider": "groq",
        "default": False,
        "supports_image": True,
        "type": "multimodal"
    },
    {
        "id": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "name": "Llama 4 Maverick (多模态)",
        "provider": "groq",
        "default": False,
        "supports_image": True,
        "type": "multimodal"
    }
]

class MultiModalChatBotService:
    def __init__(self, siliconflow_api_key: str, groq_api_key: str):
        self.siliconflow_api_key = siliconflow_api_key
        self.groq_api_key = groq_api_key
        self.siliconflow_base_url = SILICONFLOW_BASE_URL.rstrip('/') + '/chat/completions'
        self.groq_base_url = GROQ_BASE_URL.rstrip('/') + '/chat/completions'
        
    def get_response(self, messages: List[Dict], model: str = "deepseek-ai/DeepSeek-V2.5") -> Dict:
        """获取AI回复，自动选择合适的服务提供商"""
        
        # 检查是否有图片内容
        has_image = self._has_image_content(messages)
        model_info = self._get_model_info(model)
        
        if not model_info:
            return {
                "success": False,
                "error": f"未知模型: {model}"
            }
        
        # 如果有图片但模型不支持，自动切换到支持图片的模型
        if has_image and not model_info["supports_image"]:
            # 自动选择Groq的多模态模型
            model = "meta-llama/llama-4-scout-17b-16e-instruct"
            model_info = self._get_model_info(model)
            logger.info(f"检测到图片内容，自动切换到多模态模型: {model}")
        
        # 根据模型提供商选择API
        if model_info["provider"] == "groq":
            return self._get_groq_response(messages, model)
        else:
            return self._get_siliconflow_response(messages, model)
    
    def _has_image_content(self, messages: List[Dict]) -> bool:
        """检查消息中是否包含图片"""
        for msg in messages:
            if msg.get('image'):
                return True
        return False
    
    def _get_model_info(self, model: str) -> Optional[Dict]:
        """获取模型信息"""
        for m in AVAILABLE_MODELS:
            if m["id"] == model:
                return m
        return None
    
    def _get_siliconflow_response(self, messages: List[Dict], model: str) -> Dict:
        """使用SiliconFlow API获取回复"""
        if not self.siliconflow_api_key:
            return {
                "success": False,
                "error": "SiliconFlow API密钥未配置"
            }
        
        headers = {
            "Authorization": f"Bearer {self.siliconflow_api_key}",
            "Content-Type": "application/json"
        }
        
        # 转换消息格式（只处理文本）
        api_messages = []
        for msg in messages:
            if msg['role'] == 'user':
                text_content = msg.get('text', '')
                if msg.get('image'):
                    text_content += " [注：检测到图片，但当前模型不支持图片处理]"
                
                api_messages.append({
                    "role": "user",
                    "content": text_content
                })
            else:
                api_messages.append({
                    "role": msg['role'],
                    "content": msg.get('text', '')
                })
        
        data = {
            "model": model,
            "messages": api_messages,
            "stream": False,
            "max_tokens": 2000,
            "temperature": 0.7
        }
        
        logger.info(f"使用SiliconFlow API，模型: {model}")
        
        try:
            response = requests.post(self.siliconflow_base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
            return {
                "success": True,
                "response": ai_response,
                "provider": "siliconflow",
                "model": model
            }
            
        except Exception as e:
            logger.error(f"SiliconFlow API错误: {e}")
            return {
                "success": False,
                "error": f"SiliconFlow API错误: {str(e)}"
            }
    
    def _get_groq_response(self, messages: List[Dict], model: str) -> Dict:
        """使用Groq API获取回复"""
        if not self.groq_api_key:
            return {
                "success": False,
                "error": "Groq API密钥未配置"
            }
        
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        # 转换消息格式（支持多模态）
        api_messages = []
        for msg in messages:
            if msg['role'] == 'user':
                content = []
                
                # 添加文本内容
                if msg.get('text'):
                    content.append({
                        "type": "text",
                        "text": msg['text']
                    })
                
                # 添加图片内容
                if msg.get('image'):
                    image_data = msg['image']
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": image_data
                        }
                    })
                
                api_messages.append({
                    "role": "user",
                    "content": content if len(content) > 1 else (content[0]["text"] if content else "")
                })
            else:
                api_messages.append({
                    "role": msg['role'],
                    "content": msg.get('text', '')
                })
        
        data = {
            "model": model,
            "messages": api_messages,
            "temperature": 0.7,
            "max_completion_tokens": 1024,
            "top_p": 1,
            "stream": False
        }
        
        logger.info(f"使用Groq API，模型: {model}")
        
        try:
            response = requests.post(self.groq_base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
            return {
                "success": True,
                "response": ai_response,
                "provider": "groq",
                "model": model
            }
            
        except Exception as e:
            logger.error(f"Groq API错误: {e}")
            return {
                "success": False,
                "error": f"Groq API错误: {str(e)}"
            }

# 初始化多模态聊天机器人服务
if not GROQ_API_KEY:
    logger.warning("Groq API密钥未配置，多模态功能将不可用")

chatbot_service = MultiModalChatBotService(SILICONFLOW_API_KEY, GROQ_API_KEY)

@app.route('/')
def index():
    """提供前端页面"""
    return send_from_directory('.', 'index.html')

@app.route('/api/models', methods=['GET'])
def get_models():
    """获取可用模型列表"""
    # 根据API密钥可用性过滤模型
    available_models = []
    for model in AVAILABLE_MODELS:
        if model["provider"] == "siliconflow" and SILICONFLOW_API_KEY:
            available_models.append(model)
        elif model["provider"] == "groq" and GROQ_API_KEY:
            available_models.append(model)
    
    return jsonify({
        'success': True,
        'models': available_models,
        'capabilities': {
            'text_chat': bool(SILICONFLOW_API_KEY),
            'image_analysis': bool(GROQ_API_KEY),
            'multimodal': bool(GROQ_API_KEY)
        }
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """处理聊天请求"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '无效的请求数据'
            }), 400
        
        messages = data.get('messages', [])
        model = data.get('model', 'deepseek-ai/DeepSeek-V2.5')
        
        if not messages:
            return jsonify({
                'success': False,
                'error': '消息不能为空'
            }), 400
        
        # 获取AI回复
        result = chatbot_service.get_response(messages, model)
        
        if result['success']:
            return jsonify({
                'success': True,
                'response': result['response'],
                'provider': result.get('provider'),
                'model': result.get('model')
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"聊天API错误: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@app.route('/api/upload', methods=['POST'])
def upload_image():
    """处理图片上传"""
    try:
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有找到图片文件'
            }), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '没有选择文件'
            }), 400
        
        # 检查文件类型
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return jsonify({
                'success': False,
                'error': '不支持的文件格式，请上传 PNG、JPG、JPEG、GIF 或 WebP 格式的图片'
            }), 400
        
        # 检查文件大小 (4MB限制)
        file.seek(0, 2)  # 移到文件末尾
        file_size = file.tell()
        file.seek(0)  # 回到文件开头
        
        if file_size > 4 * 1024 * 1024:  # 4MB
            return jsonify({
                'success': False,
                'error': f'文件过大 ({file_size / 1024 / 1024:.1f}MB)，最大支持4MB'
            }), 400
        
        # 读取文件并转换为base64
        file_content = file.read()
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        # 获取文件MIME类型
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        mime_type = f"image/{file_extension if file_extension != 'jpg' else 'jpeg'}"
        
        # 构造data URL
        data_url = f"data:{mime_type};base64,{file_base64}"
        
        return jsonify({
            'success': True,
            'image_data': data_url,
            'file_size': file_size,
            'file_name': file.filename
        })
        
    except Exception as e:
        logger.error(f"图片上传错误: {e}")
        return jsonify({
            'success': False,
            'error': f'图片上传失败: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'message': '多模态聊天机器人服务正常运行',
        'capabilities': {
            'siliconflow_available': bool(SILICONFLOW_API_KEY),
            'groq_available': bool(GROQ_API_KEY),
            'multimodal_support': bool(GROQ_API_KEY)
        }
    })

if __name__ == '__main__':
    print("🚀 启动多模态聊天机器人 Web 应用...")
    print("📱 前端地址: http://localhost:5000")
    print("🔗 API 地址: http://localhost:5000/api")
    print("💡 功能支持:")
    print(f"   📝 文本对话: {'✅' if SILICONFLOW_API_KEY else '❌'}")
    print(f"   🖼️  图片分析: {'✅' if GROQ_API_KEY else '❌'}")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000) 