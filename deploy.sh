#!/bin/bash
# 自动化部署脚本

set -e # 如果任何命令失败，则立即退出

# 检查是否以root用户运行
if [ "$(id -u)" -ne 0 ]; then
  echo "❌ 错误：请以root用户运行此脚本。" >&2
  exit 1
fi

# -- 配置 --
PROJECT_DIR="/root/bot-v1"
SERVICE_NAME="chatbot"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="/var/log/chatbot"
# -- 结束配置 --

echo "🚀 开始部署多模态聊天机器人..."

# 1. 停止并禁用现有服务 (如果存在)
echo "🔄 停止并禁用旧的服务..."
systemctl stop ${SERVICE_NAME}.service > /dev/null 2>&1 || true
systemctl disable ${SERVICE_NAME}.service > /dev/null 2>&1 || true

# 2. 创建虚拟环境并安装依赖
if [ ! -d "$VENV_DIR" ]; then
    echo "🐍 创建Python虚拟环境于 $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

echo "📦 激活虚拟环境并安装依赖..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip > /dev/null
pip install -r "$PROJECT_DIR/requirements.txt"
deactivate

echo "✅ 依赖安装完成。"

# 3. 创建日志目录
echo "📁 创建日志目录 ${LOG_DIR}..."
mkdir -p "$LOG_DIR"
chown -R root:root "$LOG_DIR"

# 4. 复制 systemd 服务文件
echo "⚙️  配置 systemd 服务..."
cp "$PROJECT_DIR/${SERVICE_NAME}.service" "/etc/systemd/system/"
chmod 644 "/etc/systemd/system/${SERVICE_NAME}.service"

# 5. 重新加载 systemd 并启动服务
echo "🚀 重新加载 systemd 并启动服务..."
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}.service
systemctl start ${SERVICE_NAME}.service

# 6. 检查服务状态
echo ""
echo "🔍 检查服务状态 (等待5秒)..."
sleep 5
systemctl status ${SERVICE_NAME}.service --no-pager

# 获取服务监听的端口
bind_address=$(grep -oP 'bind\s*=\s*"\K[^"]+' ${PROJECT_DIR}/gunicorn_config.py)
listen_port=$(echo "$bind_address" | awk -F':' '{print $2}')

echo ""
echo "🎉 ✅ 部署完成！"
echo ""
echo "你的聊天机器人服务正在运行中。"
echo "🔗 访问地址: http://<你的服务器IP>:${listen_port}"
echo " E.g. http://127.0.0.1:${listen_port}"
echo ""
echo "常用命令:"
echo "  - 检查服务状态: systemctl status ${SERVICE_NAME}"
echo "  - 停止服务:     systemctl stop ${SERVICE_NAME}"
echo "  - 启动服务:     systemctl start ${SERVICE_NAME}"
echo "  - 查看实时日志: journalctl -u ${SERVICE_NAME} -f"
echo ""
echo "日志文件位于 ${LOG_DIR}/" 