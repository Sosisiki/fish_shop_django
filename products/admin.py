from django.contrib import admin
from .models import Product

# 🔹 Базовый класс админки для всех товаров
class ProductAdminBase(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'is_secret', 'created_at')
    list_editable = ('price', 'stock')
    list_filter = ('is_secret', 'stock')
    search_fields = ('name', 'description')
    ordering = ('-created_at',)
    fieldsets = (
        ('Основная информация', {'fields': ('name', 'description', 'price', 'image', 'is_secret')}),
        ('Характеристики', {'fields': ('category', 'difficulty', 'min_volume', 'stock')}),
    )

    def save_model(self, request, obj, form, change):
        # Автоматически присваиваем категорию при добавлении через раздел
        if hasattr(self, 'fixed_category') and not obj.category:
            obj.category = self.fixed_category
        super().save_model(request, obj, form, change)


# 🔹 Общий раздел (по желанию, можно удалить если нужны только тематические)
@admin.register(Product)
class AllProductsAdmin(ProductAdminBase):
    list_filter = ('category',) + ProductAdminBase.list_filter
    list_display = ('name', 'category', 'price', 'stock', 'is_secret')


# 🔹 Proxy-модели для разделения в боковом меню админки
class FishProduct(Product):
    class Meta:
        proxy = True
        verbose_name = "Рыбка"
        verbose_name_plural = "🐠 Рыбки"

class AquariumProduct(Product):
    class Meta:
        proxy = True
        verbose_name = "Аквариум"
        verbose_name_plural = "🐟 Аквариумы"

class AccessoryProduct(Product):
    class Meta:
        proxy = True
        verbose_name = "Аксессуар"
        verbose_name_plural = "🔧 Аксессуары"

class FoodProduct(Product):
    class Meta:
        proxy = True
        verbose_name = "Корм"
        verbose_name_plural = "🍽 Корма"


# 🔹 Регистрация отдельных разделов
@admin.register(FishProduct)
class FishAdmin(ProductAdminBase):
    fixed_category = 'fish'
    def get_queryset(self, request):
        return super().get_queryset(request).filter(category='fish')

@admin.register(AquariumProduct)
class AquariumAdmin(ProductAdminBase):
    fixed_category = 'aquarium'
    def get_queryset(self, request):
        return super().get_queryset(request).filter(category='aquarium')

@admin.register(AccessoryProduct)
class AccessoryAdmin(ProductAdminBase):
    fixed_category = 'accessory'
    def get_queryset(self, request):
        return super().get_queryset(request).filter(category='accessory')

@admin.register(FoodProduct)
class FoodAdmin(ProductAdminBase):
    fixed_category = 'food'
    def get_queryset(self, request):
        return super().get_queryset(request).filter(category='food')