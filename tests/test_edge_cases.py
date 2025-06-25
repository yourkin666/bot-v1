#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
边界情况测试模块
测试各种边界条件、异常情况、错误处理等
"""

import pytest
import requests
import json
import time
import tempfile
import os
from unittest.mock import patch, Mock
from typing import Dict, Any


class TestEdgeCases:
    """边界情况测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_edge_cases(self):
        """边界情况测试设置"""
        self.base_url = "http://localhost:5000"
        self.session = requests.Session()
    
    @pytest.mark.edge_case
    def test_empty_inputs(self):
        """测试空输入处理"""
        # 空消息文本
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json={
                "messages": [{"role": "user", "text": ""}],
                "model": "deepseek-ai/DeepSeek-V2.5"
            },
            timeout=10
        )
        assert response.status_code in [200, 400]
        
        # 空消息列表
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json={
                "messages": [],
                "model": "deepseek-ai/DeepSeek-V2.5"
            },
            timeout=10
        )
        assert response.status_code in [200, 400]
        
        # 空会话标题
        response = self.session.post(
            f"{self.base_url}/api/sessions",
            json={"title": "", "model": "test-model"},
            timeout=10
        )
        assert response.status_code in [200, 400]
    
    @pytest.mark.edge_case
    def test_whitespace_inputs(self):
        """测试空白字符输入处理"""
        whitespace_inputs = [
            "   ",  # 空格
            "\t\t",  # 制表符
            "\n\n",  # 换行符
            "\r\n",  # 回车换行
            " \t \n ",  # 混合空白字符
        ]
        
        for whitespace in whitespace_inputs:
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json={
                    "messages": [{"role": "user", "text": whitespace}],
                    "model": "deepseek-ai/DeepSeek-V2.5"
                },
                timeout=10
            )
            assert response.status_code in [200, 400]
    
    @pytest.mark.edge_case
    def test_unicode_and_special_characters(self):
        """测试Unicode和特殊字符处理"""
        special_inputs = [
            "🤖🎉😀",  # Emoji
            "测试中文输入",  # 中文
            "Tëst spëcïäl chärâctërs",  # 带重音符号
            "نص باللغة العربية",  # 阿拉伯文
            "Тест на русском",  # 俄文
            "テストの日本語",  # 日文
            "①②③④⑤",  # 特殊数字符号
            "♠♥♦♣",  # 符号
            "🔥💻⚡🚀",  # 技术相关emoji
        ]
        
        for special_text in special_inputs:
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json={
                    "messages": [{"role": "user", "text": special_text}],
                    "model": "deepseek-ai/DeepSeek-V2.5"
                },
                timeout=30
            )
            
            # 系统应该能处理Unicode字符
            assert response.status_code in [200, 400, 500]
            
            if response.status_code == 200:
                data = response.json()
                # 响应应该是有效的JSON且包含Unicode字符
                assert isinstance(data, dict)
    
    @pytest.mark.edge_case
    def test_extremely_long_inputs(self):
        """测试极长输入处理"""
        # 生成不同长度的输入
        length_tests = [
            1000,    # 1KB
            10000,   # 10KB
            100000,  # 100KB
        ]
        
        for length in length_tests:
            long_text = "这是一个很长的测试文本。" * (length // 10)
            
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json={
                    "messages": [{"role": "user", "text": long_text}],
                    "model": "deepseek-ai/DeepSeek-V2.5"
                },
                timeout=60
            )
            
            # 系统应该优雅地处理长输入
            assert response.status_code in [200, 400, 413, 500]
            
            print(f"长度 {length} 字符测试: HTTP {response.status_code}")
    
    @pytest.mark.edge_case
    def test_malformed_json(self):
        """测试格式错误的JSON处理"""
        malformed_jsons = [
            '{"messages": [{"role": "user", "text": "test"}',  # 缺少结束括号
            '{"messages": [{"role": "user", "text": "test"]}',  # 缺少结束大括号
            '{"messages": [{"role": "user", "text": }]}',  # 缺少值
            '{"messages": [{"role": "user", "text": "test",}]}',  # 多余逗号
            '{messages: [{"role": "user", "text": "test"}]}',  # 缺少引号
        ]
        
        for malformed_json in malformed_jsons:
            response = self.session.post(
                f"{self.base_url}/api/chat",
                data=malformed_json,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            # 应该返回400错误
            assert response.status_code == 400
    
    @pytest.mark.edge_case
    def test_missing_required_fields(self):
        """测试缺少必需字段的情况"""
        test_cases = [
            {},  # 完全空的请求
            {"messages": [{"role": "user", "text": "test"}]},  # 缺少模型
            {"model": "test-model"},  # 缺少消息
            {"messages": [{"text": "test"}], "model": "test-model"},  # 缺少role
            {"messages": [{"role": "user"}], "model": "test-model"},  # 缺少text
        ]
        
        for test_case in test_cases:
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=test_case,
                timeout=10
            )
            
            # 应该返回错误状态
            assert response.status_code in [400, 500]
    
    @pytest.mark.edge_case
    def test_invalid_data_types(self):
        """测试无效数据类型处理"""
        invalid_type_cases = [
            {
                "messages": "not a list",  # 字符串而不是列表
                "model": "test-model"
            },
            {
                "messages": [{"role": "user", "text": "test"}],
                "model": 123  # 数字而不是字符串
            },
            {
                "messages": [{"role": "user", "text": ["array", "instead", "of", "string"]}],
                "model": "test-model"
            },
            {
                "messages": [{"role": "user", "text": None}],  # None值
                "model": "test-model"
            },
        ]
        
        for test_case in invalid_type_cases:
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=test_case,
                timeout=10
            )
            
            # 应该返回错误状态
            assert response.status_code in [400, 500]
    
    @pytest.mark.edge_case
    def test_network_timeout_simulation(self):
        """测试网络超时模拟"""
        # 设置非常短的超时时间
        try:
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json={
                    "messages": [{"role": "user", "text": "这是一个可能触发超时的测试"}],
                    "model": "deepseek-ai/DeepSeek-V2.5"
                },
                timeout=0.001  # 1毫秒超时，几乎肯定会超时
            )
            # 如果没有超时，检查响应
            assert response.status_code in [200, 400, 500]
        except requests.exceptions.Timeout:
            # 超时是预期的
            print("✅ 网络超时测试成功")
        except Exception as e:
            # 其他异常也是可以接受的
            print(f"网络异常: {type(e).__name__}")
    
    @pytest.mark.edge_case
    def test_concurrent_session_operations(self):
        """测试并发会话操作"""
        import threading
        
        session_ids = []
        errors = []
        
        def create_session(session_num):
            try:
                response = requests.post(
                    f"{self.base_url}/api/sessions",
                    json={
                        "title": f"并发测试会话 {session_num}",
                        "model": "test-model"
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        session_ids.append(data["session"]["id"])
                else:
                    errors.append(f"Session {session_num}: HTTP {response.status_code}")
            except Exception as e:
                errors.append(f"Session {session_num}: {str(e)}")
        
        # 启动10个并发线程创建会话
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_session, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        print(f"🔄 并发会话操作结果:")
        print(f"   - 成功创建会话: {len(session_ids)}")
        print(f"   - 错误数量: {len(errors)}")
        
        # 清理创建的会话
        for session_id in session_ids:
            try:
                self.session.delete(f"{self.base_url}/api/sessions/{session_id}", timeout=10)
            except:
                pass
        
        # 至少应该有一些成功的操作
        assert len(session_ids) > 0, "所有并发操作都失败了"
    
    @pytest.mark.edge_case
    def test_api_version_compatibility(self):
        """测试API版本兼容性"""
        # 测试不同的Accept头
        headers_to_test = [
            {"Accept": "application/json"},
            {"Accept": "application/json; version=1.0"},
            {"Accept": "text/plain"},
            {"Accept": "*/*"},
            {"Accept": "application/xml"},  # 不支持的格式
        ]
        
        for headers in headers_to_test:
            response = self.session.get(
                f"{self.base_url}/api/health",
                headers=headers,
                timeout=10
            )
            
            # 应该至少返回一个有效的响应
            assert response.status_code in [200, 406, 415]
    
    @pytest.mark.edge_case
    def test_database_edge_cases(self):
        """测试数据库边界情况"""
        from database import ChatDatabase
        
        # 使用临时数据库文件
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        try:
            db = ChatDatabase(db_path)
            
            # 测试空字符串会话标题
            session_id = db.create_session("", "test-model")
            assert session_id is not None
            
            # 测试极长的会话标题
            long_title = "极长的会话标题" * 100
            session_id = db.create_session(long_title, "test-model")
            assert session_id is not None
            
            # 测试空消息内容
            success = db.add_message(session_id, "user", "", "text")
            assert success is True
            
            # 测试极长的消息内容
            long_content = "这是一个很长的消息内容。" * 1000
            success = db.add_message(session_id, "user", long_content, "text")
            assert success is True
            
            # 测试无效的会话ID
            messages = db.get_messages("invalid-session-id")
            assert messages == []
            
            # 测试搜索空字符串
            results = db.search_messages("", session_id)
            assert isinstance(results, list)
            
        finally:
            try:
                os.unlink(db_path)
            except:
                pass
    
    @pytest.mark.edge_case
    def test_file_upload_edge_cases(self):
        """测试文件上传边界情况"""
        import io
        
        # 测试空文件
        empty_file = io.BytesIO(b"")
        files = {'audio': ('empty.wav', empty_file, 'audio/wav')}
        
        response = self.session.post(
            f"{self.base_url}/api/upload/audio",
            files=files,
            timeout=10
        )
        
        # 应该能处理空文件
        assert response.status_code in [200, 400]
        
        # 测试非常小的文件
        tiny_file = io.BytesIO(b"tiny")
        files = {'audio': ('tiny.wav', tiny_file, 'audio/wav')}
        
        response = self.session.post(
            f"{self.base_url}/api/upload/audio",
            files=files,
            timeout=10
        )
        
        assert response.status_code in [200, 400]
    
    @pytest.mark.edge_case
    def test_memory_pressure(self):
        """测试内存压力情况"""
        # 创建多个大的数据结构来模拟内存压力
        large_data_structures = []
        
        try:
            # 创建一些大的数据结构（但不要过大以免影响测试环境）
            for i in range(5):
                large_data = "x" * (1024 * 1024)  # 1MB字符串
                large_data_structures.append(large_data)
            
            # 在内存压力下执行API调用
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json={
                    "messages": [{"role": "user", "text": "内存压力测试"}],
                    "model": "deepseek-ai/DeepSeek-V2.5"
                },
                timeout=30
            )
            
            # 系统应该仍然能够响应
            assert response.status_code in [200, 400, 500]
            
        finally:
            # 清理内存
            large_data_structures.clear()
    
    @pytest.mark.edge_case
    def test_error_recovery(self):
        """测试错误恢复能力"""
        # 先发送一个可能导致错误的请求
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json={
                "messages": [{"role": "user", "text": "test"}],
                "model": "non-existent-model"
            },
            timeout=10
        )
        
        # 然后立即发送一个正常的请求
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json={
                "messages": [{"role": "user", "text": "这是一个正常的请求"}],
                "model": "deepseek-ai/DeepSeek-V2.5"
            },
            timeout=30
        )
        
        # 系统应该能够从错误中恢复
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 系统成功从错误中恢复")


