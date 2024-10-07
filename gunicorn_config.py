# gunicorn_config.py

import multiprocessing

# Use the gevent worker class for I/O-bound operations
worker_class = "gevent"

# Bind to 0.0.0.0:8000 to make the app accessible externally
bind = "0.0.0.0:8000"

# workers = multiprocessing.cpu_count()
# Number of worker processes (adjust as needed)
workers = 2
worker_connections = 500
 
# threads = 3
# Set the maximum number of requests a worker will process before restarting
max_requests = 10000
max_requests_jitter = 500

# workerconnections = 10


# Request timeout (adjust as needed)
timeout = 200  # 30 seconds

# keepalive=1

# Log settings
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel="info"

# Preload the application before forking worker processes
preload = True
