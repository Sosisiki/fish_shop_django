import json
import uuid
import re
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import Order, OrderItem, CartItem
from .cart import CartManager
from .services import process_payment_mock
from .n8n_client import n8n_client
from products.models import Product

logger = logging.getLogger(__name__)

# === КОРЗИНА ===

def cart_view(request):
    """Страница корзины"""
    cart = CartManager(request)
    items = cart.get_all()
    context = {
        'items': items,
        'total': cart.cart.total_amount,
        'total_items': cart.cart.total_items,
    }
    return render(request, 'orders/cart.html', context)

@require_POST
@login_required
def cart_add(request, product_id):
    """Добавить товар в корзину (AJAX) с валидацией остатка"""
    try:
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Товар не найден'}, status=404)

        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        if quantity < 1: quantity = 1

        cart = CartManager(request)
        
        # 🔹 ПРОВЕРКА: нельзя добавить больше, чем есть на складе
        current_in_cart = CartItem.objects.filter(
            cart=cart.cart, 
            product=product
        ).values_list('quantity', flat=True).first() or 0
        
        available = product.stock - current_in_cart
        if quantity > available:
            return JsonResponse({
                'success': False, 
                'message': f'❌ Доступно только {available} шт. (на складе: {product.stock})'
            }, status=400)

        cart.add(product_id, quantity)

        return JsonResponse({
            'success': True,
            'message': f'✅ "{product.name}" (×{quantity}) добавлен в корзину',
            'total_items': cart.cart.total_items,
            'remaining_stock': product.stock - quantity - current_in_cart
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Неверный формат данных'}, status=400)
    except ValidationError as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Ошибка добавления в корзину: {e}")
        return JsonResponse({'success': False, 'message': 'Ошибка сервера'}, status=500)

@require_POST
@login_required
def cart_remove(request, product_id):
    """Удалить товар из корзины (AJAX)"""
    try:
        cart = CartManager(request)
        cart.remove(product_id)
        return JsonResponse({
            'success': True,
            'total_items': cart.cart.total_items
        })
    except Exception as e:
        logger.error(f"Ошибка удаления из корзины: {e}")
        return JsonResponse({'success': False, 'message': 'Ошибка'}, status=500)

@require_POST
@login_required
def cart_update(request, product_id):
    """Обновить количество товара с валидацией остатка"""
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        if quantity < 1: quantity = 1

        cart = CartManager(request)
        
        # 🔹 ПРОВЕРКА остатка
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Товар не найден'}, status=404)
        
        if quantity > product.stock:
            return JsonResponse({
                'success': False,
                'message': f'❌ На складе доступно только {product.stock} шт.'
            }, status=400)

        item = cart.update_quantity(product_id, quantity)

        if item:
            return JsonResponse({
                'success': True,
                'total': item.total_price,
                'cart_total': cart.cart.total_amount,
                'total_items': cart.cart.total_items,
                'remaining_stock': product.stock - quantity
            })
        return JsonResponse({'success': False, 'message': 'Товар не найден в корзине'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Неверный формат данных'}, status=400)
    except ValidationError as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Ошибка обновления корзины: {e}")
        return JsonResponse({'success': False, 'message': 'Ошибка'}, status=500)

@login_required
def cart_clear(request):
    """Очистить корзину"""
    cart = CartManager(request)
    cart.clear()
    messages.success(request, 'Корзина очищена')
    return redirect('orders:cart')

# === ОФОРМЛЕНИЕ ЗАКАЗА ===

@login_required
def checkout_view(request):
    """Страница оформления заказа"""
    cart = CartManager(request)
    items = cart.get_all()
    
    if not items:
        messages.warning(request, 'Корзина пуста')
        return redirect('products:catalog')
    
    context = {
        'items': items,
        'total': cart.cart.total_amount,
        'total_items': cart.cart.total_items,
    }
    return render(request, 'orders/checkout.html', context)

@login_required
@require_POST
def create_order(request):
    """Создание заказа из корзины и оплата"""
    try:
        data = json.loads(request.body)
        
        delivery_address = data.get('address', '').strip()
        delivery_coords = data.get('coords', '')
        delivery_comment = data.get('comment', '')
        payment_method = data.get('payment_method', 'card')
        agreement_accepted = data.get('agreement_accepted', False)
        
        if not agreement_accepted:
            return JsonResponse({'success': False, 'message': 'Необходимо принять условия оферты'}, status=400)
        if not delivery_address:
            return JsonResponse({'success': False, 'message': 'Укажите адрес доставки'}, status=400)
        
        cart = CartManager(request)
        items = cart.get_all()
        
        if not items:
            return JsonResponse({'success': False, 'message': 'Корзина пуста'}, status=400)
        
        # 🔹 ФИНАЛЬНАЯ ПРОВЕРКА остатков перед заказом
        for cart_item in items:
            if cart_item.quantity > cart_item.product.stock:
                return JsonResponse({
                    'success': False,
                    'message': f'❌ "{cart_item.product.name}": доступно только {cart_item.product.stock} шт.'
                }, status=400)
        
        total_amount = sum(item.total_price for item in items)
        
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                total_amount=total_amount,
                status='PENDING',
                delivery_address=delivery_address,
                delivery_coords=delivery_coords,
                delivery_comment=delivery_comment,
                agreement_accepted=True
            )
            
            for cart_item in items:
                # Уменьшаем остаток на складе
                product = cart_item.product
                product.stock -= cart_item.quantity
                product.save(update_fields=['stock'])
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=cart_item.price,
                    quantity=cart_item.quantity
                )
            
            cart.clear()
        
        # Тестовая оплата
        test_mode = getattr(settings, 'YOOMONEY_TEST_MODE', True)
        if test_mode is True or test_mode == 'True':
            is_paid = process_payment_mock(order)
            if is_paid:
                order.status = 'PAID'
                order.save()
                logger.info(f"✅ Заказ #{order.id} оплачен, доставка: {delivery_address}")
                return JsonResponse({
                    'success': True,
                    'message': f'Оплата прошла успешно! Заказ #{order.id}. Доставка: {delivery_address}',
                    'order_id': order.id
                })
        
        order.status = 'FAILED'
        order.save()
        return JsonResponse({'success': False, 'message': 'Оплата не прошла'}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Неверный формат данных'}, status=400)
    except Exception as e:
        logger.exception(f"Ошибка создания заказа: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Внутренняя ошибка сервера'
        }, status=500)

# === ИСТОРИЯ ЗАКАЗОВ ===

@login_required
def order_history(request):
    """История заказов пользователя"""
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product')
    return render(request, 'orders/history.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    """Детали заказа"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/detail.html', {'order': order})

@login_required
def request_refund(request, order_id):
    """Запрос на возврат средств по заказу"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status != 'PAID':
        messages.error(request, 'Возврат возможен только для оплаченных заказов.')
        return redirect('orders:order_detail', order_id=order.id)
    
    order.status = 'REFUND_REQUESTED'
    order.save()
    messages.success(request, '✅ Запрос на возврат отправлен. Ожидайте подтверждения.')
    return redirect('orders:order_detail', order_id=order.id)

# === AI-КОНСУЛЬТАНТ (n8n) ===

def extract_json_from_ai(text: str):
    """Безопасное извлечение JSON из ответа AI"""
    if not text: return None
    try:
        data = json.loads(text)
        if isinstance(data, dict) and 'action' in data:
            return data
    except (json.JSONDecodeError, TypeError):
        pass
    
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try: return json.loads(match.group(1))
        except: pass
        
    match = re.search(r'\{[^{}]*"action"[^{}]*\}', text, re.DOTALL)
    if match:
        try: return json.loads(match.group())
        except: pass
    return None

@transaction.atomic
def process_chat_order(request, payload):
    """Обработка заказа, сформированного через чат-бота"""
    try:
        items_data = payload.get('items', [])
        address = payload.get('address', '').strip()
        payment_method = payload.get('payment_method', 'card')
        
        if not items_data or not address:
            return JsonResponse({'success': False, 'message': '❌ Не указаны товары или адрес доставки.'})
        
        total_amount = 0
        order_items = []
        
        for item in items_data:
            try:
                product = Product.objects.get(id=item.get('product_id'))
            except Product.DoesNotExist:
                return JsonResponse({'success': False, 'message': f'❌ Товар с ID {item.get("product_id")} не найден.'})
            
            qty = max(1, int(item.get('quantity', 1)))
            # 🔹 Проверка остатка
            if qty > product.stock:
                return JsonResponse({'success': False, 'message': f'❌ "{product.name}": доступно только {product.stock} шт.'})
            
            total_amount += product.price * qty
            order_items.append({'product': product, 'quantity': qty, 'price': product.price})
        
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            total_amount=total_amount,
            status='PENDING',
            delivery_address=address,
            delivery_comment='Заказ оформлен через AI-чат',
            agreement_accepted=True
        )
        
        for oi in order_items:
            # Уменьшаем остаток
            oi['product'].stock -= oi['quantity']
            oi['product'].save(update_fields=['stock'])
            
            OrderItem.objects.create(
                order=order,
                product=oi['product'],
                price=oi['price'],
                quantity=oi['quantity']
            )
        
        # Тестовая оплата
        test_mode = getattr(settings, 'YOOMONEY_TEST_MODE', True)
        if test_mode is True or test_mode == 'True':
            is_paid = process_payment_mock(order)
            if is_paid:
                order.status = 'PAID'
                order.save()
                return JsonResponse({
                    'success': True,
                    'message': f'✅ Заказ #{order.id} успешно оформлен и оплачен! 🐠\n📍 Доставка: {address}\n💳 Способ: {payment_method}\nСпасибо за покупку!',
                    'session_id': payload.get('session_id')
                })
        
        return JsonResponse({
            'success': True,
            'message': f'✅ Заказ #{order.id} создан. Ожидает оплаты.',
            'session_id': payload.get('session_id')
        })
        
    except Exception as e:
        logger.exception(f"❌ Ошибка при оформлении заказа через чат: {e}")
        return JsonResponse({'success': False, 'message': '❌ Не удалось оформить заказ. Попробуйте через корзину.'})

@csrf_exempt
@require_POST
def consultant_chat(request):
    """API endpoint для чата с консультантом (n8n)"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not message:
            return JsonResponse({
                'success': False,
                'message': 'Сообщение не может быть пустым'
            }, status=400)
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        user_id = request.user.id if request.user.is_authenticated else None
        
        result = n8n_client.send_message(
            message=message,
            session_id=session_id,
            user_id=request.user.id if request.user.is_authenticated else None
        )
        
        if not result.get('success'):
            return JsonResponse(result, status=200)
        
        ai_response = result.get('message', '')
        
        # Проверяем, вернул ли AI команду на создание заказа
        order_payload = extract_json_from_ai(ai_response)
        if order_payload and order_payload.get('action') == 'create_order':
            return process_chat_order(request, order_payload)
        
        # Обычный текстовый ответ
        return JsonResponse({
            'success': True,
            'message': ai_response,
            'session_id': session_id
        })
        
    except json.JSONDecodeError:
        logger.error("❌ Ошибка парсинга JSON в consultant_chat")
        return JsonResponse({
            'success': False,
            'message': 'Неверный формат данных'
        }, status=400)
    except Exception as e:
        logger.exception(f"💥 Критическая ошибка в consultant_chat: {e}")
        # 🔹 Возвращаем мягкую ошибку вместо 500
        return JsonResponse({
            'success': False, 
            'message': '🔧 Сервис временно недоступен. Попробуйте позже.'
        }, status=200)