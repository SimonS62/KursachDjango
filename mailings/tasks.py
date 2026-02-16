from celery import shared_task
from django.core.mail import send_mail, BadHeaderError
from django.utils import timezone
from .models import Mailing, Client, MessageAttempt
import logging


logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=5, default_retry_delay=60) # max_retries - кол-во повторов, default_retry_delay - задержка в сек.
def send_email_to_client(self, mailing_id, client_id):
    """
    Асинхронная задача для отправки письма конкретному клиенту.
    """
    task_id = self.request.id # Получаем ID задачи Celery
    logger.info(f"[{task_id}] Запуск задачи для рассылки {mailing_id}, клиента {client_id}")

    try:
        # --- Получаем объекты ---
        mailing = Mailing.objects.get(id=mailing_id)
        client = Client.objects.get(id=client_id)

        # --- Проверка времени (даже если задача была поставлена, время могло измениться) ---
        now = timezone.now()
        if not (mailing.start_time <= now <= mailing.end_time):
            logger.warning(f"[{task_id}] ⏰ Время для рассылки {mailing.id} истекло или еще не началось. Задача отменена.")
            # Не создаем attempt, так как это не ошибка отправки, а изменение условий
            return False # Задача завершена, но без результата

        # --- Отправка письма ---
        try:
            send_start_time = time.time() # Замер времени отправки
            sent_count = send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=settings.DEFAULT_FROM_EMAIL, # Используем настройку из settings.py
                recipient_list=[client.email],
                fail_silently=False, # Важно: если False, то при ошибке будет выброшено исключение
            )
            send_duration_ms = int((time.time() - send_start_time) * 1000)

            # --- Обработка результата ---
            if sent_count == 1: # send_mail возвращает количество успешно отправленных адресов
                logger.info(f"[{task_id}] ✅ Письмо успешно отправлено на {client.email} (длительность: {send_duration_ms} мс).")
                MessageAttempt.objects.create(
                    mailing=mailing,
                    client=client,
                    status='success',
                    server_response='Письмо успешно отправлено.', # Здесь может быть ответ сервера, если send_mail его вернет
                    # attempt_time устанавливается автоматически через auto_now_add=True
                )
                return True
            else:
                # Если sent_count == 0, а fail_silently=False, это странно, но обработаем
                raise Exception("send_mail вернул 0, но не вызвал исключение.")

        except BadHeaderError as e:
            error_msg = f"Ошибка в заголовках письма: {e}"
            logger.error(f"[{task_id}] ❌ {error_msg} (Клиент: {client.email})")
            MessageAttempt.objects.create(
                mailing=mailing,
                client=client,
                status='failed',
                server_response=error_msg,
                # attempt_time устанавливается автоматически
            )
            # Не повторяем задачу при BadHeaderError, т.к. она скорее всего связана с некорректными данными
            return False
        except Exception as e:
            error_msg = f"Ошибка при отправке письма: {e}"
            logger.error(f"[{task_id}] ❌ {error_msg} (Клиент: {client.email})")

            MessageAttempt.objects.create(
                mailing=mailing,
                client=client,
                status='failed',
                server_response=str(e), # Сохраняем текст ошибки
                # attempt_time устанавливается автоматически
            )
            # Передаем исключение дальше, чтобы Celery знал о неудаче и мог повторить
            raise e

    except Mailing.DoesNotExist:
        logger.error(f"[{task_id}] Рассылка с ID {mailing_id} не найдена. Задача отменена.")
        return False
    except Client.DoesNotExist:
        logger.error(f"[{task_id}] Клиент с ID {client_id} не найден. Задача отменена.")
        return False
    except Exception as e: # Ловим любые другие неожиданные ошибки
        logger.error(f"[{task_id}] Непредвиденная ошибка в задаче: {e}")
        # Передаем исключение для Celery, чтобы он мог повторить задачу
        raise e
