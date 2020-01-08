import datetime
import hashlib
import random
import xml.etree.ElementTree as ET

from django.conf import settings
# from pyasn1.type.univ import Null

# 引入第三方平台密钥
from .. import access_key


class PayMent:
    # 商户平台上设置、查询
    def __init__(self):
        self.MCH_ID= access_key.MCH['MCH_ID']# 商户Id
        self.CLIENT_APP_ID=access_key.MINIPROGRAM['APP_ID'] # 微信小程序APPId
        self.MCH_KEY=access_key.MCH['MCH_KEY'] # 支付交易秘钥

    # 生成签名的函数
    def paysign(self,appid, body, mch_id, nonce_str, notify_url, openid, out_trade_no, spbill_create_ip, total_fee):
        ret = {
            "appid": appid,
            "body": body,
            "mch_id": mch_id,
            "nonce_str": nonce_str,
            "notify_url": notify_url,
            "openid": openid,
            "out_trade_no": out_trade_no,
            "spbill_create_ip": spbill_create_ip,
            "total_fee": total_fee,
            "trade_type": 'JSAPI'
        }

        # 处理函数，对参数按照key=value的格式，并按照参数名ASCII字典序排序
        stringA = '&'.join(["{0}={1}".format(k, ret.get(k)) for k in sorted(ret)])
        stringSignTemp = '{0}&key={1}'.format(stringA, self.MCH_KEY)
        sign = hashlib.md5(stringSignTemp.encode("utf-8")).hexdigest()
        return sign.upper()


    # 生成随机字符串
    def getNonceStr(self):
        """生成随机字符串
        """
        data = "123456789zxcvbnmasdfghjklqwertyuiopZXCVBNMASDFGHJKLQWERTYUIOP"
        nonce_str = ''.join(random.sample(data, 30))
        return nonce_str


    # 生成商品订单号
    def getWxPayOrdrID(self):
        date = datetime.datetime.now()
        # 根据当前系统时间来生成商品订单号。时间精确到微秒
        payOrdrID = date.strftime("%Y%m%d%H%M%S%f")

        return payOrdrID


    # 获取全部参数信息，封装成xml
    def get_bodyData(self, openid, client_ip, notify_url, body, price, out_trade_no=None):
        """获取全部参数信息，封装成xml
        
        Attributes:

            openid：微信用户openid  
            client_ip：地址的ip
            notify_url：回调地址
            body：商品描述（name）
            price：支付金额
        """
        # body = 'Mytest'  # 商品描述
        # notify_url = 'https://127.0.0.1:8000/payOrder/'  # 支付成功的回调地址  可访问 不带参数
        nonce_str = self.getNonceStr()  # 随机字符串
        if not out_trade_no: #商户订单号是否存在，如果存在则是重新支付的
            out_trade_no = self.getWxPayOrdrID()  # 生成商户订单号
        total_fee = str(price)  # 订单价格 单位是 分

        # 获取签名
        sign = self.paysign(self.CLIENT_APP_ID, body, self.MCH_ID, nonce_str, notify_url, openid, out_trade_no, client_ip, total_fee)

        bodyData = '<xml>'
        bodyData += '<appid>' + self.CLIENT_APP_ID + '</appid>'  # 小程序ID
        bodyData += '<body>' + body.encode('utf8').decode('iso-8859-1') + '</body>'  # 商品描述
        bodyData += '<mch_id>' + self.MCH_ID + '</mch_id>'  # 商户号
        bodyData += '<nonce_str>' + nonce_str + '</nonce_str>'  # 随机字符串
        bodyData += '<notify_url>' + notify_url + '</notify_url>'  # 支付成功的回调地址
        bodyData += '<openid>' + openid + '</openid>'  # 用户标识
        bodyData += '<out_trade_no>' + out_trade_no + '</out_trade_no>'  # 商户订单号
        bodyData += '<spbill_create_ip>' + client_ip + '</spbill_create_ip>'  # 客户端终端IP
        bodyData += '<total_fee>' + total_fee + '</total_fee>'  # 总金额 单位为分
        bodyData += '<trade_type>JSAPI</trade_type>'  # 交易类型 小程序取值如下：JSAPI
        bodyData += '<sign>' + sign + '</sign>'
        bodyData += '</xml>'

        return bodyData


    def xml_to_dict(self,xml_data):
        '''
        xml to dict
        :param xml_data:
        :return:
        '''
        xml_dict = {}
        root = ET.fromstring(xml_data)
        for child in root:
            xml_dict[child.tag] = child.text
        return xml_dict


    def dict_to_xml(self,dict_data):
        '''
        dict to xml
        :param dict_data:
        :return:
        '''
        xml = ["<xml>"]
        for k, v in dict_data.iteritems():
            xml.append("<{0}>{1}</{0}>".format(k, v))
        xml.append("</xml>")
        return "".join(xml)


    # 获取返回给小程序的paySign
    def get_paysign(self,prepay_id, timeStamp, nonceStr):
        pay_data = {
            'appId': self.CLIENT_APP_ID,
            'nonceStr': nonceStr,
            'package': "prepay_id=" + prepay_id,
            'signType': 'MD5',
            'timeStamp': timeStamp
        }
        stringA = '&'.join(["{0}={1}".format(k, pay_data.get(k)) for k in sorted(pay_data)])
        stringSignTemp = '{0}&key={1}'.format(stringA, self.MCH_KEY)
        sign = hashlib.md5(stringSignTemp.encode("utf-8")).hexdigest()
        return sign.upper()


