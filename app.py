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
import tempfile
import io
from typing import List, Dict, Optional
import logging
from dotenv import load_dotenv
from database import ChatDatabase
from datetime import datetime, timedelta
import re

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
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
OPENAI_BASE_URL = "https://api.openai.com/v1"

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

# 环境变量获取
BOCHA_API_KEY = os.environ.get('BOCHA_API_KEY', 'sk-38eaefcfac2d4c39a50c3cd686022e2d')

class MultiModalChatBotService:
    def __init__(self, siliconflow_api_key: str, groq_api_key: str, openai_api_key: str = None):
        self.siliconflow_api_key = siliconflow_api_key
        self.groq_api_key = groq_api_key
        self.openai_api_key = openai_api_key
        self.siliconflow_base_url = SILICONFLOW_BASE_URL.rstrip('/') + '/chat/completions'
        self.groq_base_url = GROQ_BASE_URL.rstrip('/') + '/chat/completions'
        self.openai_transcription_url = OPENAI_BASE_URL.rstrip('/') + '/audio/transcriptions'
        
    def get_response(self, messages: List[Dict], model: str = "deepseek-ai/DeepSeek-V2.5", system_prompt: str = None, temperature: float = 0.7, tools: List[Dict] = None) -> Dict:
        """获取AI回复，自动选择合适的服务提供商，支持Function Calling"""
        
        # 检查是否有多媒体内容
        has_image = self._has_image_content(messages)
        has_multimedia = self._has_multimedia_content(messages)
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
        # 如果有音频/视频但没有图片，也切换到支持多模态的模型（用于文本分析）
        elif has_multimedia and not has_image and not model_info["supports_image"]:
            model = "meta-llama/llama-4-scout-17b-16e-instruct"
            model_info = self._get_model_info(model)
            logger.info(f"检测到多媒体内容，切换到多模态模型进行文本分析: {model}")
        
        # 根据模型提供商选择API
        if model_info["provider"] == "groq":
            return self._get_groq_response(messages, model, system_prompt, temperature, tools)
        else:
            return self._get_siliconflow_response(messages, model, system_prompt, temperature, tools)
    
    def _has_image_content(self, messages: List[Dict]) -> bool:
        """检查消息中是否包含图片"""
        for msg in messages:
            if msg.get('image'):
                return True
        return False
    
    def _has_multimedia_content(self, messages: List[Dict]) -> bool:
        """检查消息中是否包含多媒体内容（图片、音频、视频）"""
        for msg in messages:
            if msg.get('image') or msg.get('audio') or msg.get('video'):
                return True
        return False
    
    def _get_model_info(self, model: str) -> Optional[Dict]:
        """获取模型信息"""
        for m in AVAILABLE_MODELS:
            if m["id"] == model:
                return m
        return None
    
    def _get_siliconflow_response(self, messages: List[Dict], model: str, system_prompt: str = None, temperature: float = 0.7, tools: List[Dict] = None) -> Dict:
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
        
        # 添加系统提示（如果有）
        if system_prompt:
            api_messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        for msg in messages:
            if msg['role'] == 'user':
                text_content = msg.get('text', '')
                
                # 添加多媒体内容的提示
                if msg.get('image'):
                    text_content += " [注：检测到图片，但当前模型不支持图片处理]"
                # 音频和视频内容提示已在预处理中加入，这里不重复添加
                
                api_messages.append({
                    "role": "user",
                    "content": text_content if text_content.strip() else "请提供帮助。"
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
            "temperature": temperature
        }
        
        # 添加工具支持
        if tools:
            data["tools"] = tools
            data["tool_choice"] = "auto"
        
        logger.info(f"使用SiliconFlow API，模型: {model}")
        
        # 尝试多次调用，处理网络超时问题
        max_retries = 2
        timeout_seconds = 60  # 增加超时时间
        
        for attempt in range(max_retries):
            try:
                logger.info(f"SiliconFlow API调用尝试 {attempt + 1}/{max_retries}")
                response = requests.post(
                    self.siliconflow_base_url, 
                    headers=headers, 
                    json=data, 
                    timeout=timeout_seconds
                )
                response.raise_for_status()
                
                result = response.json()
                message = result['choices'][0]['message']
                
                # 检查是否有工具调用
                if message.get('tool_calls'):
                    logger.info(f"SiliconFlow API调用成功 - 检测到工具调用")
                    return {
                        "success": True,
                        "message": message,
                        "tool_calls": message['tool_calls'],
                        "provider": "siliconflow",
                        "model": model,
                        "requires_tool_execution": True
                    }
                else:
                    ai_response = message.get('content', '')
                    logger.info(f"SiliconFlow API调用成功")
                    return {
                        "success": True,
                        "response": ai_response,
                        "provider": "siliconflow",
                        "model": model
                    }
                
            except requests.exceptions.Timeout as e:
                logger.warning(f"SiliconFlow API超时 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    # 最后一次尝试失败，尝试使用Groq作为备用
                    logger.info("SiliconFlow API多次超时，尝试使用Groq作为备用")
                    return self._get_groq_fallback_response(messages, system_prompt, temperature)
                continue
                
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"SiliconFlow API连接错误 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    logger.info("SiliconFlow API连接失败，尝试使用Groq作为备用")
                    return self._get_groq_fallback_response(messages, system_prompt, temperature)
                continue
                
            except Exception as e:
                logger.error(f"SiliconFlow API错误 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return {
                        "success": False,
                        "error": f"SiliconFlow API错误: {str(e)}"
                    }
                continue
        
        return {
            "success": False,
            "error": "SiliconFlow API调用失败"
        }
    
    def _get_groq_fallback_response(self, messages: List[Dict], system_prompt: str = None, temperature: float = 0.7) -> Dict:
        """当SiliconFlow失败时使用Groq作为备用"""
        logger.info("使用Groq作为SiliconFlow的备用服务")
        fallback_model = "meta-llama/llama-4-scout-17b-16e-instruct"
        return self._get_groq_response(messages, fallback_model, system_prompt, temperature)
    
    def _get_groq_response(self, messages: List[Dict], model: str, system_prompt: str = None, temperature: float = 0.7, tools: List[Dict] = None) -> Dict:
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
        
        # 添加系统提示（如果有）
        if system_prompt:
            api_messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        for msg in messages:
            if msg['role'] == 'user':
                content = []
                
                # 添加文本内容
                text_parts = []
                if msg.get('text'):
                    text_parts.append(msg['text'])
                
                # 音频和视频数据已在预处理中移除，只处理文本内容
                
                # 合并文本内容
                if text_parts:
                    content.append({
                        "type": "text",
                        "text": " ".join(text_parts)
                    })
                
                # 添加图片内容（Groq API支持图片）
                if msg.get('image'):
                    image_data = msg['image']
                    content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": image_data
                        }
                    })
                
                # 对于Groq API，总是使用数组格式来支持多模态
                # 如果没有内容，提供默认文本
                if content:
                    api_messages.append({
                        "role": "user",
                        "content": content
                    })
                else:
                    # 没有内容，使用默认提示
                    api_messages.append({
                        "role": "user",
                        "content": [{"type": "text", "text": "请提供帮助。"}]
                    })
            else:
                api_messages.append({
                    "role": msg['role'],
                    "content": msg.get('text', '')
                })
        
        data = {
            "model": model,
            "messages": api_messages,
            "temperature": temperature,
            "max_completion_tokens": 1024,
            "top_p": 1,
            "stream": False
        }
        
        # 添加工具支持
        if tools:
            data["tools"] = tools
            data["tool_choice"] = "auto"
        
        logger.info(f"使用Groq API，模型: {model}")
        
        try:
            logger.info(f"调用Groq API，模型: {model}")
            response = requests.post(self.groq_base_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            message = result['choices'][0]['message']
            
            # 检查是否有工具调用
            if message.get('tool_calls'):
                logger.info(f"Groq API调用成功 - 检测到工具调用")
                return {
                    "success": True,
                    "message": message,
                    "tool_calls": message['tool_calls'],
                    "provider": "groq",
                    "model": model,
                    "requires_tool_execution": True
                }
            else:
                ai_response = message.get('content', '')
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
    
    def transcribe_audio(self, audio_data: str, language: str = "zh") -> Dict:
        """使用OpenAI Whisper API将音频转换为文字"""
        if not self.openai_api_key:
            return {
                "success": False,
                "error": "OpenAI API密钥未配置，无法使用语音转文字功能",
                "fallback_available": True,
                "fallback_message": "建议使用浏览器内置的语音识别功能"
            }
        
        try:
            # 解析base64音频数据
            if not audio_data.startswith('data:audio/'):
                return {
                    "success": False,
                    "error": "无效的音频数据格式"
                }
            
            # 提取base64内容和MIME类型
            header, base64_content = audio_data.split(',', 1)
            mime_type = header.split(':')[1].split(';')[0]
            
            # 确定文件扩展名
            if 'webm' in mime_type:
                file_extension = 'webm'
            elif 'wav' in mime_type:
                file_extension = 'wav'
            elif 'mp3' in mime_type:
                file_extension = 'mp3'
            elif 'ogg' in mime_type:
                file_extension = 'ogg'
            else:
                file_extension = 'webm'  # 默认
            
            # 解码base64数据
            audio_bytes = base64.b64decode(base64_content)
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix=f'.{file_extension}', delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
            
            try:
                # 调用OpenAI Whisper API
                headers = {
                    "Authorization": f"Bearer {self.openai_api_key}"
                }
                
                with open(temp_file_path, 'rb') as audio_file:
                    files = {
                        'file': (f'audio.{file_extension}', audio_file, mime_type),
                        'model': (None, 'whisper-1'),
                        'language': (None, language),
                        'response_format': (None, 'json')
                    }
                    
                    response = requests.post(
                        self.openai_transcription_url,
                        headers=headers,
                        files=files,
                        timeout=30
                    )
                    
                response.raise_for_status()
                result = response.json()
                
                transcribed_text = result.get('text', '').strip()
                
                return {
                    "success": True,
                    "text": transcribed_text,
                    "language": language,
                    "duration": result.get('duration'),
                    "model": "whisper-1"
                }
                
            finally:
                # 清理临时文件
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"语音转文字错误: {e}")
            return {
                "success": False,
                "error": f"语音转文字失败: {str(e)}"
            }
    
    def transcribe_audio_fallback(self, audio_data: str, text: str = None) -> Dict:
        """备用的语音转文字方法，直接接收已转录的文本"""
        if not text:
            return {
                "success": False,
                "error": "没有提供转录文本",
                "fallback_used": True
            }
        
        return {
            "success": True,
            "text": text.strip(),
            "language": "auto",
            "model": "browser-speech-api",
            "fallback_used": True
        }
    
    def transcribe_audio_with_groq(self, audio_data: str, language: str = "zh") -> Dict:
        """使用Groq Speech-to-Text API将音频转换为文字"""
        if not self.groq_api_key:
            return {
                "success": False,
                "error": "Groq API密钥未配置，无法使用Groq语音转文字功能"
            }
        
        try:
            # 解析base64音频数据
            if not audio_data.startswith('data:audio/'):
                return {
                    "success": False,
                    "error": "无效的音频数据格式"
                }
            
            # 提取base64内容和MIME类型
            header, base64_content = audio_data.split(',', 1)
            mime_type = header.split(':')[1].split(';')[0]
            
            # 确定文件扩展名
            if 'webm' in mime_type:
                file_extension = 'webm'
            elif 'wav' in mime_type:
                file_extension = 'wav'
            elif 'mp3' in mime_type:
                file_extension = 'mp3'
            elif 'ogg' in mime_type:
                file_extension = 'ogg'
            else:
                file_extension = 'webm'  # 默认
            
            # 解码base64数据
            audio_bytes = base64.b64decode(base64_content)
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix=f'.{file_extension}', delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
            
            try:
                # 调用Groq Speech-to-Text API
                headers = {
                    "Authorization": f"Bearer {self.groq_api_key}"
                }
                
                with open(temp_file_path, 'rb') as audio_file:
                    files = {
                        'file': (f'audio.{file_extension}', audio_file, mime_type),
                        'model': (None, 'whisper-large-v3-turbo'),  # 使用Groq的快速模型
                        'language': (None, language if language != 'zh' else 'zh'),
                        'response_format': (None, 'json')
                    }
                    
                    response = requests.post(
                        'https://api.groq.com/openai/v1/audio/transcriptions',
                        headers=headers,
                        files=files,
                        timeout=30
                    )
                    
                response.raise_for_status()
                result = response.json()
                
                transcribed_text = result.get('text', '').strip()
                
                return {
                    "success": True,
                    "text": transcribed_text,
                    "language": language,
                    "duration": result.get('duration'),
                    "model": "groq-whisper-large-v3-turbo"
                }
                
            finally:
                # 清理临时文件
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Groq语音转文字错误: {e}")
            return {
                "success": False,
                "error": f"Groq语音转文字失败: {str(e)}"
            }
    
    def extract_video_frames(self, video_data: str, max_frames: int = 8) -> Dict:
        """从视频中智能提取关键帧和音频用于完整分析"""
        try:
            # 解析base64视频数据
            if not video_data.startswith('data:video/'):
                return {
                    "success": False,
                    "error": "无效的视频数据格式"
                }
            
            # 提取base64内容
            header, base64_content = video_data.split(',', 1)
            mime_type = header.split(':')[1].split(';')[0]
            
            # 确定文件扩展名
            if 'mp4' in mime_type:
                file_extension = 'mp4'
            elif 'webm' in mime_type:
                file_extension = 'webm'
            elif 'avi' in mime_type:
                file_extension = 'avi'
            else:
                file_extension = 'mp4'  # 默认
            
            # 解码base64数据
            video_bytes = base64.b64decode(base64_content)
            
            # 创建临时视频文件
            with tempfile.NamedTemporaryFile(suffix=f'.{file_extension}', delete=False) as temp_file:
                temp_file.write(video_bytes)
                temp_video_path = temp_file.name
            
            try:
                import cv2
                
                # 打开视频
                cap = cv2.VideoCapture(temp_video_path)
                if not cap.isOpened():
                    return {
                        "success": False,
                        "error": "无法打开视频文件"
                    }
                
                # 获取视频基本信息
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                duration = total_frames / fps if fps > 0 else 0
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                frames = []
                frame_analysis = []
                
                # 智能帧选择策略
                if total_frames > 0:
                    # 1. 开始帧 (第1秒)
                    start_frame = min(int(fps), total_frames - 1) if fps > 0 else 0
                    
                    # 2. 结束帧 (最后1秒)
                    end_frame = max(total_frames - int(fps), 0) if fps > 0 else total_frames - 1
                    
                    # 3. 中间均匀分布的帧
                    middle_frames = []
                    if total_frames > max_frames:
                        step = total_frames // (max_frames - 2)  # 减去开始和结束帧
                        middle_frames = [i * step for i in range(1, max_frames - 1)]
                    else:
                        middle_frames = list(range(1, total_frames - 1))
                    
                    # 4. 运动检测帧（每25%的位置采样检测）
                    motion_sample_frames = [
                        int(total_frames * 0.25),
                        int(total_frames * 0.5),
                        int(total_frames * 0.75)
                    ]
                    
                    # 合并所有帧索引并去重
                    all_frame_indices = list(set([start_frame] + middle_frames + [end_frame] + motion_sample_frames))
                    all_frame_indices = sorted([f for f in all_frame_indices if 0 <= f < total_frames])
                    
                    # 限制帧数
                    if len(all_frame_indices) > max_frames:
                        # 保留开始、结束和均匀分布的帧
                        step = len(all_frame_indices) // max_frames
                        all_frame_indices = all_frame_indices[::step][:max_frames]
                
                # 提取帧并进行基础分析
                prev_frame_gray = None
                for i, frame_idx in enumerate(all_frame_indices):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                    ret, frame = cap.read()
                    
                    if ret:
                        # 转换为base64格式
                        _, buffer = cv2.imencode('.jpg', frame)
                        frame_base64 = base64.b64encode(buffer).decode('utf-8')
                        frame_data_url = f"data:image/jpeg;base64,{frame_base64}"
                        frames.append(frame_data_url)
                        
                        # 计算时间戳
                        timestamp = frame_idx / fps if fps > 0 else frame_idx
                        
                        # 基础帧分析
                        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        
                        # 运动检测
                        motion_score = 0
                        if prev_frame_gray is not None:
                            diff = cv2.absdiff(frame_gray, prev_frame_gray)
                            motion_score = cv2.sumElems(diff)[0] / (width * height)
                        
                        # 亮度分析
                        brightness = cv2.mean(frame_gray)[0]
                        
                        # 边缘密度（场景复杂度）
                        edges = cv2.Canny(frame_gray, 50, 150)
                        edge_density = cv2.sumElems(edges)[0] / (width * height)
                        
                        frame_info = {
                            "index": frame_idx,
                            "timestamp": round(timestamp, 2),
                            "time_formatted": f"{int(timestamp//60):02d}:{int(timestamp%60):02d}",
                            "motion_score": round(motion_score, 2),
                            "brightness": round(brightness, 2),
                            "scene_complexity": round(edge_density, 2),
                            "position": "开始" if i == 0 else "结束" if i == len(all_frame_indices)-1 else f"中间{i}"
                        }
                        frame_analysis.append(frame_info)
                        prev_frame_gray = frame_gray
                
                cap.release()
                
                # 尝试提取音频信息
                audio_info = self._extract_video_audio_info(temp_video_path)
                
                # 生成视频分析摘要
                analysis_summary = self._generate_video_analysis_summary(
                    frame_analysis, duration, total_frames, fps, audio_info
                )
                
                return {
                    "success": True,
                    "frames": frames,
                    "frame_count": len(frames),
                    "total_frames": total_frames,
                    "duration": round(duration, 2),
                    "fps": round(fps, 2),
                    "resolution": f"{width}x{height}",
                    "frame_analysis": frame_analysis,
                    "audio_info": audio_info,
                    "analysis_summary": analysis_summary,
                    "video_stats": {
                        "avg_motion": round(sum(f["motion_score"] for f in frame_analysis) / len(frame_analysis), 2) if frame_analysis else 0,
                        "avg_brightness": round(sum(f["brightness"] for f in frame_analysis) / len(frame_analysis), 2) if frame_analysis else 0,
                        "scene_changes": len([f for f in frame_analysis if f["motion_score"] > 50])
                    }
                }
                
            finally:
                # 清理临时文件
                try:
                    os.unlink(temp_video_path)
                except:
                    pass
                    
        except ImportError:
            logger.warning("OpenCV未安装，无法提取视频帧。请运行: pip install opencv-python")
            return {
                "success": False,
                "error": "视频处理功能需要安装 opencv-python 库"
            }
        except Exception as e:
            logger.error(f"视频帧提取错误: {e}")
            return {
                "success": False,
                "error": f"视频帧提取失败: {str(e)}"
            }
    
    def _extract_video_audio_info(self, video_path: str) -> Dict:
        """提取视频中的音频信息"""
        try:
            import cv2
            
            # 检查视频是否包含音频
            cap = cv2.VideoCapture(video_path)
            
            # 尝试获取音频信息（OpenCV的限制，可能需要ffmpeg）
            audio_info = {
                "has_audio": False,
                "audio_extracted": False,
                "note": "需要ffmpeg支持完整音频提取"
            }
            
            cap.release()
            return audio_info
            
        except Exception as e:
            logger.warning(f"音频信息提取失败: {e}")
            return {
                "has_audio": False,
                "error": str(e)
            }
    
    def _generate_video_analysis_summary(self, frame_analysis: List[Dict], duration: float, 
                                       total_frames: int, fps: float, audio_info: Dict) -> str:
        """生成视频分析摘要"""
        if not frame_analysis:
            return "无法分析视频内容"
        
        # 分析运动模式
        motion_scores = [f["motion_score"] for f in frame_analysis]
        avg_motion = sum(motion_scores) / len(motion_scores)
        high_motion_frames = len([s for s in motion_scores if s > avg_motion * 1.5])
        
        # 分析亮度变化
        brightness_scores = [f["brightness"] for f in frame_analysis]
        brightness_range = max(brightness_scores) - min(brightness_scores)
        
        # 分析场景复杂度
        complexity_scores = [f["scene_complexity"] for f in frame_analysis]
        avg_complexity = sum(complexity_scores) / len(complexity_scores)
        
        summary_parts = []
        
        # 基本信息
        summary_parts.append(f"视频时长: {duration:.1f}秒")
        summary_parts.append(f"总帧数: {total_frames}帧")
        summary_parts.append(f"帧率: {fps:.1f}fps")
        
        # 运动分析
        if avg_motion < 20:
            summary_parts.append("视频内容相对静态")
        elif avg_motion < 50:
            summary_parts.append("视频包含适度运动")
        else:
            summary_parts.append("视频包含大量运动或场景变化")
        
        if high_motion_frames > len(frame_analysis) * 0.3:
            summary_parts.append("检测到多个高运动场景")
        
        # 亮度分析
        if brightness_range > 100:
            summary_parts.append("场景亮度变化明显，可能有不同环境或时间")
        elif brightness_range < 30:
            summary_parts.append("光照条件相对稳定")
        
        # 场景复杂度
        if avg_complexity > 0.1:
            summary_parts.append("场景内容丰富，包含较多细节")
        else:
            summary_parts.append("场景相对简单")
        
        # 音频信息
        if audio_info.get("has_audio"):
            summary_parts.append("视频包含音频内容")
        
        # 时序信息
        if len(frame_analysis) > 1:
            start_time = frame_analysis[0]["time_formatted"]
            end_time = frame_analysis[-1]["time_formatted"]
            summary_parts.append(f"分析时间范围: {start_time} - {end_time}")
        
        return "。".join(summary_parts) + "。"

