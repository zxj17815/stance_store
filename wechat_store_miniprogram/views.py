#coding:utf-8
# json库、http请求库、格式转换
import datetime
import json
import time
from os import O_DIRECTORY

import requests
from django.conf import settings
from django.core import serializers as django_ser  # django 的json转换
# 引入数据库，数据库错误回滚
from django.db import IntegrityError, transaction
# 引入Http库
from django.http import (HttpResponse, HttpResponseRedirect, JsonResponse,
                         request)
from django.shortcuts import get_object_or_404, render
from django_filters.rest_framework import DjangoFilterBackend  # 通用过滤器
from rest_framework import permissions  # 权限
from rest_framework import status  # 状态码
from rest_framework import generics, views, viewsets, mixins
from rest_framework.decorators import parser_classes, renderer_classes
from rest_framework.parsers import *  # 解析器
from rest_framework.response import Response  # 返回
from rest_framework.versioning import URLPathVersioning  # api版本控制
# 引入token应用，用于手动签发token
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_xml.parsers import XMLParser  # xml获取
from rest_framework_xml.renderers import XMLRenderer  # xml获取

# 引入model
from store import models as store_models
from store import serializers as store_serializers

# 本地保存的第三方平台密钥
# Api
from . import serializers  # 自定义的序列化类
from . import access_key, models
from .tools.payment import PayMent, RefundMent
# 引入自定义tool
from .tools.WXBizDataCrypt import WXBizDataCrypt

from rest_framework import filters  # 视图集; 查找和排序过滤器


# Create your views here.

# 物流助手对应，正式试用前请修改此为顺丰的真实key
# _delivery_id= "TEST" 
# _biz_id= "test_biz_id"
_delivery_id= "SF" 
_biz_id= "5731446951"

# 微信小程序的appid和secret
APPID = access_key.MINIPROGRAM['APP_ID']
SECRET = access_key.MINIPROGRAM['SECRET']
PAY_CALL_BACK='http://api.iceiceice.work/miniprogram/v1/pay_call_back/' # 微信支付的回调地址

# 自定义错误代码
CODE = {
    "login": {"error": "0000", "messages": "success"},
    "first_login": {"error": "0000", "messages": "first login"},
    "params": {"error": "0001", "messages": "传入参数错误"}
}

class WxLogin(views.APIView):
    """前台-微信小程序登录"""
    versioning_class = URLPathVersioning

    def post(self, request, *args, **kwargs):
        # return Response('POST请求，响应内容')
        """
        使用小程序js_code和userInfo登录，后端取得openid，返回一组token（access，refresh）
        """
        if self.request.version=='v1':
        # return Response({'received data': request.data['userInfo']})
            if request.data['js_code'] and request.data['userInfo']:
                res = requests.get('https://api.weixin.qq.com/sns/jscode2session',
                                {
                                    "appid": APPID,
                                    "secret": SECRET,
                                    "js_code": request.data['js_code'],
                                    "grant_type": "authorization_code"
                                }
                                )
                data = json.loads(res.content.decode('utf-8'))
                if 'openid' in data:
                    openid = data["openid"]
                    userInfo = request.data['userInfo']
                    obj_weuser = models.WeUser.objects.filter(open_id=openid).first()
                    if not obj_weuser:
                        # 新增系统用户，用户名由暂时为openid，创建weuser之后改为nickName加user的id
                        user = store_models.User.objects.create_user(username=openid,password=openid,user_type=2) 
                        # 新增wechat用户
                        models.WeUser(user=user,open_id=openid, nickName=userInfo['nickName'], avatar_url=userInfo['avatarUrl'], city=userInfo['city'],
                                    province=userInfo['province'], country=userInfo['country'], gender=userInfo['gender'], language=userInfo['language']).save()
                        # 重新更新用户名为nickName加user的id
                        user.username=userInfo['nickName']+"_"+str(user.id)
                        user.save()
                        token=get_tokens_for_user(user)
                        return HttpResponse(json.dumps(token), content_type="application/json,charset=utf-8")
                    else:
                        user=obj_weuser.user
                        # 判断用户名是否相等，不相等则更新数据
                        if not user.username==userInfo['nickName']+"_"+str(user.id):
                            # 更新weuser表
                            obj_weuser.nickName=userInfo['nickName']
                            obj_weuser.avatar_url=userInfo['avatarUrl']
                            obj_weuser.city=userInfo['city']
                            obj_weuser.province=userInfo['province']
                            obj_weuser.country=userInfo['country']
                            obj_weuser.gender=userInfo['gender']
                            obj_weuser.language=userInfo['language']
                            obj_weuser.save()
                            # 更新user表
                            user.username=userInfo['nickName']+"_"+str(user.id)
                            user.save()
                        token=get_tokens_for_user(user)
                        return HttpResponse(json.dumps(token), content_type="application/json,charset=utf-8")
                else:
                    return Response(data)
                
            else:
                return HttpResponse(json.dumps(CODE["params"]), content_type="application/json,charset=utf-8")        

