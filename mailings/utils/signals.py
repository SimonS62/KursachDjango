from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from celery import current_app
from datetime import timedelta
import logging


logger = logging.getLogger(__name__)

@receiver(post_save, sender='mailings.EmailMessage')
def update_mailing_stats(sender, instance, created, **kwargs):
    """
    Автоматически обновляет статистику при изменении статуса EmailMessage
    """
    if created or not hasattr(instance, 'mailing') or not instance.mailing:
        return

    mailing = instance.mailing
    now = timezone.now()

    # Определяем период (например, день)
    date_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
    date_to = date_from + timedelta(days=1)

    # Атомарно обновляем статистику
    from django.db import transaction
    with transaction.atomic():
        stats, created = MailingStats.objects.select_for_update().get_or_create(
            mailing=mailing,
            date_from=date_from,
            defaults={
                'date_to': date_to,
                'total_emails': mailing.email_messages.count(),
            }
        )

        if not created:
            # Обновляем метрики
            stats.total_emails = mailing.email_messages.count()
            stats.sent_emails = mailing.email_messages.filter(status='sent').count()
            stats.failed_emails = mailing.email_messages.filter(status='failed').count()
            stats.retry_emails = mailing.email_messages.filter(status__in=['retry', 'sending']).count()

            # Процент успеха
            total = stats.total_emails or 1
            stats.success_rate = (stats.sent_emails / total) * 100

            stats.save()

            # Проверяем условия для алертов
            check_alerts(stats)

def check_alerts(stats):
    """Проверяет статистику и отправляет алерты при необходимости"""
    if stats.success_rate < 80:  # Базовый порог
        # Получаем активные конфигурации алертов
        alerts = AlertConfig.objects.filter(is_active=True)

        for alert in alerts:
            if (stats.failed_emails / max(stats.total_emails, 1)) * 100 > alert.failed_rate_threshold:
                send_alert(f"🚨 Высокий процент неудач в рассылке '{stats.mailing.name}': {stats.success_rate:.1f}% успеха", alert)
