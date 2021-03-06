from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register),
    path('login/', views.login),
    path('logout/', views.logout),
    path('info/', views.info),
    path('address/', views.address),
    path('change/', views.change_password),
    path('verify/', views.verify),
    path('setP/', views.set_password),
    path('verifycode/', views.verifycode),
]
