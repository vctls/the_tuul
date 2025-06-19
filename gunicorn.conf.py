# Gunicorn configuration for FastAPI
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = int(os.getenv("WORKER_COUNT", "1"))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000

# Timeout - much longer for development since music separation takes time
is_debug = os.getenv("DEBUG", "False").lower() == "true"
timeout = int(os.getenv("GUNICORN_TIMEOUT", "7200"))  # 2 hours for development
max_requests = int(os.getenv("MAX_REQUESTS", "50"))
reload = is_debug

if is_debug:
    max_requests = 0  # Don't restart workers in development

keepalive = 2
max_requests_jitter = 10

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"  # Log to stderr
loglevel = os.getenv("LOG_LEVEL", "info").lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "tuul-api"

# Server mechanics
preload_app = True
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None
