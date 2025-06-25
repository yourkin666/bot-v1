#!/bin/bash
# 多模态聊天机器人管理脚本

echo "🤖 多模态聊天机器人管理工具"
echo "================================"

function show_status() {
    echo "📊 服务状态："
    systemctl status chatbot.service --no-pager
    echo ""
    echo "🌐 网络状态："
    ss -tulpn | grep :80
    echo ""
    echo "💾 内存使用："
    ps aux | grep gunicorn | grep -v grep
    echo ""
}

function show_logs() {
    echo "📋 实时日志："
    journalctl -u chatbot.service -f
}

function restart_service() {
    echo "🔄 重启服务..."
    systemctl restart chatbot.service
    sleep 2
    show_status
}

function test_api() {
    echo "🧪 API测试："
    echo "健康检查："
    curl -s localhost:80/api/health | python3 -m json.tool
    echo ""
    echo "模型列表："
    curl -s localhost:80/api/models | python3 -m json.tool
    echo ""
}

function show_access_info() {
    PUBLIC_IP=$(curl -s https://ipinfo.io/ip)
    echo "🔗 访问信息："
    echo "公网IP: $PUBLIC_IP"
    echo "访问地址: http://$PUBLIC_IP"
    echo ""
    echo "✅ 使用80端口 (HTTP标准端口，默认开放)"
    echo ""
}

case "$1" in
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "restart")
        restart_service
        ;;
    "test")
        test_api
        ;;
    "info")
        show_access_info
        ;;
    *)
        echo "使用方法:"
        echo "  $0 status   - 显示服务状态"
        echo "  $0 logs     - 查看实时日志"
        echo "  $0 restart  - 重启服务"
        echo "  $0 test     - 测试API"
        echo "  $0 info     - 显示访问信息"
        echo ""
        show_status
        show_access_info
        ;;
esac 