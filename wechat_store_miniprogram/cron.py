import datetime

from django.template.defaultfilters import first

from . import models


def delete_expired_orders():
    """定时任务，删除过期的订单
    """
    try:
        time=datetime.datetime.now()-datetime.timedelta(minutes=110)
        order=models.WeChatOreder.objects.filter(state=0).first()
        now = datetime.datetime.now()
        order.extra="执行定时任务"+now.strftime('%Y-%m-%d %H:%M:%S')
        order.save()
        print(datetime.datetime.now())
    except BaseException as e:
        print(e)