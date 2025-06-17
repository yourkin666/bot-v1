#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态聊天机器人功能演示
展示SiliconFlow + Groq的强大组合
"""

import requests
import json
import base64
import os
from dotenv import load_dotenv
import time

# 加载环境变量
load_dotenv()

class MultiModalDemo:
    def __init__(self, api_base_url="http://localhost:5000"):
        self.api_base_url = api_base_url
        self.session_history = []
        
    def test_text_chat(self):
        """测试文本对话功能"""
        print("🔥 测试文本对话功能")
        print("=" * 50)
        
        test_messages = [
            "你好，请介绍一下自己",
            "你能做什么？",
            "请用一首诗描述春天"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n📝 测试 {i}: {message}")
            response = self._send_message([{"role": "user", "text": message}])
            
            if response:
                print(f"🤖 回复: {response[:200]}..." if len(response) > 200 else f"🤖 回复: {response}")
            else:
                print("❌ 请求失败")
            
            time.sleep(1)  # 避免请求过于频繁
    
    def test_image_analysis(self):
        """测试图片分析功能"""
        print("\n🖼️ 测试图片分析功能")
        print("=" * 50)
        
        # 使用网络图片进行测试
        test_image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/640px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
        
        # 将网络图片转换为base64
        try:
            import urllib.request
            with urllib.request.urlopen(test_image_url) as response:
                image_data = response.read()
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                data_url = f"data:image/jpeg;base64,{image_base64}"
            
            test_questions = [
                "请详细描述这张图片的内容",
                "这张图片的主要色调是什么？",
                "图片中有什么自然元素？"
            ]
            
            for i, question in enumerate(test_questions, 1):
                print(f"\n🖼️ 图片分析 {i}: {question}")
                response = self._send_message([{
                    "role": "user", 
                    "text": question,
                    "image": data_url
                }])
                
                if response:
                    print(f"🤖 回复: {response[:200]}..." if len(response) > 200 else f"🤖 回复: {response}")
                else:
                    print("❌ 请求失败")
                
                time.sleep(1)
                
        except Exception as e:
            print(f"❌ 图片分析测试失败: {e}")
    
    def test_model_switching(self):
        """测试模型自动切换功能"""
        print("\n🚀 测试模型自动切换功能")
        print("=" * 50)
        
        # 首先发送纯文本消息（应该使用SiliconFlow）
        print("\n1. 发送纯文本消息（应使用SiliconFlow）:")
        response_data = self._send_message_detailed([{
            "role": "user", 
            "text": "你好，请问今天天气怎么样？"
        }])
        
        if response_data:
            print(f"   使用模型: {response_data.get('model', 'unknown')}")
            print(f"   服务提供商: {response_data.get('provider', 'unknown')}")
        
        time.sleep(1)
        
        # 然后发送带图片的消息（应该自动切换到Groq）
        print("\n2. 发送带图片的消息（应自动切换到Groq）:")
        try:
            # 创建一个简单的测试图片（1x1像素的PNG）
            test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
            data_url = f"data:image/png;base64,{test_image_base64}"
            
            response_data = self._send_message_detailed([{
                "role": "user", 
                "text": "请分析这张图片",
                "image": data_url
            }])
            
            if response_data:
                print(f"   使用模型: {response_data.get('model', 'unknown')}")
                print(f"   服务提供商: {response_data.get('provider', 'unknown')}")
            
        except Exception as e:
            print(f"   测试失败: {e}")
    
    def test_api_health(self):
        """测试API健康状态"""
        print("\n💊 API健康检查")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.api_base_url}/api/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print("✅ API服务正常")
                print(f"   状态: {data.get('status')}")
                print(f"   消息: {data.get('message')}")
                
                capabilities = data.get('capabilities', {})
                print("\n📋 功能可用性:")
                print(f"   SiliconFlow API: {'✅' if capabilities.get('siliconflow_available') else '❌'}")
                print(f"   Groq API: {'✅' if capabilities.get('groq_available') else '❌'}")
                print(f"   多模态支持: {'✅' if capabilities.get('multimodal_support') else '❌'}")
                
                return True
            else:
                print(f"❌ API服务异常: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 无法连接到API服务: {e}")
            return False
    
    def test_available_models(self):
        """测试可用模型"""
        print("\n🧠 可用模型检查")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.api_base_url}/api/models", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                
                print(f"✅ 找到 {len(models)} 个可用模型:")
                for model in models:
                    icon = "🖼️" if model.get('supports_image') else "📝"
                    provider = model.get('provider', 'unknown')
                    print(f"   {icon} {model.get('name')} ({provider})")
                
                capabilities = data.get('capabilities', {})
                print(f"\n💡 系统能力:")
                print(f"   文本对话: {'✅' if capabilities.get('text_chat') else '❌'}")
                print(f"   图片分析: {'✅' if capabilities.get('image_analysis') else '❌'}")
                print(f"   多模态: {'✅' if capabilities.get('multimodal') else '❌'}")
                
                return True
            else:
                print(f"❌ 获取模型列表失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 无法获取模型列表: {e}")
            return False
    
    def _send_message(self, messages, model="deepseek-ai/DeepSeek-V2.5"):
        """发送消息到API"""
        try:
            response = requests.post(
                f"{self.api_base_url}/api/chat",
                json={"messages": messages, "model": model},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data.get('response')
            
            return None
        except Exception as e:
            print(f"请求错误: {e}")
            return None
    
    def _send_message_detailed(self, messages, model="deepseek-ai/DeepSeek-V2.5"):
        """发送消息到API并返回详细信息"""
        try:
            response = requests.post(
                f"{self.api_base_url}/api/chat",
                json={"messages": messages, "model": model},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return data
            
            return None
        except Exception as e:
            print(f"请求错误: {e}")
            return None

def main():
    print("🚀 多模态聊天机器人功能演示")
    print("=" * 60)
    
    demo = MultiModalDemo()
    
    # 检查API服务是否可用
    if not demo.test_api_health():
        print("\n❌ API服务不可用，请确保后端服务已启动:")
        print("   python3 app.py")
        return
    
    print("\n" + "=" * 60)
    
    # 检查可用模型
    if not demo.test_available_models():
        return
    
    print("\n" + "=" * 60)
    
    # 测试文本对话
    demo.test_text_chat()
    
    # 测试图片分析
    demo.test_image_analysis()
    
    # 测试模型自动切换
    demo.test_model_switching()
    
    print("\n" + "=" * 60)
    print("🎉 演示完成！您的多模态聊天机器人功能正常！")
    print("💡 现在您可以:")
    print("   1. 访问 http://localhost:5000 使用Web界面")
    print("   2. 发送文本进行对话")
    print("   3. 上传图片进行分析")
    print("   4. 体验智能模型切换功能")

if __name__ == "__main__":
    main() 