class RefundMent:
    """微信退款
    """
    # 商户平台上设置、查询
    def __init__(self):
        self.MCH_ID= access_key.MCH['MCH_ID']# 商户Id
        self.CLIENT_APP_ID=access_key.MINIPROGRAM['APP_ID'] # 微信小程序APPId
        self.MCH_KEY=access_key.MCH['MCH_KEY'] # 支付交易秘钥

    # 生成签名的函数
    def paysign(self,appid, mch_id, nonce_str, out_refund_no, out_trade_no, refund_fee, total_fee):
        ret = {
            "appid": appid,
            "mch_id": mch_id,
            "nonce_str": nonce_str,
            "out_refund_no": out_refund_no,
            "out_trade_no": out_trade_no,
            "refund_fee": refund_fee,
            "total_fee": total_fee
        }

        # 处理函数，对参数按照key=value的格式，并按照参数名ASCII字典序排序
        stringA = '&'.join(["{0}={1}".format(k, ret.get(k)) for k in sorted(ret)])
        stringSignTemp = '{0}&key={1}'.format(stringA, self.MCH_KEY)
        sign = hashlib.md5(stringSignTemp.encode("utf-8")).hexdigest()
        return sign.upper()


    # 生成随机字符串
    def getNonceStr(self):
        """生成随机字符串
        """
        data = "123456789zxcvbnmasdfghjklqwertyuiopZXCVBNMASDFGHJKLQWERTYUIOP"
        nonce_str = ''.join(random.sample(data, 30))
        return nonce_str


    # 生成退款单号
    def getWxRefundOrdrID(self):
        date = datetime.datetime.now()
        # 根据当前系统时间来生成商品订单号。时间精确到微秒，最前面加上T
        payOrdrID ="T" + date.strftime("%Y%m%d%H%M%S%f")

        return payOrdrID


    # 获取全部参数信息，封装成xml
    def get_bodyData(self, out_trade_no, refund_fee, total_fee):
        """
        获取全部参数信息，封装成xml

            Attributes:    
            out_trade_no：商户订单号   
            refund_fee：退款金额  
            total_fee：订单总金额  
        """
        nonce_str = self.getNonceStr()  # 随机字符串
        # if not out_trade_no: #商户订单号是否存在，如果存在则是重新支付的
        out_refund_no = self.getWxRefundOrdrID()  # 生成商户订单号
        total_fee = str(total_fee)  # 订单价格 单位是 分

        # 获取签名
        sign = self.paysign(self.CLIENT_APP_ID, self.MCH_ID, nonce_str, out_refund_no, out_trade_no, refund_fee, total_fee)

        bodyData = '<xml>'
        bodyData += '<appid>' + self.CLIENT_APP_ID + '</appid>'  # 小程序ID
        bodyData += '<mch_id>' + self.MCH_ID + '</mch_id>'  # 商户号
        bodyData += '<nonce_str>' + nonce_str + '</nonce_str>'  # 随机字符串
        bodyData += '<out_refund_no>' + out_refund_no + '</out_refund_no>'  # 商户退款单号
        bodyData += '<out_trade_no>' + out_trade_no + '</out_trade_no>'  # 商户订单号
        bodyData += '<refund_fee>' + refund_fee + '</refund_fee>'  # 退款金额
        bodyData += '<total_fee>' + total_fee + '</total_fee>'  # 总金额 单位为分
        bodyData += '<transaction_id></transaction_id>'  # 总金额 单位为分
        bodyData += '<sign>' + sign + '</sign>'
        bodyData += '</xml>'

        return bodyData


    def xml_to_dict(self,xml_data):
        '''
        xml to dict
        :param xml_data:
        :return:
        '''
        xml_dict = {}
        root = ET.fromstring(xml_data)
        for child in root:
            xml_dict[child.tag] = child.text
        return xml_dict


    def dict_to_xml(self,dict_data):
        '''
        dict to xml
        :param dict_data:
        :return:
        '''
        xml = ["<xml>"]
        for k, v in dict_data.iteritems():
            xml.append("<{0}>{1}</{0}>".format(k, v))
        xml.append("</xml>")
        return "".join(xml)