from rest_framework import status, mixins, viewsets
from django.http import JsonResponse, HttpResponse
from books.serializers import BooksSerializer
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
# from django.core.paginator import Paginator
from . import enums
from books.models import Books
from django_redis import get_redis_connection
from bs4 import BeautifulSoup
import requests

# Create your views here.


class BooksListViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin,
                       viewsets.GenericViewSet):
    serializer_class = BooksSerializer
    queryset = Books.objects.all()


@csrf_exempt
@api_view(['get'])
def get_index_info(request):
    """得到每种书籍的3个最新，4个销量最高"""
    coding_new = Books.objects.get_books_by_type(enums.CODING, 3, 'new')
    coding_hot = Books.objects.get_books_by_type(enums.CODING, 4, 'hot')
    internet_new = Books.objects.get_books_by_type(enums.INTERNET, 3, 'new')
    internet_hot = Books.objects.get_books_by_type(enums.INTERNET, 4, 'hot')
    web_new = Books.objects.get_books_by_type(enums.WEB, 3, 'new')
    web_hot = Books.objects.get_books_by_type(enums.WEB, 4, 'hot')
    hci_new = Books.objects.get_books_by_type(enums.HCI, 3, 'new')
    hci_hot = Books.objects.get_books_by_type(enums.HCI, 4, 'hot')
    economic_new = Books.objects.get_books_by_type(enums.ECONOMIC, 3, 'new')
    economic_hot = Books.objects.get_books_by_type(enums.ECONOMIC, 4, 'hot')
    algorithm_new = Books.objects.get_books_by_type(enums.ALGORITHM, 3, 'new')
    algorithm_hot = Books.objects.get_books_by_type(enums.ALGORITHM, 4, 'hot')

    context = {
        'coding_new': (BooksSerializer(coding_new, many=True)).data,
        'coding_hot': (BooksSerializer(coding_hot, many=True)).data,
        'internet_new': (BooksSerializer(internet_new, many=True)).data,
        'internet_hot': (BooksSerializer(internet_hot, many=True)).data,
        'web_new': (BooksSerializer(web_new, many=True)).data,
        'web_hot': (BooksSerializer(web_hot, many=True)).data,
        'hci_new': (BooksSerializer(hci_new, many=True)).data,
        'hci_hot': (BooksSerializer(hci_hot, many=True)).data,
        'economic_new': (BooksSerializer(economic_new, many=True)).data,
        'economic_hot': (BooksSerializer(economic_hot, many=True)).data,
        'algorithm_new': (BooksSerializer(algorithm_new, many=True)).data,
        'algorithm_hot': (BooksSerializer(algorithm_hot, many=True)).data,
    }

    return JsonResponse(data=context, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['get'])
def detail(request, id):
    """根据书籍id查找书籍，并进行新书推荐"""

    # 获取书籍详细信息
    book = Books.objects.get_books_by_id(books_id=id)
    type_id = book.type_id
    if book is None:
        # 商品不存在
        return HttpResponse(
            "The books not exits", status=status.HTTP_204_NO_CONTENT)

    # 新品推荐
    new_book = BooksSerializer(
        Books.objects.get_books_by_type(type_id=type_id, limit=2, sort='new'),
        many=True).data

    # 当前商品类型
    book_type = enums.BOOKS_TYPE[type_id]

    # 用户登录之后，记录浏览记录
    # 每个用户浏览记录对应redis中的一条信息 格式:'history_用户id':[10,9,2,3,4]
    # [9, 10, 2, 3, 4]
    if request.session.has_key('islogin'):
        # 用户已登录，记录浏览记录
        conn = get_redis_connection('default')
        key = 'history_%d' % request.session.get('passport_id')
        # 先从redis列表中移除book.id
        conn.lrem(key, 0, book.id)
        conn.lpush(key, book.id)
        # 保存用户最近浏览的5个商品
        conn.ltrim(key, 0, 4)

    book = BooksSerializer(book).data
    context = {'book': book, 'new_books': new_book, 'books_type': book_type}
    return JsonResponse(data=context, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['get'])
def list(request, type_id, sort, yorn):
    """根据书籍类型，查找书籍，对结果进行分页"""
    if int(type_id) not in enums.BOOKS_TYPE.keys():
        return HttpResponse(
            'There is no such books', status=status.HTTP_204_NO_CONTENT)

    if yorn == '1':
        books_li = Books.objects.get_books_by_type(
            type_id=type_id, sort=sort, limit=4)
    else:
        books_li = Books.objects.get_books_by_type(type_id=type_id, sort=sort)

    type_title = enums.BOOKS_TYPE[int(type_id)]
    context = {
        'books_li': BooksSerializer(books_li, many=True).data,
        'type_id': type_id,
        'sort': sort,
        'type_title': type_title,
    }

    return JsonResponse(data=context, status=status.HTTP_200_OK)


def dumpData(request):
    """爬数据"""
    # types = ['编程', '互联网', 'web', '交互设计', '经济', '算法']
    types = ['算法']
    num = 5
    for t in types:

        url = "https://book.douban.com/tag" + "/" + t + "?start=20&type=T"
        # url = "https://book.douban.com/tag" + "/" + t
        # 得到网页
        data = requests.get(url)
        # 网页数据转换
        text = BeautifulSoup(data.text, 'lxml')
        # 书籍名称

        names = []
        # 简介
        descs = []
        # 价格
        prices = []
        # 详情
        details = []
        # 图片地址，使用豆瓣公开图库
        images = []

        # 先找存图书图片的img标签
        imgs = text.select("#subject_list > ul > li > div.pic > a > img")
        # 找到标签里的src的值，存起来
        for img in imgs:
            images.append(img.get('src'))

        # 找书名
        titles = text.select("#subject_list > ul > li > div.info > h2 > a")
        for title in titles:
            names.append(title.get_text().strip())

        # 找简介,包含作者，（译者），出版社，出版时间;找价格
        pubs = text.select("#subject_list > ul > li > div.info > div.pub")
        for pub in pubs:
            pub_text = pub.get_text()
            descs.append(pub_text[:pub_text.rindex("/") - 1])
            price = (pub_text[pub_text.rindex("/") + 1:])
            if price.split()[0] == "USD":
                prices.append(float(price.split()[1]) * 6)
            elif price.split()[0] == "CNY":
                prices.append(float(price.split()[1]))
            elif price.split()[0] == "$":
                prices.append(float(price.split()[1]) * 6)
            elif (price.split()[0])[-1] == "元":
                prices.append(float((price.split()[0])[0:-2]))
            elif price.split()[0].isdigit():
                prices.append(float(price.split()[0]))
            else:
                prices.append(45.00)

        # 找详情
        decos = text.select("#subject_list > ul > li > div.info > p")
        for deco in decos:
            if deco == ' ':
                details.append('')
            details.append(deco.get_text())

        if num == 2:
            details.append('这本书没有简介')

        for i in range(0, len(names)):
            # ws.append([names[i], descs[i], prices[i], details[i], images[i]])
            book = Books.objects.create(
                type_id=num,
                name=names[i],
                desc=descs[i].strip(),
                detail=details[i].strip(),
                price=prices[i],
                image=images[i])
            book.save()

        num += 1

    return HttpResponse(status=status.HTTP_200_OK)