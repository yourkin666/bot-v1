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