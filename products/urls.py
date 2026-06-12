from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='catalog'),
    path('<int:product_id>/', views.product_detail, name='product_detail'),
    path('api/context/', views.product_context_api, name='product_context_api'),
]