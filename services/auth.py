
import re
import uuid
import logging
import random
import string
import time
import os
import base64
import traceback
import requests
from datetime import datetime
from solid.oss import download_file,upload_file
from liquid import config
import json
import urllib
import settings
from solid.redisCache import get_redis
from solid.utils.sms import send_message
from solid.utils.log import log_register, log_login
from liquid.models import User



def robot_login(service,phone:str,password:str,**kwargs):
    session = service.session
    redis = get_redis()
    user = session.query(User)\
        .filter(User.phone==phone,
            User.password==password,
            User.is_robot==True)\
        .one()
    token = uuid.uuid1().hex
    key = f'USER_INFO:{token}'
    redis.hset(key,'phone',phone)
    redis.hset(key,'user_id',user.user_id)
    redis.hset(key,'login_time',time.time())
    redis.expire(key,settings.APP_AUTH_TOKEN_EXPIRE)
    user.last_time = datetime.today()
    # log_login(service, user.user_id, user.nickname, channel, ctime, ip, device, True,user.union_id)
    session.commit()
    return {'token':token,'userId':user.user_id,'nickname':user.nickname}


def login(service,phone:str,checkcode:str,channel:str="000000",device:str=None):

    session = service.session
    ctime = datetime.today()
    redis = get_redis()
    cache_code = redis.get(f'login_code-login-{phone}')
    logging.debug(cache_code)
    if not cache_code == checkcode:
        redis.delete(f'login_code-login-{phone}')
        return {'status':'error','error_msg':'验证码错误'}

    try:
        user = session.query(User).filter(User.phone==phone).one()
    except:
        logging.warning(traceback.format_exc())
        user = None
        #return {'status':'error','error_msg':'用户不存在或密码错误'}
    ip = service.kwargs['ip']
    if user:
        token = uuid.uuid1().hex
        key = f'USER_INFO:{token}'
        redis.hset(key,'phone',phone)
        redis.hset(key,'user_id',user.user_id)
        redis.hset(key,'login_time',time.time())

        redis.expire(key,settings.APP_AUTH_TOKEN_EXPIRE)
        user.last_time = datetime.today()
        log_login(service, user.user_id, user.nickname, channel, ctime, ip, device, True,user.union_id)
        session.commit()
        return {'token':token,'userId':user.user_id,'nickname':user.nickname,'head':user.head}
    else:
        logging.info('new user')
        #return {'status':'error','error_msg':'用户不存在或密码错误'}
        user_list = session.query(UserList).filter(UserList.used==False).first()
        user_id = user_list.user_id
        user_list.used = True
        nickname = f'新用户{user_id}'
        user = User(
            user_id=user_id,
            gold=500,
            phone=phone,
            password="password",
            nickname=nickname,
            channel=channel,
            device=device,
            union_id='')
        session.add(user)
        logging.info(user)
        token = uuid.uuid1().hex
        key = f'USER_INFO:{token}'
        redis.hset(key, 'phone', phone)
        redis.hset(key, 'user_id', user_id)
        redis.expire(key, settings.APP_AUTH_TOKEN_EXPIRE)
        log_register(service, user_id, nickname, channel, ctime, ip, device, True,user.union_id)
        #redis.delete(f'register_code', f'register-{phone}')
        if redis.exists(f'login_code-login-{phone}'):
            redis.delete(f'login_code-login-{phone}')
        session.commit()
        #return {'token': token}
        return {'token':token,'userId':user.user_id,'nickname':user.nickname,'head':user.head}
    


