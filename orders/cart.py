from .models import Cart, CartItem
from products.models import Product
from django.core.exceptions import ValidationError

class CartManager:
    """Управление корзиной с валидацией остатков"""
    
    def __init__(self, request):
        self.request = request
        self.user = request.user if request.user.is_authenticated else None
        self.session_key = request.session.session_key
        
        if not self.session_key and not self.user:
            request.session.create()
            self.session_key = request.session.session_key
        
        self.cart = self._get_or_create_cart()
    
    def _get_or_create_cart(self):
        if self.user:
            cart, _ = Cart.objects.get_or_create(user=self.user)
        else:
            cart, _ = Cart.objects.get_or_create(session_key=self.session_key)
        return cart
    
    def add(self, product_id, quantity=1):
        """Добавить товар с проверкой остатка на складе"""
        product = Product.objects.get(id=product_id)
        
        # 🔹 ПРОВЕРКА: нельзя добавить больше, чем есть на складе
        current_in_cart = CartItem.objects.filter(
            cart=self.cart, 
            product=product
        ).values_list('quantity', flat=True).first() or 0
        
        available = product.stock - current_in_cart
        if quantity > available:
            raise ValidationError(f'❌ Доступно только {available} шт. (на складе: {product.stock}, в корзине: {current_in_cart})')
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=self.cart,
            product=product,
            defaults={'quantity': quantity, 'price': product.price}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.price = product.price
            cart_item.save()
        
        return cart_item
    
    def update_quantity(self, product_id, quantity):
        """Обновить количество с проверкой остатка"""
        if quantity <= 0:
            return self.remove(product_id)
        
        product = Product.objects.get(id=product_id)
        
        # 🔹 ПРОВЕРКА: новое количество не должно превышать остаток
        if quantity > product.stock:
            raise ValidationError(f'❌ На складе доступно только {product.stock} шт.')
        
        try:
            item = CartItem.objects.get(cart=self.cart, product_id=product_id)
            item.quantity = quantity
            item.save()
            return item
        except CartItem.DoesNotExist:
            return None
    
    def get_all(self):
        """Получить все товары с актуальными остатками"""
        items = self.cart.items.select_related('product').all()
        # Добавляем поле available для каждого товара
        for item in items:
            item.available = item.product.stock
        return items
    
    def remove(self, product_id):
        try:
            item = CartItem.objects.get(cart=self.cart, product_id=product_id)
            item.delete()
            return True
        except CartItem.DoesNotExist:
            return False
    
    def clear(self):
        self.cart.items.all().delete()
    
    def merge_anonymous_cart(self, user):
        if not user.is_authenticated:
            return
        try:
            anon_cart = Cart.objects.get(session_key=self.session_key)
            if anon_cart.items.exists():
                user_cart, _ = Cart.objects.get_or_create(user=user)
                for item in anon_cart.items.all():
                    cart_item, created = CartItem.objects.get_or_create(
                        cart=user_cart,
                        product=item.product,
                        defaults={'quantity': item.quantity, 'price': item.price}
                    )
                    if not created:
                        cart_item.quantity += item.quantity
                        cart_item.save()
                anon_cart.delete()
        except Cart.DoesNotExist:
            pass