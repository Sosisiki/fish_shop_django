from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # === КОРЗИНА ===
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('cart/update/<int:product_id>/', views.cart_update, name='cart_update'),
    path('cart/clear/', views.cart_clear, name='cart_clear'),
    
    # === ОФОРМЛЕНИЕ ЗАКАЗА ===
    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/create/', views.create_order, name='create_order'),
    
    # === ИСТОРИЯ ЗАКАЗОВ ===
    path('history/', views.order_history, name='order_history'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),
    path('<int:order_id>/refund/', views.request_refund, name='request_refund'),
    
    # === КОНСУЛЬТАНТ ===
    path('consultant/', views.consultant_chat, name='consultant_chat'),
]