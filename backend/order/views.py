from utils.decorators import login_required
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from users.models import Address, Passport
from users.serializers import AddressSerializer
from books.models import Books
from books.serializers import BooksSerializer
from order.models import OrderInfo, OrderBooks
from django_redis import get_redis_connection
from datetime import datetime
from django.conf import settings
import os
from .serializers import OrderBooksSerializer, OrderInfoSerializer
from rest_framework.decorators import api_view
from django.db import transaction
from alipay import AliPay


@login_required
@api_view(['post'])
def order_place(request):
    '''显示提交订单页面'''
    # 接收数据
    books_ids = request.data['books_ids']
    print(books_ids)
    # 校验数据
    if not all(books_ids):
        # 跳转回购物车页面
        return HttpResponse("数据出错", status.HTTP_400_BAD_REQUEST)

    # 用户收货地址
    passport_id = request.session.get('passport_id')
    addr = Address.objects.get_default_address(passport_id=passport_id)

    # 用户要购买商品的信息
    books_li = []
    # 商品的总数目和总金额
    total_count = 0
    total_price = 0
    # 每个书籍对应的数量
    books_count = []

    conn = get_redis_connection('default')
    cart_key = 'cart_%d' % passport_id

    index = 0
    for books_id, index in books_ids:

        # 根据id获取商品的信息
        books = Books.objects.get_books_by_id(books_id=books_id)
        # 从redis中获取用户要购买的商品的数目
        if conn.hget(cart_key, books_id) is None:
            # count = request.data['count']
            count = request.data['books_count'][index]

        else:
            count = int(conn.hget(cart_key, books_id))
            # count = request.data['books_count'][index]
        conn.hset(cart_key, books_id, count)
        books_count.append(count)

        books_li.append(books)
        # 累计计算商品总金额
        total_price += int(count) * books.price
        index += 1

    total_count = len(books_ids)
    # 商品运费和实付款
    transit_price = 10
    total_pay = total_price + transit_price

    context = {
        'addr': AddressSerializer(addr).data,
        'books_li': BooksSerializer(books_li, many=True).data,
        'books_count': books_count,
        'total_count': total_count,
        'total_price': total_price,
        'transit_price': transit_price,
        'total_pay': total_pay,
        'books_ids': books_ids,
    }

    return JsonResponse(data=context, status=status.HTTP_200_OK)


@login_required
@api_view(['get'])
def order_all(request):
    """显示用户所有订单"""
    passport_id = request.session.get('passport_id')
    passport = Passport.objects.get(id=passport_id)

    # 订单信息
    order_infos = OrderInfo.objects.filter(passport=passport)
    context = {
        'order_infos': OrderInfoSerializer(order_infos, many=True).data,
    }

    if order_infos is None:
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)

    return JsonResponse(data=context, status=status.HTTP_200_OK)


@login_required
@api_view(['get'])
def books_in_one_order(request, order_id):
    """查找订单下的所有书籍"""
    order_info = OrderInfo.objects.get(order_id=order_id)
    order_books = OrderBooks.objects.filter(order=order_info)

    if order_books is None:
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)

    context = {
        'order_books': OrderBooksSerializer(order_books, many=True).data,
    }

    return JsonResponse(data=context, status=status.HTTP_200_OK)


@login_required
@api_view(['delete'])
def order_cancel(request, order_id):
    """生成订单"""
    order = OrderInfo.objects.get(order_id=order_id)
    try:
        order.delete()
        return HttpResponse(status=status.HTTP_200_OK)
    except Exception:
        return HttpResponse(status.HTTP_404_NOT_FOUND)


# 添加订单为事务的原子性操作
@login_required
@api_view(['post'])
@transaction.atomic
def order_commit(request):
    """生成订单"""
    if 'islogin' not in (request.session.keys()):
        return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

    addr_id = request.data['addr_id']
    pay_method = request.data['pay_method']
    books_ids = request.data['books_ids']

    if not all([addr_id, pay_method, books_ids]):
        return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

    try:
        Address.objects.get(id=addr_id)
    except Exception:
        return JsonResponse({'res': 2, 'errmsg': '地址信息错误'})

    if int(pay_method) not in OrderInfo.PAY_METHODS_ENUM.values():
        return JsonResponse({'res': 3, 'errmsg': '不支持的支付方式'})

    passport_id = request.session.get('passport_id')
    order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(passport_id)

    transit_price = 10

    total_count = 0
    total_price = 0

    sid = transaction.savepoint()
    try:
        order = OrderInfo.objects.create(
            order_id=order_id,
            passport_id=passport_id,
            addr_id=addr_id,
            total_count=total_count,
            total_price=total_price,
            transit_price=transit_price,
            pay_method=pay_method)
        books_ids = books_ids.split(',')
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % passport_id

        for book_id in books_ids:
            books = Books.objects.get_books_by_id(books_id=book_id)
            if books is None:
                transaction.savepoint_rollback(sid)
                return JsonResponse({'res': 4, 'errmsg': '商品信息错误'})

            count = conn.hget(cart_key, book_id)
            print(count)
            if int(count) > books.stock:
                transaction.savepoint_rollback(sid)
                return JsonResponse({'res': 5, 'errmsg': '商品库存不足'})

            OrderBooks.objects.create(
                order_id=order_id,
                books_id=book_id,
                count=count,
                price=books.price)

            books.sales += int(count)
            books.stock -= int(count)
            books.save()

            total_count += int(count)
            total_price += int(count) * books.price

        order.total_count = total_count
        order.total_price = total_price
        order.save()
    except Exception as e:
        print(e)
        transaction.savepoint_rollback(sid)
        return JsonResponse({'res': 7, 'errmsg': '服务器错误'})

    conn.hdel(cart_key, *books_ids)

    transaction.savepoint_commit(sid)

    return JsonResponse({'res': 6, 'order_id': order_id})


@login_required
@api_view(['post'])
def order_pay(request):
    '''订单支付'''

    # 接收订单id
    order_id = request.data['order_id']

    # 数据校验
    if not order_id:
        return JsonResponse({'res': 1, 'errmsg': '订单不存在'})

    try:
        order = OrderInfo.objects.get(
            order_id=order_id, status=1, pay_method=3)
    except OrderInfo.DoesNotExist:
        return JsonResponse({'res': 2, 'errmsg': '订单信息出错'})

    app_private_key_path = os.path.join(settings.BASE_DIR,
                                        'order/app_private_key.pem')
    alipay_public_key_path = os.path.join(settings.BASE_DIR,
                                          'order/app_public_key.pem')

    app_private_key_string = open(app_private_key_path).read()
    alipay_public_key_string = open(alipay_public_key_path).read()

    # 和支付宝进行交互
    alipay = AliPay(
        appid="2016091500515408",  # 应用id
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key_string,
        alipay_public_key_string=
        alipay_public_key_string,  # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=True,  # 默认False
    )

    # 电脑网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
    total_pay = order.total_price + order.transit_price  # decimal
    order_string = alipay.api_alipay_trade_page_pay(
        out_trade_no=order_id,  # 订单id
        total_amount=str(total_pay),  # Json传递，需要将浮点转换为字符串
        subject='荒岛书店%s' % order_id,
        return_url=None,
        notify_url=None  # 可选, 不填则使用默认notify url
    )
    # 返回应答
    pay_url = settings.ALIPAY_URL + '?' + order_string
    return JsonResponse({'res': 3, 'pay_url': pay_url, 'message': 'OK'})
