import multiprocessing
import os

# Gunicorn configuration

bind = f"0.0.0.0:{os.getenv('PORT', '5001')}"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
errorlog = "-"
accesslog = "-"
loglevel = "info"
