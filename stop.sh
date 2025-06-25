#!/bin/bash
# 快速停止脚本

echo "🛑 停止多模态聊天机器人..."
systemctl stop chatbot.service

echo "✅ 服务已停止"
echo ""
systemctl status chatbot.service --no-pager 