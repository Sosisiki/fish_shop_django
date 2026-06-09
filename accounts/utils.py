from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_verification_email(email, code, purpose='register'):
    """Отправляет письмо с кодом подтверждения"""
    subject = f"{settings.EMAIL_SUBJECT_PREFIX}{'Подтверждение регистрации' if purpose == 'register' else 'Сброс пароля'}"
    
    # Текст письма
    text_message = f"""
Здравствуйте!

Ваш код подтверждения: {code}

{'Для завершения регистрации' if purpose == 'register' else 'Для сброса пароля'} введите этот код на сайте.

Код действителен {getattr(settings, 'VERIFICATION_CODE_EXPIRE_MINUTES', 10)} минут.

Если вы не запрашивали этот код, просто проигнорируйте письмо.

С уважением,
Команда «Магазин Рыбок»
    """.strip()
    
    # HTML-версия (можно улучшить)
    html_message = render_to_string('accounts/emails/verification.html', {
        'code': code,
        'purpose': purpose,
        'expire_minutes': getattr(settings, 'VERIFICATION_CODE_EXPIRE_MINUTES', 10)
    })
    
    send_mail(
        subject=subject,
        message=text_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )