# Gunicorn 配置文件
import multiprocessing

# 服务器绑定地址和端口
bind = "0.0.0.0:80"

# 工作进程数 (推荐为CPU核心数*2+1)
workers = multiprocessing.cpu_count() * 2 + 1

# 工作进程类型
worker_class = "sync"

# 每个工作进程的最大请求数
max_requests = 2000
max_requests_jitter = 50

# 工作进程超时时间（秒）
timeout = 120

# 保持连接时间
keepalive = 2

# 预加载应用
preload_app = True

# 用户和组
user = "root"
group = "root"

# 临时目录
tmp_upload_dir = None

# 日志配置
accesslog = "/var/log/gunicorn_access.log"
errorlog = "/var/log/gunicorn_error.log"
loglevel = "info"

# 进程名称
proc_name = "chatbot-api"

# 进程文件
pidfile = "/var/run/gunicorn.pid"

# 守护进程模式
daemon = True

# 重新加载
reload = False
