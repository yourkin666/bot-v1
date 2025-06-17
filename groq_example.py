#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Groq多模态处理示例
演示如何使用Groq API进行图片分析
"""

import os
import requests
import base64

class GroqImageProcessor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        
    def encode_image(self, image_path: str) -> str:
        """将本地图片编码为base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def analyze_image(self, image_path: str, question: str = "请详细描述这张图片") -> str:
        """分析本地图片"""
        try:
            base64_image = self.encode_image(image_path)
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
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
                "max_completion_tokens": 1024
            }
            
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            return f"错误: {e}"
    
    def analyze_url(self, image_url: str, question: str = "请详细描述这张图片") -> str:
        """分析网络图片"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
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
                "max_completion_tokens": 1024
            }
            
            response = requests.post(self.base_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except Exception as e:
            return f"错误: {e}"

def main():
    # 从环境变量获取API密钥
    api_key = os.environ.get("GROQ_API_KEY")
    
    if not api_key:
        print("请设置GROQ_API_KEY环境变量")
        print("获取地址: https://console.groq.com/keys")
        return
    
    processor = GroqImageProcessor(api_key)
    
    # 示例1: 分析网络图片
    print("🌐 分析网络图片...")
    image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
    result = processor.analyze_url(image_url, "这张图片展示了什么场景？")
    print(f"分析结果: {result}\n")
    
    # 示例2: 分析本地图片 (如果存在)
    local_image = "test_image.jpg"
    if os.path.exists(local_image):
        print("🖼️ 分析本地图片...")
        result = processor.analyze_image(local_image, "这张图片里有什么？")
        print(f"分析结果: {result}")
    else:
        print(f"本地图片 {local_image} 不存在，跳过本地分析")

if __name__ == "__main__":
    main() 