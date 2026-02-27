import time
from django.core.mail import send_mail, BadHeaderError
from django.utils import timezone
from django.conf import settings
from celery import shared_task
from .models import Mailing, Client, MessageAttempt
import logging


logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=60, # задержка в секундах
    autoretry_for=(Exception,), # Автоматически повторять при определенных исключениях
    retry_kwargs={'exc': None} # Дополнительные аргументы для retry
)
def send_email_to_client(self, mailing_id, client_id):
    """
    Асинхронная задача для отправки письма конкретному клиенту.
    """
    # Получаем ID задачи Celery для логгирования
    task_id = self.request.id
    logger.info(f"[{task_id}] Запуск задачи для рассылки {mailing_id}, клиента {client_id}")

    try:
        # --- Получаем объекты ---
        # Использование .get() безопасно, так как они уже в блоке try/except
        mailing = Mailing.objects.get(id=mailing_id)
        client = Client.objects.get(id=client_id)

        # --- Проверка времени ---
        now = timezone.now()
        # Проверяем, что рассылка активна СЕЙЧАС
        if not (mailing.start_time <= now <= mailing.end_time):
            logger.warning(
                f"[{task_id}] ⏰ Время для рассылки {mailing.id} истекло "
                f"({mailing.start_time} - {mailing.end_time}). Текущее: {now}. Задача отменена."
            )
            # Задача не должна повторяться, если время не подошло. Return False = задача выполнена, без повтора.
            # Не создаем MessageAttempt, так как это не ошибка отправки.
            return False

        # --- Отправка письма ---
        try:
            # Используем time.time() для замера длительности
            send_start_time = time.time()

            # Убедитесь, что в Mailing есть поле message, и в нем есть subject и body.
            # Подразумевается, что Message - это отдельная модель, связанная с Mailing ForeignKey.
            # Если это не так, скорректируйте пути к subject и body.
            # --- !!! УБЕДИТЕСЬ, ЧТО ИМПОРТИРОВАНЫ ПОЛЯ И МОДЕЛЬ MESSAGE !!! ---
            # Если Message - это ваша модель, то:
            # ```python
            # from .models import Mailing, Client, MessageAttempt, Message
            # ```
            # И в Mailing модели:
            # ```python
            # message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='mailings')
            # ```
            # Если `subject` и `body` находятся непосредственно в `Mailing`, то используйте:
            # subject=mailing.subject, body=mailing.body

            sent_count = send_mail(
                subject=mailing.message.subject, # Пример
                message=mailing.message.body,    # Пример
                from_email=settings.DEFAULT_FROM_EMAIL, # !!! settings импортирован !!!
                recipient_list=[client.email],
                fail_silently=False, # Важно: выбросит исключение при ошибке
            )
            send_duration_ms = int((time.time() - send_start_time) * 1000)

            # --- Обработка результата ---
            if sent_count == 1:
                logger.info(
                    f"[{task_id}] ✅ Письмо успешно отправлено на {client.email} "
                    f"(длительность: {send_duration_ms} мс)."
                )
                # Создаем запись о попытке отправки
                MessageAttempt.objects.create(
                    mailing=mailing,
                    client=client,
                    status='success',
                    # server_response - здесь может быть что-то более конкретное,
                    # если send_mail позволит это получить. Чаще всего нет.
                    server_response=f'Отправлено за {send_duration_ms} мс.',
                    # attempt_time устанавливается автоматически через auto_now_add=True
                )
                return True # Задача успешно выполнена
            else:
                # Это сценарий, когда send_mail не выбросил исключение (fail_silently=False),
                # но и не вернул 1 (т.е. не отправил 1 письмо).
                # Это редкая, но возможная ситуация.
                error_msg = "send_mail вернул 0, но не вызвал исключение."
                logger.error(f"[{task_id}] ❌ {error_msg} (Клиент: {client.email})")
                MessageAttempt.objects.create(
                    mailing=mailing,
                    client=client,
                    status='failed',
                    server_response=error_msg,
                )
                # Не повторяем задачу при таком странном поведении, чтобы не зациклить.
                return False

        except BadHeaderError as e:
            # Явное исключение для некорректных заголовков
            error_msg = f"Ошибка в заголовках письма: {e}"
            logger.error(f"[{task_id}] ❌ {error_msg} (Клиент: {client.email})")
            MessageAttempt.objects.create(
                mailing=mailing,
                client=client,
                status='failed',
                server_response=error_msg,
            )
            # Не повторяем задачу при BadHeaderError. Проблема в данных рассылки.
            return False

        except Exception as e:
            # Ловим все остальные исключения при отправке письма
            error_msg = f"Ошибка при отправке письма: {e}"
            logger.error(f"[{task_id}] ❌ {error_msg} (Клиент: {client.email})")

            # Создаем запись о неудачной попытке
            MessageAttempt.objects.create(
                mailing=mailing,
                client=client,
                status='failed',
                server_response=str(e), # Сохраняем текст ошибки
            )
            # !!! Важно !!! Передаем исключение дальше.
            # Celery увидит это исключение и, согласно `@shared_task` декоратору,
            # попытается повторить задачу (согласно max_retries и default_retry_delay).
            raise e

    except Mailing.DoesNotExist:
        logger.error(f"[{task_id}] Рассылка с ID {mailing_id} не найдена. Задача отменена.")
        return False # Задача выполнена, но с причиной отмены. Не повторять.
    except Client.DoesNotExist:
        logger.error(f"[{task_id}] Клиент с ID {client_id} не найден. Задача отменена.")
        return False # Задача выполнена, но с причиной отмены. Не повторять.
    except Exception as e:
        # Ловим любые другие неожиданные ошибки (например, проблемы с моделями)
        # Важно, чтобы задача также повторилась
        logger.error(f"[{task_id}] !!! Непредвиденная ошибка в задаче: {e}")
        raise e # Передаем исключение, чтобы Celery мог повторить