import requests
import hashlib
import time
from django.conf import settings

def process_payment_mock(order):
    """
    ТЕСТОВАЯ ФУНКЦИЯ ОПЛАТЫ (заглушка)
    Используется если ЮMoney не настроен
    """
    print(f"💳 [MOCK] Оплата заказа #{order.id} на сумму {order.total_amount}₽")
    time.sleep(1)
    return True

def create_yoomoney_payment(order, user_email):
    """
    СОЗДАНИЕ ПЛАТЕЖА ЧЕРЕЗ ЮMONEY
    Возвращает ссылку на оплату или None при ошибке
    """
    wallet = settings.YOOMONEY_WALLET
    secret_key = settings.YOOMONEY_SECRET_KEY
    
    # Формируем параметры платежа
    params = {
        'receiver': wallet,
        'formcomment': f'Заказ #{order.id} в магазине Рыбок',
        'short-dest': f'Оплата заказа #{order.id}',
        'label': f'order_{order.id}',  # Метка для идентификации
        'amount': order.total_amount,
        'paymentType': 'PC',  # PC = кошелек ЮMoney, AC = банковская карта
        'successURL': 'http://127.0.0.1:8000/orders/success/',
    }
    
    # Для теста сразу возвращаем ссылку на форму оплаты
    payment_url = 'https://yoomoney.ru/quickpay/confirm.xml?' + '&'.join([f'{k}={v}' for k, v in params.items()])
    
    print(f"💳 Ссылка на оплату: {payment_url}")
    return payment_url

def verify_yoomoney_notification(notification_params, secret_key):
    """
    ПРОВЕРКА ПОДПИСИ УВЕДОМЛЕНИЯ ОТ ЮMONEY
    Возвращает True если уведомление подлинное
    """
    # Формируем строку для хэша
    hash_string = '&'.join([
        notification_params.get('notification_type', ''),
        notification_params.get('operation_id', ''),
        notification_params.get('amount', ''),
        notification_params.get('currency', ''),
        notification_params.get('datetime', ''),
        notification_params.get('sender', ''),
        notification_params.get('codepro', ''),
        secret_key,
        notification_params.get('label', ''),
    ])
    
    # Вычисляем хэш
    computed_hash = hashlib.sha1(hash_string.encode('utf-8')).hexdigest()
    
    # Сравниваем с полученным
    return computed_hash == notification_params.get('sha1_hash', '')

def process_yoomoney_webhook(order_id, amount, label):
    """
    ОБРАБОТКА УВЕДОМЛЕНИЯ ОТ ЮMONEY
    Обновляет статус заказа при успешной оплате
    """
    from orders.models import Order
    
    try:
        # Извлекаем ID заказа из метки (format: order_123)
        order_id_from_label = int(label.replace('order_', ''))
        
        # Находим заказ
        order = Order.objects.get(id=order_id_from_label)
        
        # Проверяем сумму
        if int(amount) == order.total_amount:
            order.status = 'PAID'
            order.payment_id = f'yoomoney_{order_id}'
            order.save()
            print(f"✅ Заказ #{order.id} оплачен через ЮMoney!")
            return True
        else:
            print(f"❌ Сумма не совпадает: {amount} vs {order.total_amount}")
            return False
            
    except Order.DoesNotExist:
        print(f"❌ Заказ #{order_id} не найден")
        return False
    except Exception as e:
        print(f"❌ Ошибка обработки webhook: {e}")
        return False