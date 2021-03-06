from django.urls import path
from . import views

urlpatterns = [
    path('show/<book_id>', views.comment),
]