# 请求微信小程序access_token
def request_access_token():
    """请求微信小程序access_token
    """
    res = requests.get('https://api.weixin.qq.com/cgi-bin/token',
                    {
                        "appid": APPID,
                        "secret": SECRET,
                        "grant_type": "client_credential"
                    }
                    )
    print(res)
    data = json.loads(res.content.decode('utf-8'))
    print(data)
    return data

# 获取小程序access_token
def get_app_access_token():
    """获取小程序access_token
    """
    datetime_now=datetime.datetime.now()
    model=models.AppToken.objects.filter(appid=APPID).first()
    if model:
        if model.expires_in<=datetime_now:
            data=request_access_token()
            if 'access_token' in data:
                expires_in= (datetime.datetime.now()+datetime.timedelta(seconds=int(data['expires_in']))).strftime('%Y-%m-%d %H:%M:%S')
                model.expires_in=expires_in
                model.token=data['access_token']
                model.save()
                return model.token
            else:
                return data
        else:
            return model.token
    else:
        data=request_access_token()
        if 'access_token' in data:
            expires_in= (datetime.datetime.now()+datetime.timedelta(seconds=int(data['expires_in']))).strftime('%Y-%m-%d %H:%M:%S')
            models.AppToken(appid=APPID,token=data['access_token'],expires_in=expires_in).save()
            model=models.AppToken.objects.filter(appid=APPID).first()
            return model.token
        else:
            return data

def get_logistitcs_data(token,order,no_html=False):
    url='https://api.weixin.qq.com/cgi-bin/express/business/order/batchget?access_token='+token
    head={"Content-Type":"application/json; charset=UTF-8"}
    send_data = {
        "order_list": [
            {
                "order_id": order.out_trade_no,
                "delivery_id": _delivery_id,
                "waybill_id": order.order_express.all()[0].code
            }
        ]
    }
    send_data=json.dumps(send_data,ensure_ascii=False).encode('utf-8')
    # print(send_data)
    res = requests.post(url,data=send_data,headers=head)
    data = json.loads(res.content.decode('utf-8'))
    print(data)
    if not data['order_list'][0]['errcode']==0:
        return Response(data,status=status.HTTP_400_BAD_REQUEST)
    # 获取运输信息
    url_path='https://api.weixin.qq.com/cgi-bin/express/business/path/get?access_token='+token
    send_path_data = {
                "order_id": order.out_trade_no,
                'openid': order.we_user.open_id,
                "delivery_id": _delivery_id,
                "waybill_id": order.order_express.all()[0].code
            }
    send_path_data=json.dumps(send_path_data,ensure_ascii=False).encode('utf-8')
    path_res = requests.post(url_path,data=send_path_data,headers=head)
    path_data = json.loads(path_res.content.decode('utf-8'))
    #合并两个数据
    express_data=data['order_list'][0]
    express_data["path"]=path_data['path_item_list']
    express_data.pop("errcode")
    express_data.pop("errmsg")
    express_data["out_trade_no"]=express_data["order_id"]
    express_data.pop("order_id")
    express_data["waybill_data"]=express_data["waybill_data"][0]
    if no_html:
        express_data.pop("print_html")
    return Response(express_data)