def device_login(service,channel:str="000000",device:str=None):

    session = service.session
    ctime = datetime.today()
    redis = get_redis()
    user = session.query(User).filter(User.device==device).first()
    ip = service.kwargs['ip']
    if user:
        token = uuid.uuid1().hex
        key = f'USER_INFO:{token}'
        redis.hset(key,'phone',user.phone)
        redis.hset(key,'user_id',user.user_id)
        redis.hset(key,'login_time',time.time())

        redis.expire(key,settings.APP_AUTH_TOKEN_EXPIRE)
        user.last_time = datetime.today()
        log_login(service, user.user_id, user.nickname, channel, ctime, ip, device, True,user.union_id)
        session.commit()
        return {'token':token,'userId':user.user_id,'nickname':user.nickname,'head':user.head}
    else:
        logging.info('new user')
        #return {'status':'error','error_msg':'用户不存在或密码错误'}
        user_list = session.query(UserList).filter(UserList.used==False).first()
        user_id = user_list.user_id
        user_list.used = True
        nickname = f'新用户{user_id}'
        user = User(
            user_id=user_id,
            gold=500,
            phone=f'phone_{user_id}',
            password="password",
            nickname=nickname,
            channel=channel,
            device=device,
            union_id='')
        session.add(user)
        logging.info(user)
        token = uuid.uuid1().hex
        key = f'USER_INFO:{token}'
        redis.hset(key, 'phone', f'phone_{user_id}')
        redis.hset(key, 'user_id', user_id)
        redis.expire(key, settings.APP_AUTH_TOKEN_EXPIRE)
        log_register(service, user_id, nickname, channel, ctime, ip, device, True,user.union_id)
        session.commit()
        #return {'token': token}
        return {'token':token,'userId':user.user_id,'nickname':user.nickname,'head':user.head}


def wx_login(service,union_id:str,head:str,channel:str,device:str,nickname:str):
    session = service.session
    user = session.query(User).filter(User.union_id==union_id).first()
    redis = get_redis()
    ctime = datetime.today()
    ip = service.kwargs['ip']
    if user:
        # 登陆
        token = uuid.uuid1().hex
        key = f'USER_INFO:{token}'
        redis.hset(key,'phone',user.phone)
        redis.hset(key,'user_id',user.user_id)
        redis.hset(key,'login_time',time.time())
        #redis.hset(key,'avail_gold',user.get_gold())

        redis.expire(key,settings.APP_AUTH_TOKEN_EXPIRE)
        user.last_time = datetime.today()
        log_login(service, user.user_id, nickname, channel, ctime, ip, device, True,union_id)
        session.commit()
        return {'token':token,'userId':user.user_id,'nickname':user.nickname,'head':user.head}
    else:
        # 注册
        user_list = session.query(UserList).filter(UserList.used==False).first()
        user_id = user_list.user_id
        user_list.used = True
        filename = f'{user_id}_head.jpg'  # I assume you have a way of picking unique filenames
        path = f'{settings.UPLOAD_PATH}/{filename}'
        urllib.request.urlretrieve(head,path)
        upload_file(path,filename)
        head_url = f'https://{settings.BUCKET_NAME}.{settings.ENDPOINT}/{filename}'
        user = User(user_id=user_id,union_id=union_id,phone=f'phone_{user_id}',password="password",nickname=nickname,channel=channel,device=device,head=head_url,gold=500)
        session.add(user)
        logging.info(user)
        if user:
            token = uuid.uuid1().hex
            redis = get_redis()
            key = f'USER_INFO:{token}'
            redis.hset(key, 'phone', user.phone)
            redis.hset(key, 'user_id', user_id)
            redis.expire(key, settings.APP_AUTH_TOKEN_EXPIRE)
            log_register(service, user_id, nickname, channel, ctime, ip, device, True,union_id)
            session.commit()
            return {'token':token,'userId':user.user_id,'nickname':user.nickname,'head':head_url}
        else:
            log_register(service, user_id, nickname, channel, ctime, ip, device, False,union_id)
            return {'status': 'error', 'error_msg': '用户注册失败'}