# 初始化多模态聊天机器人服务和数据库
if not GROQ_API_KEY:
    logger.warning("Groq API密钥未配置，多模态功能将不可用")

chatbot_service = MultiModalChatBotService(SILICONFLOW_API_KEY, GROQ_API_KEY, OPENAI_API_KEY)
chat_db = ChatDatabase()

# 博查联网搜索服务类
class BochaSearchService:
    """博查联网搜索服务类"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or BOCHA_API_KEY
        self.base_url = "https://api.bochaai.com/v1/web-search"
        
    def search(self, query: str, count: int = 5, summary: bool = True, 
               freshness: str = "noLimit", include_images: bool = True) -> Dict:
        """
        使用博查API进行联网搜索
        
        Args:
            query: 搜索查询词
            count: 返回结果数量，默认5
            summary: 是否返回摘要，默认True
            freshness: 时间新鲜度，可选 oneDay, oneWeek, oneMonth, oneYear, noLimit
            include_images: 是否包含图片结果
            
        Returns:
            搜索结果字典
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "博查API密钥未配置",
                "results": []
            }
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "query": query,
            "count": count,
            "summary": summary,
            "freshness": freshness
        }
        
        try:
            logger.info(f"开始博查搜索: {query}")
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"博查API响应状态: code={data.get('code')}, msg={data.get('msg')}")
            
            # 检查API响应状态
            if not isinstance(data, dict):
                raise ValueError(f"API返回数据格式错误: {type(data)}")
            
            # 检查博查API的响应代码
            if data.get('code') != 200:
                raise ValueError(f"博查API返回错误: code={data.get('code')}, msg={data.get('msg')}")
                
            # 获取实际数据
            api_data = data.get('data', {})
            if not isinstance(api_data, dict):
                raise ValueError(f"API数据字段格式错误: {type(api_data)}")
            
            # 解析搜索结果
            web_pages = []
            images = []
            
            # 解析网页结果
            web_pages_data = api_data.get('webPages', {})
            if isinstance(web_pages_data, dict):
                web_pages = web_pages_data.get('value', [])
            
            # 解析图片结果 
            if include_images:
                images_data = api_data.get('images', {})
                if isinstance(images_data, dict):
                    images = images_data.get('value', [])
            
            # 格式化结果
            formatted_results = []
            for item in web_pages:
                if isinstance(item, dict):
                    formatted_results.append({
                        "title": item.get('name', item.get('title', '')),
                        "url": item.get('url', item.get('link', '')),
                        "snippet": item.get('snippet', item.get('description', item.get('summary', ''))),
                        "summary": item.get('summary', item.get('snippet', '')),
                        "siteName": item.get('siteName', item.get('source', '')),
                        "publishedDate": item.get('datePublished', item.get('date', ''))
                    })
            
            # 格式化图片结果
            image_results = []
            for img in images[:3]:  # 限制图片数量
                if isinstance(img, dict):
                    image_results.append({
                        "thumbnailUrl": img.get('thumbnailUrl', img.get('thumbnail', '')),
                        "contentUrl": img.get('contentUrl', img.get('url', '')),
                        "name": img.get('name', img.get('title', ''))
                    })
            
            logger.info(f"博查搜索成功，获得{len(formatted_results)}个网页结果，{len(image_results)}个图片结果")
            
            return {
                "success": True,
                "query": query,
                "results": formatted_results,
                "images": image_results,
                "total_count": len(formatted_results),
                "search_provider": "博查AI"
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"博查搜索API请求失败: {e}")
            return {
                "success": False,
                "error": f"搜索请求失败: {str(e)}",
                "results": []
            }
        except Exception as e:
            logger.error(f"博查搜索处理失败: {e}")
            return {
                "success": False,
                "error": f"搜索处理失败: {str(e)}",
                "results": []
            }
    
    def format_search_results_for_ai(self, search_result: Dict, max_results: int = 5) -> str:
        """
        将搜索结果格式化为适合AI深度理解和分析的Markdown格式文本
        
        Args:
            search_result: 搜索结果字典
            max_results: 最大结果数量
            
        Returns:
            格式化的Markdown搜索结果文本，包含详细内容供AI分析
        """
        if not search_result.get("success"):
            return f"搜索失败: {search_result.get('error', '未知错误')}"
        
        results = search_result.get("results", [])
        query = search_result.get("query", "")
        
        if not results:
            return f"对于查询 '{query}' 没有找到相关搜索结果。"
        
        # 构建Markdown格式的搜索结果供AI分析
        formatted_text = f"""# 🔍 联网搜索结果

**查询关键词:** {query}  
**搜索时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**搜索引擎:** {search_result.get('search_provider', '博查AI')}  
**结果总数:** {search_result.get('total_count', len(results))}

## 📊 搜索结果详情

| 序号 | 来源网站 | 发布时间 | 标题 |
|------|----------|----------|------|"""
        
        # 构建表格内容
        for i, result in enumerate(results[:max_results], 1):
            title = result.get("title", "无标题")
            site_name = result.get("siteName", "未知来源")
            publish_date = result.get("publishedDate", "未知时间")
            
            # 清理标题中可能包含的管道符号，避免破坏表格格式
            title_clean = title.replace('|', '&#124;')[:50] + ('...' if len(title) > 50 else '')
            
            formatted_text += f"\n| {i} | {site_name} | {publish_date} | {title_clean} |"
        
        formatted_text += "\n\n"
        
        # 详细处理每个搜索结果
        for i, result in enumerate(results[:max_results], 1):
            title = result.get("title", "无标题")
            snippet = result.get("snippet", "")
            summary = result.get("summary", "")
            url = result.get("url", "")
            site_name = result.get("siteName", "")
            publish_date = result.get("publishedDate", "")
            
            formatted_text += f"""### {i}. {title}

**来源网站:** {site_name}  
**发布时间:** {publish_date}  
**链接:** [{url}]({url})

**内容摘要:**
{summary if summary else snippet}

"""
            if snippet and summary:
                formatted_text += f"""**详细描述:**
{snippet}

"""
        
        # 添加AI分析指导
        analysis_guide = """---

## 🤖 AI分析指导

请基于以上搜索结果，按照以下要求进行分析：

1. **📋 提取关键信息和数据**
2. **📊 整理成结构化的格式**（如表格、列表等）
3. **🔍 区分事实信息和观点**
4. **📚 提供准确的来源引用**  
5. **💹 如果涉及数据或价格信息，请组织成清晰的表格形式**
6. **📝 总结最重要的发现和结论**

> **注意:** 以上信息来自实时搜索，请确保回答的准确性和时效性。

**📝 格式要求:**
- 使用 **Markdown 格式** 回复，包括标题、表格、列表、链接等
- 对于数据和价格信息，**必须使用表格格式**呈现
- 使用适当的标题层级（##、###）组织内容
- 重要信息使用 **粗体** 强调
- 引用来源时使用链接格式：[来源名称](链接地址)
- 使用无序列表（-）或有序列表（1.）来组织要点

**示例格式:**
## 📊 价格信息

| 来源网站 | 发布时间 | 价格（元/克） |
|----------|----------|---------------|
| 网站A | 2024-XX-XX | XXX |
| 网站B | 2024-XX-XX | XXX |

## 🔢 数学计算与公式（如需要）

对于涉及数学概念或计算的问题，请使用适当的数学表达：

**行内公式示例：**
- 平均价格：\\( \\bar{x} = \\frac{1}{n}\\sum_{i=1}^{n}x_i \\)
- 增长率：\\( r = \\frac{V_f - V_i}{V_i} \\times 100\\% \\)

**块级公式示例：**

\\[
\\text{泰勒展开式} = f(a) + f'(a)(x-a) + \\frac{f''(a)}{2!}(x-a)^2 + \\cdots
\\]

**数学概念解释格式：**
- 使用 \\( \\) 包围行内数学符号
- 使用 \\[ \\] 包围重要的块级公式
- 为公式中的符号提供清晰的说明

## 📝 分析结论

1. **价格趋势:** ...
2. **主要发现:** ...

## 📚 参考来源

1. [来源1](链接1)
2. [来源2](链接2)
"""
        formatted_text += analysis_guide
        
        return formatted_text