# 物流助手-下单
class Logistics(viewsets.ViewSet):
    """物流助手
    """
    permission_classes = [permissions.DjangoModelPermissions]
    queryset = models.WeChatOreder.objects.all()
    def create(self, request, *args, **kwargs):
        """物流助手-创建物流订单（快递下单）
        """
        token=get_app_access_token()
        serializer=serializers.LogisticsByOrder(data=request.data)
        serializer.is_valid(raise_exception=True)
        order=models.WeChatOreder.objects.filter(id=request.data['order_id']).first()
        user_order=order.userorder
        order_ser=serializers.WeChatOrderSerializer(order).data

        cargo_detail_list=[]
        for target_list in order_ser['order_package']:
            cargo_detail_list.append({
                "name": target_list['product']['name']+"-"+target_list['product']['color']['name'],
                "count": target_list['count']
            })
        # 读取本地保存的默认发货地址（local_address.json）    
        loacl_address=None
        with open("wechat_store_miniprogram/local_address.json","r") as f:
            loacl_address=json.load(f)
        _today_now=datetime.date.today()
        imeArray = time.strptime(str(_today_now)+" 16:00:00", "%Y-%m-%d %H:%M:%S")
        expect_time=int(time.mktime(imeArray))
        # 拼写快递下单数据
        send_data = {
            "add_source": 0,
            "order_id": order.out_trade_no,
            "openid": order.we_user.open_id,
            "delivery_id": _delivery_id,
            "biz_id": _biz_id,
            "custom_remark": "易碎物品",
            "sender": loacl_address,
            "receiver": {
                "name": order_ser['address']['userName'],
                "tel": order_ser['address']['telNumber'],
                "mobile": order_ser['address']['telNumber'],
                "post_code": order_ser['address']['postalCode'],
                "country": "中国",
                "province": order_ser['address']['provinceName'],
                "city": order_ser['address']['cityName'],
                "area": order_ser['address']['countyName'],
                "address": order_ser['address']['detailInfo']
            },
            "shop": {
                "wxa_path": "/order-detail/order-detail?id="+str(user_order.id),
                "img_url": order_ser['order_package'][0]['product']['active_images'][0]['image'],
                "goods_name": order_ser['order_package'][0]['product']['name'],
                "goods_count": len(order_ser['order_package'])
            },
            "cargo": {
                "count": len(order_ser['order_package']),
                "weight": 5.5,
                "space_x": 30.5,
                "space_y": 20,
                "space_z": 20,
                "detail_list": cargo_detail_list
            },
            "insured": {
                "use_insured": 0,
                "insured_value": 0
            },
            "service": {
                "service_type": 0, #测试填1
                "service_name": "SF" #测试填test_service_name
            },
            "expect_time": expect_time
        }
        # return Response(send_data)
        url='https://api.weixin.qq.com/cgi-bin/express/business/order/add?access_token='+token
        head={"Content-Type":"application/json; charset=UTF-8"}
        send_data=json.dumps(send_data,ensure_ascii=False).encode('utf-8')
        print(send_data)
        res = requests.post(url,data=send_data,headers=head)
        data = json.loads(res.content.decode('utf-8'))
        print(data)
        if 'errcode' in data:
            return Response(data,status=status.HTTP_400_BAD_REQUEST)
        else:
            # 增加运单，序列化器已经集成修改订单状态为发货状态（2：待确认）
            express_ser=serializers.OrderExpressSerializer(data={
                "order":order.id,
                "code":data['waybill_id'],
                "type":1
            })
            express_ser.is_valid(raise_exception=True)
            express_ser.save() # 保存快递订单
            
            logistitcs_data = get_logistitcs_data(token,order)

            return logistitcs_data

    def retrieve(self, request, pk=None,*args, **kwargs):
        """物流助手-查询单个信息
        """
        token=get_app_access_token()
        order=models.WeChatOreder.objects.filter(id=pk).first()
        if not order: #判断是否存在订单
            return Response({"order_id":"This order is not find"},status=status.HTTP_400_BAD_REQUEST)
        
        if not order.order_express.all(): #判断是否存在快递
            return Response({"order_id":"There is no logistics information for this order"},status=status.HTTP_400_BAD_REQUEST)
        
        if order.order_express.all()[0].type==0: #判断是否为手工下单
            return Response({"order_id":"No logistics information because type is 0"},status=status.HTTP_400_BAD_REQUEST)

        logistitcs_data=get_logistitcs_data(token,order)
        return logistitcs_data

    def list(self, request,*args, **kwargs):
        """物流-查询快递list
        """
        queryset=models.OrderExpress.objects.all()
        serializer=serializers.OrderExpressSerializer(queryset,many=True)
        return Response(serializer.data)

class LocalAddress(views.APIView):
    """修改保存发货地址（保存本地json文件）
    """
    permission_classes = [permissions.DjangoModelPermissions]
    queryset = models.WeChatOreder.objects.all()
    def get(self, request, *args, **kwargs):
        """获取默认发货地址"""
        loacl_address=None
        with open("wechat_store_miniprogram/local_address.json","r") as f:
            loacl_address=json.load(f)
        return Response(loacl_address)

    def post(self, request, *args, **kwargs):
        """修改默认发货地址"""
        serializer=serializers.LocalAddress(data=request.data)
        serializer.is_valid(raise_exception=True)
        with open("wechat_store_miniprogram/local_address.json","w") as f:
            json.dump(serializer.data,f)
        return Response(serializer.data)

class UserLogistics(views.APIView):
    """前端-小程序-物流助手物流信息
    """
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, id=None, *args, **kwargs):
        token=get_app_access_token()
        user = self.request.user
        if id:
            order=models.WeChatOreder.objects.filter(userorder=id).first()
            if not order: #判断是否存在订单
                return Response({"order_id":"This order is not find"},status=status.HTTP_400_BAD_REQUEST)
            
            if not order.order_express.all(): #判断是否存在快递
                return Response({"order_id":"There is no logistics information for this order"},status=status.HTTP_400_BAD_REQUEST)
            
            if order.order_express.all()[0].type==0: #判断是否为手工下单
                return Response({"order_id":"No logistics information because type is 0"},status=status.HTTP_400_BAD_REQUEST)

            logistitcs_data=get_logistitcs_data(token,order,no_html=True)
            return logistitcs_data

# 手动签发token
def get_tokens_for_user(user):
    """手动签发token方法，传入一个用户
    """

    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


