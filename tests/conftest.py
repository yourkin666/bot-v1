#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest 配置文件
"""

import pytest
import requests
import time
import subprocess
import signal
import os
from typing import Generator


@pytest.fixture(scope="session")
def ensure_server_running() -> Generator[str, None, None]:
    """确保服务器正在运行"""
    base_url = "http://localhost:5000"
    
    # 检查服务器是否已经在运行
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器已在运行")
            yield base_url
            return
    except requests.exceptions.RequestException:
        pass
    
    # 启动服务器
    print("🚀 启动测试服务器...")
    server_process = subprocess.Popen(
        ["python3", "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    
    # 等待服务器启动
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{base_url}/api/health", timeout=2)
            if response.status_code == 200:
                print(f"✅ 服务器启动成功 (尝试 {attempt + 1}/{max_attempts})")
                break
        except requests.exceptions.RequestException:
            time.sleep(1)
    else:
        # 服务器启动失败
        server_process.terminate()
        pytest.fail("❌ 无法启动测试服务器")
    
    try:
        yield base_url
    finally:
        # 清理：关闭服务器
        print("🛑 关闭测试服务器...")
        os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
        server_process.wait(timeout=10)


@pytest.fixture
def api_client(ensure_server_running) -> Generator[requests.Session, None, None]:
    """提供HTTP客户端"""
    session = requests.Session()
    yield session
    session.close()


@pytest.fixture
def test_image_base64() -> str:
    """提供测试图片的base64编码"""
    red_square_png = (
        "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAAEklEQVR4nGP8z4APMOGVHbHSAEEsAROxCnMTAAAAAElFTkSuQmCC"
    )
    return f"data:image/png;base64,{red_square_png}"


def pytest_configure(config):
    """pytest配置钩子"""
    config.addinivalue_line(
        "markers", "integration: 标记为集成测试"
    )
    config.addinivalue_line(
        "markers", "unit: 标记为单元测试"
    )
    config.addinivalue_line(
        "markers", "slow: 标记为慢速测试"
    )
    config.addinivalue_line(
        "markers", "api: 标记为API测试"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    for item in items:
        # 为集成测试添加慢速标记
        if "integration" in item.keywords:
            item.add_marker(pytest.mark.slow)


def pytest_report_header(config):
    """添加报告头部信息"""
    import sys
    return [
        "多模态聊天机器人项目测试报告",
        f"测试环境: {os.environ.get('ENVIRONMENT', 'development')}",
        f"Python版本: {sys.version.split()[0]}"
    ] 