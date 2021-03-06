from django.shortcuts import redirect, reverse
from django.http import HttpResponse
from rest_framework import status


def login_required(view_func):
    '''登录判断装饰器'''

    def wrapper(request, *view_args, **view_kwargs):
        if request.session.has_key('islogin'):
            # 用户已登录
            return view_func(request, *view_args, **view_kwargs)
        else:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

    return wrapper