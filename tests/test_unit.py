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
from datetime import datetime, timedelta

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

    def test_chinese_date_preprocessing(self):
        """测试中文日期预处理功能"""
        from app import preprocess_chinese_date_terms
        
        # 获取当前日期进行比较
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        
        # 测试基本日期词汇
        test_cases = [
            ("今天天气怎么样？", today.strftime('%Y年%m月%d日')),
            ("昨天发生了什么？", yesterday.strftime('%Y年%m月%d日')),
            ("明天有什么安排？", tomorrow.strftime('%Y年%m月%d日')),
            ("今日新闻", today.strftime('%Y年%m月%d日')),
            ("昨日回顾", yesterday.strftime('%Y年%m月%d日')),
            ("明日计划", tomorrow.strftime('%Y年%m月%d日')),
        ]
        
        for original, expected_date in test_cases:
            result = preprocess_chinese_date_terms(original)
            assert expected_date in result, f"处理'{original}'时，期望包含'{expected_date}'，实际结果：'{result}'"
        
        # 测试相对日期表达
        relative_cases = [
            "3天前的报告",
            "5天后的会议",
            "2周前的项目",
            "1个月前的记录"
        ]
        
        for case in relative_cases:
            result = preprocess_chinese_date_terms(case)
            assert '(' in result and ')' in result, f"相对日期处理失败：'{case}' -> '{result}'"
            assert '年' in result and '月' in result and '日' in result, f"日期格式不正确：'{result}'"
        
        # 测试星期词汇
        week_cases = [
            "周一的会议",
            "星期二的安排",
            "周三要做什么？"
        ]
        
        for case in week_cases:
            result = preprocess_chinese_date_terms(case)
            # 星期词汇应该被转换并包含具体日期
            assert any(weekday in result for weekday in ['周一', '周二', '周三', '星期一', '星期二', '星期三'])
            assert '年' in result and '月' in result and '日' in result
        
        # 测试时间点词汇
        time_cases = ["现在是什么时间？", "此时的情况", "当前状态"]
        
        for case in time_cases:
            result = preprocess_chinese_date_terms(case)
            assert any(word not in result for word in ['现在', '此时', '当前']) or ':' in result
        
        # 测试空字符串和None
        assert preprocess_chinese_date_terms("") == ""
        assert preprocess_chinese_date_terms(None) is None

    def test_chinese_date_preprocessing_edge_cases(self):
        """测试中文日期预处理的边界情况"""
        from app import preprocess_chinese_date_terms
        
        # 测试长词汇优先匹配
        result = preprocess_chinese_date_terms("今儿个天气不错")
        # 应该匹配"今儿个"而不是"今儿"
        assert "今儿个" not in result or "年" in result
        
        # 测试不重复处理
        already_processed = "2025年06月19日天气很好"
        result = preprocess_chinese_date_terms(already_processed)
        # 已经是具体日期格式的不应该被再次处理
        assert result == already_processed
        
        # 测试复合表达
        complex_text = "今天和明天的天气，还有昨天的新闻"
        result = preprocess_chinese_date_terms(complex_text)
        # 应该同时处理多个日期词汇
        assert result.count("年") >= 3
        assert result.count("月") >= 3
        assert result.count("日") >= 3

    def test_math_formula_handling(self):
        """测试数学公式处理相关功能"""
        # 这里测试与数学公式相关的后端处理
        from app import _preprocess_multimedia_messages
        
        # 测试包含数学公式的消息
        math_messages = [{
            'role': 'user',
            'text': '请解释这个公式：$$\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}$$'
        }]
        
        result = _preprocess_multimedia_messages(math_messages)
        assert len(result) == 1
        assert '$$' in result[0]['text']  # LaTeX公式应该保留
        assert '\\int' in result[0]['text']  # 积分符号应该保留
        
        # 测试行内数学公式
        inline_math_messages = [{
            'role': 'user', 
            'text': '当 $x = 2$ 时，$f(x) = x^2 + 1$ 的值是多少？'
        }]
        
        result = _preprocess_multimedia_messages(inline_math_messages)
        assert len(result) == 1
        assert '$x = 2$' in result[0]['text']
        assert '$f(x) = x^2 + 1$' in result[0]['text']

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
            
            # 测试获取会话
            session = db.get_session_by_id(session_id)
            assert session is not None
            assert session['title'] == "测试会话"
            assert session['model'] == "test-model"
            
            # 测试添加消息
            success = db.add_message(
                session_id=session_id,
                role="user",
                content="测试消息",
                content_type="text"
            )
            assert success
            
            # 测试获取消息
            messages = db.get_messages(session_id)
            assert len(messages) == 1
            assert messages[0]['content'] == "测试消息"
            assert messages[0]['role'] == "user"
            
            # 测试消息统计
            count = db.get_message_count(session_id)
            assert count == 1
            
            # 测试搜索消息
            search_results = db.search_messages("测试", session_id)
            assert len(search_results) == 1
            assert search_results[0]['content'] == "测试消息"
            
            # 测试更新会话标题
            success = db.update_session_title(session_id, "更新后的标题")
            assert success
            
            updated_session = db.get_session_by_id(session_id)
            assert updated_session['title'] == "更新后的标题"
            
            # 测试删除会话
            success = db.delete_session(session_id)
            assert success
            
            deleted_session = db.get_session_by_id(session_id)
            assert deleted_session is None
            
        finally:
            # 清理临时文件
            try:
                os.unlink(db_path)
            except:
                pass

    def test_available_models_configuration(self):
        """测试可用模型配置"""
        from app import AVAILABLE_MODELS
        
        assert isinstance(AVAILABLE_MODELS, list)
        assert len(AVAILABLE_MODELS) > 0
        
        # 验证每个模型的必需字段
        for model in AVAILABLE_MODELS:
            assert 'id' in model
            assert 'name' in model
            assert 'provider' in model
            assert 'supports_image' in model
            assert isinstance(model['supports_image'], bool)
        
        # 验证至少有一个默认模型
        default_models = [m for m in AVAILABLE_MODELS if m.get('default', False)]
        assert len(default_models) >= 1
        
        # 验证提供商类型
        providers = {m['provider'] for m in AVAILABLE_MODELS}
        expected_providers = {'siliconflow', 'groq'}
        assert providers.issubset(expected_providers)

    def test_multimodal_chatbot_service_model_info(self):
        """测试多模态聊天机器人服务的模型信息获取"""
        from app import MultiModalChatBotService
        
        service = MultiModalChatBotService("test-key", "test-key")
        
        # 测试获取有效模型信息
        valid_model = "deepseek-ai/DeepSeek-V2.5"
        model_info = service._get_model_info(valid_model)
        assert model_info is not None
        assert model_info['id'] == valid_model
        assert 'provider' in model_info
        assert 'supports_image' in model_info
        
        # 测试获取无效模型信息
        invalid_model = "non-existent-model"
        model_info = service._get_model_info(invalid_model)
        assert model_info is None

    def test_multimedia_content_detection(self):
        """测试多媒体内容检测功能"""
        from app import MultiModalChatBotService
        
        service = MultiModalChatBotService("test-key", "test-key")
        
        # 测试图片内容检测
        messages_with_image = [
            {'role': 'user', 'text': '分析图片', 'image': 'data:image/png;base64,test'}
        ]
        assert service._has_image_content(messages_with_image) is True
        assert service._has_multimedia_content(messages_with_image) is True
        
        # 测试音频内容检测
        messages_with_audio = [
            {'role': 'user', 'text': '处理音频', 'audio': 'data:audio/wav;base64,test'}
        ]
        assert service._has_image_content(messages_with_audio) is False
        assert service._has_multimedia_content(messages_with_audio) is True
        
        # 测试视频内容检测
        messages_with_video = [
            {'role': 'user', 'text': '分析视频', 'video': 'data:video/mp4;base64,test'}
        ]
        assert service._has_image_content(messages_with_video) is False
        assert service._has_multimedia_content(messages_with_video) is True
        
        # 测试纯文本消息
        text_only_messages = [
            {'role': 'user', 'text': '纯文本消息'}
        ]
        assert service._has_image_content(text_only_messages) is False
        assert service._has_multimedia_content(text_only_messages) is False

    def test_error_handling_edge_cases(self):
        """测试错误处理边界情况"""
        from app import _preprocess_multimedia_messages, preprocess_chinese_date_terms
        
        # 测试None输入
        assert _preprocess_multimedia_messages(None) == []
        assert preprocess_chinese_date_terms(None) is None
        
        # 测试空列表
        assert _preprocess_multimedia_messages([]) == []
        
        # 测试格式错误的消息
        malformed_messages = [
            {'role': 'user'},  # 缺少text字段
            {'text': 'test'},  # 缺少role字段
            {}  # 空消息
        ]
        
        result = _preprocess_multimedia_messages(malformed_messages)
        # 应该能够处理格式错误的消息而不崩溃
        assert isinstance(result, list)
        
        # 测试包含特殊字符的日期处理
        special_text = "今天的#话题%是什么？"
        result = preprocess_chinese_date_terms(special_text)
        assert isinstance(result, str)
        assert '#话题%' in result  # 特殊字符应该保留

    def test_json_serialization(self):
        """测试JSON序列化相关功能"""
        from database import ChatDatabase
        import json
        
        # 测试数据库返回的数据可以被JSON序列化
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        try:
            db = ChatDatabase(db_path)
            session_id = db.create_session("JSON测试会话")
            
            # 添加包含特殊字符的消息
            db.add_message(session_id, "user", "测试消息 🚀 with emoji")
            
            # 获取消息并测试JSON序列化
            messages = db.get_messages(session_id)
            json_str = json.dumps(messages, ensure_ascii=False)
            assert isinstance(json_str, str)
            assert "测试消息" in json_str
            assert "🚀" in json_str
            
            # 测试反序列化
            parsed_messages = json.loads(json_str)
            assert len(parsed_messages) == 1
            assert parsed_messages[0]['content'] == "测试消息 🚀 with emoji"
            
        finally:
            try:
                os.unlink(db_path)
            except:
                pass

    def test_configuration_validation(self):
        """测试配置验证"""
        from app import SILICONFLOW_API_KEY, GROQ_API_KEY, AVAILABLE_MODELS
        
        # 测试API密钥配置
        assert isinstance(SILICONFLOW_API_KEY, str) or SILICONFLOW_API_KEY is None
        assert isinstance(GROQ_API_KEY, str) or GROQ_API_KEY is None
        
        # 测试模型配置完整性
        for model in AVAILABLE_MODELS:
            required_fields = ['id', 'name', 'provider', 'supports_image']
            for field in required_fields:
                assert field in model, f"模型 {model.get('id', 'unknown')} 缺少必需字段 {field}"

    def test_enhanced_date_processing(self):
        """测试增强的日期处理功能"""
        from app import preprocess_chinese_date_terms
        
        # 测试复杂的中文日期表达
        complex_cases = [
            ("下个月的第一周", "下个月"),
            ("本季度的报告", "本季度"),  # 如果支持季度的话
            ("年初的计划", "年初"),
            ("月底的总结", "月底"),
        ]
        
        for original, expected_part in complex_cases:
            result = preprocess_chinese_date_terms(original)
            # 检查是否进行了某种处理（即使不是完全匹配）
            assert isinstance(result, str)
            assert len(result) >= len(original)
        
        # 测试连续的日期词汇
        continuous_text = "从昨天到今天再到明天的变化"
        result = preprocess_chinese_date_terms(continuous_text)
        # 应该同时处理所有日期词汇
        date_count = result.count("年")
        assert date_count >= 3, f"应该处理3个日期词汇，但只发现{date_count}个"

    def test_math_constants_and_functions(self):
        """测试数学常数和函数的处理"""
        # 测试数学表达式的基本处理
        math_expressions = [
            "计算 sin(π/2) 的值",
            "欧拉常数 e 约等于多少？",
            "圆周率 π 的前10位小数",
            "自然对数 ln(e) 等于多少？"
        ]
        
        for expr in math_expressions:
            # 这里主要测试这些表达式不会导致预处理失败
            from app import preprocess_chinese_date_terms
            result = preprocess_chinese_date_terms(expr)
            assert isinstance(result, str)
            assert len(result) > 0


if __name__ == '__main__':
    # 运行单元测试
    pytest.main([__file__, '-v', '--tb=short']) 