# 此方法可以获取到unionid
def login2(request):
    if request.GET.get('js_code') and request.GET.get('signature') and request.GET.get('encryptedData') and request.GET.get('iv'):
        res = requests.get('https://api.weixin.qq.com/sns/jscode2session',
                           {
                               "appid": APPID,
                               "secret": SECRET,
                               "js_code": request.GET.get('js_code'),
                               "grant_type": "authorization_code"
                           }
                           )
        data = json.loads(res.content.decode('utf-8'))
        openid = data["openid"]
        session_key = data["session_key"]
        encryptedData = request.GET.get('encryptedData')
        iv = request.GET.get('iv')
        pc = WXBizDataCrypt(APPID, session_key)
        user_info_por = json.dumps(pc.decrypt(encryptedData, iv))
        return HttpResponse(user_info_por, content_type="application/json,charset=utf-8")
    else:
        return HttpResponse(json.dumps(CODE["params"]), content_type="application/json,charset=utf-8")


  

class PayCallBack(views.APIView):
    """后台-支付成功回调
    """
    renderer_classes = [XMLRenderer]
    parser_classes=[XMLParser]
    def post(self, request, *args, **kwargs):
        f1 = open(settings.BASE_DIR+'/tmp/test.txt','r+')
        f1.read()
        _xml = request.body
        #拿到微信发送的xml请求 即微信支付后的回调内容
        xml = str(_xml, encoding="utf-8")
        xml=PayMent().xml_to_dict(xml)
        serializer=serializers.PayCallBack(xml)
        data=serializer.data
        f1.write('\n'+datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+str(data))
        f1.close()
        if data['return_code']=='SUCCESS' and data['result_code']=='SUCCESS':
            total_fee=data['total_fee'] # 订单金额
            out_trade_no=data['out_trade_no'] # 商户订单号
            order=models.WeChatOreder.objects.get(out_trade_no=out_trade_no)
            if order:
                if int(order.total_price*100)==total_fee:
                    order.state=1
                    order.save()
        res={
            "return_code":"SUCCESS",
            "return_msg":"OK"
        }
        return Response(res)

class WeUserViewSet(viewsets.ModelViewSet):
    """后台-微信小程序用户
    """
    permission_classes = [permissions.DjangoModelPermissions]
    queryset = models.WeUser.objects.all()
    serializer_class = serializers.WeUserSerializer

class WeChatOrderViewSet(viewsets.ModelViewSet):
    """
    后台-订单
    """
    # permission_classes = [permissions.DjangoModelPermissions]
    queryset = models.WeChatOreder.objects.all()
    serializer_class = serializers.WeChatOrderSerializer
    filterset_fields = '__all__'
    filter_backends = [DjangoFilterBackend,filters.OrderingFilter]
    ordering_fields = ['id','create_time']
    ordering=['-id']
    def get_queryset(self):
        start = self.request.query_params.get('start_time', None)
        stop =  self.request.query_params.get('end_time', None)
        nick = self.request.query_params.get('nick_name', None)
        model=models.WeChatOreder.objects.all()
        if start and stop: # 按订单的创建时间区间筛选
            model=model.filter(create_time__gte=start).filter(create_time__lte=stop)
        if nick: #按订单的微信用户昵称筛选
            model=model.filter(we_user__nickName=nick)
        return model

class OrderExpressViewSet(viewsets.ModelViewSet):
    """
    后台-订单快递
    """
    permission_classes = [permissions.DjangoModelPermissions]
    queryset = models.OrderExpress.objects.all()
    serializer_class = serializers.OrderExpressSerializer
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        token=get_app_access_token()
        #判断是否为手工下单
        if instance.type==0:
            self.perform_destroy(instance)
        else:
            url='https://api.weixin.qq.com/cgi-bin/express/business/order/cancel?access_token='+token
            head={"Content-Type":"application/json; charset=UTF-8"}
            order=instance.order
            send_data={
                "order_id": order.id,
                "openid": order.we_user.open_id,
                "delivery_id": _delivery_id,
                "waybill_id": instance.code
                }
            send_data=json.dumps(send_data,ensure_ascii=False).encode('utf-8')
            # print(send_data)
            res = requests.post(url,data=send_data,headers=head)
            data = json.loads(res.content.decode('utf-8'))
            print(data)
            if not data['errcode'] == 0:
                return Response(data,status=status.HTTP_400_BAD_REQUEST)
            self.perform_destroy(instance)
        is_null=models.OrderExpress.objects.filter(order=instance.order)
        if not is_null: # 如果把最后一个对应的运单号删除，则将订单的状态调整回1，即已付款未发货
            order=instance.order
            order.state=1
            order.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class SnapshotViewSet(viewsets.ModelViewSet):
    """
    后台-商品详情，快照
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = store_models.ProductSize.objects.all()
    serializer_class = serializers.SnapshotSerializer

class SelfAddressViewSet(views.APIView):
    """前台-微信小程序 获取 用户个人收件地址信息
    """
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, *args, **kwargs):
        user = request.user
        weuser=models.WeUser.objects.filter(user=user).first() # 微信用户
        address=serializers.WeUserSerializer(weuser).data['user_address']
        if address:
            return Response(address)
        else:
            return Response(data={"error":"No address"},status=status.HTTP_400_BAD_REQUEST)

class UserOrderViewSet(viewsets.ModelViewSet):
    """
    前台-订单-获取个人订单
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.UserOrder.objects.all()
    serializer_class = serializers.UserOrderSerializer
    # filterset_fields = '__all__'
    filter_backends = [filters.OrderingFilter]
    # ordering_fields = ['id']
    def get_queryset(self):
        """重写查询方法，筛选出自己的订单
        """
        user = self.request.user
        order=models.WeChatOreder.objects.filter(we_user=user.weuser)
        return models.UserOrder.objects.filter(order__in=order,is_hide=False).order_by('-id')

