from books.models import Books
from rest_framework import serializers


# 返回Json数据
class BooksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Books
        fields = "__all__"
