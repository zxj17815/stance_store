import json
from builtins import object
from itertools import product

# from alipay.aop.api.domain import Product
# from astroid.protocols import objects
from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from store import models as store_models
from store import serializers as store_serializers

from . import models


class JSONSerializerField(serializers.Field):
    """Serializer for JSONField -- required to make field writable"""
    def to_representation(self, value):
        json_data = {}
        try:
            json_data = json.loads(value)
        except ValueError as e:
            raise e
        finally:
            return json_data

    def to_internal_value(self, data):
        if not data:
            raise serializers.ValidationError("address can not be blank")
        return json.dumps(data)

    

class WeUserSerializer(serializers.ModelSerializer):
    """微信用户类 序列化类
    """
    user_address=JSONSerializerField()
    class Meta:
        model = models.WeUser
        # fields = '__all__'
        exclude = ['user',]
        depth = 1

class RefundPackgeSerializer(serializers.ModelSerializer):
    """退货详情packge类 序列化类
    """
    refund=serializers.PrimaryKeyRelatedField(read_only=False,queryset=models.Refund.objects.all(),help_text='int，外键，Refund')
    order_package=serializers.PrimaryKeyRelatedField(read_only=False,queryset=models.OrderPackge.objects.all(),help_text='int，外键，OrderPackge')
    class Meta:
        model = models.RefundPackge
        fields = '__all__'
        depth = 1

class RefundSerializer(serializers.ModelSerializer):
    """退货单类 序列化List类
    """
    order=serializers.PrimaryKeyRelatedField(read_only=False,queryset=models.WeChatOreder.objects.all(),help_text='int，外键，WeChatOreder')
    refund_package=serializers.PrimaryKeyRelatedField(many=True,read_only=True,help_text='int，外键，RefundPackge')
    # refund_package=RefundPackgeSerializer(many=True,read_only=True)
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",required=False)
    edit_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",required=False)
    class Meta:
        model = models.Refund
        fields = '__all__'
        depth = 1
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        refund_package=[]
        for item in ret['refund_package']:
            model=models.RefundPackge.objects.get(id=item)
            refund_package.append({"product": SnapshotSerializer(model.order_package.product).data,"count":model.refund_count})
        ret['refund_package']=refund_package
        if not ret['state']==3:
            ret.pop('out_refund_no')
        if not ret['state']==4 or ret['state']==5 or ret['state']==6:
            ret.pop('re_extra')
        if not ret['state']>1 or ret['state']==4 or ret['state']==5 or ret['state']==6:
            ret.pop('express_code')    
        return ret 

class RefundDetialSerializer(serializers.ModelSerializer):
    """退货单类 序列化详情类
    """
    order=serializers.PrimaryKeyRelatedField(read_only=False,queryset=models.WeChatOreder.objects.all(),help_text='int，外键，WeChatOreder')
    refund_package=serializers.PrimaryKeyRelatedField(many=True,read_only=True,help_text='int，外键，RefundPackge')
    # refund_package=RefundPackgeSerializer(many=True,read_only=True)
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",required=False)
    edit_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",required=False)
    class Meta:
        model = models.Refund
        fields = '__all__'
        depth = 1
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        refund_package=[]
        for item in ret['refund_package']:
            model=models.RefundPackge.objects.get(id=item)
            refund_package.append({"product": SnapshotSerializer(model.order_package.product).data,"count":model.refund_count})
        ret['refund_package']=refund_package
        ret['order_address']=json.loads(model.refund.order.address)
        if not ret['state']==3:
            ret.pop('out_refund_no')
        if not ret['state']==4 or ret['state']==5 or ret['state']==6:
            ret.pop('re_extra')
        if not ret['state']>1 or ret['state']==4 or ret['state']==5 or ret['state']==6:
            ret.pop('express_code')    
        return ret  

