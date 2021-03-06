from rest_framework import serializers
from order.models import OrderInfo, OrderBooks
from books.serializers import BooksSerializer


class OrderInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderInfo
        fields = ("order_id", "status", "total_price", "trade_id",
                  "create_time")


class OrderBooksSerializer(serializers.ModelSerializer):
    books = BooksSerializer(read_only=True)

    class Meta:
        model = OrderBooks
        fields = "__all__"