# 初始化博查搜索服务
bocha_search_service = BochaSearchService()

class FunctionCallExecutor:
    """Function Calling执行器"""
    
    def __init__(self, bocha_search_service: BochaSearchService):
        self.bocha_search_service = bocha_search_service
    
    def get_available_tools(self) -> List[Dict]:
        """获取可用的工具定义"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "搜索互联网获取实时信息，包括新闻、价格、天气、股价等最新数据。适用于需要获取当前信息的问题。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索查询词，应该简洁明确，例如：'黄金价格'、'上海天气'、'特斯拉股价'等"
                            },
                            "count": {
                                "type": "integer",
                                "description": "返回搜索结果的数量，默认为6，最大为10",
                                "default": 6
                            },
                            "freshness": {
                                "type": "string",
                                "description": "搜索结果的时效性要求",
                                "enum": ["noLimit", "day", "week", "month"],
                                "default": "week"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
    
    def execute_function(self, function_name: str, arguments: Dict) -> Dict:
        """执行函数调用"""
        try:
            if function_name == "web_search":
                return self._execute_web_search(arguments)
            else:
                return {
                    "success": False,
                    "error": f"未知的函数: {function_name}"
                }
        except Exception as e:
            logger.error(f"执行函数 {function_name} 时出错: {e}")
            return {
                "success": False,
                "error": f"函数执行错误: {str(e)}"
            }
    
    def _execute_web_search(self, arguments: Dict) -> Dict:
        """执行网络搜索"""
        query = arguments.get("query", "")
        count = arguments.get("count", 6)
        freshness = arguments.get("freshness", "week")
        
        if not query:
            return {
                "success": False,
                "error": "搜索查询不能为空"
            }
        
        # 执行搜索
        search_result = self.bocha_search_service.search(
            query=query,
            count=min(count, 10),  # 限制最大数量
            freshness=freshness,
            include_images=False,
            summary=True
        )
        
        if search_result.get('success'):
            # 格式化搜索结果
            formatted_text = self.bocha_search_service.format_search_results_for_ai(
                search_result, 
                max_results=count
            )
            return {
                "success": True,
                "result": formatted_text,
                "raw_results": search_result['results'][:count],
                "total_count": search_result.get('total_count', 0)
            }
        else:
            return {
                "success": False,
                "error": search_result.get('error', '搜索失败')
            }

# 初始化Function Calling执行器
function_executor = FunctionCallExecutor(bocha_search_service)

def _preprocess_multimedia_messages(messages: List[Dict]) -> List[Dict]:
    """
    预处理多媒体消息，提取可分析的信息
    将音频转录为文本，视频提取关键帧等
    """
    # 处理None或空输入
    if not messages:
        return []
    
    processed_messages = []
    
    for msg in messages:
        # 创建消息的副本以避免修改原始数据
        processed_msg = dict(msg)
        
        # 确保基本字段存在
        if 'role' not in processed_msg:
            processed_msg['role'] = 'user'  # 默认为用户角色
        if 'text' not in processed_msg:
            processed_msg['text'] = ''  # 默认为空文本
        
        if msg.get('role') == 'user':
            additional_text = []
            has_multimedia = False
            
            # 处理音频内容 - 使用Groq Speech-to-Text API进行转录
            if msg.get('audio'):
                has_multimedia = True
                try:
                    # 使用Groq的Speech-to-Text API进行转录
                    transcription_result = chatbot_service.transcribe_audio_with_groq(msg['audio'], 'zh')
                    if transcription_result['success']:
                        transcribed_text = transcription_result['text']
                        if transcribed_text.strip():
                            additional_text.append(f"用户语音内容：\"{transcribed_text}\"")
                            additional_text.append("请分析用户的语音内容，并根据语音的语调和情感提供适当的回应。")
                            logger.info(f"Groq音频转录成功: {transcribed_text[:50]}...")
                        else:
                            additional_text.append("用户提供了一个音频文件，但未能识别到清晰的语音内容。")
                    else:
                        # 如果Groq转录失败，尝试使用OpenAI Whisper作为备选
                        fallback_result = chatbot_service.transcribe_audio(msg['audio'], 'zh')
                        if fallback_result['success']:
                            transcribed_text = fallback_result['text']
                            additional_text.append(f"用户语音内容：\"{transcribed_text}\"")
                            logger.info(f"OpenAI Whisper备选转录成功: {transcribed_text[:50]}...")
                        else:
                            additional_text.append("用户提供了一个音频文件，请根据用户的文字描述来分析音频内容。")
                            logger.warning(f"所有音频转录方法都失败了")
                except Exception as e:
                    additional_text.append("用户提供了一个音频文件，请根据用户的描述来分析。")
                    logger.error(f"音频处理错误: {e}")
                
                # 移除音频数据
                processed_msg.pop('audio', None)
            
            # 处理视频内容 - 提取视频帧进行分析
            if msg.get('video'):
                has_multimedia = True
                try:
                    # 尝试从视频中提取关键帧和进行完整分析
                    frame_result = chatbot_service.extract_video_frames(msg['video'], max_frames=8)
                    if frame_result['success'] and frame_result.get('frames'):
                        # 将提取的第一帧作为主要图片添加到消息中
                        processed_msg['image'] = frame_result['frames'][0]
                        
                        # 生成详细的视频分析提示
                        video_analysis_text = []
                        video_analysis_text.append(f"用户提供了一个视频文件，我已经进行了完整的视频分析：")
                        
                        # 基本信息
                        video_analysis_text.append(f"📊 视频信息：{frame_result.get('analysis_summary', '无法生成摘要')}")
                        
                        # 帧分析详情
                        frame_analysis = frame_result.get('frame_analysis', [])
                        if frame_analysis:
                            video_analysis_text.append(f"🎬 关键帧分析（共{len(frame_analysis)}帧）：")
                            for i, frame_info in enumerate(frame_analysis[:3]):  # 显示前3帧的详细信息
                                time_info = frame_info.get('time_formatted', '未知')
                                position = frame_info.get('position', '未知位置')
                                motion = frame_info.get('motion_score', 0)
                                brightness = frame_info.get('brightness', 0)
                                
                                motion_desc = "静态" if motion < 20 else "中等运动" if motion < 50 else "高运动"
                                light_desc = "较暗" if brightness < 80 else "适中" if brightness < 180 else "较亮"
                                
                                video_analysis_text.append(f"  • {time_info}（{position}）- {motion_desc}，光线{light_desc}")
                        
                        # 视频统计
                        video_stats = frame_result.get('video_stats', {})
                        if video_stats:
                            avg_motion = video_stats.get('avg_motion', 0)
                            scene_changes = video_stats.get('scene_changes', 0)
                            video_analysis_text.append(f"📈 运动统计：平均运动强度{avg_motion}，场景变化{scene_changes}次")
                        
                        # 分析建议
                        video_analysis_text.append("请基于以上视频分析信息和提供的关键帧图像，进行全面的视频内容分析。")
                        video_analysis_text.append("重点关注：1）视频的时序发展 2）场景变化 3）运动模式 4）整体故事情节。")
                        
                        additional_text.extend(video_analysis_text)
                        logger.info(f"完整视频分析成功，提取{len(frame_analysis)}帧，时长{frame_result.get('duration', 0)}秒")
                    else:
                        # 视频分析失败的降级处理
                        additional_text.append("用户提供了一个视频文件，但无法进行完整的视频分析。")
                        additional_text.append("请根据用户的文字描述来分析视频内容。")
                        additional_text.append("建议用户详细描述视频中的：1）主要场景 2）人物动作 3）时间顺序 4）关键事件。")
                        logger.warning(f"视频分析失败: {frame_result.get('error', '未知错误')}")
                except Exception as e:
                    additional_text.append("用户提供了一个视频文件，请根据用户的文字描述来分析视频内容。")
                    logger.error(f"视频处理错误: {e}")
                
                # 移除视频数据
                processed_msg.pop('video', None)
            
            # 合并文本内容
            if additional_text:
                original_text = processed_msg.get('text', '')
                if original_text:
                    processed_msg['text'] = f"{original_text}\n\n{' '.join(additional_text)}"
                else:
                    processed_msg['text'] = ' '.join(additional_text)
            
            # 如果有多媒体内容但没有文字描述，添加智能提示
            if has_multimedia and not msg.get('text', '').strip():
                if msg.get('audio'):
                    processed_msg['text'] += "\n\n请基于我的语音内容提供帮助和建议。"
                if msg.get('video'):
                    if msg.get('image'):  # 如果成功提取了视频帧
                        processed_msg['text'] += "\n\n请分析这个视频画面中的内容。"
                    else:
                        processed_msg['text'] += "\n\n请告诉我您想了解这个视频的哪些方面？"
        
        processed_messages.append(processed_msg)
    
    return processed_messages

def preprocess_chinese_date_terms(text: str) -> str:
    """
    预处理中文日期词汇，将"今日"、"昨日"等词汇转换为具体日期
    
    Args:
        text: 原始文本
        
    Returns:
        处理后的文本，中文日期词汇已被替换为具体日期
    """
    if not text:
        return text
    
    # 获取当前时间
    now = datetime.now()
    today = now.date()
    
    processed_text = text
    
    # 处理相对日期表达 (如: 3天前, 2天后)
    relative_patterns = [
        (r'(\d+)\s*天前', lambda m: (today - timedelta(days=int(m.group(1)))).strftime('%Y年%m月%d日')),
        (r'(\d+)\s*天后', lambda m: (today + timedelta(days=int(m.group(1)))).strftime('%Y年%m月%d日')),
        (r'(\d+)\s*周前', lambda m: (today - timedelta(weeks=int(m.group(1)))).strftime('%Y年%m月%d日')),
        (r'(\d+)\s*周后', lambda m: (today + timedelta(weeks=int(m.group(1)))).strftime('%Y年%m月%d日')),
        (r'(\d+)\s*个月前', lambda m: (today - timedelta(days=int(m.group(1)) * 30)).strftime('%Y年%m月%d日')),
        (r'(\d+)\s*个月后', lambda m: (today + timedelta(days=int(m.group(1)) * 30)).strftime('%Y年%m月%d日')),
    ]
    
    for pattern, replacement_func in relative_patterns:
        def replace_match(match):
            original = match.group(0)
            converted_date = replacement_func(match)
            return f"{original}({converted_date})"
        
        processed_text = re.sub(pattern, replace_match, processed_text)
    
    # 简单的词汇映射，使用一次性替换避免重复
    simple_mappings = [
        ('今日', today.strftime('%Y年%m月%d日')),
        ('今天', today.strftime('%Y年%m月%d日')),
        ('今儿', today.strftime('%Y年%m月%d日')),
        ('今儿个', today.strftime('%Y年%m月%d日')),
        ('昨日', (today - timedelta(days=1)).strftime('%Y年%m月%d日')),
        ('昨天', (today - timedelta(days=1)).strftime('%Y年%m月%d日')),
        ('昨儿', (today - timedelta(days=1)).strftime('%Y年%m月%d日')),
        ('昨儿个', (today - timedelta(days=1)).strftime('%Y年%m月%d日')),
        ('明日', (today + timedelta(days=1)).strftime('%Y年%m月%d日')),
        ('明天', (today + timedelta(days=1)).strftime('%Y年%m月%d日')),
        ('明儿', (today + timedelta(days=1)).strftime('%Y年%m月%d日')),
        ('明儿个', (today + timedelta(days=1)).strftime('%Y年%m月%d日')),
        ('前日', (today - timedelta(days=2)).strftime('%Y年%m月%d日')),
        ('前天', (today - timedelta(days=2)).strftime('%Y年%m月%d日')),
        ('后日', (today + timedelta(days=2)).strftime('%Y年%m月%d日')),
        ('后天', (today + timedelta(days=2)).strftime('%Y年%m月%d日')),
        ('本周', f"本周({today.strftime('%Y年%m月%d日')}这一周)"),
        ('这周', f"这周({today.strftime('%Y年%m月%d日')}这一周)"),
        ('这一周', f"这一周({today.strftime('%Y年%m月%d日')}这一周)"),
        ('上周', f"上周({(today - timedelta(days=7)).strftime('%Y年%m月%d日')}那一周)"),
        ('上一周', f"上一周({(today - timedelta(days=7)).strftime('%Y年%m月%d日')}那一周)"),
        ('下周', f"下周({(today + timedelta(days=7)).strftime('%Y年%m月%d日')}那一周)"),
        ('下一周', f"下一周({(today + timedelta(days=7)).strftime('%Y年%m月%d日')}那一周)"),
        ('本月', today.strftime('%Y年%m月')),
        ('这个月', today.strftime('%Y年%m月')),
        ('上月', (today.replace(day=1) - timedelta(days=1)).strftime('%Y年%m月')),
        ('上个月', (today.replace(day=1) - timedelta(days=1)).strftime('%Y年%m月')),
        ('下月', (today.replace(day=28) + timedelta(days=4)).replace(day=1).strftime('%Y年%m月')),
        ('下个月', (today.replace(day=28) + timedelta(days=4)).replace(day=1).strftime('%Y年%m月')),
        ('现在', now.strftime('%Y年%m月%d日 %H:%M')),
        ('此时', now.strftime('%Y年%m月%d日 %H:%M')),
        ('当前', now.strftime('%Y年%m月%d日 %H:%M')),
        ('目前', now.strftime('%Y年%m月%d日 %H:%M')),
    ]
    
    # 按照词汇长度从长到短排序，避免短词汇先匹配导致长词汇无法匹配
    simple_mappings.sort(key=lambda x: len(x[0]), reverse=True)
    
    for chinese_term, replacement in simple_mappings:
        if chinese_term in processed_text:
            processed_text = processed_text.replace(chinese_term, replacement)
    
    # 处理星期相关
    weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    chinese_weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
    
    current_weekday = today.weekday()  # 0=Monday, 6=Sunday
    
    for i, (short_name, long_name) in enumerate(zip(weekdays, chinese_weekdays)):
        days_diff = i - current_weekday
        target_date = today + timedelta(days=days_diff)
        date_str = target_date.strftime('%Y年%m月%d日')
        
        # 如果是本周的某一天，标注为本周
        if abs(days_diff) <= 3:  # 前后3天内认为是本周
            week_indicator = "本周" if days_diff >= 0 else "上周" if days_diff < -3 else "本周"
            if short_name in processed_text:
                processed_text = processed_text.replace(short_name, f"{short_name}({week_indicator}{date_str})")
            if long_name in processed_text:
                processed_text = processed_text.replace(long_name, f"{long_name}({week_indicator}{date_str})")
    
    return processed_text

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
    """处理聊天请求，支持Function Calling"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': '无效的请求数据'
            }), 400
        
        messages = data.get('messages', [])
        model = data.get('model', 'deepseek-ai/DeepSeek-V2.5')
        session_id = data.get('session_id')  # 可选的会话ID
        system_prompt = data.get('system_prompt')  # 系统提示
        temperature = data.get('temperature', 0.7)  # 温度参数
        enable_search = data.get('enable_search', True)  # 是否启用搜索功能
        
        if not messages:
            return jsonify({
                'success': False,
                'error': '消息不能为空'
            }), 400
        
        # 验证temperature参数
        if not isinstance(temperature, (int, float)) or not (0 <= temperature <= 2):
            temperature = 0.7
        
        # 获取最后一条用户消息用于存储
        last_user_message = None
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                last_user_message = msg
                break
        
        # 预处理用户消息中的日期词汇
        for message in messages:
            if message.get('role') == 'user' and message.get('text'):
                original_text = message['text']
                processed_text = preprocess_chinese_date_terms(original_text)
                if processed_text != original_text:
                    message['text'] = processed_text
                    logger.info(f"日期预处理: '{original_text}' -> '{processed_text}'")
        
        # 预处理多媒体内容，提取可分析的信息
        processed_messages = _preprocess_multimedia_messages(messages)
        
        # 如果启用搜索，使用智能判断模式
        if enable_search:
            # 先让AI判断是否需要搜索
            enhanced_system_prompt = """你是一个智能助手，可以选择性地使用网络搜索来回答问题。具备优雅的ChatGPT式回答风格。

🎯 判断规则：
如果问题涉及以下内容，请回复"SEARCH_REQUIRED:"后跟搜索关键词：
- 实时信息（如当前时间、日期、价格、股价、汇率）
- 最新新闻、事件
- 天气信息
- 体育赛事结果
- 产品价格、市场行情
- 当前政策法规
- 最新技术发展

如果是一般知识、编程帮助、创意写作、数学概念等不需要实时信息的内容，请直接回答。

📝 对于数学/科学概念，请使用以下格式：

**CRITICAL: 直接使用LaTeX分隔符，不要使用任何占位符！**

## 📚 概念定义
[简洁清晰的定义]

## 🔢 数学表达

$$
[在这里写完整的LaTeX公式，不要使用占位符]
$$

其中：
- \\( 具体符号 \\) 表示具体含义
- \\( 具体符号 \\) 表示具体含义

## 💡 直观理解
[用通俗易懂的语言和比喻解释]

## 📖 经典例子
| 函数 | 展开式 | 特点 | 应用 |
|------|--------|------|------|
| \\( e^x \\) | \\( 1 + x + \\frac{x^2}{2!} + \\frac{x^3}{3!} + \\cdots \\) | 收敛快 | 指数增长 |

## 🚀 实际应用
- **领域1**: 具体应用说明
- **领域2**: 具体应用说明

## 💭 深入思考
[启发性的思考点或相关概念]

**重要提示**: 
- 必须使用 \\( \\) 包围行内数学公式
- 必须使用 $$ $$ 包围块级数学公式（前后换行）
- 绝对不要使用MATH_LATEX_BLOCK_X或MATH_LATEX_INLINE_X这样的占位符
- 直接输出LaTeX代码

示例：
用户："黄金价格是多少" → 回复："SEARCH_REQUIRED:黄金价格"
用户："什么是泰勒展开式" → 直接用上述格式详细回答
用户："今天天气怎么样" → 回复："SEARCH_REQUIRED:今天天气"
用户："写一首诗" → 直接创作诗歌"""
            
            # 使用增强的系统提示
            final_system_prompt = enhanced_system_prompt if not system_prompt else f"{enhanced_system_prompt}\n\n{system_prompt}"
            
            # 获取AI判断
            result = chatbot_service.get_response(processed_messages, model, final_system_prompt, temperature)
            
            if not result['success']:
                # AI判断失败，返回错误
                return jsonify({
                    'success': False,
                    'error': f'AI判断失败: {result.get("error")}'
                }), 500
            
            if result['success']:
                response_text = result['response']
                
                # 检查AI是否指示需要搜索
                if response_text.startswith("SEARCH_REQUIRED:"):
                    search_query = response_text.replace("SEARCH_REQUIRED:", "").strip()
                    logger.info(f"AI判断需要搜索: {search_query}")
                    
                    # 执行搜索
                    search_result = function_executor.execute_function("web_search", {"query": search_query})
                    
                    if search_result['success']:
                        # 构建包含搜索结果的新消息
                        search_enhanced_messages = processed_messages.copy()
                        search_enhanced_messages.append({
                            "role": "assistant", 
                            "text": f"我需要搜索 '{search_query}' 来回答您的问题。"
                        })
                        search_enhanced_messages.append({
                            "role": "system", 
                            "text": f"搜索结果：\n{search_result['result']}\n\n请基于以上搜索结果回答用户的问题，提供准确、详细的信息。如果涉及价格数据，请整理成表格格式。"
                        })
                        
                        # 重新生成最终回复
                        final_result = chatbot_service.get_response(search_enhanced_messages, model, system_prompt, temperature)
                        
                        if final_result['success']:
                            # 保存消息到数据库
                            if session_id and last_user_message:
                                _save_chat_messages(session_id, last_user_message, final_result, model)
                            
                            return jsonify({
                                'success': True,
                                'response': final_result['response'],
                                'provider': final_result.get('provider'),
                                'model': final_result.get('model'),
                                'session_id': session_id,
                                'search_performed': True,
                                'search_query': search_query
                            })
                        else:
                            return jsonify({
                                'success': False,
                                'error': f'搜索后生成回复失败: {final_result.get("error")}'
                            }), 500
                    else:
                        # 搜索失败，返回提示
                        fallback_response = f"我认为需要搜索 '{search_query}' 来回答您的问题，但搜索功能暂时不可用。请稍后再试，或者您可以提供更多具体信息。"
                        
                        if session_id and last_user_message:
                            _save_chat_messages(session_id, last_user_message, {'response': fallback_response}, model)
                        
                        return jsonify({
                            'success': True,
                            'response': fallback_response,
                            'provider': result.get('provider'),
                            'model': result.get('model'),
                            'session_id': session_id,
                            'search_attempted': True,
                            'search_failed': True
                        })
                else:
                    # AI直接回答，不需要搜索
                    if session_id and last_user_message:
                        _save_chat_messages(session_id, last_user_message, result, model)
                    
                    return jsonify({
                        'success': True,
                        'response': result['response'],
                        'provider': result.get('provider'),
                        'model': result.get('model'),
                        'session_id': session_id,
                        'search_performed': False
                    })
        else:
            # 不启用搜索，使用原始系统提示
            result = chatbot_service.get_response(processed_messages, model, system_prompt, temperature)
            
            if result['success']:
                # 普通回复，保存消息到数据库
                if session_id and last_user_message:
                    _save_chat_messages(session_id, last_user_message, result, model)
                
                return jsonify({
                    'success': True,
                    'response': result['response'],
                    'provider': result.get('provider'),
                    'model': result.get('model'),
                    'session_id': session_id
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

def _handle_tool_calls(result: Dict, messages: List[Dict], model: str, system_prompt: str, temperature: float, session_id: str = None) -> Dict:
    """处理工具调用"""
    try:
        tool_calls = result.get('tool_calls', [])
        tool_results = []
        
        # 执行所有工具调用
        for tool_call in tool_calls:
            function_name = tool_call['function']['name']
            arguments = json.loads(tool_call['function']['arguments'])
            
            logger.info(f"执行工具调用: {function_name}, 参数: {arguments}")
            
            # 执行工具
            tool_result = function_executor.execute_function(function_name, arguments)
            
            # 构建工具结果消息
            tool_message = {
                "role": "tool",
                "tool_call_id": tool_call['id'],
                "content": json.dumps(tool_result, ensure_ascii=False) if tool_result['success'] else f"工具执行失败: {tool_result['error']}"
            }
            tool_results.append(tool_message)
        
        # 构建包含工具结果的消息序列
        enhanced_messages = messages.copy()
        enhanced_messages.append(result['message'])  # AI的工具调用消息
        enhanced_messages.extend(tool_results)  # 工具执行结果
        
        # 重新调用AI获取最终回复
        final_result = chatbot_service.get_response(enhanced_messages, model, system_prompt, temperature)
        
        if final_result['success']:
            # 保存完整的对话历史
            if session_id:
                # 保存用户消息
                last_user_message = None
                for msg in reversed(messages):
                    if msg.get('role') == 'user':
                        last_user_message = msg
                        break
                
                if last_user_message:
                    _save_chat_messages(session_id, last_user_message, final_result, model)
            
            return {
                'success': True,
                'response': final_result['response'],
                'provider': final_result.get('provider'),
                'model': final_result.get('model'),
                'session_id': session_id,
                'tool_calls_executed': len(tool_calls),
                'search_performed': any(tc['function']['name'] == 'web_search' for tc in tool_calls)
            }
        else:
            return {
                'success': False,
                'error': f'获取最终回复失败: {final_result.get("error")}',
                'tool_calls_executed': len(tool_calls)
            }
            
    except Exception as e:
        logger.error(f"处理工具调用错误: {e}")
        return {
            'success': False,
            'error': f'工具调用处理失败: {str(e)}'
        }

def _save_chat_messages(session_id: str, last_user_message: Dict, result: Dict, model: str):
    """保存聊天消息到数据库"""
    try:
        # 保存用户消息
        user_content = last_user_message.get('text', '')
        user_image = last_user_message.get('image')
        user_audio = last_user_message.get('audio')
        user_video = last_user_message.get('video')
        
        # 确定内容类型
        if user_image:
            content_type = 'image'
            media_data = user_image
        elif user_audio:
            content_type = 'audio'
            media_data = user_audio
        elif user_video:
            content_type = 'video'
            media_data = user_video
        else:
            content_type = 'text'
            media_data = None
        
        # 获取文件信息
        file_name = None
        file_size = None
        if user_audio or user_video:
            # 从data URL中提取文件大小（粗略估算）
            if media_data:
                try:
                    # 从base64数据中估算文件大小
                    base64_data = media_data.split(',')[1] if ',' in media_data else media_data
                    file_size = len(base64_data) * 3 // 4  # base64解码后的大小
                except:
                    pass
        
        chat_db.add_message(
            session_id=session_id,
            role='user',
            content=user_content,
            content_type=content_type,
            image_data=media_data,  # 现在用于存储所有类型的媒体数据
            model=model,
            file_name=file_name,
            file_size=file_size
        )
        
        # 保存AI回复
        chat_db.add_message(
            session_id=session_id,
            role='assistant',
            content=result['response'],
            content_type='text',
            model=result.get('model'),
            provider=result.get('provider')
        )
    except Exception as e:
        logger.error(f"保存聊天消息失败: {e}")

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

@app.route('/api/upload/audio', methods=['POST'])
def upload_audio():
    """处理音频上传"""
    try:
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有找到音频文件'
            }), 400
        
        file = request.files['audio']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '没有选择文件'
            }), 400
        
        # 检查文件类型
        allowed_extensions = {'mp3', 'wav', 'ogg', 'm4a', 'aac', 'flac', 'webm'}
        if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return jsonify({
                'success': False,
                'error': '不支持的音频格式，请上传 MP3、WAV、OGG、M4A、AAC、FLAC 或 WebM 格式的音频'
            }), 400
        
        # 检查文件大小 (10MB限制)
        file.seek(0, 2)  # 移到文件末尾
        file_size = file.tell()
        file.seek(0)  # 回到文件开头
        
        if file_size > 10 * 1024 * 1024:  # 10MB
            return jsonify({
                'success': False,
                'error': f'音频文件过大 ({file_size / 1024 / 1024:.1f}MB)，最大支持10MB'
            }), 400
        
        # 读取文件并转换为base64
        file_content = file.read()
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        # 获取文件MIME类型
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        mime_type = f"audio/{file_extension if file_extension != 'm4a' else 'mp4'}"
        
        # 构造data URL
        data_url = f"data:{mime_type};base64,{file_base64}"
        
        return jsonify({
            'success': True,
            'audio_data': data_url,
            'file_size': file_size,
            'file_name': file.filename,
            'duration': None  # TODO: 可以使用librosa或ffmpeg获取音频时长
        })
        
    except Exception as e:
        logger.error(f"音频上传错误: {e}")
        return jsonify({
            'success': False,
            'error': f'音频上传失败: {str(e)}'
        }), 500

