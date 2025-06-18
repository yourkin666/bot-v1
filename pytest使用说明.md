# pytest 测试使用说明

## 📋 概述

本项目使用 pytest 作为测试框架，提供完整的 API 测试覆盖，确保多模态聊天机器人的功能稳定性和可靠性。

## 📦 依赖安装

```bash
# 安装pytest及相关插件
pip3 install pytest pytest-html pytest-cov

# 或者安装项目所有依赖
pip3 install -r requirements.txt
```

## 🚀 快速开始

### 1. 基础运行

```bash
# 运行所有测试
./run_tests.sh

# 或者直接使用pytest
python3 -m pytest tests/ -v
```

### 2. 分类运行

```bash
# 运行快速测试（跳过慢速测试）
./run_tests.sh fast

# 运行集成测试
./run_tests.sh integration

# 运行API测试
./run_tests.sh api

# 生成详细报告
./run_tests.sh report
```

## 🏗️ 项目测试结构

```
bot-v1/
├── tests/
│   ├── __init__.py          # 测试包初始化
│   ├── conftest.py          # pytest配置和fixtures
│   └── test_api.py          # API测试套件
├── pytest.ini              # pytest主配置文件
├── run_tests.sh            # 便捷测试运行脚本
├── reports/                # 测试报告目录
│   ├── pytest_report.html  # HTML测试报告
│   └── coverage/           # 覆盖率报告
└── .pytest_cache/         # pytest缓存
```

## 🧪 测试类型和标记

### 测试标记说明

- `@pytest.mark.integration` - 集成测试，需要完整环境
- `@pytest.mark.unit` - 单元测试，独立功能测试
- `@pytest.mark.slow` - 慢速测试，可能需要较长时间
- `@pytest.mark.api` - API 测试，需要外部 API 访问

### 选择性运行

```bash
# 只运行快速测试
python3 -m pytest tests/ -m "not slow"

# 只运行集成测试
python3 -m pytest tests/ -m "integration"

# 只运行API相关测试
python3 -m pytest tests/ -m "api"

# 运行特定测试函数
python3 -m pytest tests/ -k "test_api_health"

# 运行特定测试类
python3 -m pytest tests/ -k "TestChatbotAPI"
```

## 📊 测试报告和覆盖率

### 生成 HTML 报告

```bash
# 生成详细的HTML测试报告
python3 -m pytest tests/ --html=reports/pytest_report.html --self-contained-html

# 生成覆盖率报告
python3 -m pytest tests/ --cov=. --cov-report=html:reports/coverage --cov-report=term-missing

# 同时生成测试报告和覆盖率报告
./run_tests.sh report
```

### 报告文件位置

- **HTML 测试报告**: `reports/pytest_report.html`
- **覆盖率报告**: `reports/coverage/index.html`
- **终端覆盖率**: 运行时直接显示

## 🔧 配置文件详解

### pytest.ini

```ini
[tool:pytest]
testpaths = tests                    # 测试目录
python_files = test_*.py            # 测试文件模式
python_classes = Test*              # 测试类模式
python_functions = test_*           # 测试函数模式
addopts =
    -v                              # 详细输出
    --tb=short                      # 简短错误回溯
    --strict-markers                # 严格标记模式
    --disable-warnings              # 禁用警告
    --html=reports/pytest_report.html  # HTML报告
    --self-contained-html           # 自包含HTML
    --cov=.                        # 覆盖率检测根目录
    --cov-report=html:reports/coverage  # HTML覆盖率报告
    --cov-report=term-missing       # 终端覆盖率报告
markers =
    integration: 集成测试标记
    unit: 单元测试标记
    slow: 慢速测试标记
    api: API测试标记
```

## 🧬 Fixtures 说明

### 内置 fixtures

#### `ensure_server_running`

- **作用**: 确保测试服务器在运行
- **范围**: session 级别（整个测试会话）
- **功能**: 自动检测服务器状态，必要时启动服务器

#### `api_client`

- **作用**: 提供 HTTP 客户端
- **范围**: function 级别（每个测试函数）
- **返回**: `requests.Session` 对象

#### `test_image_base64`

- **作用**: 提供测试图片数据
- **返回**: base64 编码的测试图片字符串

### 使用示例

