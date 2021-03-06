from django.db import models
from django.utils.html import format_html

# Create your models here.
from books.enums import CODING, ENOUGH, BOOKS_TYPE, STATUS_CHOICE
from db.base_model import BaseModel
from tinymce.models import HTMLField


class BooksManager(models.Manager):
    """商品管理器"""

    # sort='new' 按照创建时间进行排序
    # sort='hot' 按照商品销量进行排序
    # sort='price' 按照商品的价格进行排序
    # sort= 按照默认顺序排序,primary key降序排列
    # limit为查询数据的数量限制
    def get_books_by_type(self, type_id, limit=None, sort='default'):
        """根据商品类型的id进行商品信息查询"""
        if sort == 'new':
            order_by = ('-create_time', )
        elif sort == 'hot':
            order_by = ('sales', )
        elif sort == 'price':
            order_by = ('price', )
        else:
            order_by = ('-pk', )

        # 查询数据
        books_li = self.filter(type_id=type_id).order_by(*order_by)

        if limit:
            books_li = books_li[:limit]
        return books_li

    def get_books_by_id(self, books_id):
        try:
            books = self.get(id=books_id)
        except self.model.DoesNotExist:
            books = None
        return books


class Books(BaseModel):
    """商品类"""
    book_type_choices = ((k, v) for k, v in BOOKS_TYPE.items())
    status_choices = ((k, v) for k, v in STATUS_CHOICE.items())
    type_id = models.SmallIntegerField(
        default=CODING,
        choices=book_type_choices,
        verbose_name='类别',
        db_column='type')
    name = models.CharField(max_length=80, verbose_name='书名', db_column='name')
    desc = models.CharField(
        max_length=140, verbose_name='简介', db_column='description')
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name='价格', db_column='price')
    stock = models.IntegerField(
        default=500, verbose_name='库存', db_column='stock')
    sales = models.IntegerField(
        default=0, verbose_name='销量', db_column='sales')
    # detail = HTMLField(verbose_name='detail')
    detail = models.CharField(
        max_length=400, verbose_name='详情', db_column='detail')
    # image = models.ImageField(upload_to='books/images', verbose_name='image')
    image = models.CharField(
        max_length=140, verbose_name='图片地址', db_column='image')
    status = models.SmallIntegerField(
        default=ENOUGH,
        choices=status_choices,
        verbose_name='状态',
        db_column='status')
    discount = models.DecimalField(
        default=1.0,
        verbose_name='折扣',
        db_column='discount',
        max_digits=3,
        decimal_places=2)
    # arr_time = models.DateTimeField(verbose_name='arr_time')

    objects = BooksManager()

    def img(self):
        return format_html('<img src="{}" />',
                           'https://images.weserv.nl/?url=' + self.image[8:-1])

    img.short_description = u'图片'

    # 展示书籍的名字
    def __str__(self):
        return self.name

    class Meta:
        db_table = 'books'
        verbose_name_plural = '书籍'
        verbose_name = '书籍'