@app.route('/api/upload/video', methods=['POST'])
def upload_video():
    """处理视频上传"""
    try:
        if 'video' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有找到视频文件'
            }), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '没有选择文件'
            }), 400
        
        # 检查文件类型
        allowed_extensions = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv'}
        if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return jsonify({
                'success': False,
                'error': '不支持的视频格式，请上传 MP4、AVI、MOV、WMV、FLV、WebM 或 MKV 格式的视频'
            }), 400
        
        # 检查文件大小 (50MB限制)
        file.seek(0, 2)  # 移到文件末尾
        file_size = file.tell()
        file.seek(0)  # 回到文件开头
        
        if file_size > 50 * 1024 * 1024:  # 50MB
            return jsonify({
                'success': False,
                'error': f'视频文件过大 ({file_size / 1024 / 1024:.1f}MB)，最大支持50MB'
            }), 400
        
        # 读取文件并转换为base64
        file_content = file.read()
        file_base64 = base64.b64encode(file_content).decode('utf-8')
        
        # 获取文件MIME类型
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        mime_type = f"video/{file_extension}"
        
        # 构造data URL
        data_url = f"data:{mime_type};base64,{file_base64}"
        
        return jsonify({
            'success': True,
            'video_data': data_url,
            'file_size': file_size,
            'file_name': file.filename,
            'duration': None  # TODO: 可以使用ffmpeg获取视频时长
        })
        
    except Exception as e:
        logger.error(f"视频上传错误: {e}")
        return jsonify({
            'success': False,
            'error': f'视频上传失败: {str(e)}'
        }), 500