class OrderExpressSerializer(serializers.ModelSerializer):
    """订单快递信息
    """
    order=serializers.PrimaryKeyRelatedField(read_only=False,queryset=models.WeChatOreder.objects.all(),help_text='int，外键，WeChatOreder')
    class Meta:
        model=models.OrderExpress
        fields = '__all__'
        depth = 1
    def validate_order(self, order):
        # 注意参数，self以及字段名
        # 注意函数名写法，validate_ + 字段名字
        if not order.state>=1:
        # 查询order字段对应的state是否为1（已付款）
            raise serializers.ValidationError("The order has not been paid yet.")
        return order
    def create(self, validated_data):
        model=models.OrderExpress.objects.create(**validated_data)
        if model:
            # order=models.WeChatOreder.objects.get(id=validated_data['order'])
            order=validated_data['order']
            order.state=2
            order.save()
        return model

class LogisticsByOrder(serializers.Serializer):
    """后台-物流助手-根据订单号验证序列化器
    """
    order_id=serializers.PrimaryKeyRelatedField(read_only=False,queryset=models.WeChatOreder.objects.all(),required=False,help_text='int，外键，WeChatOrder')
    def validate_order_id(self, order_id):
        """对单一的字段进行检验"""
        # 注意参数，self以及字段名
        # 注意函数名写法，validate_ + 字段名字
        if not order_id.state>=1:
        # 查询order字段对应的state是否为1（已付款）
            raise serializers.ValidationError("The order has not been paid yet.")
        if order_id.state>=2:
        # 查询该订单order是否已发货
            raise serializers.ValidationError("The order already exists for OrderExpress.")
        return order_id

class LocalAddress(serializers.Serializer):
    """后台-默认发货地址（以json文件保存本地）序列化
    """
    company=serializers.CharField(max_length=64)
    city=serializers.CharField(max_length=64)
    mobile=serializers.CharField(max_length=32)
    province=serializers.CharField(max_length=64)
    country=serializers.CharField(max_length=64)
    name=serializers.CharField(max_length=64)
    tel=serializers.CharField(max_length=32)
    area=serializers.CharField(max_length=64)
    post_code=serializers.CharField(max_length=10)
    address=serializers.CharField(max_length=255)

class OrderPackgeSerializer(serializers.ModelSerializer):
    """OrderPackge 序列化
    """    
    order=serializers.PrimaryKeyRelatedField(read_only=False,queryset=models.WeChatOreder.objects.all(),required=False,help_text='int，外键，WeChatOrder')
    product=serializers.PrimaryKeyRelatedField(read_only=False,queryset=store_models.ProductSize.objects.all(),help_text='int，外键，ProductSize')
    class Meta:
        model = models.OrderPackge
        fields = '__all__'
        # exclude = ['id',]
        depth = 1

class WeChatOrderSerializer(serializers.ModelSerializer):
    """订单order序列化
    """    
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",required=False)
    edit_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",required=False)
    order_package=serializers.PrimaryKeyRelatedField(many=True,read_only=True,help_text='int，外键，OrderPackge')
    # order_package=OrderPackgeSerializer(many=True)
    we_user=serializers.PrimaryKeyRelatedField(read_only=False,queryset=models.WeUser.objects.all(),help_text='int，外键，WeUser')
    address=JSONSerializerField()
    order_express=OrderExpressSerializer(many=True,read_only=True)
    refund=serializers.PrimaryKeyRelatedField(many=False,read_only=True,help_text='int，外键，Refund')
    class Meta:
        model = models.WeChatOreder
        fields = '__all__'
        depth = 1
        # read_only_fields = ('is_active', 'is_staff')
        # extra_kwargs = {
        #     'security_question': {'write_only': True},
        #     'security_question_answer': {'write_only': True},
        #     'password': {'write_only': True}
        # }
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        order_package=[]
        for item in ret['order_package']:
            package=models.OrderPackge.objects.get(id=item)
            order_package.append({"product": SnapshotSerializer(package.product).data,"count":package.count})
        ret['order_package']=order_package
        if len(ret['order_express'])>0:
            ret['order_express']=ret['order_express'][-1]
        else:
            ret['order_express']=None
        # ret['address']=json.loads(ret['address'])
        # if ret['state']>1:
            # pass
        # if ret['state']==5:
        #     ret['refund_id']=instance.id
        return ret

