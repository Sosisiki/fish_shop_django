from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import random, string
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    email_verified = models.BooleanField("Email подтверждён", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"Профиль {self.user.username} ({self.user.email})"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Создаёт профиль при регистрации нового пользователя"""
    if created:
        Profile.objects.get_or_create(user=instance, defaults={'email_verified': False})


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Безопасно сохраняет профиль"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        Profile.objects.get_or_create(user=instance)


class VerificationCode(models.Model):
    """Код подтверждения для регистрации и восстановления пароля"""
    PURPOSE_CHOICES = [
        ('register', 'Регистрация'),
        ('password_reset', 'Сброс пароля'),
    ]
    
    email = models.EmailField("Email", max_length=254)
    code = models.CharField("Код подтверждения", max_length=6)
    purpose = models.CharField("Назначение", max_length=20, choices=PURPOSE_CHOICES, default='register')
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField("Использован", default=False)

    class Meta:
        verbose_name = "Код подтверждения"
        verbose_name_plural = "Коды подтверждения"
        ordering = ['-created_at']
        indexes = [models.Index(fields=['email', 'purpose', '-created_at'])]

    @classmethod
    def generate(cls, email, purpose='register'):
        """Генерирует новый 6-значный код и аннулирует старые"""
        # Аннулируем все неиспользованные коды для этого email и назначения
        cls.objects.filter(email=email, purpose=purpose, is_used=False).update(is_used=True)
        
        # Генерируем случайный 6-значный код (с сохранением ведущих нулей)
        code = str(random.randint(0, 999999)).zfill(6)
        
        return cls.objects.create(email=email, code=code, purpose=purpose)

    def is_valid(self):
        """Проверяет, действителен ли код (не использован и не истёк)"""
        from django.conf import settings
        expire_minutes = getattr(settings, 'VERIFICATION_CODE_EXPIRE_MINUTES', 10)
        expired = (timezone.now() - self.created_at).total_seconds() > (expire_minutes * 60)
        return not self.is_used and not expired


class PasswordResetToken(models.Model):
    """Токен для восстановления пароля (дополнительная защита)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField("Токен", max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField("Использован", default=False)

    class Meta:
        verbose_name = "Токен сброса пароля"
        verbose_name_plural = "Токены сброса пароля"
        ordering = ['-created_at']

    @classmethod
    def generate(cls, user):
        """Генерирует новый токен для пользователя"""
        import secrets
        # Аннулируем старые токены
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        token = secrets.token_urlsafe(32)
        return cls.objects.create(user=user, token=token)

    def is_valid(self):
        """Токен действителен 1 час"""
        from django.utils import timezone
        expired = (timezone.now() - self.created_at).total_seconds() > 3600
        return not self.is_used and not expired