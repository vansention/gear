import os
import time


WEB_PORT = 8001
LISTEN = '127.0.0.1'
BASE_PATH = os.path.dirname(__file__)
VERSION = time.time()
DEBUG = False
ADMIN_PORT = 8013
APP_NAME = 'REDPACK'
WS_CONN_KEY_EXPIRE = 60         # 登陆超时

REDIS_HOST = '127.0.0.1'
REDIS_POOL_SIZE = 32

APP_AUTH_TOKEN_EXPIRE = 60*60*60*24

AESKEY = '0123456789abcdef'
AESIV = '0123456789abcdef'


VAMP_APPID = '10127'
VAMP_KEY = ''
# 账户密码:
USERNAME = ''
PASSWORD = ''
WX_APPID= ''
WX_SECRET = ''
WX_REDIRECT_URI = ''

MONGO_URL = ''
DB_URL = ''
MONGO = ''
DB_POOL_SIZE = 64


SQLALCHEMY_MODEL_PATH = [
    'models',
    'liquid.models'
]



APPID = ''

APPKEY = ''

NAV_LIST = [
    {'name': '账户列表', 'href': 'user_list', 'perms': ['base']},
    {'name': '在线用户', 'href': 'online_list', 'perms': ['base']},
    {'name': '订单列表', 'href': 'order_list', 'perms': ['base']},
    {'name': '登录记录', 'href': 'login_log_list', 'perms': ['base']},
    {'name': '权限管理', 'href': 'perm_manager', 'perms': ['do_auth']},
    {'name': '充值配置', 'href': 'recharge_config', 'perms': ['do_auth']},
    {'name': '游戏配置', 'href': 'game_config', 'perms': ['do_auth']},
]


# 短信配置
REG_CODE = ''
SIGN = ''
ACCESS_KEY_ID = ""
ACCESS_KEY_SECRET = ""
DOMAIN = ""
SENDSMS = ''
REGION = ""

#oss
OSS_ACCESS_KET_ID = ""
OSS_ACCESS_KET_SECRET = ""
BUCKET_NAME = ''
ENDPOINT = ''
DEFAULT_HEAD = f'https://{BUCKET_NAME}.{ENDPOINT}/default_head.jpg'


try:
    from local_settings import *
except:
    pass
