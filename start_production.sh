#!/bin/bash

# 生产环境启动脚本
echo "🚀 正在启动生产环境聊天机器人..."

# 创建日志目录
sudo mkdir -p /var/log
sudo touch /var/log/gunicorn_access.log
sudo touch /var/log/gunicorn_error.log
sudo chmod 666 /var/log/gunicorn_*.log

# 启动 Gunicorn
echo "📱 启动 Gunicorn 服务器..."
gunicorn -c gunicorn_config.py app:app

echo "✅ 生产环境启动完成！"
echo "🌐 访问地址："
echo "   - 本地: http://localhost:5000"
echo "   - 内网: http://172.17.63.236:5000"
echo "   - 公网: http://47.84.70.153:5000" 