# 🤖 多模态智能聊天机器人

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-red.svg)](https://flask.palletsprojects.com/)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](./tests/)

一个功能强大的多模态 AI 聊天机器人，集成了多个 AI 服务提供商，支持文本、图片、音频、视频处理和智能网络搜索。

## 📋 目录

- [特性功能](#特性功能)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
- [详细配置](#详细配置)
- [API 文档](#api文档)
- [功能演示](#功能演示)
- [开发说明](#开发说明)
- [故障排除](#故障排除)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## ✨ 特性功能

### 🧠 多模态 AI 能力

- **💬 智能文本对话** - 基于 DeepSeek-V2.5 和 Qwen2.5 模型的自然语言处理
- **🖼️ 图片理解分析** - 利用 Llama 4 多模态模型进行图像内容识别和分析
- **🎵 音频语音处理** - 支持音频文件上传和语音转文字功能
- **🎬 视频内容分析** - 视频帧提取和内容理解
- **🌐 智能联网搜索** - 集成博查 API 实现实时信息检索

### 🎨 用户体验

- **📱 响应式设计** - 适配桌面和移动设备
- **🎭 美观界面** - 现代化的聊天界面设计
- **⚡ 实时响应** - 流畅的聊天体验和打字机效果
- **🔧 模型切换** - 支持多种 AI 模型自动或手动切换

### 📊 数据管理

- **💾 会话存储** - SQLite 数据库持久化存储聊天历史
- **🔍 历史搜索** - 支持聊天记录全文搜索
- **📁 会话管理** - 创建、编辑、删除、归档会话功能
- **📈 统计分析** - 使用情况统计和分析

### 🧮 高级功能

- **📐 数学公式渲染** - 完整的 LaTeX 数学公式支持
- **🌏 中文日期处理** - 智能的中文日期词汇预处理
- **🔧 Function Calling** - 支持工具调用和函数执行
- **🎯 智能搜索判断** - AI 自动判断是否需要网络搜索

## 🏗️ 技术架构

### 后端技术栈

- **Python 3.9+** - 主要编程语言
- **Flask 2.3.3** - Web 框架
- **SQLite** - 轻量级数据库
- **OpenCV** - 图像和视频处理
- **Requests** - HTTP 客户端

### 前端技术栈

- **HTML5/CSS3** - 页面结构和样式
- **JavaScript (ES6+)** - 交互逻辑
- **TailwindCSS** - 样式框架
- **MathJax 3** - 数学公式渲染
- **Marked.js** - Markdown 渲染
- **Prism.js** - 代码高亮

### AI 服务集成

- **SiliconFlow API** - 文本生成模型
- **Groq API** - 多模态模型
- **OpenAI API** - 语音转文字（可选）
- **博查 API** - 网络搜索服务

### 项目结构

```
bot-v1/
├── 📄 app.py                 # Flask主应用程序（2641行）
├── 📄 database.py            # 数据库操作类
├── 📄 index.html             # 前端界面（3188行）
├── 📄 requirements.txt       # Python依赖
├── 📄 run_tests.sh          # 测试运行脚本
├── 📄 pytest.ini           # 测试配置
├── 📄 DATE_PROCESSING.md    # 日期处理说明
├── 📂 tests/               # 测试文件目录
│   ├── test_api.py         # API集成测试
│   ├── test_unit.py        # 单元测试
│   └── conftest.py         # 测试配置
└── 📂 .pytest_cache/      # 测试缓存
```

## 🚀 快速开始

### 系统要求

- Python 3.9 或更高版本
- 8GB+ 内存推荐
- 稳定的网络连接

### 1. 克隆项目

```bash
git clone <repository-url>
cd bot-v1
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或者
venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

创建 `.env` 文件并添加以下配置：

```bash
# SiliconFlow API密钥（必需）
SILICONFLOW_API_KEY=sk-your-siliconflow-api-key

# Groq API密钥（图片处理必需）
GROQ_API_KEY=gsk_your-groq-api-key

# OpenAI API密钥（语音转文字可选）
OPENAI_API_KEY=sk-your-openai-api-key

# 博查搜索API密钥（网络搜索必需）
BOCHA_API_KEY=sk-your-bocha-api-key
```

### 5. 运行应用

```bash
python app.py
```

### 6. 访问应用

打开浏览器访问：[http://localhost:5000](http://localhost:5000)

## ⚙️ 详细配置

### API 密钥获取方式

#### SiliconFlow API

1. 访问 [SiliconFlow 官网](https://siliconflow.cn)
2. 注册账号并完成实名认证
3. 在控制台创建 API 密钥
4. 模型推荐：`deepseek-ai/DeepSeek-V2.5`

#### Groq API

1. 访问 [Groq 官网](https://console.groq.com)
2. 注册账号并获取免费额度
3. 创建 API 密钥
4. 模型推荐：`meta-llama/llama-4-scout-17b-16e-instruct`

#### 博查搜索 API

1. 访问 [博查官网](https://bocha.co)
2. 注册开发者账号
3. 申请搜索 API 权限
4. 获取 API 密钥

### 高级配置选项

#### 模型配置

在 `app.py` 中修改 `AVAILABLE_MODELS` 配置：

```python
AVAILABLE_MODELS = [
    {
        "id": "your-custom-model-id",
        "name": "自定义模型名称",
        "provider": "siliconflow",  # 或 "groq"
        "default": False,
        "supports_image": False,
        "type": "text"
    }
]
```

#### 数据库配置

默认使用 SQLite，可在 `database.py` 中修改数据库路径：

```python
def __init__(self, db_path: str = "chat_history.db"):
```

#### 服务器配置

在 `app.py` 末尾修改运行配置：

```python
if __name__ == "__main__":
    app.run(
        host='0.0.0.0',    # 允许外部访问
        port=5000,         # 端口号
        debug=False        # 生产环境设为False
    )
```

## 📡 API 文档

### 核心接口

#### 发送聊天消息

```http
POST /api/chat
Content-Type: application/json

{
  "messages": [
    {
      "role": "user",
      "text": "你好",
      "image": "data:image/jpeg;base64,/9j/4AAQ...",  // 可选
      "audio": "data:audio/wav;base64,UklGRi...",      // 可选
      "video": "data:video/mp4;base64,AAAAIGZ..."      // 可选
    }
  ],
  "model": "deepseek-ai/DeepSeek-V2.5",
  "session_id": "uuid-string",
  "system_prompt": "你是一个专业的AI助手",
  "temperature": 0.7,
  "enable_search": true
}
```

#### 获取可用模型

```http
GET /api/models
```

#### 会话管理

```http
# 创建会话
POST /api/sessions
{
  "title": "新对话"
}

# 获取会话列表
GET /api/sessions

# 获取会话消息
GET /api/sessions/{session_id}

# 更新会话标题
PUT /api/sessions/{session_id}
{
  "title": "更新的标题"
}

# 删除会话
DELETE /api/sessions/{session_id}
```

#### 文件上传

```http
# 图片上传
POST /api/upload
Content-Type: multipart/form-data

# 音频上传
POST /api/upload/audio

# 视频上传
POST /api/upload/video
```

#### 健康检查

```http
GET /api/health
```

### 响应格式

```json
{
  "success": true,
  "response": "AI回复内容",
  "provider": "siliconflow",
  "model": "deepseek-ai/DeepSeek-V2.5",
  "session_id": "uuid-string",
  "search_performed": false
}
```

## 🎯 功能演示

### 1. 文本对话

```
用户：你好，请介绍一下自己
AI：您好！我是一个多模态智能助手，具备以下能力：
- 💬 自然语言对话
- 🖼️ 图片分析理解
- 🎵 音频处理
- 🌐 实时信息搜索
- 🧮 数学公式计算
```

### 2. 数学公式支持

```
用户：解释一下高斯积分
AI：高斯积分是概率论中的重要公式：

$$\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}$$

这个积分表示标准正态分布的归一化常数...
```

### 3. 图片分析

```
用户：[上传图片] 这张图片里有什么？
AI：我看到这张图片中包含：
- 一座现代化的建筑
- 蓝天白云的背景
- 周围有绿化植被
建筑的设计风格偏向简约现代...
```

### 4. 智能搜索

```
用户：今天的天气怎么样？
AI：[自动触发搜索] 根据最新的天气信息：
今天（2024年6月19日）天气情况：
- 温度：25-32°C
- 天气：多云转晴
- 湿度：65%
- 风力：3-4级
```

### 5. 语音处理

```
用户：[上传音频文件]
系统：正在转录音频...
转录结果：你好，请帮我分析一下这个项目的可行性
AI：根据您的语音内容，我来分析项目可行性...
```

## 🧪 开发说明

### 运行测试

```bash
# 运行所有测试
./run_tests.sh

# 运行快速测试
./run_tests.sh fast

# 运行特定测试
pytest tests/test_api.py -v

# 生成测试报告
pytest --html=reports/test_report.html --cov=. --cov-report=html
```

### 测试覆盖

- **API 测试**：完整的 REST API 接口测试
- **单元测试**：核心功能模块测试
- **集成测试**：多服务集成测试
- **性能测试**：并发请求和响应时间测试

### 开发环境设置

```bash
# 安装开发依赖
pip install pytest pytest-cov pytest-html

# 启用开发模式
export FLASK_ENV=development
python app.py
```

### 代码质量

- 遵循 PEP 8 代码规范
- 使用类型提示
- 完善的错误处理
- 详细的日志记录

## 🔧 故障排除

### 常见问题

#### 1. API 密钥错误

```
错误：SiliconFlow API密钥未配置
解决：检查.env文件中的SILICONFLOW_API_KEY是否正确
```

#### 2. 端口占用

```
错误：Address already in use: Port 5000
解决：
lsof -ti:5000 | xargs kill -9  # 杀死占用进程
# 或修改app.py中的端口号
```

#### 3. 模块导入错误

```
错误：ModuleNotFoundError: No module named 'flask'
解决：
pip install -r requirements.txt
# 或检查虚拟环境是否激活
```

#### 4. 数据库错误

```
错误：database is locked
解决：
# 删除数据库文件重新创建
rm chat_history.db
python app.py
```

#### 5. 图片上传失败

```
错误：文件过大
解决：
# 检查文件大小限制（默认4MB）
# 在app.py中修改MAX_CONTENT_LENGTH
```

### 性能优化建议

1. **生产环境部署**

   ```bash
   # 使用Gunicorn
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. **数据库优化**

   - 定期清理旧会话数据
   - 考虑使用 PostgreSQL 替代 SQLite

3. **缓存配置**

   - 添加 Redis 缓存常用响应
   - 实现 API 响应缓存

4. **负载均衡**
   - 使用 Nginx 反向代理
   - 配置 SSL 证书

### 日志分析

```bash
# 查看应用日志
tail -f app.log

# 搜索错误日志
grep "ERROR" app.log

# 分析API调用频率
grep "API调用" app.log | wc -l
```

## 📈 监控和部署

### Docker 部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "app.py"]
```

### 环境变量配置

```bash
# 生产环境
export FLASK_ENV=production
export PYTHONPATH=/path/to/bot-v1

# 日志配置
export LOG_LEVEL=INFO
export LOG_FILE=/var/log/chatbot.log
```

## 🤝 贡献指南

### 如何贡献

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 开发规范

- 代码必须通过所有测试
- 添加适当的测试用例
- 更新相关文档
- 遵循现有代码风格

### 报告问题

请在 GitHub Issues 中报告问题，并包含：

- 详细的错误描述
- 复现步骤
- 系统环境信息
- 相关日志输出

## 📄 许可证

本项目采用 MIT 许可证。详细信息请查看 [LICENSE](LICENSE) 文件。

## 📞 联系方式

- 作者：[Your Name]
- 邮箱：[your.email@example.com]
- 项目地址：[https://github.com/username/bot-v1]

## 🙏 致谢

感谢以下项目和服务：

- [SiliconFlow](https://siliconflow.cn) 提供的大模型 API 服务
- [Groq](https://groq.com) 提供的多模态 AI 服务
- [Flask](https://flask.palletsprojects.com/) Web 框架
- [MathJax](https://www.mathjax.org/) 数学公式渲染
- [TailwindCSS](https://tailwindcss.com/) 样式框架

---

⭐ 如果这个项目对您有帮助，请给个 Star 支持一下！

📝 最后更新：2024 年 6 月 19 日
