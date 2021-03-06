from django.db import models
from db.base_model import BaseModel
from django.utils.html import format_html


class OrderInfo(BaseModel):
    PAY_METHOD_CHOICES = ((1, "货到付款"), (2, "微信支付"), (3, "支付宝"), (4, "银联支付"))

    PAY_METHODS_ENUM = {
        "CASH": 1,
        "WEIXIN": 2,
        "ALIPAY": 3,
        "UNIONPAY": 4,
    }

    ORDER_STATUS_ENUM = {
        "待支付": 1,
        "待发货": 2,
        "已发货": 3,
        "已完成": 4,
    }
    ORDER_STATUS_CHOICES = (
        (1, "待支付"),
        (2, "待发货"),
        (3, "已发货"),
        (4, "已完成"),
    )
    '''订单信息模型类'''
    order_id = models.CharField(
        max_length=64, primary_key=True, verbose_name='订单编号')
    passport = models.ForeignKey(
        'users.Passport', verbose_name='下单账户', on_delete=models.CASCADE)
    addr = models.ForeignKey(
        'users.Address', verbose_name='收货地址', on_delete=models.CASCADE)
    total_count = models.IntegerField(default=1, verbose_name='商品总数')
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name='商品总价')
    transit_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name='订单运费')
    pay_method = models.SmallIntegerField(
        choices=PAY_METHOD_CHOICES, default=1, verbose_name='支付方式')
    status = models.SmallIntegerField(
        choices=ORDER_STATUS_CHOICES, default=1, verbose_name='订单状态')
    trade_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        verbose_name='支付编号')

    def status_color(self):

        if self.status == 1:
            '''待支付'''
            color_code = 'red'
            status = '待支付'
        elif self.status == 2:
            '''待发货'''
            color_code = 'yellow'
            status = '待发货'
        elif self.status == 3:
            '''已发货'''
            color_code = 'blue'
            status = '已发货'
        elif self.status == 4:
            '''已完成'''
            color_code = 'green'
            status = '已完成'

        return format_html(
            '<span style="color:{};">{}</span>',
            color_code,
            status,
        )

    status_color.short_description = u'订单状态'

    def user_name(self):
        return self.passport.username

    user_name.short_description = u'下单账户'

    def address(self):
        return self.addr.recipient_addr

    address.short_description = u'收货地址'

    class Meta:
        db_table = 's_order_info'
        verbose_name = '订单详情'
        verbose_name_plural = '订单详情'


class OrderBooks(BaseModel):
    '''订单商品模型类'''
    order = models.ForeignKey(
        'OrderInfo', verbose_name='所属订单', on_delete=models.CASCADE)
    books = models.ForeignKey(
        'books.Books',
        related_name="books",
        verbose_name='订单商品',
        on_delete=models.CASCADE)
    count = models.IntegerField(default=1, verbose_name='商品数量')
    price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name='商品价格')

    class Meta:
        db_table = 's_order_books'
        verbose_name = '订单书籍'
        verbose_name_plural = '订单书籍'
