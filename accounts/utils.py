import logging
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_verification_email(email, code, purpose='register'):
    """Отправляет письмо с кодом подтверждения через Resend"""
    try:
        # Формируем тему письма
        subject = f"{settings.EMAIL_SUBJECT_PREFIX}{'Подтверждение регистрации' if purpose == 'register' else 'Сброс пароля'}"
        
        # Текстовая версия письма
        text_message = f"""Здравствуйте!

Ваш код подтверждения: {code}

{'Для завершения регистрации' if purpose == 'register' else 'Для сброса пароля'} введите этот код на сайте.

Код действителен {getattr(settings, 'VERIFICATION_CODE_EXPIRE_MINUTES', 10)} минут.

Если вы не запрашивали этот код, просто проигнорируйте письмо.

С уважением,
Команда «Магазин Рыбок»""".strip()
        
        # HTML-версия письма (если шаблон есть)
        html_message = None
        try:
            html_message = render_to_string('accounts/emails/verification.html', {
                'code': code,
                'purpose': purpose,
                'expire_minutes': getattr(settings, 'VERIFICATION_CODE_EXPIRE_MINUTES', 10)
            })
        except Exception as e:
            logger.warning(f"⚠️ Не удалось загрузить HTML-шаблон: {e}")
        
        # Отправляем письмо
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"✅ Email с кодом {code} отправлен на {email} (цель: {purpose})")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки email на {email}: {str(e)}")
        # В демо-режиме логируем, но не прерываем работу
        if hasattr(settings, 'EMAIL_BACKEND') and 'console' in settings.EMAIL_BACKEND:
            logger.info(f"📧 [ДЕМО-РЕЖИМ] Код {code} для {email} выведен в консоль")
        return False