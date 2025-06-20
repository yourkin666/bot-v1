#!/bin/bash

# 聊天机器人服务管理脚本

case "$1" in
    start)
        echo "🚀 启动聊天机器人服务..."
        # 停止现有进程
        pkill -f "gunicorn.*app:app" || true
        sleep 2
        # 启动新进程
        gunicorn -c gunicorn_config.py app:app --daemon
        echo "✅ 服务启动成功！"
        ;;
    stop)
        echo "🛑 停止聊天机器人服务..."
        pkill -f "gunicorn.*app:app"
        echo "✅ 服务已停止！"
        ;;
    restart)
        echo "🔄 重启聊天机器人服务..."
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        echo "🔍 检查服务状态..."
        if pgrep -f "gunicorn.*app:app" > /dev/null; then
            echo "✅ 服务正在运行"
            echo "进程信息:"
            ps aux | grep "gunicorn.*app:app" | grep -v grep
            echo ""
            echo "端口监听:"
            netstat -tlnp | grep :80
        else
            echo "❌ 服务未运行"
        fi
        ;;
    test)
        echo "🧪 测试服务访问..."
        curl -s -w "状态码: %{http_code} | 响应时间: %{time_total}s\n" http://localhost:80/ -o /dev/null
        ;;
    info)
        echo "📋 部署信息:"
        echo "   - 本地访问: http://localhost:80"
        echo "   - 内网访问: http://172.17.63.236:80"
        echo "   - 公网访问: http://47.84.70.153"
        echo ""
        echo "📊 管理命令:"
        echo "   - 启动: ./manage.sh start"
        echo "   - 停止: ./manage.sh stop"
        echo "   - 重启: ./manage.sh restart"
        echo "   - 状态: ./manage.sh status"
        echo "   - 测试: ./manage.sh test"
        echo "   - 日志: tail -f /var/log/gunicorn_*.log"
        ;;
    *)
        echo "使用方法: $0 {start|stop|restart|status|test|info}"
        exit 1
        ;;
esac 