from django.db import models
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


def get_product_placeholder_svg(product_id, name, category, price):
    """Генерирует inline SVG-заглушку как data: URI (без внешних запросов)"""
    
    # 🔹 Цвета по категориям
    category_colors = {
        'fish': ('4A90E2', '🐠'),
        'aquarium': ('50C878', '🐟'),
        'food': ('FF6B6B', '🍽'),
        'accessory': ('9B59B6', '🔧'),
    }
    
    bg_color, emoji = category_colors.get(category, ('95A5A6', '📦'))
    
    # 🔹 Короткое название (латиница, макс. 12 символов)
    short_name = transliterate_cyrillic(name)
    short_name = re.sub(r'[^a-z0-9\-]', '', short_name)[:12].strip('-')
    if not short_name:
        short_name = f'#{product_id}'
    
    # 🔹 Цена
    price_tag = f'{int(price)}₽'
    
    # 🔹 Формируем SVG
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">
  <rect width="100%" height="100%" fill="#{bg_color}"/>
  <text x="50%" y="45%" font-family="Arial, sans-serif" font-size="48" fill="white" text-anchor="middle" dominant-baseline="middle">{emoji}</text>
  <text x="50%" y="65%" font-family="Arial, sans-serif" font-size="16" fill="white" text-anchor="middle">{short_name}</text>
  <text x="50%" y="85%" font-family="Arial, sans-serif" font-size="14" fill="rgba(255,255,255,0.9)" text-anchor="middle">{price_tag}</text>
</svg>'''
    
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