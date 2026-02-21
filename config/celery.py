import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('mailings')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Планировщик задач
app.conf.beat_schedule = {
    'send-scheduled-mailings': {
        'task': 'mailings.tasks.send_scheduled_mailings',
        'schedule': 60.0,  # Каждые 60 секунд
    },
    'check-mailing-status': {
        'task': 'mailings.tasks.check_mailing_status',
        'schedule': 300.0,  # Каждые 5 минут
    },
}