class DeleteUserOrderViewSet(views.APIView):
    """
    前台-订单-删除个人订单
    """
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, *args, **kwargs):
        serializer=serializers.DeleteUserOrder(data=request.data)
        serializer.is_valid(raise_exception=True)
        ser_data=serializer.data
        user_order=models.UserOrder.objects.get(id=ser_data['order'])
        user_order.is_hide=True
        user_order.save()
        return Response(serializers.UserOrderSerializer(user_order).data)

class ActiveProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    前端-活动商品列表/详情
    """
    ermission_classes = [permissions.DjangoModelPermissionsOrAnonReadOnly]
    queryset = store_models.ActivePorduct.objects.filter(state=1) # 查询只有活动商品状态为1开启的
    serializer_class = serializers.Product

class CheckOut(generics.CreateAPIView):
    """前端-小程序支付-结算
    """
    permission_classes = [permissions.IsAuthenticated]
    # queryset = models.WeUser.objects.all()
    serializer_class = serializers.CheckOut
    def post(self, request, *args, **kwargs):
        """下单，获取订单商品信息，收件人及地址信息，订单备注
        """
        user = request.user
        request_data=request.data
        res_data=serializers.CheckOut(data=request_data)
        if not res_data.is_valid():
            return Response(res_data.errors,status=status.HTTP_400_BAD_REQUEST)
        else:
            # return Response(res_data.data)
            if "errMsg" in res_data.data['address']:
                res_data.data['address'].pop('errMsg') #删除地址里不用的errMsg
            weuser=models.WeUser.objects.filter(user=user).first() # 微信用户
            product=serializers.SnapshotSerializer(store_models.ProductSize.objects.get(id=res_data.data['order_package'][0]['product'])).data
            body=str(product['name']) # 统一下单-商品 string(128)
            price=0 #订单总价（下单商品*数量*单价）
            for item in res_data.data['order_package']:
                price=price+product['price']*item['count']
            xml=PayMent().get_bodyData(openid=weuser.open_id,client_ip=request.META['REMOTE_ADDR'],notify_url=PAY_CALL_BACK,body=body,price=int(price*100))
            # return Response(xml)
            head={"Content-Type":"text/xml; charset=UTF-8", 'Connection': 'close'} 
            res = requests.post('https://api.mch.weixin.qq.com/pay/unifiedorder',data=xml,headers=head)
            xml=PayMent().xml_to_dict(xml)
            res=PayMent().xml_to_dict(res.text.encode('iso-8859-1').decode('utf8'))
            if res['return_code']=='FAIL':
                return Response(res,status=status.HTTP_400_BAD_REQUEST)
            if res['result_code']=='SUCCESS':
                # 统一下单成功
                # 后台插入数据
                try:
                    
                    order = {
                    'out_trade_no': xml['out_trade_no'],
                    'we_user' :weuser.id,
                    'total_price':price,
                    # 'order_package':res_data.data['order_package'],
                    'extra':res_data.data['extra'],
                    'address':res_data.data['address']
                    }
                    serializer=serializers.WeChatOrderSerializer(data=order)
                    if serializer.is_valid():
                        serializer.save() # 保存订单数据
                        # order_package=[]
                        for item in res_data.data['order_package']:
                            item['order']=serializer.data['id']
                            order_package_serializer=serializers.OrderPackgeSerializer(data=item)
                            order_package_serializer.is_valid(raise_exception=True)
                            order_package_serializer.save() # 保存订单商品数据
                            # 修改库存
                            product_size_model=store_models.ProductSize.objects.get(id=order_package_serializer.data['product'])
                            product_size_model.quantity=product_size_model.quantity-order_package_serializer.data['count']
                            product_size_model.save()
                            # order_package.append(serializer.data['id'])
                        weuser.user_address=json.dumps(res_data.data['address'])
                        weuser.save() # 保存地址到用户表
                        user_order_serializer=serializers.UserOrderSerializer(data={"order":serializer.data['id']})
                        user_order_serializer.is_valid()
                        user_order_serializer.save()
                        # 返回信息给小程序支付
                        time_stamp=int(time.time())
                        paySign=PayMent().get_paysign(res['prepay_id'],time_stamp,xml['nonce_str'])
                        res_data={
                            'timeStamp':str(time_stamp),
                            'nonceStr':xml['nonce_str'],
                            'package':'prepay_id='+res['prepay_id'],
                            'signType':'MD5',
                            'paySign':paySign
                        }
                        return Response(res_data)
                    else: 
                        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
                    # return Response(order_package)
                except BaseException as e:
                    return Response(data={"Error":e},status=status.HTTP_400_BAD_REQUEST)
            else:
                head={"charset=UTF-8"} 
                return Response(res,status=status.HTTP_400_BAD_REQUEST)

class ChangeAddress(generics.CreateAPIView):
    """用户修改发货地址"""
    permission_classes = [permissions.IsAuthenticated]
    # queryset = models.WeChatOreder.objects.all()
    serializer_class = serializers.ChangeAddress
    def post(self, request, *args, **kwargs):
        serializer=serializers.ChangeAddress(data=request.data)
        serializer.is_valid(raise_exception=True)
        ser_data=serializer.data
        order=models.UserOrder.objects.get(id=ser_data['user_order_id']).order
        order.address=json.dumps(ser_data['address'])
        order.save()
        return Response(ser_data)

class ReCheckOut(generics.CreateAPIView):
    """前端-重新支付订单
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.ReCheckOut
    def post(self, request, *args, **kwargs):
        serializer=serializers.ReCheckOut(data=request.data)
        serializer.is_valid(raise_exception=True)
        refund_order=models.UserOrder.objects.get(id=serializer.data['order_id'])
        order=refund_order.order
        if order.state==0:
            weuser=order.we_user
            body=str(serializers.SnapshotSerializer(order.order_package.first().product).data['name'])
            price=order.total_price
            out_trade_no=order.out_trade_no
            xml=PayMent().get_bodyData(openid=weuser.open_id,client_ip=request.META['REMOTE_ADDR'],notify_url=PAY_CALL_BACK,body=body,price=int(price*100),out_trade_no=out_trade_no)
            head={"Content-Type":"text/xml; charset=UTF-8", 'Connection': 'close'} 
            res = requests.post('https://api.mch.weixin.qq.com/pay/unifiedorder',data=xml,headers=head)
            xml=PayMent().xml_to_dict(xml)
            res=PayMent().xml_to_dict(res.text.encode('iso-8859-1').decode('utf8'))
            if res['return_code']=='FAIL':
                return Response(res,status=status.HTTP_400_BAD_REQUEST)
            if res['result_code']=='SUCCESS':
                # 统一下单成功
                # 返回信息给小程序支付
                time_stamp=int(time.time())
                paySign=PayMent().get_paysign(res['prepay_id'],time_stamp,xml['nonce_str'])
                res_data={
                    'timeStamp':str(time_stamp),
                    'nonceStr':xml['nonce_str'],
                    'package':'prepay_id='+res['prepay_id'],
                    'signType':'MD5',
                    'paySign':paySign
                }
                return Response(res_data)