@app.route('/api/upload/record', methods=['POST'])
def upload_recording():
    """处理录音上传并转换为文字"""
    try:
        data = request.get_json()
        if not data or 'audio_data' not in data:
            return jsonify({
                'success': False,
                'error': '没有找到音频数据'
            }), 400
        
        audio_data = data['audio_data']
        language = data.get('language', 'zh')  # 默认中文
        transcribe = data.get('transcribe', True)  # 是否转录，默认为True
        client_transcript = data.get('transcript')  # 客户端提供的转录文本
        
        # 验证base64数据
        if not audio_data.startswith('data:audio/'):
            return jsonify({
                'success': False,
                'error': '无效的音频数据格式'
            }), 400
        
        # 提取base64内容
        try:
            header, base64_content = audio_data.split(',', 1)
            audio_bytes = base64.b64decode(base64_content)
            file_size = len(audio_bytes)
        except Exception:
            return jsonify({
                'success': False,
                'error': '音频数据解析失败'
            }), 400
        
        # 检查文件大小 (5MB限制)
        if file_size > 5 * 1024 * 1024:  # 5MB
            return jsonify({
                'success': False,
                'error': f'录音文件过大 ({file_size / 1024 / 1024:.1f}MB)，最大支持5MB'
            }), 400
        
        # 基本响应数据
        response_data = {
            'success': True,
            'audio_data': audio_data,
            'file_size': file_size,
            'file_name': f"录音_{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm"
        }
        
        # 如果需要转录，进行语音转文字
        if transcribe:
            # 优先使用客户端提供的转录文本（浏览器语音API）
            if client_transcript:
                logger.info("使用客户端语音识别结果...")
                fallback_result = chatbot_service.transcribe_audio_fallback(audio_data, client_transcript)
                
                if fallback_result['success']:
                    response_data.update({
                        'transcription': {
                            'text': fallback_result['text'],
                            'language': fallback_result['language'],
                            'model': fallback_result['model'],
                            'source': 'browser-speech-api'
                        }
                    })
                    logger.info(f"客户端语音识别成功: {fallback_result['text'][:50]}...")
                else:
                    response_data['transcription_error'] = fallback_result['error']
            else:
                # 使用服务端OpenAI Whisper API
                logger.info("开始服务端语音转文字...")
                transcription_result = chatbot_service.transcribe_audio(audio_data, language)
                
                if transcription_result['success']:
                    response_data.update({
                        'transcription': {
                            'text': transcription_result['text'],
                            'language': transcription_result['language'],
                            'duration': transcription_result.get('duration'),
                            'model': transcription_result.get('model'),
                            'source': 'openai-whisper'
                        }
                    })
                    logger.info(f"服务端语音转文字成功: {transcription_result['text'][:50]}...")
                else:
                    logger.warning(f"服务端语音转文字失败: {transcription_result['error']}")
                    response_data['transcription_error'] = transcription_result['error']
                    
                    # 如果OpenAI API不可用，提供备用建议
                    if transcription_result.get('fallback_available'):
                        response_data['fallback_suggestion'] = transcription_result.get('fallback_message')
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"录音上传错误: {e}")
        return jsonify({
            'success': False,
            'error': f'录音上传失败: {str(e)}'
        }), 500

