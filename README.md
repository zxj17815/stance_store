#### 介绍
###### stance-store 系统     
1. 前后端分离：**数据后台前后端**和**商店应用前后端**    
2. 前端使用：    
3. 后端使用：Django   
4. 数据库使用：Mysql   
5. 后端[API文档](https://futurestitchstore.postman.co/collections/7890631-3b3f9d49-4c09-45a5-bf32-72202956b079?version=latest&workspace=cc570e90-4cdd-488b-a5cf-cb08819d9a6a)
#### 目录
```
├── cert # 微信商户密钥
│   ├── apiclient_cert.pem
│   └── apiclient_key.pem
├── collected_static # 静态文件生成文件夹（直接放在这方便调试）
├── manage.py
├── README.md
├── stance_store
│   ├── __init__.py
│   ├── settings_por.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi_por.py
│   └── wsgi.py
├── store
│   ├── access_key.py
│   ├── admin.py
│   ├── apps.py
│   ├── __init__.py
│   ├── migrations
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── tmp
│   └── delete_expired_orders_job.log
├── uwsgi
│   ├── uwsgi.log
│   ├── uwsgi.pid
│   └── uwsgi.status
├── uwsgi.ini # 开发uwsgi
├── uwsgi_por.ini # 生产uwsgi
└── wechat_store_miniprogram
    ├── access_key.py
    ├── admin.py
    ├── apps.py
    ├── cron.py
    ├── __init__.py
    ├── local_address.json
    ├── migrations
    ├── models.py
    ├── serializers.py
    ├── tests.py
    ├── tools
    │   ├── __init__.py
    │   ├── payment.py
    │   ├── __pycache__
    │   │   ├── __init__.cpython-35.pyc
    │   │   ├── payment.cpython-35.pyc
    │   │   └── WXBizDataCrypt.cpython-35.pyc
    │   └── WXBizDataCrypt.py
    ├── urls.py
    └── views.py
```
##### 运行前必读，否则将会出错
需要的pip依赖
```shell
pip install django-crontab
pip install djangorestframework
pip install markdown
pip install django-filter
pip install djangorestframework_simplejwt
pip install requests
pip install djangorestframework-xml
pip install drf-writable-nested
pip install coreapi
pip install oss2
```
1. 需要在store下增加access_key.py，存放阿里云oss密钥：
    ```python
    # 阿里云OSS变量
    ALIYUN={
        'OSS_ACCESS_KEY_ID':'阿里云oss的KEY ID',
        'OSS_ACCESS_KEY_SECRET': '阿里云oss的密钥',
        'OSS_BUCKET': 'oss的存储bucket',
        'OSS_ENDPOINT': 'oss-cn-hangzhou.aliyuncs.com',# oss地区，此例为杭州
        'OSS_VIEW_URL':'image.iceiceice.work',# 指向的域名，重点，如果不用域名访问图片的资源地址将会直接下载而不是预览
    }
    ```
2. 需要在wechat_store_miniprogram下也增加access_key.py，存放微信相关密钥：
    ```python
    # 微信小程序的appid和secret
    MINIPROGRAM={
        'APP_ID':'微信小程序的appid',
        'SECRET':'微信小程序的secret'
    }

    # 微信商户id和支付交易秘钥
    MCH={
        'MCH_ID':'商户id',
        'MCH_KEY':'交易密钥'
    }
    ```
3. 需要在backend/administration/cert里添加两个微信商户的ssl钥匙文件   
将公钥文件名命名为**apiclient_cert.pem**；  
将密钥文件名命名为**apiclient_key.pem**

4. 使用物流助手功能时需要将默认快递公司测试代码修改掉（目前只支持发散单）  
可根据微信小程序文档找到物流公司代码   
位置在小程序的views   
    ```python
    # 物流助手对应，正式试用前请修改此为顺丰的真实key
    _delivery_id= "TEST"
    _biz_id= "test_biz_id"
    ```
#### 启动
1. 开发环境下使用默认命令即可
2. 生成环境下uwsgi启动需要使用uwsgi_por.ini文件 
    ```shell
    sudo uwsgi --ini uwsgi.ini
    ```
3. 生成环境下数据库迁移需要使用指定settings命令：
    ```shell
    python3 manage.py migrate --settings=stance_store.settings_por
    ```