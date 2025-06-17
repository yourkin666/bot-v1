#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态聊天机器人
支持SiliconFlow文本处理和Groq图片处理的智能聊天机器人
"""

import os
import requests
import json
import base64
from typing import List, Dict, Union, Optional
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class MultiModalChatBot:
    def __init__(self, siliconflow_api_key: str, groq_api_key: str, 
                 siliconflow_base_url: str = "https://api.siliconflow.cn/v1",
                 groq_base_url: str = "https://api.groq.com/openai/v1"):
        # SiliconFlow配置 (用于文本处理)
        self.siliconflow_api_key = siliconflow_api_key
        self.siliconflow_base_url = siliconflow_base_url.rstrip('/') + '/chat/completions'
        
        # Groq配置 (用于多模态处理)
        self.groq_api_key = groq_api_key
        self.groq_base_url = groq_base_url.rstrip('/') + '/chat/completions'
        
        self.conversation_history: List[Dict[str, str]] = []
        
    def add_message(self, role: str, content: Union[str, List[Dict]]):
        """添加消息到对话历史"""
        self.conversation_history.append({"role": role, "content": content})
        
    def encode_image(self, image_path: str) -> str:
        """将本地图片编码为base64格式"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise Exception(f"图片编码失败: {e}")
    
    def process_image(self, image_path: str, question: str = "请描述这张图片的内容") -> str:
        """使用Groq API处理图片"""
        try:
            # 检查图片文件是否存在
            if not os.path.exists(image_path):
                return f"❌ 图片文件不存在: {image_path}"
            
            # 检查文件大小 (4MB限制)
            file_size = os.path.getsize(image_path)
            if file_size > 4 * 1024 * 1024:  # 4MB
                return f"❌ 图片文件过大: {file_size / 1024 / 1024:.1f}MB，最大支持4MB"
            
            # 编码图片
            base64_image = self.encode_image(image_path)
            
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": question},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "temperature": 0.7,
                "max_completion_tokens": 1024,
                "top_p": 1,
                "stream": False
            }
            
            response = requests.post(self.groq_base_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except requests.exceptions.RequestException as e:
            return f"❌ Groq API请求错误: {e}"
        except Exception as e:
            return f"❌ 图片处理错误: {e}"
    
    def process_image_url(self, image_url: str, question: str = "请描述这张图片的内容") -> str:
        """使用Groq API处理网络图片"""
        try:
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": question},
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            }
                        ]
                    }
                ],
                "temperature": 0.7,
                "max_completion_tokens": 1024,
                "top_p": 1,
                "stream": False
            }
            
            response = requests.post(self.groq_base_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except requests.exceptions.RequestException as e:
            return f"❌ Groq API请求错误: {e}"
        except Exception as e:
            return f"❌ 网络图片处理错误: {e}"
    
    def get_text_response(self, user_input: str, model: str = "deepseek-ai/DeepSeek-V2.5") -> str:
        """使用SiliconFlow API获取文本回复"""
        # 添加用户消息到历史
        self.add_message("user", user_input)
        
        headers = {
            "Authorization": f"Bearer {self.siliconflow_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": self.conversation_history,
            "stream": False,
            "max_tokens": 2000,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(self.siliconflow_base_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
            # 添加AI回复到历史
            self.add_message("assistant", ai_response)
            
            return ai_response
            
        except requests.exceptions.RequestException as e:
            return f"❌ SiliconFlow API请求错误: {e}"
        except KeyError as e:
            return f"❌ 响应格式错误: {e}"
        except Exception as e:
            return f"❌ 未知错误: {e}"
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
        print("✅ 对话历史已清空")
    
    def show_history(self):
        """显示对话历史"""
        if not self.conversation_history:
            print("📝 暂无对话历史")
            return
            
        print("\n=== 对话历史 ===")
        for i, message in enumerate(self.conversation_history, 1):
            role = "用户" if message["role"] == "user" else "助手"
            content = message["content"]
            if isinstance(content, list):
                content = "包含图片的消息"
            elif isinstance(content, str):
                content = content[:100] + "..." if len(content) > 100 else content
            print(f"{i}. {role}: {content}")
        print("===============\n")

def main():
    print("🤖 多模态聊天机器人启动中...")
    
    # API配置 - 从环境变量或.env文件加载
    SILICONFLOW_API_KEY = os.environ.get("SILICONFLOW_API_KEY")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    
    if not GROQ_API_KEY:
        print("❌ 请设置GROQ_API_KEY环境变量或在.env文件中配置")
        print("💡 获取API密钥: https://console.groq.com/keys")
        return
    
    if not SILICONFLOW_API_KEY:
        print("❌ 请设置SILICONFLOW_API_KEY环境变量或在.env文件中配置")
        return
    
    # 初始化多模态聊天机器人
    chatbot = MultiModalChatBot(SILICONFLOW_API_KEY, GROQ_API_KEY)
    
    print("✅ 多模态聊天机器人已启动！")
    print("💡 功能说明:")
    print("  📝 文本对话: 直接输入文字")
    print("  🖼️  本地图片: image:/path/to/image.jpg")
    print("  🌐 网络图片: url:https://example.com/image.jpg")
    print("  🎯 图片问答: image:/path/to/image.jpg 这是什么?")
    print("💡 特殊命令:")
    print("  - 输入 'quit' 或 'exit' 退出程序")
    print("  - 输入 'clear' 清空对话历史")
    print("  - 输入 'history' 查看对话历史")
    print("=" * 50)
    
    while True:
        try:
            user_input = input("\n👤 你: ").strip()
            
            if not user_input:
                continue
                
            # 处理特殊命令
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("👋 再见！")
                break
            elif user_input.lower() in ['clear', '清空']:
                chatbot.clear_history()
                continue
            elif user_input.lower() in ['history', '历史']:
                chatbot.show_history()
                continue
            
            # 处理图片相关命令
            if user_input.startswith('image:'):
                parts = user_input.split(' ', 1)
                image_path = parts[0][6:]  # 去掉 'image:' 前缀
                question = parts[1] if len(parts) > 1 else "请描述这张图片的内容"
                
                print("🖼️ 正在分析图片...")
                response = chatbot.process_image(image_path, question)
                print(f"🤖 助手: {response}")
                
            elif user_input.startswith('url:'):
                parts = user_input.split(' ', 1)
                image_url = parts[0][4:]  # 去掉 'url:' 前缀
                question = parts[1] if len(parts) > 1 else "请描述这张图片的内容"
                
                print("🌐 正在分析网络图片...")
                response = chatbot.process_image_url(image_url, question)
                print(f"🤖 助手: {response}")
                
            else:
                # 普通文本对话
                print("💭 助手正在思考中...")
                response = chatbot.get_text_response(user_input)
                print(f"🤖 助手: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 程序被中断，再见！")
            break
        except Exception as e:
            print(f"❌ 程序错误: {e}")

if __name__ == "__main__":
    main() 