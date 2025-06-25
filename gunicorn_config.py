# gunicorn_config.py

import multiprocessing
import os

# 服务器绑定地址和端口
bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:80")

# 工作进程数 (推荐 2 * cpu_cores + 1)
workers = os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1)

# 工作进程类型 (gthread 适用于 I/O 密集型应用)
worker_class = "gthread"
threads = 4

# 请求超时时间 (秒)
timeout = 120

# 日志配置
accesslog = "/var/log/chatbot/access.log"
errorlog = "/var/log/chatbot/error.log"
loglevel = "info"

# 启用后台运行 (由 systemd 管理)
daemon = False

# 预加载应用程序以节省内存
preload_app = True 