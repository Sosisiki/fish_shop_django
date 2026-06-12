from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 🔹 Лендинг на главной (/)
    path('', include('pages.urls')),
    
    # 🔹 Каталог на /catalog/
    path('catalog/', include('products.urls')),
    
    path('orders/', include('orders.urls')),
    path('accounts/', include('accounts.urls')),

    path('products/', include('products.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)