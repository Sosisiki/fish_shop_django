from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'price', 'quantity', 'total_price')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'agreement_accepted', 'created_at')
    list_filter = ('status', 'created_at', 'agreement_accepted', 'user')
    search_fields = ('user__username', 'user__email', 'delivery_address', 'id')
    readonly_fields = ('created_at', 'updated_at', 'payment_id')
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'
    actions = ['approve_refund']

    def approve_refund(self, request, queryset):
        updated = queryset.filter(status='REFUND_REQUESTED').update(status='REFUNDED')
        self.message_user(request, f'✅ Возврат одобрен для {updated} заказов.')
    approve_refund.short_description = "Одобрить возврат средств"