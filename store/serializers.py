import json
import this

from django.conf import settings
# 引入密码加密
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group, Permission
from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from . import models

# 本地保存的第三方平台密钥
from . import access_key

class UserSerializer(serializers.ModelSerializer):
    """原生 用户user 序列化类
    """
    last_login = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",required=False)
    date_joined = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",required=False)
    groups=serializers.PrimaryKeyRelatedField(many=True,read_only=False,queryset=Group.objects.all(),help_text='数组，用户组（角色）id')
    # password = make_password(password)
    class Meta:
        model = models.User
        # fields = '__all__'
        exclude = ['user_type',]
        depth = 1
        extra_kwargs = {
            'username': {'help_text': '用户名'},
            'password':{'help_text': '密码'},
        }
    # 修改创建用户方法，设定加密密码
    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super(UserSerializer, self).create(validated_data)

class GroupSerializer(serializers.ModelSerializer):
    """原生 组 序列化类
    """
    permissions=serializers.PrimaryKeyRelatedField(many=True,read_only=False,queryset=Permission.objects.all(),help_text='数组，权限id')
    class Meta:
        model = Group
        fields = '__all__'
        depth = 1
        extra_kwargs = {
            'name': {'help_text': '组名'},
        }

class PermissionSerializer(serializers.ModelSerializer):
    """原生 权限 序列化类
    """
    class Meta:
        model = Permission
        fields = '__all__'
        depth = 3   





class ProductSizeSerializer(serializers.ModelSerializer):
    """Size类 序列化类
    """    
    color=serializers.PrimaryKeyRelatedField(read_only=True,help_text='int，外键，Color.id')
    class Meta:
        model = models.ProductSize
        fields = '__all__'
        # exclude = ['color',]
        depth = 1

class ImageSerializer(serializers.ModelSerializer):
    """图片类 序列化类
    """    
    class Meta:
        model = models.Image
        # fields='__all__'
        exclude = ['request_id','etag']
        depth = 1
    def to_representation(self, instance):
        """Convert `username` to lowercase."""
        ret = super().to_representation(instance)
        ret['image'] = 'https://'+access_key.ALIYUN['OSS_VIEW_URL']+'/'+ret['image']
        return ret
    def to_internal_value(self, data):
        data['image']=data['image'].replace('https://'+access_key.ALIYUN['OSS_VIEW_URL']+'/','')
        return data

class ColorSerializer(WritableNestedModelSerializer):
    """Color类 序列化查看类
    """    
    # images=serializers.PrimaryKeyRelatedField(many=True,read_only=False,queryset=models.Image.objects.all(),help_text='数组，外键，图片id')
    images=ImageSerializer(many=True)
    active_porduct=serializers.PrimaryKeyRelatedField(read_only=True,help_text='int，外键，产品id')
    sizes=ProductSizeSerializer(many=True)
    class Meta:
        model = models.ProductColor
        fields = '__all__'
        # exclude = ['id']
        depth = 1
    # def to_representation(self, instance):
    #     """Convert `username` to lowercase."""
    #     ret = super().to_representation(instance)
    #     # ret['images'] = 'https://'+access_key.ALIYUN['OSS_VIEW_URL']+'/'+str(ret['images'])
    #     for index,item in enumerate(ret['images']):
    #         file_name=models.Image.objects.get(id=item).image
    #         ret['images'][index]='https://'+access_key.ALIYUN['OSS_VIEW_URL']+'/'+file_name
    #     return ret

class ActivePorductSerializer(serializers.ModelSerializer):
    """活动产品 序列化查看类
    """
    colors=ColorSerializer(many=True,read_only=True)
    start_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    end_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",required=False)
    edit_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",required=False)
    feature = serializers.ListField(
        source='feature_as_list',
        child=serializers.CharField(allow_blank=True)
    )
    care = serializers.ListField(
        source='care_as_list',
        child=serializers.CharField(allow_blank=True)
    )
    class Meta:
        model = models.ActivePorduct
        fields = '__all__'
        depth = 1

class PorductSerializer(WritableNestedModelSerializer):
    """活动产品 序列化查看类
    """
    colors=ColorSerializer(many=True,help_text='int，外键，Color.id')
    start_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",help_text="datetime，活动开始时间")
    end_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",help_text="datetime，活动结束时间")
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",required=False,help_text="datetime，创建时间")
    edit_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",required=False,help_text="datetime，更新时间")
    active_images=ImageSerializer(many=True,help_text='[int]，外键-Image，活动图片')
    feature = serializers.ListField(
        source='feature_as_list',
        child=serializers.CharField(allow_blank=True),
        help_text='text，特征'
    )
    care = serializers.ListField(
        source='care_as_list',
        child=serializers.CharField(allow_blank=True),
        help_text='text，养护'
    )
    class Meta:
        model = models.ActivePorduct
        fields = '__all__'
        depth = 1