class UserOrderSerializer(serializers.ModelSerializer):
    """面向用户订单user_order
    """
    order=serializers.PrimaryKeyRelatedField(read_only=False,queryset=models.WeChatOreder.objects.all(),help_text='int，外键，WeChatOreder')
    # create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",read_only=True)
    class Meta:
        model = models.UserOrder
        fields = '__all__'
        depth = 3
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        order=models.WeChatOreder.objects.get(id=ret['order'])
        user_order=WeChatOrderSerializer(order).data
        user_order['id']=ret["id"]
        user_order.pop('we_user')
        user_order['is_hide']=ret['is_hide']
        user_order.pop('edit_time')
        # for index, item in enumerate(user_order['product_packge']):
        #     user_order['product_packge'][index]['product']=SnapshotSerializer(store_models.ProductSize.objects.get(id=item['product'])).data
        return user_order

class DeleteUserOrder(serializers.Serializer):
    """删除（隐藏）面向用户订单user_order
    """
    order=serializers.PrimaryKeyRelatedField(read_only=False,queryset=models.UserOrder.objects.all(),help_text='int，外键，UserOreder')
    

class UserRefundSerializer(serializers.ModelSerializer):
    """面向用户退货单类 序列化类
    """
    order=serializers.PrimaryKeyRelatedField(read_only=False,queryset=models.WeChatOreder.objects.all(),help_text='int，外键，WeChatOreder')
    refund_package=serializers.PrimaryKeyRelatedField(many=True,read_only=True,help_text='int，外键，RefundPackge')
    # refund_package=RefundPackgeSerializer(many=True,read_only=True)
    create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",required=False)
    edit_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",required=False)
    class Meta:
        model = models.Refund
        fields = '__all__'
        depth = 1
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        refund_package=[]
        for item in ret['refund_package']:
            model=models.RefundPackge.objects.get(id=item)
            refund_package.append({"product": SnapshotSerializer(model.order_package.product).data,"count":model.refund_count})
        ret['refund_package']=refund_package
        if not ret['state']==3:
            ret.pop('out_refund_no')
        if not ret['state']==4 or ret['state']==5 or ret['state']==6:
            ret.pop('re_extra')
        if not ret['state']>1 or ret['state']==4 or ret['state']==5 or ret['state']==6:
            ret.pop('express_code')    
        ret.pop('order')
        return ret 

class SnapshotSerializer(serializers.ModelSerializer):
    """反向细节，使用Size类，用于产品快照
    """    
    class Meta:
        model = store_models.ProductSize
        fields = '__all__'
        depth = 3
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        
        color=store_serializers.ColorSerializer(store_models.ProductColor.objects.get(id=ret['color']['id'])).data
        color.pop('sizes')
        active_porduct=color.pop('active_porduct')
        product=store_serializers.PorductSerializer(store_models.ActivePorduct.objects.get(id=active_porduct)).data
        product.pop('colors')
        product.pop('start_time')
        product.pop('end_time')
        product.pop('create_time')
        product.pop('edit_time')
        product.pop('state')
        product['id']=ret['id'] # 把product的id改成了ProductSize的id
        out=product
        out['color']=color
        out['size']=ret['size']
        return out

class CheckOut(serializers.Serializer):
    """下单结算请求序列化
    """
    order_package=OrderPackgeSerializer(many=True,required=True)
    address=JSONSerializerField(required=True,allow_null=False)
    extra=serializers.CharField(allow_blank=True,required=False)
    
class ChangeAddress(serializers.Serializer):
    """修改地址序列化"""
    user_order_id=serializers.PrimaryKeyRelatedField(read_only=False,queryset=models.UserOrder.objects.all(),help_text='int，外键，UserOrder')
    address=JSONSerializerField(required=True,allow_null=False,help_text='json，地址')
    def validate_user_order_id(self, user_order_id):
        """对单一的字段进行检验"""
        # 注意参数，self以及字段名
        # 注意函数名写法，validate_ + 字段名字
        order=user_order_id.order
        if order.state>1:
            raise serializers.ValidationError("Order has been shipped, cannot change address")
        return user_order_id

