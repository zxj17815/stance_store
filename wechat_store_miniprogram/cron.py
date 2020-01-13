import datetime

from . import models


def delete_expired_orders():
    """定时任务，删除过期的订单,每半小时执行一次，删除12小时前未付款的订单
    """
    try:
        time=datetime.datetime.now()-datetime.timedelta(minutes=720)
        order=models.WeChatOreder.objects.filter(state=0)
        order=order.filter(create_time__lt=time)
        order.delete()
        # order.save()
        print("执行定时任务"+datetime.datetime.now(.strftime('%Y-%m-%d %H:%M:%S') ))
    except BaseException as e:
        print(e)