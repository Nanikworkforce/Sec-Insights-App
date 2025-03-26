import os
from celery import Celery
from celery.signals import celeryd_after_setup

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')

# Windows specific settings
app.conf.update(
    broker_connection_retry_on_startup=True,
    worker_pool_restarts=True,
    worker_cancel_long_running_tasks_on_connection_loss=True,
    task_track_started=True,
    broker_connection_max_retries=None
)

# Load task modules from all registered Django app configs.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

@celeryd_after_setup.connect
def configure_worker(sender, instance, **kwargs):
    print("Worker is ready!") 