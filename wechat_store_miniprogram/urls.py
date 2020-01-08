from django.urls import include, path, re_path
# 引入同级目录下的views.py文件
from . import views
from rest_framework import routers
# jwt
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


router = routers.DefaultRouter()
router.register(r'wx_user', views.WeUserViewSet)
router.register(r'wx_order', views.WeChatOrderViewSet)
router.register(r'order_express', views.OrderExpressViewSet)
router.register(r'user_order', views.UserOrderViewSet) # 小程序查看个人订单
router.register(r'snapshot', views.SnapshotViewSet)
router.register(r'active_product', views.ActiveProductViewSet)
router.register(r'refund', views.RefundViewSet)
router.register(r'user_refund', views.UserRefund) # 小程序查看个人退货单
router.register(r'logistics', views.Logistics) # 后台物流

app_name = 'wechat_store_miniprogram'

urlpatterns = [
    # 微信小程序登录
    re_path(r'^(?P<version>(v1|v2))/wx_login/', views.WxLogin.as_view(), name='wx_login'),
    # 以下是小程序用户获取token的url
    # re_path(r'^(?P<version>(v1|v2))/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    re_path(r'^(?P<version>(v1|v2))/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # 获取微信用户个人地址
    re_path(r'^(?P<version>(v1|v2))/get_address/', views.SelfAddressViewSet.as_view(), name='get_address'),
    # 小程序结算-支付
    re_path(r'^(?P<version>(v1|v2))/check_out/', views.CheckOut.as_view(), name='check_out'),
    # 小程序-修改发货地址
    re_path(r'^(?P<version>(v1|v2))/change_address/', views.ChangeAddress.as_view(), name='change_address'),
    # 小程序-重新支付
    re_path(r'^(?P<version>(v1|v2))/re_check_out/', views.ReCheckOut.as_view(), name='re_check_out'),
    # 小程序支付完成回调地址
    re_path(r'^(?P<version>(v1|v2))/pay_call_back/', views.PayCallBack.as_view(), name='pay_call_back'),
    # 小程序退款申请（未发货直接退款）
    re_path(r'^(?P<version>(v1|v2))/refund_undelivered/', views.RefundUndelivered.as_view(), name='refund_undelivered'),
    # 小程序退货申请
    re_path(r'^(?P<version>(v1|v2))/refund_application/', views.RefundApplication.as_view(), name='refund_application'),
    # 后台-退货申请确认（是否通过申请）
    # re_path(r'^(?P<version>(v1|v2))/confirmrefund/', views.ConfirmRefund.as_view(), name='confirmrefund'),
    # 小程序-添加退货运单号
    re_path(r'^(?P<version>(v1|v2))/refundexpress/', views.RefundExpress.as_view(), name='refundexpress'),
    # 小程序-用户确认收货
    re_path(r'^(?P<version>(v1|v2))/receipt/', views.UserReceipt.as_view(), name='refundexpress'),
    # 小程序-用户确认收货
    re_path(r'^(?P<version>(v1|v2))/delete_user_order/', views.DeleteUserOrderViewSet.as_view(), name='refundexpress'),

    #小程序-物流助手-查询细节(get by id)
    re_path(r'^(?P<version>(v1|v2))/user_logistics/(?P<id>[0-9]*)/$', views.UserLogistics.as_view(), name='user_logistics_detail'),
    #小程序-物流助手-推送信息
    re_path(r'^(?P<version>(v1|v2))/logistics_call_back/', views.LogisticsCallBack.as_view(), name='logistics_call_back'),

    #小程序-数据分析-访问留存
    re_path(r'^(?P<version>(v1|v2))/analysis/', views.GetAnalysis.as_view(), name='analysis'),   

    #后台-修改默认发货地址local_address
    re_path(r'^(?P<version>(v1|v2))/local_address/', views.LocalAddress.as_view(), name='local_address'),    
    
    re_path(r'^(?P<version>(v1|v2))/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
