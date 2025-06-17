#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SiliconFlow 聊天机器人 Web 应用
Flask后端服务，支持前端页面的API交互
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import json
import base64
import os
from typing import List, Dict, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# API配置
API_KEY = "sk-icupqsqwcgsfnqbwpcgfertxbdlkksapxtacxlupjzanguyv"
BASE_URL = "https://api.siliconflow.cn/v1"

# 可用模型列表
AVAILABLE_MODELS = [
    {
        "id": "deepseek-ai/DeepSeek-V2.5",
        "name": "DeepSeek-V2.5",
        "default": True,
        "supports_image": False
    },
    {
        "id": "Qwen/Qwen2.5-7B-Instruct",
        "name": "Qwen2.5-7B-Instruct",
        "default": False,
        "supports_image": False
    }
]

class ChatBotService:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/') + '/chat/completions'
        
    def get_response(self, messages: List[Dict], model: str = "deepseek-ai/DeepSeek-V2.5") -> Dict:
        """获取AI回复"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 转换消息格式
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
                
                # 添加图片内容（如果模型支持）
                if msg.get('image') and self.model_supports_image(model):
                    # 处理base64图片
                    image_data = msg['image']
                    if image_data.startswith('data:image/'):
                        # 提取base64部分
                        base64_data = image_data.split(',')[1]
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
            "stream": False,
            "max_tokens": 2000,
            "temperature": 0.7
        }
        
        logger.info(f"发送请求到 {self.base_url}，模型: {model}")
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
            return {
                "success": True,
                "response": ai_response
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求错误: {e}")
            return {
                "success": False,
                "error": f"网络请求错误: {str(e)}"
            }
        except KeyError as e:
            logger.error(f"响应格式错误: {e}")
            return {
                "success": False,
                "error": f"响应格式错误: {str(e)}"
            }
        except Exception as e:
            logger.error(f"未知错误: {e}")
            return {
                "success": False,
                "error": f"未知错误: {str(e)}"
            }
    
    def model_supports_image(self, model: str) -> bool:
        """检查模型是否支持图片"""
        for m in AVAILABLE_MODELS:
            if m["id"] == model:
                return m.get("supports_image", False)
        return False

# 初始化聊天机器人服务
chatbot_service = ChatBotService(API_KEY, BASE_URL)

@app.route('/')
def index():
    """提供前端页面"""
    return send_from_directory('.', 'index.html')

@app.route('/api/models', methods=['GET'])
def get_models():
    """获取可用模型列表"""
    return jsonify({
        'success': True,
        'models': AVAILABLE_MODELS
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
                'response': result['response']
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

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'message': 'SiliconFlow 聊天机器人服务正常运行'
    })

if __name__ == '__main__':
    print("🚀 启动 SiliconFlow 聊天机器人 Web 应用...")
    print("📱 前端地址: http://localhost:5000")
    print("🔗 API 地址: http://localhost:5000/api")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000) 