class Product(serializers.ModelSerializer):
    colors=store_serializers.ColorSerializer(many=True,read_only=True)
    start_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",help_text="datetime，活动开始时间")
    end_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",help_text="datetime，活动结束时间")
    # create_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",required=False)
    # edit_time = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S",required=False)
    active_images=store_serializers.ImageSerializer(many=True,help_text='[int]，外键-Image，活动图片')
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
        model = store_models.ActivePorduct
        # fields = '__all__'
        exclude = ['create_time','edit_time','state']
        depth = 1
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # ret['colors'].pop('id')
        # ret['colors'].pop('active_porduct')
        return ret

class ReCheckOut(serializers.Serializer):
    """重新下单支付序列化
    """
    order_id=serializers.PrimaryKeyRelatedField(read_only=False,queryset=models.UserOrder.objects.all(),help_text='int，外键，UserOrder')

class PayCallBack(serializers.Serializer):
    """支付回调序列化
    """
    appid=serializers.CharField(required=False)
    coupon_type=serializers.CharField(required=False)
    nonce_str=serializers.CharField(required=False)
    trade_type=serializers.CharField(required=False)
    time_end=serializers.CharField(required=False)
    sub_mch_id=serializers.CharField(required=False)
    sign=serializers.CharField(required=False)
    out_trade_no=serializers.CharField(required=False)
    attach=serializers.CharField(required=False)
    mch_id=serializers.CharField(required=False)
    coupon_count=serializers.CharField(required=False)
    coupon_id=serializers.CharField(required=False)
    transaction_id=serializers.CharField(required=False)
    coupon_fee_0=serializers.CharField(required=False)
    total_fee=serializers.FloatField(required=False)
    fee_type=serializers.CharField(required=False)
    result_code=serializers.CharField(required=False)
    is_subscribe=serializers.CharField(required=False)
    openid=serializers.CharField(required=False)
    return_code=serializers.CharField()
    bank_type=serializers.CharField(required=False)

class RefundUndeliveredserializers(serializers.Serializer):
    """未发货直接退款序列化"""
    order_id=serializers.PrimaryKeyRelatedField(read_only=False,queryset=models.UserOrder.objects.all(),help_text='int，外键，UserOrder')
    extra=serializers.CharField(allow_blank=False)
    def validate_order_id(self, order_id):
        order=order_id.order 
        if order.state!=1:
            raise serializers.ValidationError("Order State Not 1.")
        return order_id

class RefundApplication(serializers.Serializer):
    """退货申请序列化 退款退货情况
    """
    order_id=serializers.PrimaryKeyRelatedField(read_only=False,queryset=models.UserOrder.objects.all(),help_text='int，外键，UserOrder')
    refund_package=OrderPackgeSerializer(many=True,read_only=False)
    extra=serializers.CharField(allow_blank=False)
    def validate_order_id(self, order_id):
        if order_id.order.state!=2 and order_id.order.state!=6:
            raise serializers.ValidationError("Order State is " +str(order_id.order.state)+ ", Not 2 or 6.")
        return order_id

    def validate_refund_packge(self, refund_package):
        """对单一的字段进行检验"""
        # 注意参数，self以及字段名
        # 注意函数名写法，validate_ + 字段名字
        # order=models.WeChatOreder.objects.get(id=int(self.initial_data['order_id'].order))
        userorder=models.UserOrder.objects.get(id=int(self.initial_data['order_id']))
        order=userorder.order
        # raise serializers.ValidationError(refund_package[0]['product'])
        for packge in refund_package:
            product_packge_model=order.order_package.filter(product=packge['product']).first()
            # raise serializers.ValidationError(packge['count']<product_packge_model.count)
            if not product_packge_model:
                raise serializers.ValidationError("Order Porduct ["+ str(packge['product']) +"] Not Found.")
            if product_packge_model.count<packge['count']:
                raise serializers.ValidationError("Order Porduct ["+ str(packge['product']) +"] Count is Error.")
            if models.RefundPackge.objects.filter(order_package=product_packge_model).first():
                raise serializers.ValidationError("Order Porduct ["+ str(packge['product']) +"] Refund is Existing.")

        return refund_package

