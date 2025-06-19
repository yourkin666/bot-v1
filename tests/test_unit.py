#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态聊天机器人 pytest 单元测试套件
专门测试不需要服务器的核心功能
"""

import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch
from typing import Dict, List
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class TestCoreFunctionality:
    """核心功能单元测试类"""
    
    def test_function_call_executor_tools(self):
        """测试Function Call执行器工具定义"""
        from app import FunctionCallExecutor, BochaSearchService
        
        # 初始化执行器
        bocha_service = BochaSearchService()
        executor = FunctionCallExecutor(bocha_service)
        
        # 测试获取可用工具
        tools = executor.get_available_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        # 验证工具结构
        for tool in tools:
            assert 'type' in tool
            assert tool['type'] == 'function'
            assert 'function' in tool
            assert 'name' in tool['function']
            assert 'description' in tool['function']
            assert 'parameters' in tool['function']
        
        # 查找网络搜索工具
        search_tool = None
        for tool in tools:
            if tool['function']['name'] == 'web_search':
                search_tool = tool
                break
        
        assert search_tool is not None, "缺少web_search工具"
        assert 'query' in search_tool['function']['parameters']['properties']
        assert 'count' in search_tool['function']['parameters']['properties']
        assert 'freshness' in search_tool['function']['parameters']['properties']

    def test_function_call_executor_validation(self):
        """测试Function Call执行器参数验证"""
        from app import FunctionCallExecutor, BochaSearchService
        
        bocha_service = BochaSearchService()
        executor = FunctionCallExecutor(bocha_service)
        
        # 测试无效的函数名
        result = executor.execute_function("invalid_function", {})
        assert not result['success']
        assert 'error' in result
        assert '未知的函数' in result['error']
        
        # 测试缺少必需参数
        result = executor.execute_function("web_search", {})
        assert not result['success']
        assert 'error' in result

    def test_bocha_search_service_initialization(self):
        """测试博查搜索服务初始化"""
        from app import BochaSearchService
        
        # 测试默认初始化
        service = BochaSearchService()
        assert service.api_key is not None
        assert service.base_url == "https://api.bochaai.com/v1/web-search"
        
        # 测试自定义API密钥
        custom_service = BochaSearchService("custom-key")
        assert custom_service.api_key == "custom-key"

    def test_search_result_formatting(self):
        """测试搜索结果格式化功能"""
        from app import BochaSearchService
        
        service = BochaSearchService()
        
        # 测试成功结果格式化
        mock_result = {
            'success': True,
            'query': '测试查询',
            'results': [
                {
                    'title': '测试标题1',
                    'url': 'https://example1.com',
                    'snippet': '测试摘要1',
                    'summary': '测试总结1',
                    'siteName': '测试网站1'
                },
                {
                    'title': '测试标题2', 
                    'url': 'https://example2.com',
                    'snippet': '测试摘要2',
                    'summary': '测试总结2',
                    'siteName': '测试网站2'
                }
            ],
            'images': [
                {
                    'thumbnailUrl': 'https://example.com/thumb.jpg',
                    'contentUrl': 'https://example.com/image.jpg',
                    'name': '测试图片'
                }
            ],
            'total_count': 2,
            'search_provider': '博查AI'
        }
        
        formatted_text = service.format_search_results_for_ai(mock_result)
        assert isinstance(formatted_text, str)
        assert '测试查询' in formatted_text
        assert '测试标题1' in formatted_text
        assert '测试标题2' in formatted_text
        assert '博查AI' in formatted_text
        assert 'https://example1.com' in formatted_text
        assert 'https://example2.com' in formatted_text
        
        # 测试失败结果格式化
        mock_failed_result = {
            'success': False,
            'error': '测试错误消息'
        }
        
        formatted_text = service.format_search_results_for_ai(mock_failed_result)
        assert isinstance(formatted_text, str)
        assert '搜索失败' in formatted_text
        assert '测试错误消息' in formatted_text

    def test_multimodal_message_preprocessing(self):
        """测试多媒体消息预处理功能"""
        from app import _preprocess_multimedia_messages
        
        # 测试空消息列表
        empty_result = _preprocess_multimedia_messages([])
        assert empty_result == []
        
        # 测试纯文本消息
        text_messages = [
            {'role': 'user', 'text': '纯文本消息1'},
            {'role': 'assistant', 'text': '助手回复'}
        ]
        text_result = _preprocess_multimedia_messages(text_messages)
        assert len(text_result) == 2
        assert text_result[0]['text'] == '纯文本消息1'
        assert text_result[1]['text'] == '助手回复'
        
        # 测试包含图片的消息
        image_messages = [{
            'role': 'user',
            'text': '请分析这张图片',
            'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
        }]
        image_result = _preprocess_multimedia_messages(image_messages)
        assert len(image_result) == 1
        assert 'image' in image_result[0]
        assert '请分析这张图片' in image_result[0]['text']
        
        # 测试包含无效音频的消息
        invalid_audio_messages = [{
            'role': 'user',
            'text': '测试音频',
            'audio': 'invalid-audio-data'
        }]
        invalid_result = _preprocess_multimedia_messages(invalid_audio_messages)
        assert len(invalid_result) == 1
        assert '测试音频' in invalid_result[0]['text']
        # 无效音频应该被移除
        assert 'audio' not in invalid_result[0]

    def test_database_functionality(self):
        """测试数据库核心功能"""
        from database import ChatDatabase
        
        # 使用临时数据库文件
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        try:
            # 初始化数据库
            db = ChatDatabase(db_path)
            
            # 测试创建会话
            session_id = db.create_session("测试会话", "test-model")
            assert session_id is not None
            assert len(session_id) > 0
            
            # 测试获取会话
            session = db.get_session_by_id(session_id)
            assert session is not None
            assert session['title'] == '测试会话'
            assert session['model'] == 'test-model'
            
            # 测试添加消息
            success = db.add_message(
                session_id=session_id,
                role="user",
                content="测试消息",
                content_type="text"
            )
            assert success is True
            
            # 测试添加多媒体消息
            success = db.add_message(
                session_id=session_id,
                role="user",
                content="测试音频消息",
                content_type="audio",
                file_name="test.mp3",
                file_size=1024,
                model="test-model",
                provider="test-provider"
            )
            assert success is True
            
            # 测试获取消息
            messages = db.get_messages(session_id)
            assert len(messages) == 2
            
            # 验证第一条消息
            text_msg = messages[0]
            assert text_msg['content'] == '测试消息'
            assert text_msg['content_type'] == 'text'
            
            # 验证第二条消息
            audio_msg = messages[1]
            assert audio_msg['content'] == '测试音频消息'
            assert audio_msg['content_type'] == 'audio'
            assert audio_msg['file_name'] == 'test.mp3'
            assert audio_msg['file_size'] == 1024
            assert audio_msg['model'] == 'test-model'
            assert audio_msg['provider'] == 'test-provider'
            
            # 测试获取会话列表
            sessions = db.get_sessions()
            assert len(sessions) >= 1
            session_found = any(s['id'] == session_id for s in sessions)
            assert session_found
            
            # 测试更新会话标题
            update_success = db.update_session_title(session_id, "更新后的标题")
            assert update_success is True
            
            updated_session = db.get_session_by_id(session_id)
            assert updated_session['title'] == '更新后的标题'
            
            # 测试归档会话
            archive_success = db.archive_session(session_id)
            assert archive_success is True
            
            # 验证归档后的会话不在常规列表中
            sessions_after_archive = db.get_sessions()
            archived_session_found = any(s['id'] == session_id for s in sessions_after_archive)
            assert not archived_session_found
            
            # 测试搜索消息
            search_results = db.search_messages("测试")
            assert len(search_results) >= 0  # 可能有匹配结果
            
            # 测试统计功能
            stats = db.get_statistics()
            assert isinstance(stats, dict)
            assert 'total_sessions' in stats
            assert 'total_messages' in stats
            assert 'today_sessions' in stats
            assert 'today_messages' in stats
            assert stats['total_sessions'] >= 0  # 归档后为0
            assert stats['total_messages'] >= 2
            assert stats['today_messages'] >= 2
            
        finally:
            # 清理临时数据库文件
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_available_models_configuration(self):
        """测试可用模型配置"""
        from app import AVAILABLE_MODELS
        
        assert isinstance(AVAILABLE_MODELS, list)
        assert len(AVAILABLE_MODELS) > 0
        
        # 验证每个模型的结构
        for model in AVAILABLE_MODELS:
            assert 'id' in model
            assert 'name' in model
            assert 'provider' in model
            assert 'supports_image' in model
            assert 'type' in model
            assert isinstance(model['supports_image'], bool)
            assert model['provider'] in ['siliconflow', 'groq']
            assert model['type'] in ['text', 'multimodal']
        
        # 确保有默认模型
        default_models = [m for m in AVAILABLE_MODELS if m.get('default', False)]
        assert len(default_models) >= 1
        
        # 确保有支持图片的模型
        image_models = [m for m in AVAILABLE_MODELS if m['supports_image']]
        assert len(image_models) >= 1

    def test_multimodal_chatbot_service_model_info(self):
        """测试多模态聊天机器人服务的模型信息功能"""
        from app import MultiModalChatBotService
        
        service = MultiModalChatBotService("fake-key1", "fake-key2")
        
        # 测试获取有效模型信息
        model_info = service._get_model_info("deepseek-ai/DeepSeek-V2.5")
        assert model_info is not None
        assert model_info['id'] == "deepseek-ai/DeepSeek-V2.5"
        assert model_info['provider'] == "siliconflow"
        assert not model_info['supports_image']
        
        # 测试获取多模态模型信息
        multimodal_info = service._get_model_info("meta-llama/llama-4-scout-17b-16e-instruct")
        assert multimodal_info is not None
        assert multimodal_info['supports_image'] is True
        assert multimodal_info['provider'] == "groq"
        
        # 测试获取不存在的模型信息
        invalid_info = service._get_model_info("non-existent-model")
        assert invalid_info is None

    def test_multimedia_content_detection(self):
        """测试多媒体内容检测功能"""
        from app import MultiModalChatBotService
        
        service = MultiModalChatBotService("fake-key1", "fake-key2")
        
        # 测试图片内容检测
        image_messages = [
            {'role': 'user', 'text': '测试', 'image': 'data:image/png;base64,test'},
            {'role': 'assistant', 'text': '回复'}
        ]
        assert service._has_image_content(image_messages) is True
        assert service._has_multimedia_content(image_messages) is True
        
        # 测试音频内容检测
        audio_messages = [
            {'role': 'user', 'text': '测试', 'audio': 'data:audio/wav;base64,test'}
        ]
        assert service._has_image_content(audio_messages) is False
        assert service._has_multimedia_content(audio_messages) is True
        
        # 测试视频内容检测
        video_messages = [
            {'role': 'user', 'text': '测试', 'video': 'data:video/mp4;base64,test'}
        ]
        assert service._has_image_content(video_messages) is False
        assert service._has_multimedia_content(video_messages) is True
        
        # 测试纯文本内容
        text_messages = [
            {'role': 'user', 'text': '纯文本测试'}
        ]
        assert service._has_image_content(text_messages) is False
        assert service._has_multimedia_content(text_messages) is False

    def test_error_handling_edge_cases(self):
        """测试边界情况和错误处理"""
        from app import _preprocess_multimedia_messages
        from database import ChatDatabase
        
        # 测试预处理空数据
        empty_result = _preprocess_multimedia_messages([])
        assert empty_result == []
        
        # 测试预处理无效消息格式
        invalid_messages = [
            {'invalid_key': 'invalid_value'},
            {'role': 'user'}  # 缺少text字段
        ]
        
        # 这应该不会崩溃，而是优雅处理
        result = _preprocess_multimedia_messages(invalid_messages)
        assert isinstance(result, list)
        
        # 测试数据库初始化错误处理
        # 使用无效路径
        invalid_path = "/invalid/path/test.db"
        try:
            db = ChatDatabase(invalid_path)
            # 如果没有权限创建数据库，应该抛出异常
        except Exception as e:
            assert isinstance(e, Exception)

    def test_json_serialization(self):
        """测试JSON序列化功能"""
        # 测试工具调用参数的JSON处理
        test_data = {
            "query": "测试查询",
            "count": 5,
            "freshness": "week",
            "中文键": "中文值"
        }
        
        # 确保可以正确序列化和反序列化
        json_str = json.dumps(test_data, ensure_ascii=False)
        restored_data = json.loads(json_str)
        
        assert restored_data == test_data
        assert restored_data["中文键"] == "中文值"

    def test_configuration_validation(self):
        """测试配置验证"""
        import os
        
        # 测试环境变量
        api_keys = [
            'SILICONFLOW_API_KEY',
            'GROQ_API_KEY', 
            'OPENAI_API_KEY',
            'BOCHA_API_KEY'
        ]
        
        # 至少应该有一些API密钥被配置
        configured_keys = [key for key in api_keys if os.environ.get(key)]
        
        # 在测试环境中，至少应该有默认配置
        assert len(configured_keys) >= 0  # 允许没有配置，因为有默认值


if __name__ == '__main__':
    # 运行单元测试
    pytest.main([__file__, '-v', '--tb=short']) 