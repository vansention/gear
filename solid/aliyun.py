
import logging

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkbssopenapi.request.v20171214 import QueryAccountBalanceRequest
from aliyunsdkcdn.request.v20180510 import DescribeRefreshQuotaRequest



def get_account_balance(aliyun_account_info):
    """
    获取阿里云账户余额
    :param aliyun_account_info:
    :return:
    """
    client = AcsClient(
            aliyun_account_info['ACCESS_KEY'],
            aliyun_account_info['ACCESS_SECRET'],
            )

    request = QueryAccountBalanceRequest.QueryAccountBalanceRequest()
    resp = client.do_action_with_exception(request)
    logging.debug(resp)

def get_cdn_resource_quota(aliyun_account_info):
    """
    获取阿里云cdn info
    :param aliyun_account_info:
    :return:
    """
    client = AcsClient(
        aliyun_account_info['ACCESS_KEY'],
        aliyun_account_info['ACCESS_SECRET'],
    )
    request = DescribeRefreshQuotaRequest.DescribeRefreshQuotaRequest()
    resp = client.do_action_with_exception(request)
    logging.debug(resp)
