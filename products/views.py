from django.shortcuts import render, get_object_or_404
from django.db.models import Case, When, Value, IntegerField
from .models import Product

def product_list(request):
    """Каталог товаров с фильтрацией и сортировкой"""
    products = Product.objects.filter(is_secret=False)
    
    # 🔹 Получаем параметры фильтрации
    category = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'name')  # name, name_desc, price_asc, price_desc
    
    # 🔹 Применяем фильтры
    if category:
        products = products.filter(category=category)
    if min_price and min_price.isdigit():
        products = products.filter(price__gte=int(min_price))
    if max_price and max_price.isdigit():
        products = products.filter(price__lte=int(max_price))
    
    # 🔹 Применяем сортировку
    order_field = 'name'
    if sort_by == 'price_asc':
        order_field = 'price'
    elif sort_by == 'price_desc':
        order_field = '-price'
    elif sort_by == 'name_desc':
        order_field = '-name'
    # else: name (по умолчанию)
    
    # 🔹 Вторичная сортировка: сначала в наличии, потом распроданные
    products = products.annotate(
        in_stock_order=Case(
            When(stock__lte=0, then=Value(1)),
            default=Value(0),
            output_field=IntegerField()
        )
    ).order_by('in_stock_order', order_field)

    return render(request, 'products/list.html', {
        'products': products,
        'filters': request.GET,
        'sort_by': sort_by
    })

def product_detail(request, product_id):
    """Детали товара"""
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'products/detail.html', {'product': product})