from django.conf import settings
from django.contrib.admin.utils import help_text_for_field
from django.contrib.auth.models import AbstractUser
from django.db import models
import json
# Create your models here.

class User(AbstractUser):
    """扩展用户表

    增加用户类型 user_type:

        1：admin 管理员
        2：weuser 微信用户
        3：other 其他类型用户
    """
    user_type=models.IntegerField("UserType",choices=((0,'unknown'),(1, 'admin'),(2, 'weuser'),(3, 'other')), default=1,help_text='用户类型')


class ActivePorduct(models.Model):
    """活动商品
    """
    id = models.AutoField(primary_key=True,help_text='id')
    active_name=models.CharField("ActiveName", max_length=128,help_text='string，活动名称')
    active_describe=models.TextField("ActiveDescribe",help_text='string，活动简介')
    active_images=models.ManyToManyField("Image", verbose_name="Active_Image",help_text='[int]，外键-Image，活动图片')
    name=models.CharField("Name", max_length=128,help_text='string，产品名称')
    series=models.TextField("Series",help_text='text，系列')
    height=models.IntegerField("Height",choices=((0,'NO-SHOW'),(1, 'TAB'),(2, 'ANKLE'),(3, 'CREW'),(4,'OVER THE CALF')),help_text='int，高度')
    height_des=models.TextField("HeightDes", null=True, blank=True,help_text='高度描述')
    thickness=models.IntegerField("Thickness",choices=((0,'THIN'),(1, 'MEDIUM'),(2, 'THICK')),help_text='int，厚度')
    thickness_des=models.TextField("ThicknessDes", null=True, blank=True,help_text='厚度描述')
    material=models.TextField("Material",help_text='text，材质')
    material_des=models.TextField("MaterialDes", null=True, blank=True,help_text='材质描述')
    price=models.FloatField("Price",help_text='float，商品价格')
    describe=models.TextField("Describe",help_text='text，详情描述')
    # feature=models.CharField("Features", max_length=500,help_text='text，特征')
    feature=models.TextField("Features",help_text='text，特征')
    care=models.TextField("Care",help_text='text，养护')
    start_time=models.DateTimeField("StartTime", auto_now=False, auto_now_add=False,help_text="datetime，活动开始时间")
    end_time=models.DateTimeField("EndTime", auto_now=False, auto_now_add=False,help_text="datetime，活动结束时间")
    state=models.IntegerField("State",choices=((0,'close'),(1, 'open')), default=0,help_text="int，状态（0：关闭；1：启用）")
    create_time = models.DateTimeField( "CreateTime", auto_now=False, auto_now_add=True,null=True, blank=True,)
    edit_time = models.DateTimeField("EditTime", auto_now=True, auto_now_add=False, null=True, blank=True,)

    @property
    def feature_as_list(self):
        """ Feature are stored on DB as a text json convert to object again
        """
        return json.loads(self.feature) if self.feature else None

    @feature_as_list.setter
    def feature_as_list(self, value):
        """ Feature are stored on DB as a text json of the list object
        """
        self.feature = json.dumps(value)

    @property
    def care_as_list(self):
        """ Care are stored on DB as a text json convert to object again
        """
        return json.loads(self.care) if self.care else None

    @care_as_list.setter
    def care_as_list(self, value):
        """ Care are stored on DB as a text json of the list object
        """
        self.care = json.dumps(value)

class ProductColor(models.Model):
    id = models.AutoField(primary_key=True,help_text='id')
    active_porduct=models.ForeignKey("ActivePorduct", verbose_name="ActivePorduct",related_name="colors",on_delete=models.CASCADE)
    name=models.CharField("Name", max_length=100,help_text='string，Color名称')
    images=models.ManyToManyField("Image", verbose_name="Image",help_text='[int]，外键-Image，商品图片')

class ProductSize(models.Model):
    id = models.AutoField(primary_key=True,help_text='id')
    color=models.ForeignKey("ProductColor", verbose_name="ProductColor",related_name="sizes",on_delete=models.CASCADE)
    size=models.IntegerField("Sizes",choices=((0,'XS'),(1, 'S'),(2, 'M'),(3, 'L'),(4,'XL'),(5,'XXXL')),default=0,help_text='int，Size大小')
    quantity=models.IntegerField("Quantity",default=0,help_text='int，库存量')

class Image(models.Model):
    id = models.AutoField(primary_key=True,help_text='id')
    image=models.CharField("Image", max_length=250,help_text='上传图片路径及文件名')
    # image = models.URLField("Image",help_text='上传图片')
    request_id=models.CharField("RequestId", max_length=250)
    etag=models.CharField("Etag", max_length=250)