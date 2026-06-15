from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import random, string, hashlib
from django.utils import timezone
from django.conf import settings
import re


def transliterate_cyrillic(text):
    """Преобразует кириллицу в латиницу для URL"""
    converter = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '',
        'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya', ' ': '-'
    }
    text = text.lower().strip()
    return ''.join(converter.get(c, c) for c in text)


def get_product_placeholder(product_id, name, category, price):
    """Генерирует уникальную заглушку для товара"""
    
    # 🔹 Цвета по категориям
    category_colors = {
        'fish': ('4A90E2', '🐠'),      # синий + рыбка
        'aquarium': ('50C878', '🐟'),   # зелёный + аквариум
        'food': ('FF6B6B', '🍽'),       # красный + корм
        'accessory': ('9B59B6', '🔧'),  # фиолетовый + инструмент
    }
    
    bg_color, emoji = category_colors.get(category, ('95A5A6', '📦'))
    
    # 🔹 Короткое название для изображения (макс. 15 символов)
    short_name = transliterate_cyrillic(name)
    short_name = re.sub(r'[^a-z0-9\-]', '', short_name)[:15].strip('-')
    if not short_name:
        short_name = f'item{product_id}'
    
    # 🔹 Цена в углу (последние 2-3 цифры для уникальности)
    price_tag = str(price)[-3:] if price >= 100 else str(price)
    
    # 🔹 Формируем URL заглушки
    # via.placeholder.com поддерживает текст до ~50 символов
    text = f"{emoji}+{short_name}+{price_tag}₽"
    text = text.replace(' ', '+')[:45]  # Обрезаем, чтобы уложиться в лимит
    
    return f"https://via.placeholder.com/400x300/{bg_color}/FFFFFF?text={text}"


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
    if created:
        Profile.objects.get_or_create(user=instance, defaults={'email_verified': False})


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        Profile.objects.get_or_create(user=instance)


class VerificationCode(models.Model):
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
        cls.objects.filter(email=email, purpose=purpose, is_used=False).update(is_used=True)
        code = str(random.randint(0, 999999)).zfill(6)
        return cls.objects.create(email=email, code=code, purpose=purpose)

    def is_valid(self):
        from django.conf import settings
        expire_minutes = getattr(settings, 'VERIFICATION_CODE_EXPIRE_MINUTES', 10)
        expired = (timezone.now() - self.created_at).total_seconds() > (expire_minutes * 60)
        return not self.is_used and not expired


class PasswordResetToken(models.Model):
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
        import secrets
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        token = secrets.token_urlsafe(32)
        return cls.objects.create(user=user, token=token)

    def is_valid(self):
        from django.utils import timezone
        expired = (timezone.now() - self.created_at).total_seconds() > 3600
        return not self.is_used and not expired


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('fish', '🐠 Рыбки'),
        ('aquarium', '🐟 Аквариумы'),
        ('food', '🍽 Корма'),
        ('accessory', '🔧 Аксессуары'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('beginner', 'Новичок'),
        ('intermediate', 'Средний'),
        ('pro', 'Профи'),
    ]

    name = models.CharField("Название", max_length=200)
    category = models.CharField("Категория", max_length=20, choices=CATEGORY_CHOICES)
    price = models.DecimalField("Цена", max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField("Остаток", default=0)
    description = models.TextField("Описание", blank=True)
    difficulty = models.CharField("Сложность", max_length=20, choices=DIFFICULTY_CHOICES, blank=True, null=True)
    min_volume = models.PositiveIntegerField("Мин. объём аквариума (л)", blank=True, null=True)
    image = models.ImageField("Изображение", upload_to='products/', blank=True, null=True)
    is_secret = models.BooleanField("Скрытый товар", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.price}₽)"

    def get_image_url(self):
        """Возвращает уникальную заглушку или реальное изображение"""
        if self.image and hasattr(self.image, 'url') and self.image.url:
            return self.image.url
        return get_product_placeholder(self.id, self.name, self.category, int(self.price))

    def get_category_emoji(self):
        """Возвращает emoji категории"""
        emojis = {
            'fish': '🐠',
            'aquarium': '🐟',
            'food': '🍽',
            'accessory': '🔧',
        }
        return emojis.get(self.category, '📦')

    def get_difficulty_badge(self):
        """Возвращает цветной бейдж сложности"""
        badges = {
            'beginner': ('success', 'Новичок'),
            'intermediate': ('warning', 'Средний'),
            'pro': ('danger', 'Профи'),
        }
        return badges.get(self.difficulty, ('secondary', '—'))

    def is_in_stock(self):
        """Проверяет наличие"""
        return self.stock > 0