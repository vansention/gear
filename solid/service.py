
import json
import logging
import asyncio
import pdb
import inspect
import traceback
import types
import uuid
import time

from bson import json_util
from tornado.util import import_object
from tornado.websocket import WebSocketHandler
from bson.objectid import ObjectId

from solid.mongo import Mongo
from solid.redisCache import get_redis
from solid.format import u2h_dic,h2u_dic
from solid import Singleton

from models import Session,get_session


class Context(object):
    pass


class MockService(object):

    def __init__(self,**kwargs):
        for k,v in kwargs.items():
            setattr(self,k,v)

class BaseService(object):

    def __init__(self,handler,name,**kwargs):

        '''
        TODO: 需要优化为只import一次service func
        '''
        self.kwargs = kwargs
        mod_name,func_name = name.split('.')
        self.service_func = import_object(f'services.{mod_name}.{func_name}')

        self.mongo = Mongo.instance().client
        self.handler = handler
        #self.session = Session()
        #self.redis = self.handler.current_redis
        

    def api_encode_wapper(self,func):
        def _(obj,*args,**kwargs):
            if isinstance(obj,ObjectId):
                return str(obj)
    
            return func(obj,*args,**kwargs)
        return _

class AppService(BaseService):

    def check_auth(self) -> (bool, dict):
        redis = get_redis()
        NO_TOKEN_API_TUPLE = ('auth.login', 'auth.register', 'auth.send_code','auth.robot_login','auth.get_wx_user_info','auth.wx_login','auth.device_login')

        if not self.data.get('service'):
            return False, {'status':'error','message':'格式错误'}

        if self.data.get('service') in NO_TOKEN_API_TUPLE:
            return True,{}

        token = self.data.get('token')
        if not token:
            return False, {'status':'error','message':'非法数据'}

        key = f'USER_INFO:{token}'
        self.user_cache = redis.hgetall(key)
        self.user_cache['token'] = token
        logging.info(self.user_cache)
        return True,{}

    def serv(self,data):
        self.data = data
        redis = get_redis()
        is_auth,info = self.check_auth()
        if not is_auth:
            return info
        service = data.get('service')
        del data['service']
        del data['token']
        
        logging.debug(data)
        data = h2u_dic(data)
        
        with get_session() as session:
            self.session = session
            try:
                ret = self.service_func(self, **data)
            except:
                logging.error(traceback.format_exc())
                ret = {'status': 'error', 'message': '接口错误'}

        ret = u2h_dic(ret)
        if 'status' not in ret: ret['status'] = 'success'
        logging.info(service)
        if service in ['auth.wx_login','auth.login',"auth.robot_login","auth.device_login"]:
            # user_id = ret.get("userId")
            if redis.exists(f'aes_key:{ret["userId"]}') or redis.exists(f'aes_iv:{ret["userId"]}'):
                redis.delete(f'aes_key:{ret["userId"]}')
                redis.delete(f'aes_iv:{ret["userId"]}')
            aes_key = uuid.uuid1().hex[0:16]
            aes_iv = uuid.uuid1().hex[0:16]
            ret['aesKey'] = aes_key
            ret['aesIv'] = aes_iv
            redis.set(f'aes_key:{ret["userId"]}',aes_key)
            redis.set(f'aes_iv:{ret["userId"]}',aes_iv)
        return json.dumps(ret,default=self.api_encode_wapper(json_util.default))
    def get_user_cache(self):
        
        return self.user_cache


class WebService(BaseService):
    pass


class WebSocketService(BaseService):

    handler: WebSocketHandler

    def check_auth(self):
        token = self.data['userToken']
        redis = get_redis()
        key = f'USER_INFO:{token}'
        user = redis.hgetall(key)
        if not user:
            return False
        self.user_cache = user
        return True
 

    async def serv(self,data):
        self.data = data
        if not self.check_auth():
            data['status'] = 'error'
            data['error_msg'] = '非法用户'
            return json.dumps(data)
        self.msg_id = data['msgId']
        self.service_name = data['service']
        del data['msgId']
        del data['service']
        data = h2u_dic(data)
        with get_session() as session:
            self.session = session
            is_async = inspect.iscoroutinefunction(self.service_func)
            if is_async:
                ret = await self.service_func(self,**data['data'])
            else:
                ret = self.service_func(self,**data['data'])

        if not ret:
            return
        ret = u2h_dic(ret)
        resp = {'data':ret,'service':self.service_name,'msgId':self.msg_id}
        return json.dumps(resp,default=self.api_encode_wapper(json_util.default))

    def get_user_cache(self):
        
        return self.handler.user_cache

    def send_msg(self,msg:dict):
        '''
        给客户端发送 websocket消息
        '''
        msg['msgId'] = uuid.uuid1().hex
        msg['ctime'] = time.time()
        msg = u2h_dic(msg)
        msg_json = json.dumps(msg,default=self.api_encode_wapper(json_util.default))
        logging.debug(msg_json)
        self.handler.write_message(msg_json)

ws_message_filter_dic = {}


def ws_message_filter(handler:WebSocketHandler,
    filter_name:str,
    message:dict):
    
    user_id = handler.user_cache['user_id']
    filter_func = ws_message_filter_dic.get(filter_name)
    if not filter_func:
        module_name = f'services.{filter_name}'
        try:
            filter_func = import_object(module_name)
        except ImportError:
            raise Exception(f'no ws message filter {filter_name}')

        ws_message_filter_dic[filter_name] = filter_func

    return filter_func(handler,user_id,message)
