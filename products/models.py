from django.db import models

class Product(models.Model):
    # 🔹 Основные разделы каталога
    CATEGORY_CHOICES = [
        ('fish', '🐠 Рыбки'),
        ('aquarium', '🐟 Аквариумы'),
        ('accessory', '🔧 Аксессуары'),
        ('food', '🍽 Корма'),
    ]
    
    # 🔹 Только для рыбок
    DIFFICULTY_CHOICES = [
        ('easy', 'Новичок'),
        ('medium', 'Средний'),
        ('hard', 'Профи'),
    ]

    name = models.CharField("Название", max_length=100)
    description = models.TextField("Описание", default="Товар с доставкой")
    full_description = models.TextField("Полное описание", blank=True, default="")  # 🔹 НОВОЕ ПОЛЕ
    price = models.IntegerField("Цена (₽)")
    price = models.IntegerField("Цена (₽)")
    image = models.ImageField("Картинка", upload_to="products/", blank=True, null=True)
    is_secret = models.BooleanField("Секретный товар", default=False)
    created_at = models.DateTimeField("Дата добавления", auto_now_add=True)

    # 🔹 Категория (обязательная)
    category = models.CharField("Раздел", max_length=20, choices=CATEGORY_CHOICES, default='fish')
    
    # 🔹 Дополнительные поля (только для рыбок)
    difficulty = models.CharField("Сложность", max_length=20, choices=DIFFICULTY_CHOICES, default='easy', blank=True, null=True)
    min_volume = models.IntegerField("Мин. объём (л)", default=10, blank=True, null=True)
    
    # 🔹 Остаток на складе (для всех товаров)
    stock = models.IntegerField("Остаток на складе", default=10)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['category', 'name']