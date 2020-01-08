"""administration URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from rest_framework.documentation import include_docs_urls #自带api文档

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('backend/', include('wechat_store.urls')),
    path('miniprogram/', include('wechat_store_miniprogram.urls')),
    path('store/', include('store.urls')),
    path('docs/', include_docs_urls(title='Store API文档')),
]
