import uuid
import time
import asyncio
import logging
import traceback

from solid.redisCache import get_redis,get_aio_redis,get_redis_conn

from settings import APP_NAME,WS_CONN_KEY_EXPIRE


#WS_HANDLER = {}

async def check_online_connection(duration=10):
    """
    初始化清理残留链接信息
    维护在线用户列表。定时清除已断线的链接
    """
    
    redis_conn_key = f'{APP_NAME}:WS_CONN'
    redis = get_redis()

    while True:
        conn_key_list = redis.smembers(redis_conn_key)
        for key in conn_key_list:
            if not redis.exists(f'{APP_NAME}:WS_CONN:{key}'):
                redis.srem(redis_conn_key,key)

        await asyncio.sleep(duration)


def get_online_cache():
    """
    获取当前所有在线
    """
    redis = get_redis()
    redis_conn_key = f'{APP_NAME}:WS_CONN'
    conn_key_list = redis.smembers(redis_conn_key)

    for key in conn_key_list:
        yield redis.hgetall(f'{redis_conn_key}:{key}')


class WSConnMixin:

    user_cache:dict
    conn_key:str
    redis_conn_key:str
    is_connecting: bool
    is_auth: bool
    user_token: str

    ws_conn_prifix = f'{APP_NAME}:WS_CONN'

    async def _recv_respnose_chan(self,chan_name):
        # chan_redis = await get_aio_redis()
        # chan_name = f'chan:user:{self.user_cache["user_id"]}'
        async with get_redis_conn() as chan_redis:

            chan_list = await chan_redis.subscribe(chan_name) 
            chan = chan_list[0]
            # logging.info(f'建立监听用户频道:{chan_name}')

            while await chan.wait_message() and self.running and chan.is_active:
                try:
                    msg = await chan.get_json()
                    logging.debug(msg)
                    self.write_message(msg)
                except:
                    logging.error(traceback.format_exc())
                    continue

    def init_connection_cache(self):
        self.is_auth = False
        self.is_connecting = True
        self.conn_key = uuid.uuid1().hex
        self.redis_conn_key = f'{self.ws_conn_prifix}:{self.conn_key}'
        redis = get_redis()

        # 在线列表
        redis.sadd(self.ws_conn_prifix,self.conn_key)
        redis.hmset(self.redis_conn_key,
            {'start_time':time.time(),'last_check':time.time()}
            )
        redis.expire(self.redis_conn_key,WS_CONN_KEY_EXPIRE)

        asyncio.create_task(self.check_connecting())

    async def check_connecting(self):
        redis = get_redis()
        while self.is_connecting:
            redis.hset(self.redis_conn_key,'last_check',time.time())
            redis.expire(self.redis_conn_key,WS_CONN_KEY_EXPIRE)
            await asyncio.sleep(10)

        # 如果 self.is_connecting == False， 清理链接信息
        redis.delete(self.redis_conn_key)
        redis.srem(self.ws_conn_prifix,self.conn_key)
    
    def clear_connection(self):
        self.is_connecting = False

    def set_conn_val(self,**kwargs):
        redis = get_redis()
        for k,v in kwargs.items():
            redis.hset(self.redis_conn_key,k,v)

    def get_conn_val(self,*args):
        redis = get_redis()
        for arg in args:
            yield redis.hget(self.conn_key,arg)

    def del_conn_val(self,k):
        redis = get_redis()
        redis.hdel(self.redis_conn_key,k)

    def auth(self,token:str) -> bool:
        logging.debug(token)
        redis_cli = get_redis()
        user_info = redis_cli.hgetall(f'USER_INFO:{token}')
        logging.debug(user_info)
        if user_info:
            self.is_auth = True
            self.user_cache = user_info
            self.user_token = token

            redis_cli.hset(self.redis_conn_key,'user_token',token)
            redis_cli.hset(self.redis_conn_key,'user_id',user_info['user_id'])
            redis_cli.hset(self.redis_conn_key,'room_id',0)

            asyncio.create_task(self._recv_respnose_chan(f'chan:public'))
            asyncio.create_task(self._recv_respnose_chan(f'chan:user:{self.user_cache["user_id"]}'))

            logging.info('websocket connect recv')

        return self.is_auth


