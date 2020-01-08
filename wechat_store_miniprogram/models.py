from django.db import models
# from store import models as store_models
from django.conf import settings
import datetime

class AppToken(models.Model):
    """微信access_token
    """
    appid = models.CharField(max_length=128, blank=True, null=True, verbose_name='APPID')  #appid 
    expires_in = models.DateTimeField(verbose_name='expires_in',default=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), auto_now=False, auto_now_add=False)  #过期时间
    token = models.CharField(max_length=255,  unique=True, blank=True, null=True, verbose_name='token', db_index=True) #access_token 这里要注意长度，太短存储会失败 token官方给出的长度是512个字符空间
 
    class Meta:
        verbose_name = '小程序access_token信息'
        verbose_name_plural = verbose_name
    def __str__(self):
        return self.appid

# Create your models here.
class WeUser(models.Model):
    """微信用户 model

    Attributes:
        user: 默认用户

        open_id: 对应微信用户的独立OpenId

        session_key: 会话密码，用于解密用户敏感信息

        union_id: 微信开放平台下统一id

        user_info: 微信用户的信息

        user_address: 微信用户收货地址信息
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # id=models.AutoField(primary_key=True)
    open_id = models.CharField("OpenId", max_length=250)
    union_id = models.CharField("UnionID", max_length=250, null=True, blank=True)
    nickName=models.CharField("NickName", max_length=50)
    avatar_url=models.URLField("AvatarUrl", max_length=300)
    city=models.CharField("City", max_length=50)
    province=models.CharField("Province", max_length=50)
    country=models.CharField("Country", max_length=50)
    gender=models.IntegerField("Gender",choices=((1,'man'),(2,'woman')))
    language=models.CharField("Language", max_length=50)
    user_address=models.TextField("UserAddress", null=True, blank=True)

class WeChatOreder(models.Model):
    """订单
    """
    id = models.AutoField(primary_key=True,help_text='id')
    out_trade_no=models.CharField("OutTradeNo", max_length=50,help_text='string，商户订单号')
    we_user=models.ForeignKey("WeUser", verbose_name="WeUser", on_delete=models.PROTECT,help_text='int，外键-WeUser')
    # product_packge=models.ManyToManyField("OrderPackge", verbose_name="Product",help_text='[int]，外键-models.Model')
    # count=models.IntegerField("Count",default=1,help_text='购买数量')
    address=models.TextField("Address",help_text='收货信息')
    total_price=models.FloatField("TotalPrice",help_text='总价')
    extra=models.TextField("Extra",help_text='备注', null=True, blank=True)
    state=models.IntegerField("State",choices=((0,'待付款'),(1, '待发货'),(2, '待确认'),(3, '退货中'),(4,'退款中'),(5,'已完成'),(6,'确认收货')),default=0,help_text='int，订单状态')
    create_time = models.DateTimeField( "CreateTime", auto_now=False, auto_now_add=True,null=True, blank=True,)
    edit_time = models.DateTimeField("EditTime", auto_now=True, auto_now_add=False, null=True, blank=True,)
    receive_time = models.DateTimeField("ReceiveTime", auto_now=False, auto_now_add=False, null=True, blank=True,)

class OrderPackge(models.Model):
    """订单商品详细
    """
    id = models.AutoField(primary_key=True,help_text='id')
    order=models.ForeignKey("WeChatOreder", verbose_name="WeChatOreder",related_name="order_package", on_delete=models.CASCADE,help_text='int，外键-WeChatOreder')
    product=models.ForeignKey("store.ProductSize", verbose_name="Product", on_delete=models.CASCADE,help_text='int，外键-ProductSize')
    count=models.IntegerField("Count",help_text='int，数量')

class OrderExpress(models.Model):
    """订单快递信息
    """
    id = models.AutoField(primary_key=True,help_text='id')
    order=models.ForeignKey("WeChatOreder", verbose_name="WeChatOreder",related_name="order_express",null=True, blank=True, on_delete=models.CASCADE,help_text='int，外键-WeChatOreder')
    code=models.TextField("ExpressCode",help_text='text，快递单号')
    type=models.IntegerField("type",choices=((0,'手工下单'),(1, '物流助手下单')),default=0,help_text='int，下单类型')

class Refund(models.Model):
    """退货单
    """
    id = models.AutoField(primary_key=True,help_text='id')
    order=models.OneToOneField("WeChatOreder", verbose_name="WeChatOreder", related_name="refund",on_delete=models.PROTECT)
    # refund_package=models.ManyToManyField("RefundPackge", verbose_name="RefundPackge",help_text='[int]，外键-RefundPackge')
    out_refund_no=models.CharField("OutRefundNo", max_length=50,help_text='string，退款单号',null=True, blank=True)
    extra=models.TextField("Extra",help_text='退货理由')
    # images=models.TextField("Images",help_text='退货附图')
    price=models.FloatField("Price",help_text='待退款金额')
    state=models.IntegerField("State",choices=((0,'待通过'),(1, '待退货'),(2, '待确认'),(3, '已完成'),(4, '未通过'),(5, '未发货退款待通过'),(6, '未发货退款已完成')),default=0,help_text='int，状态')
    re_extra=models.TextField("ReExtra",help_text='答复信息',null=True, blank=True)
    express_code=models.TextField("ExpressCode",null=True, blank=True,help_text='text，快递单号')
    create_time = models.DateTimeField( "CreateTime", auto_now=False, auto_now_add=True,null=True, blank=True,)
    edit_time = models.DateTimeField("EditTime", auto_now=True, auto_now_add=False, null=True, blank=True,)

class RefundPackge(models.Model):
    """退货商品详情
    """
    id = models.AutoField(primary_key=True,help_text='id')
    refund=models.ForeignKey("Refund", verbose_name="Refund",related_name="refund_package", on_delete=models.CASCADE,help_text='int，外键-Refund')
    order_package=models.OneToOneField("OrderPackge", verbose_name="OrderPackge", on_delete=models.CASCADE,help_text='int，外键-OrderPackge')
    refund_count=models.IntegerField("RefundCount",default=0,help_text='int，退货数量')

class UserOrder(models.Model):
    """用户订单
    """
    id = models.AutoField(primary_key=True,help_text='id')
    is_hide=models.BooleanField("Destroy",default=False)
    order=models.OneToOneField("WeChatOreder", verbose_name="Order", on_delete=models.CASCADE)