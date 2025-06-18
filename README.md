# 🚀 多模态智能聊天机器人

> 集成 SiliconFlow 和 Groq 双引擎的强大多模态 AI 助手

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3%2B-green.svg)](https://flask.palletsprojects.com)
[![pytest](https://img.shields.io/badge/pytest-8.4%2B-red.svg)](https://pytest.org)

## ✨ 核心特性

- 📝 **智能文本对话** - 基于 SiliconFlow 的 DeepSeek 和 Qwen 模型
- 🖼️ **图片分析识别** - 基于 Groq 的 Llama 4 多模态模型
- 🚀 **智能模型切换** - 根据输入内容自动选择最适合的 AI 引擎
- 🎛️ **System Prompt & Temperature** - 可调节的系统提示和创意温度
- 💾 **会话管理** - 支持会话创建、存储和历史记录
- 💬 **现代化 Web 界面** - 优雅的界面设计，支持图片上传、实时对话
- 🧪 **完整测试覆盖** - 基于 pytest 的专业测试框架

## 🏗️ 项目结构

```
bot-v1/
├── 🎯 核心应用
│   ├── app.py              # Flask web应用主程序
│   ├── index.html          # 现代化前端界面
│   ├── chatbot.py          # 命令行版本
│   └── database.py         # 数据库管理
├── 🧪 测试框架
│   ├── tests/              # pytest测试套件
│   ├── pytest.ini         # pytest配置
│   ├── run_tests.sh        # 测试运行脚本
│   └── pytest使用说明.md   # 测试文档
├── 📋 配置文档
│   ├── requirements.txt    # 项目依赖
│   ├── README.md          # 项目说明
│   └── .gitignore         # Git配置
└── 💾 数据
    └── chat_history.db    # 聊天历史数据库
```

## 🚀 快速开始

### 1. 环境配置

```bash
# 克隆项目
git clone <your-repo-url>
cd bot-v1

# 安装依赖
pip3 install -r requirements.txt

# 配置API密钥（创建.env文件）
echo "GROQ_API_KEY=your_groq_api_key" > .env
echo "SILICONFLOW_API_KEY=your_sf_api_key" >> .env
```

### 2. 启动服务

```bash
# 启动Web服务
python3 app.py

# 或者使用命令行版本
python3 chatbot.py
```

### 3. 访问应用

🌐 **Web 界面**: http://localhost:5000

## 💡 使用方式

### Web 界面功能

- **文本对话**: 直接输入文字进行智能对话
- **图片分析**: 点击 📷 按钮上传图片，AI 将进行分析和问答
- **系统设置**: 调节 System Prompt 和 Temperature 参数
- **模型选择**: 手动选择或自动切换 AI 模型
- **会话管理**: 创建、查看、删除聊天会话

### 智能特性

- **自动模型切换**: 文本使用 SiliconFlow，图片自动切换到 Groq
- **温度控制**: 精准(0.1) / 平衡(0.7) / 创意(1.5)
- **系统提示模板**: 技术助手 / 创意写作 / 学习助手 / 商务助手

## 🧪 测试运行

项目包含完整的 pytest 测试套件，确保功能稳定：

```bash
# 运行所有测试
./run_tests.sh

# 运行快速测试（跳过慢速测试）
./run_tests.sh fast

# 运行集成测试
./run_tests.sh integration

# 生成详细报告
./run_tests.sh report
```

### 测试覆盖

- ✅ API 健康检查和模型列表
- ✅ 文本聊天和多模态功能
- ✅ System Prompt 和 Temperature 设置
- ✅ 模型自动切换逻辑
- ✅ 会话管理和错误处理

详细测试说明请查看：📋 [pytest 使用说明.md](./pytest使用说明.md)

## 🛠️ 技术架构

### 前端技术栈

- **HTML5** + **TailwindCSS** - 现代化响应式界面
- **JavaScript** + **Fetch API** - 异步通信
- **本地存储** - 设置持久化

### 后端技术栈

- **Flask** - 轻量级 Web 框架
- **SQLite** - 数据存储
- **Requests** - HTTP 客户端
- **python-dotenv** - 环境变量管理

### AI 引擎集成

- **SiliconFlow API** - DeepSeek, Qwen 模型（文本对话）
- **Groq API** - Llama 4 Scout/Maverick（多模态分析）
- **智能路由** - 根据输入自动选择最适合的引擎

### 测试基础设施

- **pytest** - 测试框架
- **pytest-html** - HTML 测试报告
- **pytest-cov** - 代码覆盖率分析

## 🎯 API 端点

| 端点                 | 方法           | 功能         |
| -------------------- | -------------- | ------------ |
| `/api/health`        | GET            | 健康检查     |
| `/api/models`        | GET            | 获取可用模型 |
| `/api/chat`          | POST           | 发送聊天消息 |
| `/api/sessions`      | GET/POST       | 会话管理     |
| `/api/sessions/<id>` | GET/PUT/DELETE | 单个会话操作 |

## 🔧 配置选项

### 环境变量

```bash
GROQ_API_KEY=your_groq_api_key           # Groq API密钥
SILICONFLOW_API_KEY=your_sf_api_key      # SiliconFlow API密钥
```

### 支持的模型

- **SiliconFlow**: DeepSeek-V2.5, Qwen2.5-7B (文本)
- **Groq**: Llama 4 Scout, Llama 4 Maverick (多模态)

## 📝 开发和贡献

### 开发环境设置

```bash
# 安装开发依赖
pip3 install -r requirements.txt

# 运行测试确保环境正常
./run_tests.sh

# 启动开发服务器
python3 app.py
```

### 代码质量

- 所有功能都有对应的 pytest 测试
- 代码遵循 Python PEP 8 规范
- 使用类型注解提高代码可读性

## 🚨 注意事项

1. **API 密钥**: 需要有效的 Groq 和 SiliconFlow API 密钥
2. **网络要求**: 需要稳定的网络连接访问 API 服务
3. **Python 版本**: 建议使用 Python 3.9+
4. **端口占用**: 默认使用 5000 端口，确保端口未被占用

## 📄 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

---

⚡ **体验双引擎 AI 的强大能力！文本对话使用 SiliconFlow，图片分析使用 Groq，智能切换，极速响应！**

🧪 **专业测试覆盖，确保功能稳定可靠！**
