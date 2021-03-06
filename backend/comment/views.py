from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from comment.models import Comment
from books.models import Books
from users.models import Passport
from django.views.decorators.csrf import csrf_exempt
import json
import redis
from rest_framework import status
from utils.decorators import login_required
from rest_framework.decorators import api_view

from .serializers import CommentSerializers

# Create your views here.
# 设置过期时间
EXPIRE_TIME = 60 * 10
# 连接redis数据库
pool = redis.ConnectionPool(host='localhost', port=6379, db=2)
redis_db = redis.Redis(connection_pool=pool)


@csrf_exempt
@login_required
@api_view(['GET', 'POST'])
def comment(request, book_id):
    book_id = int(book_id)
    try:
        book = Books.objects.get(id=book_id)
    except Exception:
        return JsonResponse(
            data={
                'errmsg': '书籍不存在',
            }, status=status.HTTP_204_NO_CONTENT)

    if request.method == 'GET':
        comments = Comment.objects.filter(book=book)
        # return JsonResponse(
        #     data={'comments': CommentSerializers(comments, many=True).data},
        #     status=status.HTTP_200_OK)
        # # 先在redis里面寻找评论
        c = redis_db.get('comment_%s' % book_id)
        try:
            c = c.decode('utf-8')
        except Exception:
            pass

        if c:
            return JsonResponse(
                CommentSerializers(c).data, status=status.HTTP_200_OK)
        else:
            # 找不到，就从数据库里面取
            try:
                book = Books.objects.get(id=book_id)
            except Exception:
                return JsonResponse({'errmsg': '书籍不存在'},
                                    status=status.HTTP_204_NO_CONTENT)

            comments = Comment.objects.filter(book=book)
            data = []
            for c in comments:
                # data.append({
                #     'user_id': c.user_id,
                #     'content': c.content,
                # })
                data.append(c)

            try:
                redis_db.setex('comment_%s' % book_id, json.dumps(data),
                               EXPIRE_TIME)
            except Exception as e:
                print('e: ', e)
            # return JsonResponse({'data': data}, status=status.HTTP_200_OK)
            return JsonResponse(
                CommentSerializers(data, many=True).data,
                status=status.HTTP_200_OK)

    elif request.method == 'POST':
        user_id = request.session.get('passport_id')
        content = request.data['content']

        user = Passport.objects.get(id=user_id)

        comment = Comment(book=book, user=user, content=content)
        comment.save()

        return JsonResponse(
            CommentSerializers(comment).data, status=status.HTTP_200_OK)
