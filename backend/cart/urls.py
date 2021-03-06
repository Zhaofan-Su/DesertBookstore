from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.cart_add),
    path('count/', views.cart_count),
    path('delete/', views.cart_del),
    path('update/', views.cart_update),
    path('', views.cart_show),
]