class UserReceipt(generics.CreateAPIView):
    """前端-确认收货
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.Receipt
    def post(self, request, *args, **kwargs):
        serializer=serializers.Receipt(data=request.data)
        serializer.is_valid(raise_exception=True)
        data=serializer.data
        order=models.UserOrder.objects.get(id=data['order_id']).order
        order.state=6
        order.save()
        return Response(serializers.UserOrderSerializer(models.UserOrder.objects.get(id=data['order_id'])).data)


class RefundUndelivered(generics.CreateAPIView):
    """前端-未发货退款
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.RefundUndeliveredserializers
    def post(self, request, *args, **kwargs):
        serializer=serializers.RefundUndeliveredserializers(data=request.data)
        serializer.is_valid(raise_exception=True)
        data=serializer.data
        order=models.UserOrder.objects.get(id=data['order_id']).order # order为系统订单
        refund={ #refun为退款单
            "order":order.id,
            "extra":data['extra'],
            "price":order.total_price,
            "state":5
        }
        refund_ser=serializers.RefundSerializer(data=refund)
        refund_ser.is_valid(raise_exception=True)
        refund_ser.save() 
        order.state=4 #系统订单 状态改为4申请退款中
        order.save()
        order_package=models.OrderPackge.objects.filter(order=order)
        refund_package=[]
        for item in order_package:
            packge={
                "refund":refund_ser.data['id'],
                "order_package":item.id,
                "refund_count":item.count
            }
            refund_packge_ser=serializers.RefundPackgeSerializer(data=packge)
            refund_packge_ser.is_valid(raise_exception=True)
            refund_packge_ser.save()
            # 库存数量退回 修改库存
            product_size_model=item.product
            product_size_model.quantity=product_size_model.quantity+item.count
            product_size_model.save()
        res_data={  #此处只返回退货单id
            "refund_id":order.refund.id
        }
        return Response(res_data)
        
