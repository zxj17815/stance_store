# json库、http请求库、格式转换
import json
import os
# 随机字符串
import random
import string
import sys
import time
from builtins import object

# 本地保存的第三方平台密钥
from . import access_key

import oss2  # 阿里云oss
import requests
from django.conf import settings
from django.contrib.auth.models import Group, Permission, User
# 引入Http库
from django.http import (HttpResponse, HttpResponseRedirect, JsonResponse,
                         request)
# csrf安全防御
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, render
from django_filters.rest_framework import DjangoFilterBackend  # 通用过滤器
from requests.api import request
from rest_framework import permissions  # 权限
from rest_framework import status  # 状态码
from rest_framework import generics, views, viewsets
from rest_framework.parsers import *  # 解析器
from rest_framework.response import Response  # 返回
from rest_framework.versioning import URLPathVersioning  # api版本控制
from rest_framework_simplejwt.tokens import AccessToken  # yoken

# from django_filters.rest_framework import DjangoFilterBackend # 过滤器,setting已经全局设置，这里就不用了
# Models
# from django.core import serializers
# Api
from . import serializers  # 自定义的序列化类
from . import models

from rest_framework import filters  # 视图集; 查找和排序过滤器



# Create your views here.



class UpdateImageView(views.APIView):
    """上传图片测试
    """
    versioning_class = URLPathVersioning
    # queryset = models.Image.objects.all()
    # permission_classes = [permissions.DjangoObjectPermissions]
    def post(self, request, *args, **kwargs):
        """
        上传图片
        """
        try:
            # 阿里云主账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM账号进行API访问或日常运维，请登录 https://ram.console.aliyun.com 创建RAM账号。
            # 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
            bucket = oss2.Bucket(oss2.Auth(access_key.ALIYUN['OSS_ACCESS_KEY_ID'], access_key.ALIYUN['OSS_ACCESS_KEY_SECRET']), access_key.ALIYUN['OSS_ENDPOINT'], access_key.ALIYUN['OSS_BUCKET'])
            # <yourObjectName>上传文件到OSS时需要指定包含文件后缀在内的完整路径，例如abc/efg/123.jpg。
            # <yourLocalFile>由本地文件路径加文件名包括后缀组成，例如/users/local/myfile.txt。
            file_obj = request.data['image']
            # 生成随机字符串作为文件名
            ran_str = ''.join(random.sample(string.ascii_letters + string.digits, 4))
            time_stamp = time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
            postfix = os.path.splitext(file_obj.name)[-1]
            image_name = 'stance_store/'+ran_str+str(time_stamp)+postfix
            result=bucket.put_object(image_name, file_obj)
            image=models.Image(image='https://'+access_key.ALIYUN['OSS_VIEW_URL']+'/'+image_name,file_name=image_name,request_id=result.request_id,etag=result.etag)
            image.save()
            return Response(serializers.ImageSerializer(image).data,status=result.status)
        except oss2.exceptions.OssError as e:
            return Response(data={"AliYunError":e.details},status=e.status)

class ProductImageValViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Images to be viewed or edited.
    """
    permission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    queryset = models.Image.objects.all()
    serializer_class = serializers.ImageSerializer
    # filterset_fields = '__all__'
    def create(self, request, *args, **kwargs):
        # headers=self.get_success_headers(serializer.data)
        # return Response(serializer.data,status=status.HTTP_201_CREATED,headers=headers)
        """
        上传图片
        """
        if 'image' in request.data:
            try:
                # 阿里云主账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM账号进行API访问或日常运维，请登录 https://ram.console.aliyun.com 创建RAM账号。
                # 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
                bucket = oss2.Bucket(oss2.Auth(access_key.ALIYUN['OSS_ACCESS_KEY_ID'], access_key.ALIYUN['OSS_ACCESS_KEY_SECRET']), access_key.ALIYUN['OSS_ENDPOINT'], access_key.ALIYUN['OSS_BUCKET'])
                # <yourObjectName>上传文件到OSS时需要指定包含文件后缀在内的完整路径，例如abc/efg/123.jpg。
                # <yourLocalFile>由本地文件路径加文件名包括后缀组成，例如/users/local/myfile.txt。
                file_obj = request.data['image']
                # 生成随机字符串作为文件名
                ran_str = ''.join(random.sample(string.ascii_letters + string.digits, 4))
                time_stamp = time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
                postfix = os.path.splitext(file_obj.name)[-1]
                image_name = 'stance_store/'+ran_str+str(time_stamp)+postfix
                result=bucket.put_object(image_name, file_obj)
                image=models.Image(image=image_name,request_id=result.request_id,etag=result.etag)
                image.save()
                return Response(serializers.ImageSerializer(image).data,status=result.status)
            except oss2.exceptions.OssError as e:
                return Response(data={"AliYunError":e.details},status=e.status)
        else:
            return Response(data={"image": ["该字段是必填项，请选择文件上传"],},status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        # headers=self.get_success_headers(serializer.data)
        # return Response(serializer.data,status=status.HTTP_201_CREATED,headers=headers)
        """
        更新图片
        """
        if 'image' in request.data:
            try:
                # 阿里云主账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM账号进行API访问或日常运维，请登录 https://ram.console.aliyun.com 创建RAM账号。
                # 创建Bucket对象，所有Object相关的接口都可以通过Bucket对象来进行
                bucket = oss2.Bucket(oss2.Auth(access_key.ALIYUN['OSS_ACCESS_KEY_ID'], access_key.ALIYUN['OSS_ACCESS_KEY_SECRET']), access_key.ALIYUN['OSS_ENDPOINT'], access_key.ALIYUN['OSS_BUCKET'])
                # <yourObjectName>上传文件到OSS时需要指定包含文件后缀在内的完整路径，例如abc/efg/123.jpg。
                # <yourLocalFile>由本地文件路径加文件名包括后缀组成，例如/users/local/myfile.txt。
                file_obj = request.data['image']
                ran_str = ''.join(random.sample(string.ascii_letters + string.digits, 4))
                time_stamp = time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
                postfix = os.path.splitext(file_obj.name)[-1]
                image_name = 'stance_store/'+ran_str+str(time_stamp)+postfix
                result=bucket.put_object(image_name, file_obj)
                image=models.Image(image=image_name,request_id=result.request_id,etag=result.etag)
                image.save()
                # # 获取原文件名
                # image=self.get_object()
                # image_name = image.file_name
                # result=bucket.put_object(image_name, file_obj)
                return Response(serializers.ImageSerializer(image).data,status=result.status)
            except oss2.exceptions.OssError as e:
                return Response(data={"AliYunError":e.details},status=e.status)
        else:
            return Response(data={"image": ["该字段是必填项，请选择文件上传"],},status=status.HTTP_400_BAD_REQUEST)

class ActivePorductViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Product to be viewed or edited.
    """
    permission_classes = [permissions.DjangoModelPermissions]
    queryset = models.ActivePorduct.objects.all()
    serializer_class = serializers.PorductSerializer

class ColorViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Product to be viewed or edited.
    """
    permission_classes = [permissions.DjangoModelPermissions]
    queryset = models.ProductColor.objects.all()
    serializer_class = serializers.ColorSerializer

class SizeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Product to be viewed or edited.
    """
    permission_classes = [permissions.DjangoModelPermissions]
    queryset = models.ProductSize.objects.all()
    serializer_class = serializers.ProductSizeSerializer

class MyView(generics.RetrieveAPIView):
    """
    返回用户信息
    """
    def retrieve(self, request, *args, **kwargs):
        user = request.user
        serializer = serializers.UserSerializer(user)
        instance=1
        return Response(serializer.data)

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    permission_classes = [permissions.DjangoModelPermissions]
    queryset = models.User.objects.filter(user_type=1)
    serializer_class = serializers.UserSerializer

class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    permission_classes = [permissions.DjangoModelPermissions]
    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializer

class PermissionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows permission to be viewed or edited.
    """
    permission_classes = [permissions.IsAdminUser]
    queryset = Permission.objects.all()
    serializer_class = serializers.PermissionSerializer
    filterset_fields = '__all__'
