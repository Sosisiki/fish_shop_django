from django.db import models
from django.conf import settings
import os
import urllib.parse


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
        """
        Возвращает URL картинки из static/products/{id}.jpg
        или цветную SVG-заглушку, если файла нет.
        """
        # 🔹 Формируем путь к файлу: static/products/{id}.jpg
        filename = f"{self.id}.jpg"
        relative_path = os.path.join('products', filename)
        full_path = os.path.join(settings.BASE_DIR, 'static', 'products', filename)
        
        # 🔹 Проверяем существование файла на диске
        if os.path.exists(full_path):
            # ✅ Файл есть — возвращаем URL через static()
            from django.templatetags.static import static
            return static(relative_path)
        
        # ❌ Файла нет — возвращаем inline SVG-заглушку
        return self._get_fallback_svg()

    def _get_fallback_svg(self):
        """Генерирует inline SVG-заглушку как data: URI (без внешних запросов)"""
        # 🔹 Цвета по категориям
        colors = {
            'fish': ('4A90E2', '🐠'),
            'aquarium': ('50C878', '🐟'),
            'food': ('FF6B6B', '🍽'),
            'accessory': ('9B59B6', '🔧'),
        }
        bg_color, emoji = colors.get(self.category, ('95A5A6', '📦'))
        
        # 🔹 Короткое название и цена
        short_name = self.name[:15]
        price_tag = f'{int(self.price)}₽'
        
        # 🔹 Формируем SVG
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">
  <rect width="100%" height="100%" fill="#{bg_color}"/>
  <text x="50%" y="45%" font-family="Arial, sans-serif" font-size="48" fill="white" text-anchor="middle" dominant-baseline="middle">{emoji}</text>
  <text x="50%" y="65%" font-family="Arial, sans-serif" font-size="14" fill="white" text-anchor="middle">{short_name}</text>
  <text x="50%" y="85%" font-family="Arial, sans-serif" font-size="12" fill="rgba(255,255,255,0.9)" text-anchor="middle">{price_tag}</text>
</svg>'''
        
        # 🔹 Кодируем в data: URI
        encoded = urllib.parse.quote(svg)
        return f'data:image/svg+xml,{encoded}'

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