class RefundApplicationConfirmRefund(serializers.Serializer):
    """申请是否通过序列化
    """
    refund_id=serializers.PrimaryKeyRelatedField(read_only=False,queryset=models.Refund.objects.all(),help_text='int，外键，Refund')
    confirmrefund=serializers.BooleanField()
    re_extra=serializers.CharField(required=False)
    def validate_re_extra(self, re_extra):
        # 当不通过时（confirmrefund=false），答复不能为空
        if not self.initial_data['confirmrefund']:
            if re_extra==None:
                raise serializers.ValidationError("re_extra Can Not be blank when confirmrefund is False.")
        return re_extra
    def validate_refund_id(self, refund_id):
        # 只有当state为0时可以修改
        if not refund_id.state==0:
            raise serializers.ValidationError("Refund ["+ str(refund_id) +"] state is not '0'.")
        return refund_id    

# class RefundMoneyConfirmRefund(serializers.Serializer):
#     """是否退款金额
#     """
#     refund_id=serializers.PrimaryKeyRelatedField(read_only=False,queryset=models.Refund.objects.all(),help_text='int，外键，Refund')
#     confirmrefund=serializers.BooleanField() 
#     price=serializers.FloatField(required=False)
#     re_extra=serializers.CharField(required=False)
#     def validate_re_extra(self, re_extra):
#         # 当为否时，可以修改退款金额，并需要填写回复
#         if not self.initial_data['confirmrefund']:
#             if re_extra==None:
#                 raise serializers.ValidationError("re_extra Can Not be blank when confirmrefund is False.")
#         return re_extra
#     def validate_refund_id(self, refund_id):
#         # 只有当state为0时可以修改
#         if not refund_id.state==2:
#             raise serializers.ValidationError("Refund ["+ str(refund_id) +"] state is not '0'.")
#         return refund_id  
#     def validate_price(self, price):
#         # 只有当state为0时可以修改
#         if  price > refund_id.price:
#             raise serializers.ValidationError("The refund amount shall not be greater than ["+ str(refund_id.price) +"].")
#         return refund_id  

class RefundMoneyConfirmRefund(serializers.Serializer):
    """是否退款金额
    """
    refund_id=serializers.PrimaryKeyRelatedField(read_only=False,queryset=models.Refund.objects.all(),help_text='int，外键，Refund')
    confirmrefund=serializers.BooleanField() 
    def validate_refund_id(self, refund_id):
        # 只有当state为2时可以修改
        if not refund_id.state==2:
            raise serializers.ValidationError("Refund ["+ str(refund_id) +"] state is not '2'.")
        return refund_id 

class RefundExpress(serializers.Serializer):
    """前端-添加运单号
    """
    refund_id=serializers.PrimaryKeyRelatedField(read_only=False,queryset=models.Refund.objects.all(),help_text='int，外键，Refund')
    express_code=serializers.CharField()
    def validate_refund_id(self, refund_id):
        # 只有当state为1时可以修改
        if not refund_id.state==1:
            if not refund_id.state==2:
                raise serializers.ValidationError("Refund ["+ str(refund_id) +"] state is not '1 or 2'.")
        return refund_id 

class Receipt(serializers.Serializer):
    """前端-确认收货序列化
    """
    order_id=serializers.PrimaryKeyRelatedField(read_only=False,queryset=models.UserOrder.objects.all(),help_text='int，外键，UserOrder')
    def validate_order_id(self, order_id):
        # 只有当state为2时可以修改
        if not order_id.order.state==2:
            raise serializers.ValidationError("Refund state is not '2'.")
        return order_id 