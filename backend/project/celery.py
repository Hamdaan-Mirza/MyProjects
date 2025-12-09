from __future__ import annotations
import os
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

BROKER = os.getenv('REDIS_URL', 'redis://redis:6379/0')

app = Celery('project', broker=BROKER)

# Load config from Django settings with `CELERY_` namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in installed apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
