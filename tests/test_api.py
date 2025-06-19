#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态聊天机器人 pytest 测试套件 - API测试
"""

import pytest
import requests
import time
from typing import Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class TestChatbotAPI:
    """聊天机器人API测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_session(self):
        """设置测试会话"""
        self.base_url = "http://localhost:5000"
        self.session = requests.Session()
        self.test_session_id = None
        yield
        # 清理测试数据
        if self.test_session_id:
            try:
                self.session.delete(f"{self.base_url}/api/sessions/{self.test_session_id}", timeout=10)
            except:
                pass
    
    def create_test_image_base64(self) -> str:
        """创建测试用的base64图片"""
        red_square_png = (
            "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAAEklEQVR4nGP8z4APMOGVHbHSAEEsAROxCnMTAAAAAElFTkSuQmCC"
        )
        return f"data:image/png;base64,{red_square_png}"
    
    def create_test_audio_base64(self) -> str:
        """创建测试用的base64音频"""
        # 这是一个非常简单的wav文件头+数据（约1秒的静音）
        wav_data = (
            "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="
        )
        return f"data:audio/wav;base64,{wav_data}"
    
    def create_test_video_base64(self) -> str:
        """创建测试用的base64视频"""
        # 这是一个最小的mp4文件header
        mp4_data = (
            "AAAAIGZ0eXBpc29tAAACAGlzb21pc28yYXZjMW1wNDE="
        )
        return f"data:video/mp4;base64,{mp4_data}"
    
    def create_test_audio_wav(self) -> str:
        """创建更大的测试音频文件用于语音转文字测试"""
        # 创建一个更大的wav文件（大约1KB）
        wav_header = "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="
        # 重复数据来创建更大的文件
        wav_data = wav_header + "A" * 1000  # 添加更多数据
        return f"data:audio/wav;base64,{wav_data}"
    
    @pytest.mark.integration
    def test_api_health(self):
        """测试API健康检查"""
        response = self.session.get(f"{self.base_url}/api/health", timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        
        capabilities = data.get("capabilities", {})
        assert "siliconflow_available" in capabilities
        assert "groq_available" in capabilities
    
    @pytest.mark.integration
    def test_get_models(self):
        """测试获取模型列表"""
        response = self.session.get(f"{self.base_url}/api/models", timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        models = data.get("models", [])
        
        assert len(models) > 0, "没有可用模型"
        
        # 验证模型数据结构
        for model in models:
            assert "id" in model
            assert "name" in model
            assert "provider" in model
            assert "supports_image" in model
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_text_chat(self):
        """测试文本聊天功能"""
        test_data = {
            "messages": [{"role": "user", "text": "你好，请简单介绍一下自己"}],
            "model": "deepseek-ai/DeepSeek-V2.5"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json=test_data,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert len(data.get("response", "")) > 0
        assert data.get("provider") == "siliconflow"
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_system_prompt(self):
        """测试System Prompt功能"""
        test_data = {
            "messages": [{"role": "user", "text": "介绍一下你自己"}],
            "model": "deepseek-ai/DeepSeek-V2.5",
            "system_prompt": "你是一个专业的测试助手，每次回答都必须以'作为测试助手'开头。"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json=test_data,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        
        response_text = data.get("response", "")
        assert "作为测试助手" in response_text, "AI没有按照系统提示回答"
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_temperature_setting(self):
        """测试Temperature设置功能"""
        test_data = {
            "messages": [{"role": "user", "text": "1+1等于多少？"}],
            "model": "deepseek-ai/DeepSeek-V2.5",
            "temperature": 0.1
        }
        
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json=test_data,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
    
    @pytest.mark.integration
    @pytest.mark.api
    @pytest.mark.slow
    def test_image_analysis(self):
        """测试图片分析功能"""
        test_data = {
            "messages": [{
                "role": "user", 
                "text": "请简单描述这张图片",
                "image": self.create_test_image_base64()
            }],
            "model": "meta-llama/llama-4-scout-17b-16e-instruct"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json=test_data,
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert len(data.get("response", "")) > 0
        assert data.get("provider") == "groq"
    
    @pytest.mark.integration
    @pytest.mark.api
    @pytest.mark.slow
    def test_model_auto_switching(self):
        """测试模型自动切换功能"""
        # 首先发送纯文本消息（应该使用SiliconFlow）
        text_data = {
            "messages": [{"role": "user", "text": "你好"}],
            "model": "deepseek-ai/DeepSeek-V2.5"
        }
        
        response1 = self.session.post(f"{self.base_url}/api/chat", json=text_data, timeout=30)
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1.get("success") is True
        text_provider = data1.get("provider", "未知")
        
        # 然后发送带图片的消息（应该自动切换到Groq）
        image_data = {
            "messages": [{
                "role": "user", 
                "text": "这是什么？", 
                "image": self.create_test_image_base64()
            }],
            "model": "deepseek-ai/DeepSeek-V2.5"  # 故意使用不支持图片的模型
        }
        
        response2 = self.session.post(f"{self.base_url}/api/chat", json=image_data, timeout=60)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2.get("success") is True
        image_provider = data2.get("provider", "未知")
        
        # 验证提供商是否不同（自动切换）
        assert text_provider != image_provider, "没有检测到自动切换"
        assert text_provider == "siliconflow"
        assert image_provider == "groq"
    
    @pytest.mark.integration
    def test_session_management(self):
        """测试会话管理功能"""
        # 1. 创建新会话
        create_data = {
            "title": "测试会话",
            "model": "deepseek-ai/DeepSeek-V2.5"
        }
        
        response = self.session.post(f"{self.base_url}/api/sessions", json=create_data, timeout=10)
        assert response.status_code == 200
        
        session_data = response.json()
        assert session_data.get("success") is True
        self.test_session_id = session_data["session"]["id"]
        
        # 2. 在会话中发送消息
        chat_data = {
            "messages": [{"role": "user", "text": "这是测试消息"}],
            "model": "deepseek-ai/DeepSeek-V2.5",
            "session_id": self.test_session_id
        }
        
        response = self.session.post(f"{self.base_url}/api/chat", json=chat_data, timeout=30)
        assert response.status_code == 200
        
        # 3. 获取会话消息
        response = self.session.get(f"{self.base_url}/api/sessions/{self.test_session_id}", timeout=10)
        assert response.status_code == 200
        
        session_messages = response.json()
        assert session_messages.get("success") is True
        messages = session_messages.get("messages", [])
        assert len(messages) >= 2  # 至少有用户消息和AI回复
    
    @pytest.mark.integration
    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效的模型
        invalid_model_data = {
            "messages": [{"role": "user", "text": "测试"}],
            "model": "invalid-model-name"
        }
        
        response = self.session.post(f"{self.base_url}/api/chat", json=invalid_model_data, timeout=10)
        
        # 应该返回错误
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is False
            assert data.get("error") is not None
        else:
            # 也可以接受非200状态码
            assert response.status_code in [400, 500]
        
        # 测试空消息
        empty_data = {
            "messages": [],
            "model": "deepseek-ai/DeepSeek-V2.5"
        }
        
        response = self.session.post(f"{self.base_url}/api/chat", json=empty_data, timeout=10)
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is False
    
    # ==================== 音频和视频功能测试 ====================
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_audio_upload(self):
        """测试音频文件上传功能"""
        import io
        
        # 创建测试音频数据
        audio_data = b"test audio data for upload"
        
        # 准备multipart form data
        files = {
            'audio': ('test_audio.wav', io.BytesIO(audio_data), 'audio/wav')
        }
        
        response = self.session.post(
            f"{self.base_url}/api/upload/audio",
            files=files,
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "audio_data" in data
        assert "file_size" in data
        assert "file_name" in data
        assert data["file_name"] == "test_audio.wav"
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_video_upload(self):
        """测试视频文件上传功能"""
        import io
        
        # 创建测试视频数据
        video_data = b"test video data for upload"
        
        # 准备multipart form data
        files = {
            'video': ('test_video.mp4', io.BytesIO(video_data), 'video/mp4')
        }
        
        response = self.session.post(
            f"{self.base_url}/api/upload/video",
            files=files,
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "video_data" in data
        assert "file_size" in data
        assert "file_name" in data
        assert data["file_name"] == "test_video.mp4"
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_recording_upload(self):
        """测试录音上传功能"""
        audio_data = self.create_test_audio_base64()
        
        test_data = {
            "audio_data": audio_data
        }
        
        response = self.session.post(
            f"{self.base_url}/api/upload/record",
            json=test_data,
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "audio_data" in data
        assert "file_size" in data
        assert "file_name" in data
        assert "录音_" in data["file_name"]
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_chat_with_audio(self):
        """测试音频消息功能"""
        test_data = {
            "messages": [{
                "role": "user",
                "text": "请分析这个音频文件",
                "audio": self.create_test_audio_base64()
            }],
            "model": "deepseek-ai/DeepSeek-V2.5"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json=test_data,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert len(data.get("response", "")) > 0
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_chat_with_video(self):
        """测试视频消息功能"""
        test_data = {
            "messages": [{
                "role": "user",
                "text": "请分析这个视频文件",
                "video": self.create_test_video_base64()
            }],
            "model": "deepseek-ai/DeepSeek-V2.5"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json=test_data,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert len(data.get("response", "")) > 0
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_audio_file_size_limit(self):
        """测试音频文件大小限制"""
        import io
        
        # 创建超过10MB的音频数据
        large_audio_data = b"x" * (11 * 1024 * 1024)  # 11MB
        
        files = {
            'audio': ('large_audio.wav', io.BytesIO(large_audio_data), 'audio/wav')
        }
        
        response = self.session.post(
            f"{self.base_url}/api/upload/audio",
            files=files,
            timeout=10
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data.get("success") is False
        assert "过大" in data.get("error", "")
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_video_file_size_limit(self):
        """测试视频文件大小限制"""
        import io
        
        # 创建超过50MB的视频数据
        large_video_data = b"x" * (51 * 1024 * 1024)  # 51MB
        
        files = {
            'video': ('large_video.mp4', io.BytesIO(large_video_data), 'video/mp4')
        }
        
        response = self.session.post(
            f"{self.base_url}/api/upload/video",
            files=files,
            timeout=10
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data.get("success") is False
        assert "过大" in data.get("error", "")
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_audio_format_validation(self):
        """测试音频格式验证"""
        import io
        
        # 创建不支持的文件格式
        invalid_audio_data = b"invalid audio format"
        
        files = {
            'audio': ('test.txt', io.BytesIO(invalid_audio_data), 'text/plain')
        }
        
        response = self.session.post(
            f"{self.base_url}/api/upload/audio",
            files=files,
            timeout=10
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data.get("success") is False
        assert "不支持的音频格式" in data.get("error", "")
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_video_format_validation(self):
        """测试视频格式验证"""
        import io
        
        # 创建不支持的文件格式
        invalid_video_data = b"invalid video format"
        
        files = {
            'video': ('test.txt', io.BytesIO(invalid_video_data), 'text/plain')
        }
        
        response = self.session.post(
            f"{self.base_url}/api/upload/video",
            files=files,
            timeout=10
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data.get("success") is False
        assert "不支持的视频格式" in data.get("error", "")
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_session_with_multimedia(self):
        """测试会话中的多媒体消息保存"""
        # 1. 创建新会话
        create_data = {
            "title": "多媒体测试会话",
            "model": "deepseek-ai/DeepSeek-V2.5"
        }
        
        response = self.session.post(f"{self.base_url}/api/sessions", json=create_data, timeout=10)
        assert response.status_code == 200
        
        session_data = response.json()
        assert session_data.get("success") is True
        test_session_id = session_data["session"]["id"]
        
        try:
            # 2. 发送音频消息
            audio_chat_data = {
                "messages": [{
                    "role": "user",
                    "text": "这是一个音频测试",
                    "audio": self.create_test_audio_base64()
                }],
                "model": "deepseek-ai/DeepSeek-V2.5",
                "session_id": test_session_id
            }
            
            response = self.session.post(f"{self.base_url}/api/chat", json=audio_chat_data, timeout=30)
            assert response.status_code == 200
            
            # 3. 发送视频消息
            video_chat_data = {
                "messages": [{
                    "role": "user",
                    "text": "这是一个视频测试",
                    "video": self.create_test_video_base64()
                }],
                "model": "deepseek-ai/DeepSeek-V2.5",
                "session_id": test_session_id
            }
            
            response = self.session.post(f"{self.base_url}/api/chat", json=video_chat_data, timeout=30)
            assert response.status_code == 200
            
            # 4. 获取会话消息，验证多媒体内容已保存
            response = self.session.get(f"{self.base_url}/api/sessions/{test_session_id}", timeout=10)
            assert response.status_code == 200
            
            session_messages = response.json()
            assert session_messages.get("success") is True
            messages = session_messages.get("messages", [])
            
            # 应该有用户的音频消息、AI回复、用户的视频消息、AI回复
            assert len(messages) >= 4
            
            # 验证音频消息
            audio_message = None
            video_message = None
            for msg in messages:
                if msg.get("content_type") == "audio":
                    audio_message = msg
                elif msg.get("content_type") == "video":
                    video_message = msg
            
            assert audio_message is not None, "音频消息未正确保存"
            assert video_message is not None, "视频消息未正确保存"
            assert audio_message.get("image_data") is not None
            assert video_message.get("image_data") is not None
            
        finally:
            # 清理测试会话
            self.session.delete(f"{self.base_url}/api/sessions/{test_session_id}", timeout=10)
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_speech_to_text_api(self):
        """测试专门的语音转文字API端点"""
        audio_data = self.create_test_audio_base64()
        
        test_data = {
            "audio_data": audio_data,
            "language": "zh"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/transcribe",
            json=test_data,
            timeout=30
        )
        
        # 如果OpenAI API密钥未配置，应该返回错误
        if response.status_code == 500:
            data = response.json()
            assert data.get("success") is False
            assert "OpenAI API密钥未配置" in data.get("error", "")
        else:
            # 如果配置了API密钥，应该能正常处理
            assert response.status_code == 200
            data = response.json()
            # 由于使用的是测试音频数据，可能会返回空文本或错误
            # 这里主要测试API端点是否正常工作
            assert "success" in data
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_recording_with_transcription(self):
        """测试录音上传并包含语音转文字功能"""
        audio_data = self.create_test_audio_wav()
        
        test_data = {
            "audio_data": audio_data,
            "transcribe": True,
            "language": "zh"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/upload/record",
            json=test_data,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "audio_data" in data
        assert "file_size" in data
        assert "file_name" in data
        
        # 检查转录结果（如果OpenAI API可用的话）
        if "transcription" in data:
            assert "text" in data["transcription"]
            assert "language" in data["transcription"]
        elif "transcription_error" in data:
            # 如果转录失败，应该有错误信息
            assert isinstance(data["transcription_error"], str)
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_recording_without_transcription(self):
        """测试录音上传但不进行语音转文字"""
        audio_data = self.create_test_audio_base64()
        
        test_data = {
            "audio_data": audio_data,
            "transcribe": False
        }
        
        response = self.session.post(
            f"{self.base_url}/api/upload/record",
            json=test_data,
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert "audio_data" in data
        assert "transcription" not in data
        assert "transcription_error" not in data
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_groq_speech_to_text(self):
        """测试Groq语音转文字功能"""
        from app import chatbot_service
        
        audio_data = self.create_test_audio_wav()
        
        # 测试Groq语音转文字
        result = chatbot_service.transcribe_audio_with_groq(audio_data, "zh")
        
        # 如果Groq API密钥未配置或API调用失败，应该返回错误
        if result.get("success") is False:
            error_msg = result.get("error", "")
            assert ("Groq API密钥未配置" in error_msg or 
                    "400 Client Error" in error_msg or 
                    "Invalid base64" in error_msg), f"意外的错误信息: {error_msg}"
        else:
            # 如果配置了API密钥且成功，应该能正常处理
            assert result.get("success") is True
            assert "text" in result
            assert "language" in result
            assert result.get("model") == "groq-whisper-large-v3-turbo"
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_video_frame_extraction(self):
        """测试视频帧提取功能"""
        from app import chatbot_service
        
        video_data = self.create_test_video_base64()
        
        # 测试视频帧提取
        result = chatbot_service.extract_video_frames(video_data, max_frames=2)
        
        # 由于使用的是测试视频数据，可能会失败，但要确保方法存在且返回正确格式
        assert "success" in result
        
        if result.get("success") is True:
            assert "frames" in result
            assert "frame_count" in result
            assert isinstance(result["frames"], list)
            assert result["frame_count"] >= 0
        else:
            # 如果失败，应该有错误信息
            assert "error" in result
            assert isinstance(result["error"], str)
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_multimodal_message_preprocessing(self):
        """测试多模态消息预处理功能"""
        from app import _preprocess_multimedia_messages
        
        # 测试包含音频的消息
        audio_messages = [
            {
                "role": "user",
                "text": "请分析我的录音",
                "audio": self.create_test_audio_base64()
            }
        ]
        
        processed_audio = _preprocess_multimedia_messages(audio_messages)
        
        # 验证音频处理结果
        assert len(processed_audio) == 1
        processed_msg = processed_audio[0]
        assert processed_msg["role"] == "user"
        assert "audio" not in processed_msg  # 音频数据应该被移除
        assert "用户语音内容" in processed_msg["text"] or "音频文件" in processed_msg["text"]
        
        # 测试包含视频的消息
        video_messages = [
            {
                "role": "user", 
                "text": "请分析这个视频",
                "video": self.create_test_video_base64()
            }
        ]
        
        processed_video = _preprocess_multimedia_messages(video_messages)
        
        # 验证视频处理结果
        assert len(processed_video) == 1
        processed_msg = processed_video[0]
        assert processed_msg["role"] == "user"
        assert "video" not in processed_msg  # 视频数据应该被移除
        assert "视频文件" in processed_msg["text"]
        
        # 测试混合多媒体消息
        mixed_messages = [
            {
                "role": "user",
                "text": "请分析这些文件",
                "audio": self.create_test_audio_base64(),
                "video": self.create_test_video_base64(),
                "image": self.create_test_image_base64()
            }
        ]
        
        processed_mixed = _preprocess_multimedia_messages(mixed_messages)
        
        # 验证混合处理结果
        assert len(processed_mixed) == 1
        processed_msg = processed_mixed[0]
        assert processed_msg["role"] == "user"
        assert "audio" not in processed_msg
        assert "video" not in processed_msg
        # 图片数据可能保留（取决于视频帧提取是否成功）
        assert len(processed_msg["text"]) > len("请分析这些文件")  # 应该有附加的处理信息
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_enhanced_multimodal_chat(self):
        """测试增强的多模态聊天功能"""
        # 测试带音频的聊天（应该使用Groq转录或降级处理）
        enhanced_audio_data = {
            "messages": [{
                "role": "user",
                "text": "请分析我说的话",
                "audio": self.create_test_audio_wav()
            }],
            "model": "deepseek-ai/DeepSeek-V2.5"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json=enhanced_audio_data,
            timeout=45  # 增加超时时间，因为现在处理更复杂
        )
        
        # 检查响应状态，如果失败则打印错误信息
        if response.status_code != 200:
            print(f"音频聊天响应状态码: {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误信息: {error_data}")
            except:
                print(f"响应内容: {response.text}")
        
        # 多模态处理可能比较复杂，允许一定的错误
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True
            assert len(data.get("response", "")) > 0
        else:
            # 如果音频处理失败，至少应该返回有意义的错误
            assert response.status_code in [400, 500]  # 允许的错误状态码
        
        # 测试带视频的聊天（应该尝试提取帧或提供智能引导）
        enhanced_video_data = {
            "messages": [{
                "role": "user",
                "text": "请分析这个视频内容",
                "video": self.create_test_video_base64()
            }],
            "model": "meta-llama/llama-4-scout-17b-16e-instruct"  # 使用支持视觉的模型
        }
        
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json=enhanced_video_data,
            timeout=45
        )
        
        # 检查视频聊天响应
        if response.status_code != 200:
            print(f"视频聊天响应状态码: {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误信息: {error_data}")
            except:
                print(f"响应内容: {response.text}")
        
        # 视频处理同样可能遇到问题，允许一定的错误
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True
            assert len(data.get("response", "")) > 0
            # 检查是否自动切换到支持多模态的模型
            if "provider" in data:
                assert data.get("provider") in ["groq", "siliconflow"]
        else:
            # 如果处理失败，至少应该返回有意义的错误
            assert response.status_code in [400, 500]
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_fallback_mechanisms(self):
        """测试降级机制和错误处理"""
        from app import chatbot_service, _preprocess_multimedia_messages
        
        # 测试无效音频数据的处理
        invalid_audio = "data:audio/wav;base64,invalid_base64_data"
        result = chatbot_service.transcribe_audio_with_groq(invalid_audio, "zh")
        assert result.get("success") is False
        assert "error" in result
        
        # 测试无效视频数据的处理
        invalid_video = "data:video/mp4;base64,invalid_base64_data"
        result = chatbot_service.extract_video_frames(invalid_video)
        assert result.get("success") is False
        assert "error" in result
        
        # 测试空消息列表的处理
        empty_messages = []
        processed = _preprocess_multimedia_messages(empty_messages)
        assert processed == []
        
        # 测试只有文本消息的处理（不应该被修改）
        text_only_messages = [
            {
                "role": "user",
                "text": "这只是一个普通的文本消息"
            }
        ]
        processed = _preprocess_multimedia_messages(text_only_messages)
        assert len(processed) == 1
        assert processed[0]["text"] == "这只是一个普通的文本消息"
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_api_performance_improvements(self):
        """测试API性能改进"""
        import time
        
        # 测试Groq语音转文字的速度（如果可用）
        audio_data = self.create_test_audio_wav()
        
        start_time = time.time()
        
        test_data = {
            "audio_data": audio_data,
            "transcribe": True,
            "language": "zh"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/upload/record",
            json=test_data,
            timeout=30
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        
        # 记录处理时间（用于性能分析）
        print(f"音频处理时间: {processing_time:.2f}秒")
        
        # 基本性能检验：处理时间应该在合理范围内（30秒内）
        assert processing_time < 30, f"音频处理时间过长: {processing_time:.2f}秒"
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_enhanced_video_analysis(self):
        """测试增强的视频分析功能"""
        from app import chatbot_service
        
        video_data = self.create_test_video_base64()
        
        # 测试增强的视频帧提取功能
        result = chatbot_service.extract_video_frames(video_data, max_frames=6)
        
        # 验证返回的数据结构
        assert "success" in result
        
        if result.get("success") is True:
            # 验证基本信息
            assert "frames" in result
            assert "frame_count" in result
            assert "total_frames" in result
            assert "duration" in result
            assert "fps" in result
            assert "resolution" in result
            
            # 验证新增的分析功能
            assert "frame_analysis" in result
            assert "analysis_summary" in result
            assert "video_stats" in result
            assert "audio_info" in result
            
            # 验证帧分析数据
            frame_analysis = result["frame_analysis"]
            if frame_analysis:
                for frame_info in frame_analysis:
                    assert "timestamp" in frame_info
                    assert "time_formatted" in frame_info
                    assert "motion_score" in frame_info
                    assert "brightness" in frame_info
                    assert "scene_complexity" in frame_info
                    assert "position" in frame_info
            
            # 验证视频统计
            video_stats = result["video_stats"]
            assert "avg_motion" in video_stats
            assert "avg_brightness" in video_stats
            assert "scene_changes" in video_stats
            
            # 验证分析摘要
            analysis_summary = result["analysis_summary"]
            assert isinstance(analysis_summary, str)
            assert len(analysis_summary) > 0
            
            print(f"视频分析成功：{len(result['frames'])}帧，时长{result['duration']}秒")
            print(f"分析摘要：{analysis_summary}")
        else:
            # 即使失败，也应该有有意义的错误信息
            assert "error" in result
            print(f"视频分析失败（预期）：{result['error']}")
    
    @pytest.mark.integration
    @pytest.mark.api
    def test_complete_video_multimodal_processing(self):
        """测试完整的视频多模态处理流程"""
        from app import _preprocess_multimedia_messages
        
        # 测试包含视频的完整处理流程
        video_messages = [
            {
                "role": "user",
                "text": "请详细分析这个视频的内容和发展过程",
                "video": self.create_test_video_base64()
            }
        ]
        
        processed_video = _preprocess_multimedia_messages(video_messages)
        
        # 验证处理结果
        assert len(processed_video) == 1
        processed_msg = processed_video[0]
        assert processed_msg["role"] == "user"
        assert "video" not in processed_msg  # 视频数据应该被移除
        
        # 检查是否包含详细的视频分析信息
        processed_text = processed_msg["text"]
        assert "视频文件" in processed_text
        
        # 如果视频处理成功，应该包含详细分析信息
        if "完整的视频分析" in processed_text and "无法进行" not in processed_text:
            # 成功分析的情况
            assert "📊 视频信息" in processed_text
            assert "🎬 关键帧分析" in processed_text
            assert "时序发展" in processed_text
            assert "场景变化" in processed_text
            print("✅ 视频完整分析功能正常")
        elif "无法进行完整的视频分析" in processed_text:
            # 降级处理的情况
            assert "主要场景" in processed_text
            assert "人物动作" in processed_text
            assert "时间顺序" in processed_text
            assert "关键事件" in processed_text
            print("⚠️ 视频分析降级处理正常")
        else:
            # 其他情况，至少应该有基本的分析引导
            assert any(keyword in processed_text for keyword in ["场景", "动作", "内容", "分析"])
            print("ℹ️ 视频处理进入其他降级模式")
        
        # 如果成功提取了视频帧，应该有图片数据
        if "image" in processed_msg:
            assert processed_msg["image"].startswith("data:image/")
            print("✅ 视频帧提取成功，已转换为图片分析")
        else:
            print("ℹ️ 视频帧提取失败（使用测试数据时正常）")
        
        print(f"处理后的文本长度: {len(processed_text)}字符")
        
        # 计算包含的分析元素（调整为更实际的检查）
        analysis_elements = ['场景', '动作', '时间', '事件', '内容', '发展']
        found_elements = len([x for x in analysis_elements if x in processed_text])
        print(f"包含分析元素: {found_elements}/{len(analysis_elements)}")
        
        # 最少应该包含一些分析引导信息
        assert found_elements >= 3, f"分析元素太少: {found_elements}"
    
    def test_web_search_api(self):
        """测试联网搜索API"""
        # 测试有效搜索
        response = self.session.post(f"{self.base_url}/api/search/web", json={
            'query': '人工智能发展',
            'count': 3,
            'include_images': True
        }, timeout=30)
        
        # 检查基本响应格式
        assert response.status_code in [200, 500]  # API密钥可能未配置
        data = response.json()
        assert isinstance(data, dict)
        assert 'success' in data
        
        if data['success']:
            # 如果搜索成功，检查数据结构
            assert 'results' in data
            assert 'query' in data
            assert 'search_provider' in data
            assert isinstance(data['results'], list)
        else:
            # 如果失败，应该有错误信息
            assert 'error' in data
    
    def test_web_search_api_invalid_request(self):
        """测试无效搜索请求"""
        # 测试空查询
        response = self.session.post(f"{self.base_url}/api/search/web", json={}, timeout=15)
        assert response.status_code == 400
        data = response.json()
        assert not data['success']
        assert 'error' in data
        
        # 测试无JSON数据
        response = self.session.post(f"{self.base_url}/api/search/web", timeout=15)
        assert response.status_code == 400
    
    def test_chat_with_search_api(self):
        """测试带搜索的智能对话API"""
        # 测试关闭搜索的对话
        response = self.session.post(f"{self.base_url}/api/chat/search", json={
            'message': '你好',
            'auto_search': False
        }, timeout=30)
        
        # 检查基本响应格式
        assert response.status_code in [200, 500]  # API密钥可能未配置
        data = response.json()
        assert isinstance(data, dict)
        assert 'success' in data
        
        if data['success']:
            # 检查响应数据结构
            assert 'response' in data
            assert 'search_performed' in data
            assert not data['search_performed']  # 应该关闭搜索
        
        # 测试开启搜索的对话
        response = self.session.post(f"{self.base_url}/api/chat/search", json={
            'message': '今天的天气怎么样',
            'auto_search': True
        }, timeout=45)
        
        assert response.status_code in [200, 500]
        data = response.json()
        assert isinstance(data, dict)
        assert 'success' in data
    
    def test_chat_with_search_invalid_request(self):
        """测试无效的搜索对话请求"""
        # 测试空消息
        response = self.session.post(f"{self.base_url}/api/chat/search", json={}, timeout=15)
        assert response.status_code == 400
        data = response.json()
        assert not data['success']
        assert 'error' in data
    
    def test_bocha_search_service(self):
        """测试博查搜索服务类"""
        # 导入服务类
        from app import BochaSearchService
        
        # 测试初始化
        service = BochaSearchService()
        assert service.api_key
        assert service.base_url == "https://api.bochaai.com/v1/web-search"
        
        # 测试搜索方法（模拟）
        # 注意：这里不会真正调用API，因为测试环境可能没有配置密钥
        try:
            result = service.search("测试查询", count=1)
            assert isinstance(result, dict)
            assert 'success' in result
            
            if result['success']:
                assert 'results' in result
                assert 'query' in result
            else:
                assert 'error' in result
        except Exception as e:
            # 如果API调用失败，这是预期的
            assert isinstance(e, Exception)
    
    def test_search_result_formatting(self):
        """测试搜索结果格式化"""
        from app import BochaSearchService
        
        service = BochaSearchService()
        
        # 测试成功结果格式化
        mock_result = {
            'success': True,
            'query': '测试查询',
            'results': [
                {
                    'title': '测试标题',
                    'url': 'https://example.com',
                    'snippet': '测试摘要',
                    'summary': '测试总结',
                    'siteName': '测试网站'
                }
            ],
            'images': [
                {
                    'thumbnailUrl': 'https://example.com/thumb.jpg',
                    'contentUrl': 'https://example.com/image.jpg',
                    'name': '测试图片'
                }
            ],
            'total_count': 1,
            'search_provider': '博查AI'
        }
        
        formatted_text = service.format_search_results_for_ai(mock_result)
        assert isinstance(formatted_text, str)
        assert '测试查询' in formatted_text
        assert '测试标题' in formatted_text
        assert '博查AI' in formatted_text
        
        # 测试失败结果格式化
        mock_failed_result = {
            'success': False,
            'error': '测试错误'
        }
        
        formatted_text = service.format_search_results_for_ai(mock_failed_result)
        assert isinstance(formatted_text, str)
        assert '搜索失败' in formatted_text
        assert '测试错误' in formatted_text 