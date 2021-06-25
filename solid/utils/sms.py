import json
import uuid

try:
    from aliyunsdkcore.client import AcsClient
    from aliyunsdkcore.request import CommonRequest
except:
    pass

import settings

acs_client = AcsClient(settings.ACCESS_KEY_ID, settings.ACCESS_KEY_SECRET, settings.REGION)

def send_sms(business_id, phone_number, sign_name, template_code, template_param=None):
    smsRequest = CommonRequest()
    smsRequest.set_domain(settings.DOMAIN)
    smsRequest.set_accept_format('json')
    smsRequest.set_method('POST')
    smsRequest.set_action_name(settings.SENDSMS)
    smsRequest.set_version('2017-05-25')
    if template_param is not None:
        smsRequest.add_query_param('TemplateParam', template_param)
    smsRequest.add_query_param('RegionId', settings.REGION)
    smsRequest.add_query_param('PhoneNumbers', phone_number)
    smsRequest.add_query_param('SignName', sign_name)
    smsRequest.add_query_param('TemplateCode', template_code)
    smsRequest.add_query_param('OutId', business_id)
    smsResponse = acs_client.do_action_with_exception(smsRequest)
    return smsResponse




def send_message(phone_num, code):
    send_sms(uuid.uuid1().hex,
             phone_num,
             settings.SIGN,
             settings.REG_CODE,
             json.dumps({'code':code})
             )
    return 'success'
