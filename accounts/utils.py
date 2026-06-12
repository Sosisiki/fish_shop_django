import logging
from django.conf import settings
from django.template.loader import render_to_string
import resend  # ← Официальный пакет Resend

logger = logging.getLogger(__name__)

# Инициализируем клиент один раз при импорте
resend.api_key = getattr(settings, 'RESEND_API_KEY', '')


def send_verification_email(email, code, purpose='register'):
    """Отправляет письмо с кодом подтверждения через Resend API"""
    
    # 🔹 Если ключ не настроен — используем демо-режим
    if not resend.api_key:
        logger.warning("⚠️ RESEND_API_KEY не настроен. Демо-режим: код выведен в логи.")
        logger.info(f"📧 [ДЕМО] Код подтверждения для {email}: {code}")
        return True
    
    try:
        # Формируем тему письма
        subject = f"{settings.EMAIL_SUBJECT_PREFIX}{'Подтверждение регистрации' if purpose == 'register' else 'Сброс пароля'}"
        
        # Текстовая версия
        text_message = f"""Здравствуйте!

Ваш код подтверждения: {code}

{'Для завершения регистрации' if purpose == 'register' else 'Для сброса пароля'} введите этот код на сайте.

Код действителен {getattr(settings, 'VERIFICATION_CODE_EXPIRE_MINUTES', 10)} минут.

Если вы не запрашивали этот код, просто проигнорируйте письмо.

С уважением,
Команда «Магазин Рыбок»""".strip()
        
        # HTML-версия (если шаблон есть)
        html_message = None
        try:
            html_message = render_to_string('accounts/emails/verification.html', {
                'code': code,
                'purpose': purpose,
                'expire_minutes': getattr(settings, 'VERIFICATION_CODE_EXPIRE_MINUTES', 10)
            })
        except Exception as e:
            logger.warning(f"⚠️ Не удалось загрузить HTML-шаблон: {e}")
        
        # 🔹 Отправляем через официальный клиент Resend
        email_params = {
            "from": settings.DEFAULT_FROM_EMAIL,  # Например: noreply@fishshop.resend.dev
            "to": email,
            "subject": subject,
            "text": text_message,
        }
        if html_message:
            email_params["html"] = html_message
        
        response = resend.Emails.send(email_params)
        
        logger.info(f"✅ Email отправлен через Resend: {response.get('id', 'unknown')}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки через Resend: {str(e)}")
        # В демо-режиме показываем код в логах
        logger.info(f"📧 [ДЕМО] Код для {email}: {code}")
        return False