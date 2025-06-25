#!/bin/bash
# 快速查看日志

echo "📋 查看聊天机器人实时日志 (按 Ctrl+C 退出)..."
echo ""
journalctl -u chatbot.service -f --no-pager 