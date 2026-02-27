import os
from celery import Celery


# Устанавливаем переменную окружения, чтобы Django мог найти настройки
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mailing_project.settings')

# Создаем экземпляр Celery
app = Celery('mailing_project')

# Используем namespace='CELERY', чтобы все настройки Celery начинались с CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находим задачи в файлах tasks.py всех установленных приложений
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
