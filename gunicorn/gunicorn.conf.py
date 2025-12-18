import os
from dotenv import load_dotenv

# if os.environ.get("ENV_NAME") == 'Production':
#     load_dotenv(".env.prod")
# elif os.environ.get("ENV_NAME") == 'Staging':
#     load_dotenv(".env.staging")
# elif os.environ.get("ENV_NAME") == 'Testing':
#     load_dotenv(".env.testing")
# else:
#     load_dotenv(".env.local")


# load_dotenv(".env.testing")

# [ Logging ]
logconfig = os.getenv(
    'GC_LOGCONFIG', './Ai_TMS/gunicorn/gunicorn-logging.conf')
accesslog = os.getenv('GC_ACCESSLOG', '-')
errorlog = os.getenv('GC_ERRORLOG', '-')
statsd_host = os.getenv('GC_STATSD_HOST', None)
statsd_prefix = os.getenv('GC_STATSD_PREFIX', None)


# [ Server Socket ]
bind = ['%s:%s' % (os.getenv('GC_HOST', '0.0.0.0'),
                   os.getenv('GC_PORT', '8000'))]


# [ Worker Processes ]
workers = os.getenv('GC_WORKERS')
timeout = os.getenv('GC_TIMEOUT', 120)
