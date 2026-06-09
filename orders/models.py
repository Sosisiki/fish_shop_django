from django.db import models
from django.conf import settings

class Cart(models.Model):
    """Корзина пользователя (хранится в БД для авторизованных)"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        verbose_name="Пользователь",
        null=True, blank=True
    )
    session_key = models.CharField("Сессия", max_length=40, blank=True, null=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"
        unique_together = ['user', 'session_key']

    def __str__(self):
        return f"Корзина #{self.id}"

    @property
    def total_amount(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

class CartItem(models.Model):
    """Товар в корзине"""
    cart = models.ForeignKey(
        Cart, 
        on_delete=models.CASCADE, 
        related_name="items", 
        verbose_name="Корзина"
    )
    product = models.ForeignKey(
        'products.Product', 
        on_delete=models.CASCADE, 
        verbose_name="Товар"
    )
    quantity = models.IntegerField("Количество", default=1)
    price = models.IntegerField("Цена на момент добавления")

    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзине"
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.product.name} × {self.quantity}"

    @property
    def total_price(self):
        return self.price * self.quantity

# === Старые модели заказа (оставляем как есть) ===

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Ожидание оплаты'),
        ('PAID', 'Оплачено'),
        ('FAILED', 'Ошибка оплаты'),
        ('CANCELLED', 'Отменено'),
        ('REFUND_REQUESTED', 'Запрос на возврат'),
        ('REFUNDED', 'Возврат выполнен'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        verbose_name="Покупатель"
    )
    total_amount = models.IntegerField("Сумма заказа")
    status = models.CharField(
        "Статус", 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING'
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)
    payment_id = models.CharField("ID платежа", max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Заказ #{self.id} ({self.status})"
    
    delivery_address = models.TextField("Адрес доставки", blank=True, null=True)
    delivery_coords = models.CharField("Координаты (Яндекс.Карты)", max_length=50, blank=True, null=True)
    delivery_comment = models.TextField("Комментарий к доставке", blank=True, null=True)
    agreement_accepted = models.BooleanField("Согласие с офертой", default=False)
    
    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name="items", 
        verbose_name="Заказ"
    )
    product = models.ForeignKey(
        'products.Product', 
        on_delete=models.CASCADE, 
        verbose_name="Товар"
    )
    price = models.IntegerField("Цена на момент покупки")
    quantity = models.IntegerField("Количество", default=1)

    def __str__(self):
        return self.product.name

    @property
    def total_price(self):
        return self.price * self.quantity