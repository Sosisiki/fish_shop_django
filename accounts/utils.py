import threading
import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def send_verification_email(email, code, purpose='register'):
    """Отправляет письмо с кодом подтверждения в отдельном потоке (не блокирует воркер)"""
    
    def _send_email():
        """Внутренняя функция, которая выполняется в отдельном потоке"""
        try:
            # Формируем тему письма
            subject = f"{settings.EMAIL_SUBJECT_PREFIX}{'Подтверждение регистрации' if purpose == 'register' else 'Сброс пароля'}"
            
            # Текстовая версия письма
            text_message = f"""
Здравствуйте!

Ваш код подтверждения: {code}

{'Для завершения регистрации' if purpose == 'register' else 'Для сброса пароля'} введите этот код на сайте.

Код действителен {getattr(settings, 'VERIFICATION_CODE_EXPIRE_MINUTES', 10)} минут.

Если вы не запрашивали этот код, просто проигнорируйте письмо.

С уважением,
Команда «Магазин Рыбок»
            """.strip()
            
            # HTML-версия письма
            try:
                html_message = render_to_string('accounts/emails/verification.html', {
                    'code': code,
                    'purpose': purpose,
                    'expire_minutes': getattr(settings, 'VERIFICATION_CODE_EXPIRE_MINUTES', 10)
                })
            except Exception as e:
                logger.warning(f"⚠️ Не удалось загрузить HTML-шаблон письма: {e}. Используем только текст.")
                html_message = None
            
            # Отправляем письмо с таймаутом
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
                # 🔹 Таймаут SMTP-соединения (берём из settings или используем 10 сек)
                timeout=getattr(settings, 'EMAIL_TIMEOUT', 10),
            )
            
            logger.info(f"✅ Email с кодом {code} успешно отправлен на {email} (цель: {purpose})")
            
        except Exception as e:
            # 🔹 Логируем ошибку, но не прерываем работу приложения
            logger.error(f"❌ Ошибка отправки email на {email}: {str(e)}")
            
            # В демо-режиме (консольный бэкенд) ошибка не критична
            if hasattr(settings, 'EMAIL_BACKEND') and 'console' in settings.EMAIL_BACKEND:
                logger.info(f"📧 [ДЕМО-РЕЖИМ] Код {code} для {email} выведен в консоль сервера")
    
    # 🔹 Запускаем отправку в отдельном потоке (daemon=True — поток завершится вместе с приложением)
    thread = threading.Thread(target=_send_email, daemon=True)
    thread.start()
    
    # 🔹 Возвращаем управление сразу, не ждём завершения отправки
    logger.info(f"📤 Запущена асинхронная отправка email на {email}")