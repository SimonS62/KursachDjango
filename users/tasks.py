from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.utils.html import strip_tags
from .models import EmailVerificationToken, PasswordResetToken


@shared_task
def send_verification_email_task(user_id):
    from .models import CustomUser, EmailVerificationToken

    user = CustomUser.objects.get(id=user_id)
    token, created = EmailVerificationToken.objects.get_or_create(user=user)

    verification_url = reverse('users:verify-email', kwargs={'token': str(token.token)})
    full_url = f"{settings.FRONTEND_URL or 'http://localhost:8000'}{verification_url}"

    subject = 'Подтверждение email адреса'
    html_message = render_to_string('users/emails/verify_email.html', {
        'user': user,
        'verification_url': full_url,
    })
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
    )

@shared_task
def send_password_reset_email_task(user_id, token_str):
    from .models import CustomUser

    user = CustomUser.objects.get(id=user_id)

    reset_url = reverse('users:reset-password-confirm', kwargs={'token': token_str})
    full_url = f"{settings.FRONTEND_URL or 'http://localhost:8000'}{reset_url}"

    subject = 'Сброс пароля'
    html_message = render_to_string('users/emails/password_reset.html', {
        'user': user,
        'reset_url': full_url,
    })
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
    )
