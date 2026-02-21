from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from mailings.models import Mailing, Client, Message


class Command(BaseCommand):
    help = 'Create user groups and set permissions'

    def handle(self, *args, **options):
        # Создаем группу Менеджеры
        managers_group, created = Group.objects.get_or_create(name='Менеджеры')

        # Добавляем все права на рассылки
        content_types = [
            ContentType.objects.get_for_model(Mailing),
            ContentType.objects.get_for_model(Client),
            ContentType.objects.get_for_model(Message),
        ]

        for content_type in content_types:
            permissions = Permission.objects.filter(content_type=content_type)
            managers_group.permissions.add(*permissions)

        self.stdout.write(self.style.SUCCESS('Группа "Менеджеры" создана с полными правами'))