@app.route('/api/transcribe', methods=['POST'])
def transcribe_audio_api():
    """专门的语音转文字API端点"""
    try:
        data = request.get_json()
        if not data or 'audio_data' not in data:
            return jsonify({
                'success': False,
                'error': '没有找到音频数据'
            }), 400
        
        audio_data = data['audio_data']
        language = data.get('language', 'zh')  # 默认中文
        
        # 验证base64数据
        if not audio_data.startswith('data:audio/'):
            return jsonify({
                'success': False,
                'error': '无效的音频数据格式'
            }), 400
        
        logger.info(f"开始语音转文字，语言: {language}")
        result = chatbot_service.transcribe_audio(audio_data, language)
        
        if result['success']:
            logger.info(f"语音转文字成功: {result['text'][:100]}...")
            return jsonify({
                'success': True,
                'text': result['text'],
                'language': result['language'],
                'duration': result.get('duration'),
                'model': result.get('model')
            })
        else:
            logger.error(f"语音转文字失败: {result['error']}")
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
        
    except Exception as e:
        logger.error(f"语音转文字API错误: {e}")
        return jsonify({
            'success': False,
            'error': f'语音转文字失败: {str(e)}'
        }), 500

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """获取对话会话列表"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        offset = (page - 1) * limit
        
        sessions = chat_db.get_sessions(limit=limit, offset=offset)
        statistics = chat_db.get_statistics()
        
        return jsonify({
            'success': True,
            'sessions': sessions,
            'statistics': statistics,
            'pagination': {
                'page': page,
                'limit': limit,
                'has_more': len(sessions) == limit
            }
        })
        
    except Exception as e:
        logger.error(f"获取会话列表错误: {e}")
        return jsonify({
            'success': False,
            'error': f'获取会话列表失败: {str(e)}'
        }), 500

@app.route('/api/sessions', methods=['POST'])
def create_session():
    """创建新的对话会话"""
    try:
        data = request.get_json()
        title = data.get('title') if data else None
        model = data.get('model') if data else None
        
        session_id = chat_db.create_session(title=title, model=model)
        session = chat_db.get_session_by_id(session_id)
        
        return jsonify({
            'success': True,
            'session': session
        })
        
    except Exception as e:
        logger.error(f"创建会话错误: {e}")
        return jsonify({
            'success': False,
            'error': f'创建会话失败: {str(e)}'
        }), 500

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session_messages(session_id):
    """获取会话的消息历史"""
    try:
        session = chat_db.get_session_by_id(session_id)
        if not session:
            return jsonify({
                'success': False,
                'error': '会话不存在'
            }), 404
        
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        offset = (page - 1) * limit
        
        messages = chat_db.get_messages(session_id, limit=limit, offset=offset)
        
        return jsonify({
            'success': True,
            'session': session,
            'messages': messages,
            'pagination': {
                'page': page,
                'limit': limit,
                'has_more': len(messages) == limit
            }
        })
        
    except Exception as e:
        logger.error(f"获取会话消息错误: {e}")
        return jsonify({
            'success': False,
            'error': f'获取会话消息失败: {str(e)}'
        }), 500

@app.route('/api/sessions/<session_id>', methods=['PUT'])
def update_session(session_id):
    """更新会话信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': '无效的请求数据'
            }), 400
        
        title = data.get('title')
        if title:
            success = chat_db.update_session_title(session_id, title)
            if not success:
                return jsonify({
                    'success': False,
                    'error': '会话不存在或更新失败'
                }), 404
        
        # 获取更新后的会话信息
        session = chat_db.get_session_by_id(session_id)
        
        return jsonify({
            'success': True,
            'session': session
        })
        
    except Exception as e:
        logger.error(f"更新会话错误: {e}")
        return jsonify({
            'success': False,
            'error': f'更新会话失败: {str(e)}'
        }), 500

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """删除会话"""
    try:
        success = chat_db.delete_session(session_id)
        if not success:
            return jsonify({
                'success': False,
                'error': '会话不存在或删除失败'
            }), 404
        
        return jsonify({
            'success': True,
            'message': '会话已删除'
        })
        
    except Exception as e:
        logger.error(f"删除会话错误: {e}")
        return jsonify({
            'success': False,
            'error': f'删除会话失败: {str(e)}'
        }), 500

