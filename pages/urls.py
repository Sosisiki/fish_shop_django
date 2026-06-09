from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('support/', views.support, name='support'),
    path('delivery/', views.delivery, name='delivery'),
    path('returns/', views.returns, name='returns'),
    path('guarantee/', views.guarantee, name='guarantee'),
]