```python
import pytest

class TestExample:
    def test_with_client(self, api_client):
        """使用API客户端的测试"""
        response = api_client.get("http://localhost:5000/api/health")
        assert response.status_code == 200

    def test_with_image(self, api_client, test_image_base64):
        """使用测试图片的测试"""
        data = {
            "messages": [{
                "role": "user",
                "text": "分析这张图片",
                "image": test_image_base64
            }],
            "model": "meta-llama/llama-4-scout-17b-16e-instruct"
        }
        response = api_client.post(
            "http://localhost:5000/api/chat",
            json=data
        )
        assert response.status_code == 200
```

## 📋 当前测试覆盖

### ✅ 基础功能测试

- **API 健康检查** (`test_api_health`)
  - 验证服务器状态
  - 检查 API 能力配置
- **模型列表获取** (`test_get_models`)
  - 验证可用模型数量
  - 检查模型数据结构

### ✅ 核心聊天功能测试

- **文本聊天** (`test_text_chat`)
  - 基础对话功能
  - 提供商验证
- **System Prompt** (`test_system_prompt`)
  - 系统提示功能
  - AI 响应验证
- **Temperature 设置** (`test_temperature_setting`)
  - 温度参数控制
  - 参数生效验证

### ✅ 多模态功能测试

- **图片分析** (`test_image_analysis`)
  - 图片上传和分析
  - 多模态模型验证
- **模型自动切换** (`test_model_auto_switching`)
  - 智能模型选择
  - 提供商切换验证

### ✅ 会话管理测试

- **会话管理** (`test_session_management`)
  - 会话创建和删除
  - 消息存储和检索

### ✅ 错误处理测试

- **错误处理** (`test_error_handling`)
  - 无效输入处理
  - 错误响应格式验证

## 🚨 测试前提条件

### 1. 服务器状态

- 聊天机器人服务器必须在 `localhost:5000` 运行
- 或者让 pytest 自动启动服务器（通过 fixture）

### 2. API 密钥配置

```bash
# .env文件必须包含有效的API密钥
GROQ_API_KEY=your_groq_api_key
SILICONFLOW_API_KEY=your_siliconflow_api_key
```

### 3. 网络连接

- 需要稳定的网络连接访问外部 API
- 某些测试依赖于 Groq 和 SiliconFlow 服务

## 🛠️ 常见问题和解决方案

### Q1: 测试服务器启动失败

```bash
# 检查端口占用
lsof -i :5000

# 手动启动服务器
python3 app.py
```

### Q2: API 密钥未配置错误

```bash
# 检查.env文件
cat .env

# 验证API密钥格式
echo $GROQ_API_KEY
echo $SILICONFLOW_API_KEY
```

### Q3: 依赖包缺失

```bash
# 重新安装所有依赖
pip3 install -r requirements.txt

# 验证pytest安装
python3 -m pytest --version
```

### Q4: 测试运行缓慢

```bash
# 只运行快速测试
./run_tests.sh fast

# 并行运行测试（需要安装pytest-xdist）
pip3 install pytest-xdist
python3 -m pytest tests/ -n auto
```

### Q5: 图片测试失败

- 检查 Groq API 密钥是否有效
- 验证模型 ID 是否正确更新
- 确保网络连接稳定

## 🎯 最佳实践

### 1. 测试运行策略

```bash
# 开发过程中：运行快速测试
./run_tests.sh fast

# 功能完成后：运行完整测试
./run_tests.sh

# 发布前：生成详细报告
./run_tests.sh report
```

### 2. 测试编写原则

- 每个测试应该独立且可重复
- 使用有意义的测试函数名
- 添加适当的测试标记
- 包含足够的断言验证

### 3. 持续集成建议

```yaml
# GitHub Actions示例
- name: Run tests
  run: |
    pip install -r requirements.txt
    python3 -m pytest tests/ --html=pytest_report.html
```

## 🚀 扩展测试

### 添加新测试

1. 在 `tests/test_api.py` 中添加新的测试方法
2. 使用适当的标记装饰器
3. 编写清晰的测试文档字符串
4. 运行测试验证功能

### 示例：添加新的 API 测试

```python
@pytest.mark.integration
@pytest.mark.api
def test_new_feature(self, api_client):
    """测试新功能"""
    response = api_client.post(
        f"{self.base_url}/api/new_endpoint",
        json={"test": "data"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True
```

## 📈 测试指标

通过运行 `./run_tests.sh report`，你可以获得以下指标：

- **测试通过率**: 目前达到 100%
- **代码覆盖率**: 主要功能模块的覆盖情况
- **性能指标**: 每个测试的执行时间
- **测试分布**: 不同类型测试的数量分布

---

🧪 **使用 pytest 确保代码质量，让你的多模态聊天机器人更加稳定可靠！**
