from django.urls import path
from .views import (
    RegisterView,
    VerifyEmailView,
    LoginView,
    logout_view,
    PasswordResetView,
    PasswordResetConfirmView
)

app_name = 'users'

urlpatterns = [
    # Регистрация и подтверждение почты
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/<uuid:token>/', VerifyEmailView.as_view(), name='verify-email'),

    # Авторизация
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'), # Это функция, .as_view() не нужен

    # Сброс пароля
    path('password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('password-reset/confirm/<uuid:token>/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]
