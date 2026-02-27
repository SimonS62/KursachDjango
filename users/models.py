from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator


class CustomUser(AbstractUser):
    # Добавьте поля, которые вам нужны.
    # Например:
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Номер телефона должен быть в формате: '+999999999'. Допускается до 15 цифр."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, unique=True, null=True, blank=True)
    email = models.EmailField(_('email address'), unique=True) # Делаем email уникальным и обязательным
    first_name = models.CharField(_('first name'), max_length=150, blank=False) # Меняем blank=True на blank=False
    last_name = models.CharField(_('last name'), max_length=150, blank=False)  # Меняем blank=True на blank=False
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Обязательные поля из AbstractUser, которые мы делаем обязательными
    USERNAME_FIELD = 'email' # Использовать email для логина
    REQUIRED_FIELDS = ['first_name', 'last_name'] # Поля, которые нужно будет заполнить при создании пользователя через командную строку

    def __str__(self):
        # Возвращаем email, если имя не указано, или полное имя
        return self.email if not self.get_full_name() else self.get_full_name()