class RefundApplication(generics.CreateAPIView):
    """前端-退货申请（退款退货）
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.RefundApplication
    def post(self, request, *args, **kwargs):
        serializer=serializers.RefundApplication(data=request.data)
        serializer.is_valid(raise_exception=True)
        data=serializer.data
        print(request.data)
        print(data)
        order=models.UserOrder.objects.filter(id=data['order_id']).first().order
        price=int(serializers.SnapshotSerializer(store_models.ProductSize.objects.get(id=data['refund_package'][0]['product'])).data['price']*100)
        count=0
        for item_refund_packge in data['refund_package']:
            count+=item_refund_packge['count']
        out_trade_no=order.out_trade_no
        refund_fee=price*count
        total_fee=int(order.total_price*100)
        refund={
            "order":order.id,
            "extra":data['extra'],
            "price":float(total_fee/100), #此处为退款金额
            "state":0
        }
        refund_res=serializers.RefundSerializer(data=refund)
        refund_res.is_valid(raise_exception=True)
        refund_res.save()
        
        for item_refund_packge in data['refund_package']:
            model=order.order_package.filter(product=item_refund_packge['product']).first()
            packge={
                "refund":refund_res.data['id'],
                "order_package":model.id,
                "refund_count":item_refund_packge['count']
            }
            refund_packge_ser=serializers.RefundPackgeSerializer(data=packge)
            refund_packge_ser.is_valid(raise_exception=True)
            refund_packge_ser.save()
        order.state=3
        order.save()
        res_data={  #此处只返回退货单id
            "refund_id":order.refund.id
        }
        return Response(res_data)

class UserRefund(viewsets.ModelViewSet):
    """
    前台-订单-获取个人退货单
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = models.Refund.objects.all().order_by('-id')
    serializer_class = serializers.UserRefundSerializer
    def get_queryset(self):
        """重写查询方法，筛选出自己的订单
        """
        user = self.request.user
        order=models.WeChatOreder.objects.filter(we_user=user.weuser)
        refund=models.Refund.objects.filter(order__in=order).order_by('-id')
        return refund


