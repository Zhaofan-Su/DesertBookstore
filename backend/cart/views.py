from django.http import JsonResponse, HttpResponse
from books.models import Books
from rest_framework import status
from django_redis import get_redis_connection
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from utils.decorators import login_required
from books.serializers import BooksSerializer


@csrf_exempt
@api_view(['POST'])
@login_required
def cart_add(request):
    """向购物车中添加数据"""

    # 接收数据
    books_id = request.data['books_id']
    books_count = request.data['books_count']

    books = Books.objects.get_books_by_id(int(books_id))
    if books is None:
        return JsonResponse({'res': 1, 'errmsg': '商品不存在'})
    count = int(books_count)

    # 添加商品到购物车
    # 每个用户的购物车记录用一条hash数据保存，格式:cart_用户id: 商品id 商品数量
    conn = get_redis_connection('default')
    cart_key = 'cart_%d' % request.session.get('passport_id')

    res = conn.hget(cart_key, books_id)
    if res is None:
        # 购物车中没有加入过该商品，加入商品
        res = count
    else:
        # 用户的购物车已经添加过该商品，则累计商品数目
        res = int(res) + count

    # 判断商品的库存
    if res > books.stock:
        return JsonResponse({'res': 2, 'errmsg': '商品库存不足'})
    else:
        conn.hset(cart_key, books_id, res)

    # 返回结果
    return JsonResponse({'res': 3})


@csrf_exempt
@api_view(['get'])
# @login_required
def cart_count(request):
    """获取用户购物车中商品的数目"""
    # 计算用户购物车商品的数量
    conn = get_redis_connection('default')
    cart_key = 'cart_%d' % request.session.get('passort_id')
    res = 0
    res_list = conn.hvals(cart_key)

    for i in res_list:
        res += int(i)

    # 返回结果
    return JsonResponse({'res': res})


@csrf_exempt
@api_view(['get'])
@login_required
def cart_show(request):
    """显示用户购物车"""
    passport_id = request.session.get('passport_id')
    # 获取用户购物车记录
    conn = get_redis_connection('default')
    cart_key = 'cart_%d' % passport_id
    res_dict = conn.hgetall(cart_key)

    books_li = []
    # 商品数目
    counts = []

    # 遍历res_dict获取商品的数据
    for books_id, count in res_dict.items():
        # 获取商品信息
        books = Books.objects.get_books_by_id(books_id=books_id)
        counts.append(int(count))

        books_li.append(books)

    context = {
        'books_li': BooksSerializer(books_li, many=True).data,
        'counts': counts,
    }

    return JsonResponse(data=context, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['delete'])
@login_required
def cart_del(request):
    """删除用户购物车中商品的信息"""

    # 接收数据
    books_id = request.data['books_id']

    # 检验商品是否存放
    if not all([books_id]):
        return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

    books = Books.objects.get_books_by_id(books_id=books_id)
    if books is None:
        return JsonResponse({'res': 2, 'errmsg': '商品不存在'})

    # 删除购物车中商品的信息
    conn = get_redis_connection('default')
    cart_key = 'cart_%d' % request.session.get('passport_id')
    conn.hdel(cart_key, books_id)

    # 返回信息
    return JsonResponse({'res': 3})


@csrf_exempt
@api_view(['PUT'])
@login_required
def cart_update(request):
    '''更新购物车商品数目'''

    # 接收数据
    books_id = request.data['books_id']
    books_count = request.data['books_count']

    # 数据的校验
    if not all([books_id, books_count]):
        return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

    books = Books.objects.get_books_by_id(books_id=books_id)
    if books is None:
        return JsonResponse({'res': 2, 'errmsg': '商品不存在'})

    try:
        books_count = int(books_count)
    except Exception as e:
        print("e: ", e)
        return JsonResponse({'res': 3, 'errmsg': '商品数目必须为数字'})

    # 更新操作
    conn = get_redis_connection('default')
    cart_key = 'cart_%d' % request.session.get('passport_id')

    # 判断商品库存
    if books_count > books.stock:
        return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})

    conn.hset(cart_key, books_id, books_count)

    return JsonResponse({'res': 5})