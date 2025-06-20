#!/bin/bash

echo "🚀 开始部署多模态AI聊天机器人..."

# 创建日志目录
echo "📂 创建日志目录..."
sudo mkdir -p /var/log
sudo touch /var/log/gunicorn_access.log
sudo touch /var/log/gunicorn_error.log
sudo chmod 666 /var/log/gunicorn_*.log

# 停止现有的Gunicorn进程
echo "🛑 停止现有进程..."
pkill -f gunicorn || true

# 将服务文件复制到systemd目录
echo "⚙️ 配置系统服务..."
sudo cp chatbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable chatbot

# 启动服务
echo "🌟 启动服务..."
sudo systemctl start chatbot

# 检查服务状态
echo "🔍 检查服务状态..."
sudo systemctl status chatbot --no-pager

# 显示访问信息
echo ""
echo "✅ 部署完成！"
echo "🌐 访问地址："
echo "   - 本地访问: http://localhost:5000"
echo "   - 内网访问: http://172.17.63.236:5000"
echo "   - 公网访问: http://47.84.70.153:5000"
echo ""
echo "📊 管理命令："
echo "   - 查看状态: sudo systemctl status chatbot"
echo "   - 启动服务: sudo systemctl start chatbot"
echo "   - 停止服务: sudo systemctl stop chatbot"
echo "   - 重启服务: sudo systemctl restart chatbot"
echo "   - 查看日志: sudo journalctl -u chatbot -f"
echo "   - 访问日志: tail -f /var/log/gunicorn_access.log"
echo "   - 错误日志: tail -f /var/log/gunicorn_error.log" 