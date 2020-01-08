from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register([WeUser,WeChatOreder,UserOrder,OrderPackge,OrderExpress,Refund,RefundPackge])
