#!/bin/bash
# 超级简单的快速启动脚本

echo "🚀 快速启动多模态聊天机器人..."

# 检查服务是否已经在运行
if systemctl is-active --quiet chatbot.service; then
    echo "✅ 服务已经在运行中！"
else
    echo "🔄 启动服务..."
    systemctl start chatbot.service
    sleep 2
fi

# 显示状态
echo ""
echo "📊 当前状态："
systemctl status chatbot.service --no-pager -l

# 获取访问地址
PUBLIC_IP=$(curl -s --max-time 3 https://ipinfo.io/ip 2>/dev/null)
if [ -n "$PUBLIC_IP" ]; then
    echo ""
    echo "🌐 访问地址: http://$PUBLIC_IP"
else
    echo ""
    echo "🌐 本地访问: http://localhost"
fi

echo ""
echo "💡 其他命令："
echo "   ./stop.sh    - 停止服务"
echo "   ./logs.sh    - 查看日志"
echo "   ./status.sh  - 查看状态" 