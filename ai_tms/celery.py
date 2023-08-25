import os
from datetime import datetime, timedelta
from celery import Celery
from kombu import Queue

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_tms.settings')

app = Celery('ai_tms')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.task_queues = (
    Queue('high-priority', routing_key='high.priority'),
    Queue('medium-priority', routing_key='medium.priority'),
    Queue('low-priority', routing_key='low.priority'),
)

app.conf.task_routes = {
    'high_priority_task': {'queue': 'high-priority'},
    'medium_priority_task': {'queue': 'medium-priority'},
    'low_priority_task': {'queue': 'low-priority'},
}


from celery.schedules import crontab

app.conf.beat_schedule = {
    # Executes every day at  7:00 am.
    'run-every-day': {
        'task': 'ai_auth.tasks.delete_inactive_user_account',
        'schedule': crontab(hour=6, minute=30),#crontab(hour=1, minute=15),
        'args': (),
        'options': {'queue': 'low-priority'},
    },
    # 'invoice-sync': {
    #     'task': 'ai_auth.tasks.sync_invoices_and_charges',
    #     'schedule': crontab(hour=12, minute=00),
    #     'args': (30,),
    # },
    'renew-credits': {
        'task': 'ai_auth.tasks.renewal_list',
        'schedule': crontab(hour=23, minute=57),#crontab(hour=1, minute=15),
        'args': (),
    },
    'run-every': {
        'task': 'ai_auth.tasks.delete_hired_editors',
        'schedule': crontab(hour=6, minute=30),#crontab(hour=1, minute=15),
        'args': (),
        'options': {'queue': 'low-priority'},
    },
    'sync-bi-data': {
        'task': 'ai_auth.tasks.sync_user_details_bi',
        'schedule': crontab(minute=0, hour='*/4'),#crontab(hour=1, minute=15),
        'args': (),
        'options': {'queue': 'low-priority'},
    },
    # 'run-every-15-minutes': {
    #     'task': 'ai_auth.tasks.send_notification_email_for_unread_messages',
    #     'schedule': crontab(minute='*/15'),
    #     'args': (),
    # },

   'run-every-15-minutes': {
    'task': 'ai_auth.tasks.send_notification_email_for_unread_messages',
    'schedule': crontab(minute='*/15'),
    'args': (),
    'options': {'queue': 'low-priority'},
    },
   'send-ext-ven-mail-5-min': {
    'task': 'ai_auth.tasks.existing_vendor_onboard_check',
    'schedule': crontab(minute='*/5'),
    'args': (),
    'options': {'queue': 'low-priority'},
    },
   'media-backup': {
    'task': 'ai_auth.tasks.backup_media',
    'schedule': crontab(hour=23, minute=40),
    'args': (),
    'options': {'queue': 'low-priority'},
    },
    'run-daily': {
        'task': 'ai_auth.tasks.delete_express_task_history',
        'schedule': crontab(hour=6, minute=30),#crontab(hour=1, minute=15),
        'args': (),
        'options': {'queue': 'low-priority'},
    },
   # 'send-mail-30-minutes': {
   #  'task': 'ai_auth.tasks.email_send_subscription_extension',
   #  'schedule': crontab(minute='*/30'),
   #  'args': (),
   #  },
}

app.conf.timezone = 'UTC'

# @app.task
# def add(x, y):
#     return x + y
# # tomorrow = datetime.utcnow() + timedelta(minutes=5)
# add.apply_async((2, 2), countdown=20)

# @app.task(bind=True)
# def hello(self,a):
#     print(a)
#     return 'hello world'

# tomorrow = datetime.utcnow() + timedelta(minutes=3)
# hello.apply_async((1,),eta=tomorrow)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# @app.task(bind=True):
#     pass

