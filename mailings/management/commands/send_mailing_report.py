from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from django.template.loader import render_to_string
from mailings.models import Mailing, MailingAttempt


class Command(BaseCommand):
    help = 'Send daily mailing report'

    def handle(self, *args, **options):
        today = timezone.now().date()
        mailings = Mailing.objects.filter(created_at__date=today)
        attempts = MailingAttempt.objects.filter(attempt_time__date=today)

        context = {
            'date': today,
            'mailings_count': mailings.count(),
            'attempts_count': attempts.count(),
            'success_count': attempts.filter(status='success').count(),
            'failed_count': attempts.filter(status='failed').count(),
        }

        message = render_to_string('mailings/report_email.html', context)

        send_mail(
            subject=f'Отчет по рассылкам за {today}',
            message='',
            html_message=message,
            from_email='noreply@example.com',
            recipient_list=['admin@example.com'],
        )

        self.stdout.write(self.style.SUCCESS(f'Отчет отправлен за {today}'))