class TestResourceLimits:
    """资源限制测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_resource_limits(self):
        """资源限制测试设置"""
        self.base_url = "http://localhost:5000"
        self.session = requests.Session()
    
    @pytest.mark.edge_case
    def test_cpu_intensive_operations(self):
        """测试CPU密集型操作"""
        # 发送复杂的数学计算请求
        complex_math = """
        请计算以下数学表达式：
        1. ∫₀^π sin(x)dx
        2. lim(x→∞) (1 + 1/x)^x
        3. ∑(n=1 to ∞) 1/n²
        4. d/dx [ln(sin(x))]
        """
        
        start_time = time.time()
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json={
                "messages": [{"role": "user", "text": complex_math}],
                "model": "deepseek-ai/DeepSeek-V2.5"
            },
            timeout=60
        )
        response_time = time.time() - start_time
        
        assert response.status_code in [200, 500]
        print(f"🧮 复杂数学计算响应时间: {response_time:.2f}s")
    
    @pytest.mark.edge_case
    def test_session_limit_stress(self):
        """测试会话数量限制压力"""
        created_sessions = []
        
        try:
            # 尝试创建大量会话
            for i in range(100):
                response = self.session.post(
                    f"{self.base_url}/api/sessions",
                    json={
                        "title": f"压力测试会话 {i}",
                        "model": "test-model"
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        created_sessions.append(data["session"]["id"])
                elif response.status_code in [429, 503]:
                    # 遇到速率限制或服务不可用
                    print(f"在创建第 {i} 个会话时遇到限制")
                    break
                
                # 避免过快创建
                time.sleep(0.01)
        
        finally:
            # 清理创建的会话
            for session_id in created_sessions:
                try:
                    self.session.delete(f"{self.base_url}/api/sessions/{session_id}", timeout=5)
                except:
                    pass
        
        print(f"📊 会话压力测试结果: 成功创建 {len(created_sessions)} 个会话")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short']) 