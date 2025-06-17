#!/bin/bash
# 多模态聊天机器人启动脚本

echo "🚀 启动多模态聊天机器人..."

# 检查.env文件是否存在
if [ ! -f ".env" ]; then
    echo "❌ 未找到.env文件，请先配置API密钥"
    exit 1
fi

# 加载环境变量
export $(cat .env | xargs)

# 检查API密钥
if [ -z "$GROQ_API_KEY" ]; then
    echo "❌ 未找到GROQ_API_KEY，请检查.env文件配置"
    exit 1
fi

if [ -z "$SILICONFLOW_API_KEY" ]; then
    echo "❌ 未找到SILICONFLOW_API_KEY，请检查.env文件配置"
    exit 1
fi

echo "✅ 环境配置检查通过"
echo "🤖 正在启动聊天机器人..."

# 启动聊天机器人
python3 chatbot.py 