@app.route('/api/sessions/<session_id>/archive', methods=['POST'])
def archive_session(session_id):
    """归档会话"""
    try:
        success = chat_db.archive_session(session_id)
        if not success:
            return jsonify({
                'success': False,
                'error': '会话不存在或归档失败'
            }), 404
        
        return jsonify({
            'success': True,
            'message': '会话已归档'
        })
        
    except Exception as e:
        logger.error(f"归档会话错误: {e}")
        return jsonify({
            'success': False,
            'error': f'归档会话失败: {str(e)}'
        }), 500

@app.route('/api/search', methods=['GET'])
def search_messages():
    """搜索消息"""
    try:
        query = request.args.get('q', '').strip()
        session_id = request.args.get('session_id')
        limit = int(request.args.get('limit', 50))
        
        if not query:
            return jsonify({
                'success': False,
                'error': '搜索关键词不能为空'
            }), 400
        
        search_result = bocha_search_service.search(query, count=limit)
        
        return jsonify({
            'success': True,
            'query': query,
            'results': search_result['results'],
            'images': search_result['images'],
            'total': search_result['total_count'],
            'search_provider': search_result['search_provider']
        })
        
    except Exception as e:
        logger.error(f"搜索消息错误: {e}")
        return jsonify({
            'success': False,
            'error': f'搜索失败: {str(e)}'
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
            'openai_available': bool(OPENAI_API_KEY),
            'multimodal_support': bool(GROQ_API_KEY),
            'speech_to_text': True,  # 支持浏览器语音识别 + OpenAI Whisper备选
            'browser_speech_recognition': True,  # 浏览器内置语音识别
            'server_speech_to_text': bool(OPENAI_API_KEY),  # 服务端语音转文字
            'history_storage': True
        }
    })

