from django.http import JsonResponse, HttpResponse
from books.models import Books
from books.serializers import BooksSerializer
from .serializers import AddressSerializer
from rest_framework import status
from django_redis import get_redis_connection
import redis, random
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.backends import ModelBackend
from users.models import Passport, Address
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings
from order.models import OrderInfo, OrderBooks
from utils.decorators import login_required
from order.serializers import OrderInfoSerializer
import os
from django.core.paginator import Paginator
from django.core.mail import send_mail


# 通过用户名和密码验证用户是否登录
class CustomBackend(ModelBackend):
    def authenticate(self, username=None, password=None, **kwargs):
        try:
            user = Passport.objects.get_one_passport(username, password)
            return user
        except Exception:
            return None


@csrf_exempt
@api_view(['post'])
def register(request):
    username = request.data['username']
    password = request.data['password']
    email = request.data['email']

    # 注册，向账户系统添加账户
    try:
        passport = Passport.objects.add_one_passport(username, password, email)
        serializer = Serializer(settings.SECRET_KEY, 3600)
        token = serializer.dumps({'confirm': passport.id})  # 返回bytes
        token = token.decode()
        return HttpResponse(token, status=status.HTTP_201_CREATED)
    except Exception:
        return HttpResponse("注册失败", status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['post'])
def login(request):
    """用户登录"""
    if request.COOKIES.get('username'):
        # 用户已登录
        username = request.COOKIES.get("username")
    else:
        username = request.data['username']
        password = request.data['password']
        remember = request.data['remember']
        verifycode = request.data['verifycode']
        if username is None or password is None or remember is None or verifycode is None:
            # 有数据为空
            return JsonResponse({'res': 3, 'errmsg': 'data cannot be null'})

        # 验证码错误
        if verifycode.upper() != request.session['verifycode']:
            return JsonResponse({'res': 2, 'errmsg': 'verify code is wrong'})

        # 根据用户名和密码查找账户信息
        passport = Passport.objects.get_one_passport(username, password)
        # 登录成功
        if passport:
            jres = JsonResponse({'res': 1})
            if remember == 'true':
                # 记住用户名
                jres.set_cookie('username', username, max_age=7 * 24 * 3600)
            else:
                # 不要记住用户名
                jres.delete_cookie('username')

            # 记住用户的登录状态
            request.session['islogin'] = True
            request.session['username'] = username
            request.session['passport_id'] = passport.id
            print(request.session['islogin'])
            print(request.session['username'])
            print(request.session['passport_id'])
            print(request.session.get('vertifycode'))
            cache_clean()
            return jres
        else:
            # 用户名或者密码错误
            return JsonResponse({
                'res':
                0,
                'errmsg':
                'username or password cannot be wrong'
            })


