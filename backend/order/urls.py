from django.urls import path
from . import views

urlpatterns = [
    path('place/', views.order_place),
    path('commit/', views.order_commit),
    path('all/', views.order_all),
    path('all/<order_id>/books', views.books_in_one_order),
    path('pay/', views.order_pay),
    path('cancel/<order_id>', views.order_cancel),
]
