from django.db import models
from db.base_model import BaseModel
from users.models import Passport
from books.models import Books

# Create your models here.


class Comment(BaseModel):
    disabled = models.BooleanField(default=False, verbose_name='是否违规')
    user = models.ForeignKey(
        'users.Passport',
        verbose_name="用户",
        on_delete=models.CASCADE,
        related_name='user')
    book = models.ForeignKey(
        'books.Books',
        verbose_name="书籍",
        on_delete=models.CASCADE,
        related_name='book')
    content = models.CharField(max_length=1000, verbose_name="评论内容")

    # @property
    # def book_name(self):
    #     return self.book.name

    # @property
    # def user_name(self):
    #     return self.user.username

    def book_name(self):
        return self.book.name

    book_name.short_description = u'书籍'

    def user_name(self):
        return self.user.username

    user_name.short_description = u'用户'

    class Meta:
        db_table = 'comment'
        verbose_name = '评论'
        verbose_name_plural = '评论'
