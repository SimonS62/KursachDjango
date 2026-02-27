from django.core.mail import send_mail
from django.conf import settings
from mailings.models import Mailing, Client


def send_email_to_client(client_email, subject, body):
    """Отправляет одно электронное письмо конкретному клиенту."""
    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [client_email],
            fail_silently=False, # Если True, ошибки не будут выбрасываться
        )
        print(f"Email успешно отправлен на {client_email}")
        return True
    except Exception as e:
        print(f"Ошибка отправки email на {client_email}: {e}")
        return False

def send_mailing_to_clients(mailing_id):
    """
    Отправляет сообщение из рассылки всем клиентам, связанным с этой рассылкой.
    Возвращает количество успешно отправленных писем.
    """
    try:
        mailing = Mailing.objects.get(pk=mailing_id)
        if not mailing.is_active:
            print(f"Рассылка '{mailing.name}' не активна, пропуск.")
            return 0

        subject = mailing.message.subject
        body = mailing.message.body
        clients_to_send = mailing.clients.all()
        sent_count = 0

        print(f"Начинаем отправку для рассылки '{mailing.name}'...")

        for client in clients_to_send:
            if send_email_to_client(client.email, subject, body):
                sent_count += 1

        # Обновляем статус рассылки после завершения (или можно вести более детальную статистику)
        # В реальном приложении здесь может быть обновление поля status, last_sent_at и т.д.
        print(f"Рассылка '{mailing.name}' завершена. Успешно отправлено: {sent_count}/{clients_to_send.count()}.")
        return sent_count

    except Mailing.DoesNotExist:
        print(f"Рассылка с ID {mailing_id} не найдена.")
        return 0
    except Exception as e:
        print(f"Непредвиденная ошибка при отправке рассылки {mailing_id}: {e}")
        return 0

# Этот код будет использоваться для проверки работы
if __name__ == '__main__':
    # Пример использования (только для тестирования, не для продакшена)
    # Предполагается, что у вас есть созданные клиенты и сообщения
    # и вы хотите отправить тестовую рассылку.
    print("Тестирование отправки email...")
    # test_result = send_email_to_client("test_recipient@example.com", "Тестовое письмо", "Это тестовое сообщение.")
    # print(f"Тестовая отправка: {'Успех' if test_result else 'Ошибка'}")

    # Чтобы протестировать send_mailing_to_clients, вам нужно:
    # 1. Создать тестовых клиентов.
    # 2. Создать тестовое сообщение.
    # 3. Создать тестовую рассылку, связав её с клиентами и сообщением.
    # 4. Убедиться, что рассылка is_active = True.
    # 5. Установить schedule_time в прошлое или ближайшее будущее.
    # 6. Запустить этот скрипт как отдельный процесс (python mailings/utils/email_sender.py).
    #    В реальном приложении это будет делать планировщик.

    # Пример:
    # try:
    #     test_mailing_id = 1 # ID вашей тестовой рассылки
    #     sent = send_mailing_to_clients(test_mailing_id)
    #     print(f"Отправлено писем для рассылки {test_mailing_id}: {sent}")
    # except Exception as e:
    #     print(f"Ошибка при тестировании send_mailing_to_clients: {e}")
    pass # Оставляем pass, чтобы избежать выполнения при обычном импорте