class RefundViewSet(viewsets.ModelViewSet):
    """后端-退款表
    """
    permission_classes = [permissions.DjangoModelPermissions]
    queryset = models.Refund.objects.all().order_by('-id')
    serializer_class = serializers.RefundSerializer
    filterset_fields = '__all__'
    filter_backends = [DjangoFilterBackend,filters.OrderingFilter]

    def retrieve(self, request, *args, **kwargs):
        """详情加上原订单的地址及用户
        """
        instance=self.get_object()
        serializer=serializers.RefundDetialSerializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """后端-是否通过退款申请和确认退款
        """
        instance=self.get_object()
        request.data['refund_id']=instance.id
        if instance.state==0:
            # 当原状态为0时，即为是否通过退款申请request
            serializer=serializers.RefundApplicationConfirmRefund(data=request.data)
            serializer.is_valid(raise_exception=True)
            data=serializer.data
            refund=models.Refund.objects.get(id=data['refund_id'])
            if not data['confirmrefund']:
                refund.re_extra=data['re_extra']
                refund.state=4
                refund.save()
            else:
                refund.state=1
                refund.save()
            return Response(self.get_serializer(self.get_object()).data)
        elif instance.state==2 or instance.state==5:
            # 当原状态为2时，即为退款request
            serializer=serializers.RefundMoneyConfirmRefund(data=request.data)
            out_trade_no=instance.order.out_trade_no
            refund_fee=int(instance.price*100)
            total_fee=int(instance.order.total_price*100)
            xml=RefundMent().get_bodyData(out_trade_no,str(refund_fee),str(total_fee))
            head={"Content-Type":"text/xml; charset=UTF-8", 'Connection': 'close'} 
            cert_path="{}/cert/apiclient_cert.pem".format(settings.BASE_DIR)
            key_path="{}/cert/apiclient_key.pem".format(settings.BASE_DIR)
            res = requests.post('https://api.mch.weixin.qq.com/secapi/pay/refund',data=xml,headers=head,cert=(cert_path,key_path))
            # xml=PayMent().xml_to_dict(xml)
            res=PayMent().xml_to_dict(res.text.encode('iso-8859-1').decode('utf8'))
            if res['return_code']=='SUCCESS':
                if res['result_code']=='SUCCESS':
                    order=instance.order
                    if order.state==4 and instance.state==5:
                        instance.state=6
                    else:
                        instance.state=3
                    instance.out_refund_no=res['out_refund_no']
                    instance.save()
                    order.state=5
                    order.save()
                    return Response(self.get_serializer(self.get_object()).data)
                else:
                    return Response(data=res,status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(data=res,status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(data={"error":"Refund state is "+str(instance.state)},status=status.HTTP_400_BAD_REQUEST)     

    def get_queryset(self):
        """自定义查询
        """
        start = self.request.query_params.get('start_time', None)
        stop =  self.request.query_params.get('end_time', None)
        nick = self.request.query_params.get('nick_name', None)
        model=models.Refund.objects.all()
        if start and stop: # 按订单的创建时间区间筛选
            model=model.filter(create_time__gte=start).filter(create_time__lte=stop)
        if nick: #按订单的微信用户昵称筛选
            model=model.filter(order__we_user__nickName=nick)
        return model

class RefundExpress(generics.CreateAPIView):
    """小程序-前端-填写退款运单
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.RefundExpress
    def post(self, request, *args, **kwargs):
        serializer=serializers.RefundExpress(data=request.data)
        serializer.is_valid(raise_exception=True)
        data=serializer.data
        refund=models.Refund.objects.get(id=data['refund_id'])
        if refund.state==1:
            refund.express_code=data['express_code']
            refund.state=2
            refund.save()
            return Response(serializer.data)
        else:
            refund.express_code=data['express_code']
            refund.save()
            return Response(serializer.data)
        


class RfundCallBack(views.APIView):
    """后端-退款结果回调
    """
    # permission_classes = [permissions.DjangoModelPermissions]
    def post(self, request, *args, **kwargs):
        serializer=serializers.RefundApplicationConfirmRefund(data=request.data)
        serializer.is_valid(raise_exception=True)
        data=serializer.data
        refund=models.Refund.objects.get(id=data['refund_id'])
        if not data['confirmrefund']:
            refund.re_extra=data['re_extra']
            refund.state=4
            refund.save()
        else:
            refund.state=1
            refund.save()
        return Response(serializer.data)


class LogisticsCallBack(views.APIView):
    """后端-物流助手位置信息变更回调
    """
    def post(self, request, *args, **kwargs):
        print(request.data)
        if 'Event' in request.data and request.data['Event']=='add_express_path':
            last_actions_type=request.data['Actions'][0]['ActionType']
            action_time=request.data['Actions'][0]['ActionTime']
            print(last_actions_type)
            if last_actions_type==300003:
                order=models.OrderExpress.objects.get(code=request.data['WayBillId']).order
                order.state=6
                order.receive_time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(action_time))
                order.save()
            return HttpResponse('success',content_type="application/json,charset=utf-8")
        elif 'FromUserName' in request.data :
            if request.data['MsgType']=="text" or request.data['MsgType']=="image":
                data = {
                        "CreateTime": request.data['CreateTime'], 
                        "FromUserName": request.data['ToUserName'],
                        "MsgType": "transfer_customer_service",
                        "ToUserName": request.data['FromUserName'], 
                        }
                # print(data)
                return Response(data,content_type="application/json,charset=utf-8")
            else:
                return HttpResponse('error',content_type="application/json,charset=utf-8")
        
    def get(self, request, *args, **kwargs):
        if 'echostr' in request.query_params:
            return HttpResponse(int(request.query_params['echostr']),content_type="application/json,charset=utf-8")

class GetAnalysis(views.APIView):
    def get(self, request, *args, **kwargs):
        token=get_app_access_token()
        # if 'retain_type' in request.query_params:
        #     return Response(1)
        # else:
        #     return Response(2)
        retain_type=request.query_params['retain_type'] if 'retain_type' in request.query_params else ''
        begin_date=request.query_params['begin_date'] if 'begin_date' in request.query_params else ''
        end_date=request.query_params['end_date'] if 'end_date' in request.query_params else ''
        if retain_type=='daily' or retain_type=='':
            url='https://api.weixin.qq.com/datacube/getweanalysisappiddailyretaininfo?access_token='+token
            head={"Content-Type":"application/json; charset=UTF-8"}
            send_data = {
                "begin_date": begin_date,
                "end_date": end_date
            }
            send_data=json.dumps(send_data).encode('utf-8')
            print(send_data)
            res = requests.post(url,data=send_data,headers=head)
            data = json.loads(res.content.decode('utf-8'))
            print(data)
            return Response(data)
        elif retain_type=='monthly':
            url='https://api.weixin.qq.com/datacube/getweanalysisappidmonthlyretaininfo?access_token='+token
            head={"Content-Type":"application/json; charset=UTF-8"}
            send_data = {
                "begin_date": begin_date,
                "end_date": end_date
            }
            send_data=json.dumps(send_data,ensure_ascii=False).encode('utf-8')
            print(send_data)
            res = requests.post(url,data=send_data,headers=head)
            data = json.loads(res.content.decode('utf-8'))
            print(data)
            return Response(data)
        elif retain_type=='weekly':
            url='https://api.weixin.qq.com/datacube/getweanalysisappidweeklyretaininfo?access_token='+token
            head={"Content-Type":"application/json; charset=UTF-8"}
            send_data = {
                "begin_date": begin_date,
                "end_date": end_date
            }
            send_data=json.dumps(send_data,ensure_ascii=False).encode('utf-8')
            print(send_data)
            res = requests.post(url,data=send_data,headers=head)
            data = json.loads(res.content.decode('utf-8'))
            print(data)
            return Response(data)
        else:
            return Response({"retain_type":'parameter error'},status=status.HTTP_400_BAD_REQUEST)
