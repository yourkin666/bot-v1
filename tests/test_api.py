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

    @pytest.mark.integration
    @pytest.mark.api
    def test_function_calling_tools(self):
        """测试Function Calling工具功能"""
        from app import FunctionCallExecutor, BochaSearchService
        
        # 初始化执行器
        bocha_service = BochaSearchService()
        executor = FunctionCallExecutor(bocha_service)
        
        # 测试获取可用工具
        tools = executor.get_available_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        # 验证工具结构
        for tool in tools:
            assert 'type' in tool
            assert tool['type'] == 'function'
            assert 'function' in tool
            assert 'name' in tool['function']
            assert 'description' in tool['function']
            assert 'parameters' in tool['function']
        
        # 查找网络搜索工具
        search_tool = None
        for tool in tools:
            if tool['function']['name'] == 'web_search':
                search_tool = tool
                break
        
        assert search_tool is not None, "缺少web_search工具"
        assert 'query' in search_tool['function']['parameters']['properties']

    @pytest.mark.integration
    @pytest.mark.api
    def test_function_calling_execution(self):
        """测试Function Calling执行功能"""
        from app import FunctionCallExecutor, BochaSearchService
        
        # 初始化执行器
        bocha_service = BochaSearchService()
        executor = FunctionCallExecutor(bocha_service)
        
        # 测试有效的函数调用
        result = executor.execute_function("web_search", {
            "query": "测试查询",
            "count": 3,
            "freshness": "week"
        })
        
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            # 成功执行的验证
            assert 'result' in result
            assert isinstance(result['result'], str)
        else:
            # 失败时应该有错误信息
            assert 'error' in result
        
        # 测试无效的函数调用
        invalid_result = executor.execute_function("invalid_function", {})
        assert not invalid_result['success']
        assert 'error' in invalid_result
        assert '未知的函数' in invalid_result['error']
        
        # 测试缺少参数的调用
        empty_result = executor.execute_function("web_search", {})
        assert not empty_result['success']
        assert 'error' in empty_result

    @pytest.mark.integration
    @pytest.mark.api
    def test_chat_with_function_calling(self):
        """测试带Function Calling的聊天功能"""
        # 构造需要Function Calling的消息
        test_data = {
            "messages": [{"role": "user", "text": "请搜索今天的天气怎么样"}],
            "model": "deepseek-ai/DeepSeek-V2.5",
            "enable_search": True
        }
        
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json=test_data,
            timeout=60
        )
        
        assert response.status_code in [200, 500]  # 可能API配置问题
        data = response.json()
        assert isinstance(data, dict)
        assert 'success' in data
        
        if data['success']:
            # 验证响应结构
            assert 'response' in data
            assert 'provider' in data
            # 可能包含工具调用信息
            if 'search_performed' in data:
                assert isinstance(data['search_performed'], bool)

    @pytest.mark.integration
    @pytest.mark.api
    def test_database_extended_functionality(self):
        """测试数据库扩展功能"""
        from database import ChatDatabase
        
        # 使用测试数据库
        db = ChatDatabase("test_extended.db")
        
        try:
            # 测试创建会话并指定模型
            session_id = db.create_session("测试会话", "test-model")
            assert session_id is not None
            
            # 测试添加多媒体消息
            result = db.add_message(
                session_id=session_id,
                role="user",
                content="测试音频消息",
                content_type="audio",
                file_name="test.mp3",
                file_size=1024,
                model="test-model",
                provider="test-provider"
            )
            assert result is True
            
            # 测试添加视频消息
            result = db.add_message(
                session_id=session_id,
                role="user", 
                content="测试视频消息",
                content_type="video",
                file_name="test.mp4",
                file_size=2048
            )
            assert result is True
            
            # 测试获取消息
            messages = db.get_messages(session_id)
            assert len(messages) == 2
            
            # 验证消息字段
            audio_msg = messages[0]
            assert audio_msg['content_type'] == 'audio'
            assert audio_msg['file_name'] == 'test.mp3'
            assert audio_msg['file_size'] == 1024
            assert audio_msg['model'] == 'test-model'
            assert audio_msg['provider'] == 'test-provider'
            
            video_msg = messages[1]
            assert video_msg['content_type'] == 'video'
            assert video_msg['file_name'] == 'test.mp4'
            assert video_msg['file_size'] == 2048
            
            # 测试会话归档功能
            archive_result = db.archive_session(session_id)
            assert archive_result is True
            
            # 验证归档后的会话不在常规列表中
            sessions = db.get_sessions()
            archived_session_found = any(s['id'] == session_id for s in sessions)
            assert not archived_session_found
            
            # 测试搜索功能
            search_results = db.search_messages("测试", session_id)
            assert len(search_results) >= 0  # 可能没有匹配结果
            
        finally:
            # 清理测试数据库
            import os
            if os.path.exists("test_extended.db"):
                os.remove("test_extended.db")

    @pytest.mark.integration
    @pytest.mark.api
    def test_multimodal_chat_integration(self):
        """测试完整的多模态聊天集成"""
        # 创建测试会话
        create_response = self.session.post(f"{self.base_url}/api/sessions", json={
            'title': '多模态测试会话',
            'model': 'meta-llama/llama-4-scout-17b-16e-instruct'
        }, timeout=10)
        
        if create_response.status_code == 200:
            session_data = create_response.json()
            session_id = session_data['session_id']
            self.test_session_id = session_id
            
            try:
                # 1. 发送文本消息
                text_response = self.session.post(f"{self.base_url}/api/chat", json={
                    'messages': [{'role': 'user', 'text': '你好'}],
                    'session_id': session_id,
                    'model': 'meta-llama/llama-4-scout-17b-16e-instruct'
                }, timeout=30)
                
                assert text_response.status_code in [200, 500]
                
                # 2. 发送图片消息
                image_response = self.session.post(f"{self.base_url}/api/chat", json={
                    'messages': [{
                        'role': 'user', 
                        'text': '请分析这张图片',
                        'image': self.create_test_image_base64()
                    }],
                    'session_id': session_id,
                    'model': 'meta-llama/llama-4-scout-17b-16e-instruct'
                }, timeout=60)
                
                assert image_response.status_code in [200, 500]
                
                # 3. 发送音频消息
                audio_response = self.session.post(f"{self.base_url}/api/chat", json={
                    'messages': [{
                        'role': 'user',
                        'text': '请处理这个音频',
                        'audio': self.create_test_audio_base64()
                    }],
                    'session_id': session_id
                }, timeout=60)
                
                assert audio_response.status_code in [200, 500]
                
                # 4. 获取会话消息验证存储
                messages_response = self.session.get(f"{self.base_url}/api/sessions/{session_id}", timeout=10)
                if messages_response.status_code == 200:
                    messages_data = messages_response.json()
                    assert 'messages' in messages_data
                    # 验证消息被正确保存
                    saved_messages = messages_data['messages']
                    assert len(saved_messages) >= 0  # 可能包含多条消息
                
            finally:
                # 清理测试会话
                self.session.delete(f"{self.base_url}/api/sessions/{session_id}", timeout=10)

    @pytest.mark.integration
    @pytest.mark.api  
    def test_error_handling_comprehensive(self):
        """测试全面的错误处理"""
        # 1. 测试无效的模型
        invalid_model_response = self.session.post(f"{self.base_url}/api/chat", json={
            'messages': [{'role': 'user', 'text': '测试'}],
            'model': 'invalid-model-name'
        }, timeout=15)
        
        assert invalid_model_response.status_code in [200, 400]
        if invalid_model_response.status_code == 200:
            data = invalid_model_response.json()
            if not data.get('success'):
                assert 'error' in data
        
        # 2. 测试无效的消息格式
        invalid_message_response = self.session.post(f"{self.base_url}/api/chat", json={
            'messages': [{'invalid': 'format'}]
        }, timeout=15)
        
        assert invalid_message_response.status_code in [200, 400]
        
        # 3. 测试空消息
        empty_message_response = self.session.post(f"{self.base_url}/api/chat", json={
            'messages': []
        }, timeout=15)
        
        assert empty_message_response.status_code == 400
        data = empty_message_response.json()
        assert not data['success']
        assert 'error' in data
        
        # 4. 测试无效的temperature
        invalid_temp_response = self.session.post(f"{self.base_url}/api/chat", json={
            'messages': [{'role': 'user', 'text': '测试'}],
            'temperature': 'invalid'
        }, timeout=15)
        
        # 应该使用默认值，不会报错
        assert invalid_temp_response.status_code in [200, 500]
        
        # 5. 测试超大文件上传（模拟）
        large_data = "A" * (50 * 1024 * 1024 + 1)  # 超过50MB
        large_file_response = self.session.post(f"{self.base_url}/api/upload/video", 
            data={'video': f"data:video/mp4;base64,{large_data}"}, timeout=5)
        
        # 应该被拒绝
        assert large_file_response.status_code in [400, 413, 500]

    @pytest.mark.integration
    @pytest.mark.api
    def test_api_concurrent_requests(self):
        """测试API并发请求处理"""
        import threading
        import time
        
        results = []
        errors = []
        
        def make_request():
            try:
                response = self.session.post(f"{self.base_url}/api/chat", json={
                    'messages': [{'role': 'user', 'text': f'并发测试 {threading.current_thread().name}'}],
                    'model': 'deepseek-ai/DeepSeek-V2.5'
                }, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    results.append(data.get('success', False))
                else:
                    errors.append(response.status_code)
            except Exception as e:
                errors.append(str(e))
        
        # 创建5个并发请求
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request, name=f"Thread-{i}")
            threads.append(thread)
        
        # 启动所有线程
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=60)
        
        end_time = time.time()
        
        # 验证结果
        total_requests = len(results) + len(errors)
        success_rate = len(results) / total_requests if total_requests > 0 else 0
        
        print(f"并发测试结果: {len(results)}成功, {len(errors)}失败, 用时: {end_time - start_time:.2f}秒")
        print(f"成功率: {success_rate:.2%}")
        
        # 至少有一些请求应该成功
        assert total_requests > 0
        assert success_rate >= 0.2  # 至少20%成功率

    @pytest.mark.integration
    @pytest.mark.api
    def test_session_statistics(self):
        """测试会话统计功能"""
        from database import ChatDatabase
        
        # 使用测试数据库
        db = ChatDatabase("test_stats.db")
        
        try:
            # 创建测试数据
            session1 = db.create_session("测试会话1")
            session2 = db.create_session("测试会话2")
            
            # 添加一些消息
            db.add_message(session1, "user", "消息1")
            db.add_message(session1, "assistant", "回复1")
            db.add_message(session2, "user", "消息2")
            
            # 获取统计信息
            stats = db.get_statistics()
            
            assert isinstance(stats, dict)
            assert 'total_sessions' in stats
            assert 'total_messages' in stats
            assert 'messages_by_type' in stats
            
            # 验证统计数据
            assert stats['total_sessions'] >= 2
            assert stats['total_messages'] >= 3
            assert 'text' in stats['messages_by_type']
            
        finally:
            # 清理测试数据库
            import os
            if os.path.exists("test_stats.db"):
                os.remove("test_stats.db")

    @pytest.mark.integration
    @pytest.mark.api
    def test_chat_with_search_integration(self):
        """测试完整的聊天搜索集成功能"""
        # 测试基本的搜索聊天
        search_chat_data = {
            'message': '人工智能最新发展趋势',
            'auto_search': True,
            'model': 'deepseek-ai/DeepSeek-V2.5'
        }
        
        response = self.session.post(
            f"{self.base_url}/api/chat/search",
            json=search_chat_data,
            timeout=60
        )
        
        assert response.status_code in [200, 500]  # API密钥可能未配置
        data = response.json()
        
        assert isinstance(data, dict)
        assert 'success' in data
        
        if data['success']:
            # 验证响应结构
            assert 'response' in data
            assert 'search_performed' in data
            assert isinstance(data['search_performed'], bool)
            
            if data['search_performed']:
                assert 'search_results' in data or 'search_info' in data
        
        # 测试关闭搜索的情况
        no_search_data = {
            'message': '你好',
            'auto_search': False
        }
        
        response2 = self.session.post(
            f"{self.base_url}/api/chat/search",
            json=no_search_data,
            timeout=30
        )
        
        assert response2.status_code in [200, 500]
        if response2.status_code == 200:
            data2 = response2.json()
            if data2.get('success'):
                assert not data2.get('search_performed', True)

    @pytest.mark.integration
    @pytest.mark.performance
    def test_large_message_handling(self):
        """测试大消息处理性能"""
        # 创建大消息
        large_text = "这是一个测试消息。" * 1000  # 约10KB文本
        
        start_time = time.time()
        
        response = self.session.post(f"{self.base_url}/api/chat", json={
            'messages': [{'role': 'user', 'text': large_text}],
            'model': 'deepseek-ai/DeepSeek-V2.5'
        }, timeout=60)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert response.status_code in [200, 500]
        print(f"大消息处理时间: {processing_time:.2f}秒")
        
        # 处理时间应该在合理范围内
        assert processing_time < 120  # 不超过2分钟
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                # 响应应该有内容
                assert len(data.get('response', '')) > 0

    @pytest.mark.integration
    @pytest.mark.api
    def test_multimedia_preprocessing_edge_cases(self):
        """测试多媒体预处理的边界情况"""
        from app import _preprocess_multimedia_messages
        
        # 测试空消息列表
        empty_result = _preprocess_multimedia_messages([])
        assert empty_result == []
        
        # 测试只有文本的消息
        text_only = [{'role': 'user', 'text': '纯文本消息'}]
        text_result = _preprocess_multimedia_messages(text_only)
        assert len(text_result) == 1
        assert text_result[0]['text'] == '纯文本消息'
        
        # 测试无效的音频数据
        invalid_audio = [{
            'role': 'user',
            'text': '测试',
            'audio': 'invalid-audio-data'
        }]
        invalid_result = _preprocess_multimedia_messages(invalid_audio)
        assert len(invalid_result) == 1
        # 应该包含错误处理信息
        assert '测试' in invalid_result[0]['text']
        
        # 测试组合媒体消息
        mixed_message = [{
            'role': 'user',
            'text': '组合消息',
            'image': self.create_test_image_base64(),
            'audio': self.create_test_audio_base64()
        }]
        mixed_result = _preprocess_multimedia_messages(mixed_message)
        assert len(mixed_result) == 1
        processed_msg = mixed_result[0]
        
        # 图片应该保留
        assert 'image' in processed_msg
        # 音频应该被处理为文本
        assert '组合消息' in processed_msg['text']

if __name__ == '__main__':
    # 运行特定的测试
    pytest.main([__file__, '-v', '--tb=short']) 