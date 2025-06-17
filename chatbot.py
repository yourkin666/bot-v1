#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SiliconFlow 聊天机器人
使用SiliconFlow API实现的智能聊天机器人
"""

import os
import requests
import json
from typing import List, Dict

class SiliconFlowChatBot:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/') + '/chat/completions'
        self.conversation_history: List[Dict[str, str]] = []
        
    def add_message(self, role: str, content: str):
        """添加消息到对话历史"""
        self.conversation_history.append({"role": role, "content": content})
        
    def get_response(self, user_input: str, model: str = "deepseek-ai/DeepSeek-V2.5") -> str:
        """获取AI回复"""
        # 添加用户消息到历史
        self.add_message("user", user_input)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
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
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
            # 添加AI回复到历史
            self.add_message("assistant", ai_response)
            
            return ai_response
            
        except requests.exceptions.RequestException as e:
            return f"网络请求错误: {e}"
        except KeyError as e:
            return f"响应格式错误: {e}"
        except Exception as e:
            return f"未知错误: {e}"
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
        print("对话历史已清空")
    
    def show_history(self):
        """显示对话历史"""
        if not self.conversation_history:
            print("暂无对话历史")
            return
            
        print("\n=== 对话历史 ===")
        for i, message in enumerate(self.conversation_history, 1):
            role = "用户" if message["role"] == "user" else "助手"
            print(f"{i}. {role}: {message['content'][:100]}...")
        print("===============\n")

def main():
    print("🤖 SiliconFlow 聊天机器人启动中...")
    
    # API配置
    API_KEY = "sk-icupqsqwcgsfnqbwpcgfertxbdlkksapxtacxlupjzanguyv"
    BASE_URL = "https://api.siliconflow.cn/v1"
    
    # 初始化聊天机器人
    chatbot = SiliconFlowChatBot(API_KEY, BASE_URL)
    
    print("✅ 聊天机器人已启动！")
    print("💡 提示:")
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
            
            # 获取AI回复
            print("🤖 助手正在思考中...")
            response = chatbot.get_response(user_input)
            print(f"🤖 助手: {response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 程序被中断，再见！")
            break
        except Exception as e:
            print(f"❌ 程序错误: {e}")

if __name__ == "__main__":
    main() 