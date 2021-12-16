import os
from datetime import datetime, timedelta
from celery import Celery

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


from celery.schedules import crontab

app.conf.beat_schedule = {
    # Executes every day at  7:00 am.
    'run-every-day': {
        'task': 'ai_auth.tasks.delete_inactive_user_account',
        'schedule': crontab(hour=7, minute=00),#crontab(hour=1, minute=15),
        'args': (),
    },
}

# @app.task(bind=True)
# def hello(self,a):
#     print(a)
#     return 'hello world'

# tomorrow = datetime.utcnow() + timedelta(minutes=3)
# hello.apply_async((1,),eta=tomorrow)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')