@csrf_exempt
@api_view(['post'])
def change_password(request):
    '''用户通过邮箱验证码修改密码'''
    email = request.data['email']
    title = '猫的天空书城——用户密码修改验证码'

    emali_from = settings.EMAIL_FROM
    reciever = []
    reciever.append(email)

    # 生成验证码
    verifycode = random.randint(100000, 999999)

    msg = '您正在修改猫的天空书城的账户密码！您的验证码是：' + str(verifycode)

    try:
        send_mail(title, msg, emali_from, reciever)
        # 存下验证码
        conn = get_redis_connection('default')
        verifycode_key = 'verifycode_%s' % email
        conn.set(verifycode_key, verifycode)

        return HttpResponse(status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return HttpResponse(status=status.HTTP_503_SERVICE_UNAVAILABLE)


@csrf_exempt
@api_view(['post'])
def verify(request):
    """验证码验证"""
    verifycode = int(request.data['code'])
    email = request.data['email']
    verifycode_key = 'verifycode_%s' % email

    conn = get_redis_connection('default')
    if verifycode == int(conn.get(verifycode_key)):
        conn.delete(verifycode_key)
        return HttpResponse(status=status.HTTP_200_OK)
    else:
        return JsonResponse({'errmsg': '验证码错误'},
                            status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['post'])
def set_password(request):
    email = request.data['email']
    password = request.data['password']

    user = Passport.objects.get(email=email)
    user.password = password
    user.save()

    return HttpResponse(status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['post'])
def logout(request):
    '''用户退出登录'''
    # 清空用户的session信息
    request.session.flush()
    cache_clean()
    return HttpResponse('成功退出', status=status.HTTP_200_OK)


# 清空高速缓冲中的内容
def cache_clean():
    r = redis.StrictRedis(host='localhost', port=6379, db=2)
    for key in r.keys():
        if 'bookstore-index' in key.decode('utf8'):
            print('key: ', key)
            r.delete(key)


@csrf_exempt
# @login_required
@api_view(['get'])
def info(request):
    '''用户中心-信息页'''
    passport_id = request.session.get('passport_id')
    # 获取用户的基本信息
    addr = Address.objects.get_default_address(passport_id=passport_id)

    conn = get_redis_connection('default')
    key = 'history_%d' % passport_id
    # 取出用户最近浏览的5个商品的id
    history_li = conn.lrange(key, 0, 4)
    books_li = []
    for id in history_li:
        books = Books.objects.get_books_by_id(books_id=id)
        books_li.append(books)

    context = {
        'addr': AddressSerializer(addr).data,
        # 'page': 'user',
        'books_li': BooksSerializer(books_li, many=True).data,
    }

    return JsonResponse(data=context, status=status.HTTP_200_OK)


@csrf_exempt
@login_required
@api_view(['GET', 'POST'])
def address(request):
    '''用户中心-地址页'''
    # 获取登录用户的id
    passport_id = request.session.get('passport_id')
    if request.method == 'GET':
        # 显示地址页面
        # 查询用户的默认地址
        addr = Address.objects.get_default_address(passport_id=passport_id)
        # 查询用户的全部地址
        addrs = Address.objects.get_all_addresses(passport_id=passport_id)
        return JsonResponse(data={
            'addrs': AddressSerializer(addrs, many=True).data,
        })
    elif request.method == 'POST':
        # 添加收货地址
        # 1.接收数据

        recipient_name = request.data['username']
        recipient_addr = request.data['addr']
        zip_code = request.data['zip_code']
        recipient_phone = request.data['phone']

        # 2.进行校验
        if not all([recipient_name, recipient_addr, zip_code, recipient_phone
                    ]):

            return JsonResponse({
                'errmsg': '参数不能为空',
            })
        # 3.添加收货地址
        Address.objects.add_one_address(
            passport_id=passport_id,
            recipient_name=recipient_name,
            recipient_addr=recipient_addr,
            zip_code=zip_code,
            recipient_phone=recipient_phone)

        # 4.返回应答
        return HttpResponse('成功添加地址', status=status.HTTP_201_CREATED)


@api_view(['get'])
def verifycode(request):
    # 引入绘图模块
    from PIL import Image, ImageDraw, ImageFont
    # 引入随机函数模块
    import random
    # 定义变量，用于画面的背景色、宽、高
    bgcolor = (random.randrange(20, 100), random.randrange(20, 100), 255)
    width = 100
    height = 25
    # 创建画面对象
    im = Image.new('RGB', (width, height), bgcolor)
    # 创建画笔对象
    draw = ImageDraw.Draw(im)
    # 调用画笔的point()函数绘制噪点
    for i in range(0, 100):
        xy = (random.randrange(0, width), random.randrange(0, height))
        fill = (random.randrange(0, 255), 255, random.randrange(0, 255))
        draw.point(xy, fill=fill)
    # 定义验证码的备选值
    str1 = 'ABCD123EFGHIJK456LMNOPQRS789TUVWXYZ0'
    # 随机选取4个值作为验证码
    rand_str = ''
    for i in range(0, 4):
        rand_str += str1[random.randrange(0, len(str1))]
    # 构造字体对象
    font = ImageFont.truetype(
        os.path.join(settings.BASE_DIR, "Ubuntu-RI.ttf"), 15)
    # 构造字体颜色
    fontcolor = (255, random.randrange(0, 255), random.randrange(0, 255))
    # 绘制4个字
    draw.text((5, 2), rand_str[0], font=font, fill=fontcolor)
    draw.text((25, 2), rand_str[1], font=font, fill=fontcolor)
    draw.text((50, 2), rand_str[2], font=font, fill=fontcolor)
    draw.text((75, 2), rand_str[3], font=font, fill=fontcolor)
    # 释放画笔
    del draw
    # 存入session，用于做进一步验证
    request.session['verifycode'] = rand_str

    # 内存文件操作
    import io
    buf = io.BytesIO()
    # 将图片保存在内存中，文件类型为png
    im.save(buf, 'png')
    # 将内存中的图片数据返回给客户端，MIME类型为图片png
    return HttpResponse(buf.getvalue(), 'image/png')
