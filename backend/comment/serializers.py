from rest_framework import serializers
from .models import Comment


class CommentSerializers(serializers.ModelSerializer):
    book_name = serializers.CharField(source='book.name')
    user_name = serializers.CharField(source='user.username')

    class Meta:
        model = Comment
        fields = ('content', 'book_name', 'user_name', 'create_time',
                  'disabled')