@app.route('/api/search/web', methods=['POST'])
def web_search():
    """联网搜索API"""
    try:
        # 检查请求是否包含JSON数据
        if not request.is_json:
            return jsonify({'success': False, 'error': '请求必须包含JSON数据'}), 400
            
        data = request.get_json()
        if data is None:
            return jsonify({'success': False, 'error': '无效的JSON数据'}), 400
        
        query = data.get('query')
        if not query or not query.strip():
            return jsonify({'success': False, 'error': '搜索查询不能为空'}), 400
        
        # 获取搜索参数
        count = data.get('count', 5)
        freshness = data.get('freshness', 'noLimit')
        include_images = data.get('include_images', True)
        format_for_ai = data.get('format_for_ai', False)
        
        # 执行搜索
        search_result = bocha_search_service.search(
            query=query,
            count=count,
            freshness=freshness,
            include_images=include_images
        )
        
        # 如果需要格式化为AI可读文本
        if format_for_ai and search_result.get('success'):
            formatted_text = bocha_search_service.format_search_results_for_ai(search_result)
            search_result['formatted_text'] = formatted_text
        
        return jsonify(search_result)
        
    except Exception as e:
        logger.error(f"联网搜索错误: {e}")
        return jsonify({
            'success': False,
            'error': f'搜索失败: {str(e)}'
        }), 500

@app.route('/api/chat/search', methods=['POST'])
def chat_with_search():
    """带联网搜索的智能对话API"""
    try:
        # 检查请求是否包含JSON数据
        if not request.is_json:
            return jsonify({'success': False, 'error': '请求必须包含JSON数据'}), 400
            
        data = request.get_json()
        if data is None:
            return jsonify({'success': False, 'error': '无效的JSON数据'}), 400
        
        user_message = data.get('message')
        if not user_message or not user_message.strip():
            return jsonify({'success': False, 'error': '消息内容不能为空'}), 400
        
        session_id = data.get('session_id', 'default')
        model = data.get('model', 'deepseek-ai/DeepSeek-V2.5')
        search_query = data.get('search_query', user_message)
        auto_search = data.get('auto_search', True)
        
        search_info = ""
        search_results = None
        
        # 如果启用自动搜索，先进行联网搜索
        if auto_search:
            logger.info(f"执行自动联网搜索: {search_query}")
            # 增加搜索结果数量，提高搜索质量
            search_results = bocha_search_service.search(
                query=search_query, 
                count=8,  # 增加搜索结果数量
                freshness="oneWeek",  # 获取更新的信息
                include_images=False,  # 专注于文本内容
                summary=True
            )
            
            if search_results.get('success'):
                search_info = bocha_search_service.format_search_results_for_ai(search_results, max_results=6)
                # 构建强制使用搜索结果的消息
                enhanced_message = f"""用户问题：{user_message}

【重要提示】：以下是为回答用户问题而获取的实时搜索结果，你必须基于这些搜索结果来回答用户的问题，不要给出通用回答。

{search_info}

请根据以上搜索结果，为用户提供详细、准确的回答。如果涉及价格信息，请整理成表格格式。"""
            else:
                enhanced_message = user_message
                logger.warning(f"联网搜索失败: {search_results.get('error')}")
        else:
            enhanced_message = user_message
        
        # 构建消息列表
        messages = [
            {
                'role': 'system',
                'content': f"""You are an intelligent assistant that combines web search results with elegant presentation. Your responses should be informative, well-structured, and visually appealing like ChatGPT.

🎯 CORE PRINCIPLES:
1. **Use search results as primary source**: Extract information from provided search data
2. **Structure like ChatGPT**: Use clear headings, tables, lists, and professional formatting
3. **Be comprehensive yet accessible**: Explain complex concepts clearly
4. **Include visual elements**: Use emojis, tables, and markdown formatting

📝 RESPONSE FORMAT REQUIREMENTS:

For **mathematical concepts** (like Taylor series, calculus, etc.):
```markdown
## 📚 概念定义
[Clear, concise definition]

## 🔢 数学表达

$$
[Write complete LaTeX formula here - NO placeholders]
$$

其中：
- \\( actual_symbol \\) 表示具体含义
- \\( actual_symbol \\) 表示具体含义

## 💡 直观理解
[Intuitive explanation with analogies]

## 📖 经典例子
| 函数 | 展开式 | 收敛范围 | 应用 |
|------|--------|----------|------|
| \\( e^x \\) | \\( 1 + x + \\frac{{x^2}}{{2!}} + \\frac{{x^3}}{{3!}} + \\cdots \\) | 所有实数 | 指数增长 |
| \\( \\sin x \\) | \\( x - \\frac{{x^3}}{{3!}} + \\frac{{x^5}}{{5!}} - \\cdots \\) | 所有实数 | 振荡分析 |

## 🚀 实际应用
- **领域1**: 具体应用
- **领域2**: 具体应用

## 💭 深入思考
[Thought-provoking insights]

**CRITICAL LATEX REQUIREMENTS**: 
- Use \\( \\) for inline math like \\( f(x) \\), \\( x^2 \\), \\( \\sin(x) \\)
- Use $$ $$ for display math (with line breaks before and after)
- ABSOLUTELY FORBIDDEN: MATH_LATEX_BLOCK_X or MATH_LATEX_INLINE_X or any placeholders
- Write complete LaTeX formulas directly in response
- Example: \\( e^x = 1 + x + \\frac{{x^2}}{{2!}} + \\cdots \\)
- Example display: 

$$
f(x) = \\sum_{{n=0}}^{{\\infty}} \\frac{{f^{{(n)}}(a)}}{{n!}} (x-a)^n
$$
```

For **price/data queries**:
```markdown
## 📊 [主题] 信息
数据更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}

| 来源/机构 | 价格/数据 | 单位 | 变化 | 更新时间 |
|----------|-----------|------|------|----------|
[Extract from search results]

## 📈 关键发现
- **主要趋势**: ...
- **重要数据**: ...

## 📚 数据来源
[List sources with links]
```

For **general information**:
```markdown
## 🔍 [主题概述]
[Brief introduction]

## 📋 核心要点
- **要点1**: 详细说明
- **要点2**: 详细说明

## 📊 详细信息
[Use tables, lists, or structured content]

## 🔗 参考资料
[Source links from search results]
```

🎨 FORMATTING RULES:
- Use **bold** for emphasis
- Use \\( \\) for inline math, \\[ \\] for display math
- Use tables for structured data
- Use emojis for section headers (📊📚🔍🚀💡)
- Include source links in markdown format
- Use proper heading hierarchy (##, ###)

❌ AVOID:
- Generic responses without using search data
- Poor formatting or plain text responses
- Ignoring the mathematical or technical nature of questions

✅ ALWAYS:
- Extract specific information from search results
- Present in visually appealing format
- Include proper mathematical notation when relevant
- Cite sources appropriately
- Match the tone and structure of professional AI assistants

Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            },
            {
                'role': 'user',
                'content': enhanced_message
            }
        ]
        
        # 调用AI模型生成回答
        response = chatbot_service.get_response(messages, model=model)
        
        if response['success']:
            # 保存对话到数据库
            chat_db.add_message(session_id, 'user', user_message)
            chat_db.add_message(session_id, 'assistant', response['response'])
            
            return jsonify({
                'success': True,
                'response': response['response'],
                'model_used': response.get('model_used', model),
                'provider': response.get('provider'),
                'search_performed': auto_search,
                'search_results': search_results,
                'session_id': session_id
            })
        else:
            return jsonify({
                'success': False,
                'error': response.get('error', '生成回答失败'),
                'search_results': search_results
            }), 500
            
    except Exception as e:
        logger.error(f"联网对话错误: {e}")
        return jsonify({
            'success': False,
            'error': f'对话失败: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("🚀 启动聊天机器人...")
    print("📱 访问地址: http://localhost:5000")
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except OSError as e:
        if "Address already in use" in str(e):
            print("❌ 端口5000已被占用，请关闭占用端口的程序或使用: lsof -ti:5000 | xargs kill -9")
        else:
            print(f"❌ 启动失败: {e}") 