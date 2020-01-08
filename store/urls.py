from django.urls import include,path,re_path
# 引入同级目录下的views.py文件
from . import views
from rest_framework import routers
#jwt
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
# 重写authenticate方法，继承ModelBackend这个类来重写方法
from django.contrib.auth.backends import ModelBackend
# from .models import User

router = routers.DefaultRouter()
router.register(r'user', views.UserViewSet)
# router.register(r'weuser', views.WeUserViewSet)
router.register(r'group', views.GroupViewSet)
router.register(r'permission', views.PermissionViewSet)
router.register(r'product_image', views.ProductImageValViewSet)
# router.register(r'color', views.ColorViewSet)
# router.register(r'size', views.SizeViewSet)
router.register(r'activr_product', views.ActivePorductViewSet)
# router.register(r'product', views.ProductViewSet)
# router.register(r'good_type', views.GoodTypeViewSet)
# router.register(r'attribute_key', views.AttributeKeyViewSet)
# router.register(r'attribute_val', views.AttributeValViewSet)
# # router.register(r'images', views.ImagesValViewSet)
# router.register(r'good_images', views.GoodImageValViewSet)
# router.register(r'good', views.GoodViewSet)
app_name = 'store'
urlpatterns = [
    # /test/
    # path('login/', views.login, name='login'),
    re_path(r'^(?P<version>(v1|v2))/update_image/', views.UpdateImageView.as_view(), name='update_image'),
    # path('v1/login/', views.login, name='login'),

    # 以下是获取token的url
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('my_view/',views.my_view),
    re_path(r'^(?P<version>(v1|v2))/my_view/', views.MyView.as_view(), name='my_view'),
    re_path(r'^(?P<version>(v1|v2))/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    # re_path(r'^files/(?P<path>.*)$', serve, {"document_root": settings.MEDIA_ROOT})
]