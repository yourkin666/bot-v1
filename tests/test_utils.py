#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工具函数模块
提供测试中常用的辅助功能和工具函数
"""

import base64
import io
import random
import string
import tempfile
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class TestDataGenerator:
    """测试数据生成器"""
    
    @staticmethod
    def generate_random_text(length: int = 100) -> str:
        """生成随机文本"""
        return ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=length))
    
    @staticmethod
    def generate_chinese_text() -> str:
        """生成中文测试文本"""
        chinese_texts = [
            "你好，我是一个AI助手。",
            "请帮我分析这个问题。",
            "今天天气很好，适合户外活动。",
            "人工智能技术正在快速发展。",
            "测试中文字符处理能力。"
        ]
        return random.choice(chinese_texts)
    
    @staticmethod
    def generate_test_image_base64() -> str:
        """生成测试用的base64编码图片"""
        # 1x1像素的红色PNG图片
        red_pixel_png = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        )
        return f"data:image/png;base64,{red_pixel_png}"
    
    @staticmethod
    def generate_test_audio_base64() -> str:
        """生成测试用的base64编码音频"""
        # 简单的WAV文件头
        wav_header = (
            "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="
        )
        return f"data:audio/wav;base64,{wav_header}"


if __name__ == '__main__':
    # 测试工具函数
    generator = TestDataGenerator()
    print("随机文本:", generator.generate_random_text(50))
    print("中文文本:", generator.generate_chinese_text())
    print("测试图片:", generator.generate_test_image_base64()[:50] + "...") 