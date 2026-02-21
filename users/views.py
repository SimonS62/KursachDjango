from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.urls import reverse
from django.conf import settings
from .models import CustomUser, EmailVerificationToken, PasswordResetToken
from .tasks import send_verification_email_task, send_password_reset_email_task
from django.utils import timezone
from datetime import timedelta
import uuid


class RegisterView(View):
    template_name = 'users/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('mailings:list')
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get('email')
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Пароли не совпадают')
            return render(request, self.template_name)

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Пользователь с таким email уже существует')
            return render(request, self.template_name)

        user = CustomUser.objects.create_user(
            email=email,
            username=username,
            password=password1
        )

        # Отправляем email для верификации асинхронно
        send_verification_email_task.delay(user.id)

        messages.success(request,
            'Регистрация прошла успешно! Проверьте почту для подтверждения email.')

        return redirect('users:login')

class VerifyEmailView(View):
    def get(self, request, token):
        token_obj = get_object_or_404(EmailVerificationToken, token=token)

        if token_obj.is_used:
            messages.error(request, 'Ссылка уже использована')
        elif token_obj.user.is_email_verified:
            messages.info(request, 'Email уже подтвержден')
        else:
            token_obj.user.is_email_verified = True
            token_obj.user.save()
            token_obj.is_used = True
            token_obj.save()
            messages.success(request, 'Email успешно подтвержден!')

        return redirect('users:login')

class LoginView(View):
    template_name = 'users/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('mailings:list')
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

        if user:
            if not user.is_email_verified:
                messages.error(request, 'Подтвердите email перед входом')
                return render(request, self.template_name)

            login(request, user)
            return redirect('mailings:list')
        else:
            messages.error(request, 'Неверный email или пароль')
            return render(request, self.template_name)

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('users:login')

class PasswordResetView(View):
    template_name = 'users/password_reset.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get('email')

        try:
            user = CustomUser.objects.get(email=email)

            # Создаем или обновляем токен
            token_obj, created = PasswordResetToken.objects.get_or_create(
                user=user,
                defaults={
                    'expires_at': timezone.now() + timedelta(hours=1)
                }
            )

            if not created:
                token_obj.expires_at = timezone.now() + timedelta(hours=1)
                token_obj.token = uuid.uuid4()
                token_obj.is_used = False
                token_obj.save()

            # Отправляем email асинхронно
            send_password_reset_email_task.delay(user.id, str(token_obj.token))

            messages.success(request,
                'Инструкции по сбросу пароля отправлены на вашу почту.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'Пользователь с таким email не найден')

        return render(request, self.template_name)

class PasswordResetConfirmView(View):
    template_name = 'users/password_reset_confirm.html'

    def get(self, request, token):
        token_obj = get_object_or_404(PasswordResetToken, token=token)

        if token_obj.is_used:
            messages.error(request, 'Ссылка уже использована')
            return redirect('users:password-reset')

        if token_obj.expires_at < timezone.now():
            messages.error(request, 'Ссылка истекла')
            return redirect('users:password-reset')

        request.session['reset_token_user_id'] = token_obj.user.id
        request.session['reset_token'] = token
        return render(request, self.template_name)

    def post(self, request):
        user_id = request.session.get('reset_token_user_id')
        token = request.session.get('reset_token')

        if not user_id or not token:
            messages.error(request, 'Неверная сессия')
            return redirect('users:password-reset')

        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Пароли не совпадают')
            return render(request, self.template_name)

        try:
            user = CustomUser.objects.get(id=user_id)
            token_obj = PasswordResetToken.objects.get(token=token, user=user)

            if token_obj.is_used or token_obj.expires_at < timezone.now():
                messages.error(request, 'Ссылка недействительна')
                return redirect('users:password-reset')

            user.set_password(password1)
            user.save()

            token_obj.is_used = True
            token_obj.save()

            messages.success(request, 'Пароль успешно изменен!')
            del request.session['reset_token_user_id']
            del request.session['reset_token']

        except (CustomUser.DoesNotExist, PasswordResetToken.DoesNotExist):
            messages.error(request, 'Ошибка сброса пароля')

        return redirect('users:login')


def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')

        if pass1 != pass2:
            messages.error(request, 'Пароли не совпадают!')
            return render(request, 'users/register.html')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Пользователь с таким email уже существует')
            return render(request, 'users/register.html')

        user = CustomUser.objects.create_user(username=username, email=email, password=pass1)
        user.save()
        messages.success(request, 'Аккаунт успешно создан! Теперь вы можете войти.')
        return redirect('users:login')

    return render(request, 'users/register.html')

def index_view(request):
    return render(request, 'index.html')