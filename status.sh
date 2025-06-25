#!/bin/bash
# 快速查看状态

echo "📊 多模态聊天机器人状态："
echo "=========================="

# 服务状态
systemctl status chatbot.service --no-pager

echo ""
echo "🌐 网络监听："
ss -tulpn | grep :80

echo ""
echo "💾 进程信息："
ps aux | grep gunicorn | grep -v grep

echo ""
# 获取访问地址
PUBLIC_IP=$(curl -s --max-time 3 https://ipinfo.io/ip 2>/dev/null)
if [ -n "$PUBLIC_IP" ]; then
    echo "🔗 公网访问: http://$PUBLIC_IP"
else
    echo "🔗 本地访问: http://localhost"
fi 