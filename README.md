# 🤖 AI 聊天机器人

简单易用的多模态 AI 聊天助手

## 特性

- 💬 文本对话
- 🖼️ 图片分析
- 🎵 音频处理
- 🎬 视频分析
- 🌐 联网搜索
- 💾 会话管理

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API 密钥

创建 `.env` 文件：

```bash
GROQ_API_KEY=your_groq_api_key
SILICONFLOW_API_KEY=your_sf_api_key
BOCHA_API_KEY=your_bocha_api_key
```

### 3. 运行

```bash
python app.py
```

### 4. 访问

打开浏览器访问：http://localhost:5000

## 运行测试

```bash
# 运行所有测试
./run_tests.sh

# 快速测试
./run_tests.sh fast
```

## 注意事项

- 需要有效的 API 密钥
- Python 3.9+
- 端口 5000 需要空闲