def sync_user_info(service,data=None):
    
    user_cache = User.cache.get(service.user_cache.get('user_id'))
    # logging.debug(user_cache)
    del user_cache['password']
    del user_cache['gold']
    user_cache['gold'] = gold_utils.get_user_avail_gold(service.user_cache.get('user_id'))
    phone = user_cache.get('phone')
    user_id = user_cache.get('user_id')
    if phone == f'phone_{user_id}':
        user_cache['phone'] = ''
    return user_cache

def get_status(service,data=None):
    user_cache = User.cache.get(service.user_cache.get('user_id'))
    del user_cache['password']
    del user_cache['gold']
    user_cache['award'] = config.AWARD_GOLD
    return user_cache

def user_head(service,user_id:str) -> str:

    user_head = User.cache.get_val(user_id,'head')
    return user_head

def view_page(service,page_name):
    pass

def send_code(service, phone, api):
    # breakpoint()
    code = ''.join(random.choices(string.digits, k=4))
    redis = get_redis()
    redis.set(f'{api}_code-{api}-{phone}', code,ex=config.CHECKCODE_EXPIRE)
    logging.debug(f'{api}-{phone}-{code}')
    ret = 'error'
    if not settings.DEBUG:
        ret = send_message(phone, code)
    else:
        ret = 'success'
    if ret == 'success':
        return {'status': 'success', 'message': '发送成功'}
    else:
        return {'status': 'error', 'message': '发送失败'}
    
    
def register(service,phone:str,password:str,checkcode:str,channel:str,device:str):
    phone_fmt = re.compile('^1\d{10}$')
    session = service.session
    if not re.match(phone_fmt, phone):
        return {'status': 'error', 'error_msg': '手机号格式错误'}
    ctime = datetime.today()
    redis = get_redis()
    re_code = redis.get(f'register_code-register-{phone}')
    ip = service.kwargs['ip']
    user = session.query(User).filter(User.phone==phone).first()
    
    if not re_code == checkcode:
        #log_register(service, None, None, channel, ctime, ip, device, False,'')
        return {'status': 'error', 'error_msg': '验证码输入错误'}
    if not user:
        user_id = redis.spop('REDPACK:USER_ID_LIST')
        nickname = f'新用户{user_id}'
        user = User(user_id=user_id,phone=phone,password="password",nickname=nickname,channel=channel,device=device)
        session.add(user)
        logging.info(user)
        if user:
            token = uuid.uuid1().hex
            redis = get_redis()
            key = f'USER_INFO:{token}'
            redis.hset(key, 'phone', phone)
            redis.hset(key, 'user_id', user_id)
            redis.expire(key, settings.APP_AUTH_TOKEN_EXPIRE)
            log_register(service, user_id, nickname, channel, ctime, ip, device, True,user.union_id)
            if redis.exists(f'register_code-register-{phone}'):
                redis.delete(f'register_code-register-{phone}')
            session.commit()
            return {'token': token}
    else:
        if redis.exists(f'register_code-register-{phone}'):
            redis.delete(f'register_code-register-{phone}')
        log_register(service, user.user_id, user.nickname, channel, ctime, ip, device, False,'')
        return {'status': 'error', 'error_msg': '用户注册失败'}
        
def get_wx_user_info(service,code:str):
    resp = requests.get(f'https://api.weixin.qq.com/sns/oauth2/access_token?appid={settings.WX_APPID}&secret={settings.WX_SECRET}&code={code}&grant_type=authorization_code')
    info = json.loads(resp.text)
    openid = info.get('openid')
    access_token = info.get('access_token')
    if openid:
        res = requests.get(f'https://api.weixin.qq.com/sns/userinfo?access_token={access_token}&openid={openid}')
        data = json.loads(res.text)
        ret = {
            'status':'success',
            'nickname':data.get('nickname').encode('l1').decode('utf8'),
            'unionid':data.get('unionid'),
            'head':data.get('headimgurl')
        }
        return ret
    else:
        return {'status': 'error', 'message': '请求失败'}
