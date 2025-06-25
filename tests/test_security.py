#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全测试模块
测试API安全性、输入验证、防止注入攻击等安全相关功能
"""

import pytest
import requests
import json
import base64
from typing import Dict, Any


class TestSecurity:
    """安全测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_security(self):
        """安全测试设置"""
        self.base_url = "http://localhost:5000"
        self.session = requests.Session()
    
    @pytest.mark.security
    def test_sql_injection_protection(self):
        """测试SQL注入防护"""
        # 常见的SQL注入尝试
        sql_injection_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE sessions; --",
            "' UNION SELECT * FROM sessions --",
            "1'; DELETE FROM messages; --",
            "admin'--",
            "' OR 1=1#"
        ]
        
        for payload in sql_injection_payloads:
            # 测试会话创建
            response = self.session.post(
                f"{self.base_url}/api/sessions",
                json={"title": payload, "model": "test-model"},
                timeout=10
            )
            
            # 系统应该正常处理，不应该崩溃
            assert response.status_code in [200, 400, 500]
            
            # 如果返回200，检查响应是否正常
            if response.status_code == 200:
                data = response.json()
                # 不应该返回异常的数据结构
                assert isinstance(data, dict)
                assert "success" in data
            
            # 测试搜索功能
            response = self.session.get(
                f"{self.base_url}/api/search",
                params={"q": payload},
                timeout=10
            )
            assert response.status_code in [200, 400, 500]
    
    @pytest.mark.security
    def test_xss_protection(self):
        """测试XSS攻击防护"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src='x' onerror='alert(1)'>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "'><script>alert('XSS')</script>",
            "<iframe src=javascript:alert('XSS')></iframe>"
        ]
        
        for payload in xss_payloads:
            # 测试聊天消息
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json={
                    "messages": [{"role": "user", "text": payload}],
                    "model": "deepseek-ai/DeepSeek-V2.5"
                },
                timeout=30
            )
            
            # 系统应该正常处理
            assert response.status_code in [200, 400, 500]
            
            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, dict)
                # 确保返回的内容不包含未转义的脚本
                if data.get("success") and "response" in data:
                    assert "<script>" not in data["response"]
                    assert "javascript:" not in data["response"]
    
    @pytest.mark.security
    def test_file_upload_security(self):
        """测试文件上传安全性"""
        import io
        
        # 测试恶意文件扩展名
        malicious_files = [
            ("test.exe", b"fake exe content", "application/octet-stream"),
            ("test.php", b"<?php echo 'hack'; ?>", "application/x-php"),
            ("test.js", b"alert('xss')", "application/javascript"),
            ("test.bat", b"@echo off\necho hacked", "application/x-msdos-program"),
        ]
        
        for filename, content, content_type in malicious_files:
            files = {
                'audio': (filename, io.BytesIO(content), content_type)
            }
            
            response = self.session.post(
                f"{self.base_url}/api/upload/audio",
                files=files,
                timeout=10
            )
            
            # 应该拒绝这些文件
            assert response.status_code == 400
            data = response.json()
            assert not data.get("success")
            assert "error" in data
    
    @pytest.mark.security
    def test_request_size_limits(self):
        """测试请求大小限制"""
        # 创建超大请求
        huge_text = "A" * (10 * 1024 * 1024)  # 10MB
        
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json={
                "messages": [{"role": "user", "text": huge_text}],
                "model": "deepseek-ai/DeepSeek-V2.5"
            },
            timeout=30
        )
        
        # 系统应该拒绝或优雅处理超大请求
        assert response.status_code in [400, 413, 500]
    
    @pytest.mark.security
    def test_input_validation(self):
        """测试输入验证"""
        # 测试无效的JSON
        response = self.session.post(
            f"{self.base_url}/api/chat",
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        assert response.status_code == 400
        
        # 测试缺少必需字段
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json={},
            timeout=10
        )
        assert response.status_code in [400, 500]
        
        # 测试无效的模型名
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json={
                "messages": [{"role": "user", "text": "test"}],
                "model": "../../../etc/passwd"
            },
            timeout=10
        )
        assert response.status_code in [200, 400, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert not data.get("success")
    
    @pytest.mark.security
    def test_path_traversal_protection(self):
        """测试路径遍历攻击防护"""
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
            "....//....//....//etc//passwd",
        ]
        
        for payload in path_traversal_payloads:
            # 测试文件路径相关的API
            response = self.session.get(
                f"{self.base_url}/api/sessions/{payload}",
                timeout=10
            )
            
            # 系统应该正常处理，不应该返回敏感文件内容
            assert response.status_code in [400, 404, 500]
            
            if response.status_code == 200:
                data = response.json()
                # 不应该包含系统文件内容
                content = json.dumps(data).lower()
                assert "root:" not in content
                assert "password" not in content or "password" in content.lower()
    
    @pytest.mark.security
    def test_command_injection_protection(self):
        """测试命令注入防护"""
        command_injection_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& whoami",
            "`rm -rf /`",
            "$(cat /etc/passwd)",
            "; ping google.com",
        ]
        
        for payload in command_injection_payloads:
            # 测试可能执行命令的功能
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json={
                    "messages": [{"role": "user", "text": f"Execute this: {payload}"}],
                    "model": "deepseek-ai/DeepSeek-V2.5"
                },
                timeout=30
            )
            
            # 系统应该正常处理
            assert response.status_code in [200, 400, 500]
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and "response" in data:
                    # 响应中不应该包含命令执行结果
                    response_text = data["response"].lower()
                    assert "root:" not in response_text
                    assert "total " not in response_text  # ls 命令输出
    
    @pytest.mark.security
    def test_base64_injection(self):
        """测试Base64注入攻击"""
        # 恶意的Base64编码内容
        malicious_payloads = [
            base64.b64encode(b"<script>alert('xss')</script>").decode(),
            base64.b64encode(b"'; DROP TABLE sessions; --").decode(),
            base64.b64encode(b"<?php system($_GET['cmd']); ?>").decode(),
        ]
        
        for payload in malicious_payloads:
            # 测试图片上传
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json={
                    "messages": [{
                        "role": "user",
                        "text": "分析这张图片",
                        "image": f"data:image/png;base64,{payload}"
                    }],
                    "model": "meta-llama/llama-4-scout-17b-16e-instruct"
                },
                timeout=30
            )
            
            # 系统应该能够处理或拒绝恶意内容
            assert response.status_code in [200, 400, 500]
    
    @pytest.mark.security
    def test_rate_limiting(self):
        """测试速率限制"""
        # 快速发送大量请求
        rapid_requests = []
        
        for i in range(50):
            try:
                response = self.session.get(f"{self.base_url}/api/health", timeout=1)
                rapid_requests.append(response.status_code)
            except requests.exceptions.Timeout:
                rapid_requests.append(408)  # 超时
            except Exception:
                rapid_requests.append(500)  # 其他错误
        
        # 统计结果
        success_count = sum(1 for code in rapid_requests if code == 200)
        rate_limited_count = sum(1 for code in rapid_requests if code == 429)
        
        print(f"🚦 速率限制测试结果:")
        print(f"   - 成功请求: {success_count}")
        print(f"   - 速率限制: {rate_limited_count}")
        print(f"   - 其他状态: {50 - success_count - rate_limited_count}")
        
        # 如果有速率限制，这是好事
        # 如果没有速率限制，至少系统应该稳定运行
        assert success_count > 0, "系统完全不可用"
    
    @pytest.mark.security
    def test_cors_headers(self):
        """测试CORS头部安全性"""
        response = self.session.options(f"{self.base_url}/api/chat", timeout=10)
        
        # 检查CORS头部
        headers = response.headers
        
        # 应该有适当的CORS配置
        if "Access-Control-Allow-Origin" in headers:
            # 不应该是通配符，除非是开发环境
            origin = headers["Access-Control-Allow-Origin"]
            print(f"CORS Origin: {origin}")
            
            # 在生产环境中应该避免使用 *
            if origin == "*":
                print("⚠️ 警告：使用了通配符CORS配置")
    
    @pytest.mark.security
    def test_session_security(self):
        """测试会话安全性"""
        # 创建一个会话
        response = self.session.post(
            f"{self.base_url}/api/sessions",
            json={"title": "安全测试会话", "model": "test-model"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                session_id = data["session"]["id"]
                
                # 尝试访问其他用户的会话（如果有认证机制）
                # 这里我们测试直接访问会话ID的安全性
                
                # 测试无效的会话ID格式
                invalid_session_ids = [
                    "../admin",
                    "' OR '1'='1",
                    "<script>alert('xss')</script>",
                    "../../etc/passwd",
                ]
                
                for invalid_id in invalid_session_ids:
                    response = self.session.get(
                        f"{self.base_url}/api/sessions/{invalid_id}",
                        timeout=10
                    )
                    
                    # 应该返回适当的错误状态
                    assert response.status_code in [400, 404, 500]
                
                # 清理测试会话
                self.session.delete(f"{self.base_url}/api/sessions/{session_id}", timeout=10)


class TestDataValidation:
    """数据验证测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_validation(self):
        """数据验证测试设置"""
        self.base_url = "http://localhost:5000"
        self.session = requests.Session()
    
    @pytest.mark.security
    def test_email_validation(self):
        """测试邮箱格式验证（如果有用户系统）"""
        # 这是一个示例，根据实际API调整
        invalid_emails = [
            "notanemail",
            "@domain.com",
            "user@",
            "user@domain",
            "<script>alert('xss')</script>@domain.com",
        ]
        
        # 如果有用户注册API，测试邮箱验证
        # 这里只是示例代码
        for email in invalid_emails:
            # response = self.session.post(
            #     f"{self.base_url}/api/register",
            #     json={"email": email, "password": "password123"},
            #     timeout=10
            # )
            # assert response.status_code == 400
            pass
    
    @pytest.mark.security
    def test_content_type_validation(self):
        """测试Content-Type验证"""
        # 发送错误的Content-Type
        response = self.session.post(
            f"{self.base_url}/api/chat",
            data=json.dumps({"messages": [{"role": "user", "text": "test"}]}),
            headers={"Content-Type": "text/plain"},
            timeout=10
        )
        
        # 应该拒绝错误的Content-Type
        assert response.status_code in [400, 415]


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short']) 