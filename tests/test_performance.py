#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试模块
测试API响应时间、并发处理能力、内存使用等性能指标
"""

import pytest
import time
import threading
import requests
import psutil
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any


class TestPerformance:
    """性能测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_performance(self):
        """性能测试设置"""
        self.base_url = "http://localhost:5000"
        self.session = requests.Session()
        self.process = psutil.Process(os.getpid())
        
        # 记录初始内存使用
        self.initial_memory = self.process.memory_info().rss
        yield
        
        # 检查内存泄漏
        final_memory = self.process.memory_info().rss
        memory_increase = final_memory - self.initial_memory
        
        # 如果内存增加超过100MB，发出警告
        if memory_increase > 100 * 1024 * 1024:
            print(f"⚠️ 检测到内存使用增加：{memory_increase / 1024 / 1024:.2f}MB")
    
    @pytest.mark.performance
    def test_api_response_time(self):
        """测试API响应时间"""
        endpoints = [
            ("/api/health", {}),
            ("/api/models", {}),
        ]
        
        for endpoint, params in endpoints:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=10)
            response_time = time.time() - start_time
            
            assert response.status_code == 200
            assert response_time < 2.0, f"{endpoint} 响应时间过长: {response_time:.2f}s"
            print(f"✅ {endpoint} 响应时间: {response_time:.3f}s")
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_concurrent_chat_requests(self):
        """测试并发聊天请求"""
        def make_chat_request(request_id: int) -> Dict[str, Any]:
            start_time = time.time()
            try:
                response = self.session.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "messages": [{"role": "user", "text": f"并发测试请求 {request_id}"}],
                        "model": "deepseek-ai/DeepSeek-V2.5"
                    },
                    timeout=30
                )
                response_time = time.time() - start_time
                
                return {
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "success": response.status_code == 200,
                    "data": response.json() if response.status_code == 200 else None
                }
            except Exception as e:
                return {
                    "request_id": request_id,
                    "status_code": 500,
                    "response_time": time.time() - start_time,
                    "success": False,
                    "error": str(e)
                }
        
        # 并发执行10个请求
        num_requests = 10
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_chat_request, i) for i in range(num_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        # 分析结果
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        success_rate = len(successful_requests) / len(results)
        avg_response_time = sum(r["response_time"] for r in successful_requests) / len(successful_requests) if successful_requests else 0
        
        print(f"📊 并发测试结果:")
        print(f"   - 总请求数: {num_requests}")
        print(f"   - 成功请求: {len(successful_requests)}")
        print(f"   - 失败请求: {len(failed_requests)}")
        print(f"   - 成功率: {success_rate:.2%}")
        print(f"   - 平均响应时间: {avg_response_time:.3f}s")
        
        # 断言：至少80%的请求应该成功
        assert success_rate >= 0.8, f"并发成功率过低: {success_rate:.2%}"
        
        # 断言：平均响应时间应该在合理范围内
        if successful_requests:
            assert avg_response_time < 10.0, f"并发平均响应时间过长: {avg_response_time:.2f}s"
    
    @pytest.mark.performance
    def test_large_payload_handling(self):
        """测试大负载处理能力"""
        # 创建大文本消息
        large_text = "这是一个长文本测试。" * 1000  # 约10KB
        
        start_time = time.time()
        response = self.session.post(
            f"{self.base_url}/api/chat",
            json={
                "messages": [{"role": "user", "text": large_text}],
                "model": "deepseek-ai/DeepSeek-V2.5"
            },
            timeout=60
        )
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        
        print(f"📝 大负载测试结果:")
        print(f"   - 文本大小: {len(large_text)} 字符")
        print(f"   - 响应时间: {response_time:.3f}s")
        
        # 响应时间应该在合理范围内
        assert response_time < 30.0, f"大负载处理时间过长: {response_time:.2f}s"
    
    @pytest.mark.performance
    def test_memory_usage_monitoring(self):
        """测试内存使用监控"""
        initial_memory = self.process.memory_info().rss
        
        # 执行多次API调用
        for i in range(20):
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json={
                    "messages": [{"role": "user", "text": f"内存测试消息 {i}"}],
                    "model": "deepseek-ai/DeepSeek-V2.5"
                },
                timeout=30
            )
            assert response.status_code == 200
        
        final_memory = self.process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        print(f"🧠 内存使用情况:")
        print(f"   - 初始内存: {initial_memory / 1024 / 1024:.2f}MB")
        print(f"   - 最终内存: {final_memory / 1024 / 1024:.2f}MB")
        print(f"   - 内存增长: {memory_increase / 1024 / 1024:.2f}MB")
        
        # 内存增长应该在合理范围内（小于50MB）
        assert memory_increase < 50 * 1024 * 1024, f"内存增长过多: {memory_increase / 1024 / 1024:.2f}MB"
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_session_management_performance(self):
        """测试会话管理性能"""
        session_ids = []
        
        # 创建多个会话
        create_start = time.time()
        for i in range(50):
            response = self.session.post(
                f"{self.base_url}/api/sessions",
                json={
                    "title": f"性能测试会话 {i}",
                    "model": "deepseek-ai/DeepSeek-V2.5"
                },
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    session_ids.append(data["session"]["id"])
        
        create_time = time.time() - create_start
        
        # 获取会话列表
        list_start = time.time()
        response = self.session.get(f"{self.base_url}/api/sessions", timeout=10)
        list_time = time.time() - list_start
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        
        # 清理创建的会话
        delete_start = time.time()
        for session_id in session_ids:
            self.session.delete(f"{self.base_url}/api/sessions/{session_id}", timeout=10)
        delete_time = time.time() - delete_start
        
        print(f"📂 会话管理性能:")
        print(f"   - 创建50个会话用时: {create_time:.3f}s")
        print(f"   - 获取会话列表用时: {list_time:.3f}s")
        print(f"   - 删除50个会话用时: {delete_time:.3f}s")
        print(f"   - 平均创建时间: {create_time/50:.3f}s/session")
        
        # 性能断言
        assert create_time < 30.0, f"会话创建时间过长: {create_time:.2f}s"
        assert list_time < 5.0, f"会话列表获取时间过长: {list_time:.2f}s"
    
    @pytest.mark.performance
    def test_api_rate_limiting(self):
        """测试API速率限制和稳定性"""
        # 快速发送请求测试
        request_times = []
        success_count = 0
        
        for i in range(30):
            start = time.time()
            try:
                response = self.session.get(f"{self.base_url}/api/health", timeout=5)
                request_time = time.time() - start
                request_times.append(request_time)
                
                if response.status_code == 200:
                    success_count += 1
                
            except Exception as e:
                print(f"请求 {i} 失败: {e}")
        
        avg_response_time = sum(request_times) / len(request_times) if request_times else 0
        success_rate = success_count / 30
        
        print(f"⚡ 速率测试结果:")
        print(f"   - 总请求数: 30")
        print(f"   - 成功请求: {success_count}")
        print(f"   - 成功率: {success_rate:.2%}")
        print(f"   - 平均响应时间: {avg_response_time:.3f}s")
        
        # 断言：大部分请求应该成功
        assert success_rate >= 0.9, f"高频请求成功率过低: {success_rate:.2%}"


class TestStressTest:
    """压力测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_stress(self):
        """压力测试设置"""
        self.base_url = "http://localhost:5000"
        
    @pytest.mark.stress
    @pytest.mark.slow
    def test_sustained_load(self):
        """测试持续负载能力"""
        def worker():
            session = requests.Session()
            success_count = 0
            error_count = 0
            
            for i in range(10):
                try:
                    response = session.post(
                        f"{self.base_url}/api/chat",
                        json={
                            "messages": [{"role": "user", "text": f"压力测试 {i}"}],
                            "model": "deepseek-ai/DeepSeek-V2.5"
                        },
                        timeout=30
                    )
                    if response.status_code == 200:
                        success_count += 1
                    else:
                        error_count += 1
                except Exception:
                    error_count += 1
                
                # 间隔1秒
                time.sleep(1)
            
            return success_count, error_count
        
        # 启动5个并发工作线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        print("🔥 压力测试完成")
        # 压力测试主要是为了观察系统行为，不设置严格的断言


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short']) 