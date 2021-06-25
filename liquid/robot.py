
import asyncio
import random
import uuid
import json
import inspect
import traceback
import logging

import requests
from solid.sign import aes
import settings
from solid.redisCache import get_redis

logging.getLogger('asyncio').setLevel(logging.ERROR)
logging.getLogger('asyncio.coroutines').setLevel(logging.ERROR)
logging.getLogger('websockets.server').setLevel(logging.ERROR)
logging.getLogger('websockets.protocol').setLevel(logging.ERROR)
logging.getLogger('websockets.client').setLevel(logging.ERROR)
logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)


"""
机器人渠道 00 开头
测试用机器人渠道 000001 user_id [800000 - 809999]
业务用机器人渠道 000000 user_id [810000 - 819999]
"""


class Robot(object):

    def __init__(self,
                 phone,
                 password,
                 go_room: int = None,
                 send_prob: int = 30,
                 grab_prob: int = 10,
                 in_out_prob: int = 600,
                 max_send_amount: int = 20,
                 min_send_amount: int = 5,
                 http_url='http://127.0.0.1:8001/http/app/service',
                 ws_url='ws://127.0.0.1:8001/ws/app/service',
                 ):
        '''
        @send_prob n秒内发包
        @grab_prob 收到红包消息，概率抢包概率百分比 
        '''
        self.phone = phone
        self.password = password
        self.go_room = go_room
        self.send_prob = int(send_prob)
        self.grab_prob = int(grab_prob)
        self.in_out_prob = in_out_prob
        self.max_send_amount = max_send_amount
        self.min_send_amount = min_send_amount
        self.http_url = http_url
        self.ws_url = ws_url
        self.redis = get_redis()

        self.custom_room = {"game_name": "全部", "status": "open", "name": "全部",
                            "info": "普通场", "min": 10, "max": 100, "room_id": 4}

        self.room_dic = {
        }

    def _get_sv_name(self, game_id=None):

        # return "BAO"

        serv_dic = {
            1: 'NIU',
            2: 'BOOM',
            3: 'BAO'
        }

        return serv_dic.get(game_id, 'ONE')

    async def run(self):
        self.login()
        self.connect()

    def login(self):

        data = {'service': 'auth.robot_login', 'phone': self.phone, 'password': self.password, 'token': '', 'device': f'robot-phone', 'channel': '999999'}
        aes_data = aes.encrypt_cbc(json.dumps(
            data), settings.AESKEY, settings.AESIV)
        resp = requests.post(self.http_url, aes_data)
        try:
            resp_text = json.loads(
                aes.decrypt_cbc(
                    json.loads(resp.text).get(
                        'data'), settings.AESKEY, settings.AESIV
                )
            )
            self.token = resp_text['token']
            self.nickname = resp_text['nickname']
            self.user_id = resp_text['userId']
        except:
            print(traceback.format_exc())
            raise
        print(self.token)

    async def enter_room_random(self):

        self.room = random.choice(list(self.room_dic.values()))
        await self.enter_room(self.room['room_id'])

    async def enter_room(self, room_id):
        await self.send_msg('GAME.ENTER_ROOM', {'roomId': room_id})

    async def out_room(self):
        await self.send_msg('GAME.OUT_ROOM', {'roomId': self.room['room_id']})
        self.room = None

    async def send_msg(self, service_name: str, data: dict):
        msg_id = uuid.uuid1().hex
        app_msg = {'service': service_name, 'data': {},
                   'userToken': self.token, 'msgId': msg_id}
        logging.info(self.token)
        key = f'USER_INFO:{self.token}'
        user_cache = self.redis.hgetall(key)
        user_id = user_cache['user_id']
        key = self.redis.get(f"aes_key:{user_id}")
        iv = self.redis.get(f"aes_iv:{user_id}")
        if data:
            app_msg['data'] = aes.encrypt_cbc(
                json.dumps(data), key, iv).decode("utf-8")
        app_msg = json.dumps(app_msg)
        await self.ws_conn.send(app_msg)

    async def connect(self):
        self.ws_conn = await websockets.connect(self.ws_url)
        data = {'service': 'CONN_AUTH', 'userToken': self.token}
        await self.ws_conn.send(json.dumps(data))
        asyncio.create_task(self.recv())

        await asyncio.sleep(1)
        await self.send_msg('AUTH.SYNC_USER_INFO', {})
        await asyncio.sleep(2)

        if self.go_room:
            self.room = self.room_dic.get(self.go_room, {})
            # await self.enter_room(self.room['room_id'])

            await self.enter_room(self.go_room)
        else:
            await self.enter_room_random()

        if self.send_prob > 0:
            asyncio.create_task(self.send_redpack())

    async def send_redpack(self):

        while True:

            sleep = random.randrange(0, self.send_prob)
            await asyncio.sleep(sleep)

            amount = 100 * \
                random.randrange(self.min_send_amount, self.max_send_amount)
            # boom_count = random.randrange(1, 4)
            booms = random.sample(range(9), 1)

            is_multi = False
            # serv = self.room['serv']
            serv = self._get_sv_name()

            if not self.room.get('game_id'):
                self.room['game_id'] = random.choice([1, 2, 3])

            print(f'{self.nickname} 发红包 {amount}')
            await self.send_msg(f'GAME_{serv}.SEND_REDPACK', {
                'gameId': self.room['game_id'],
                'roomId': self.go_room,
                # 'grabUserIdList':[],
                'gold': amount,
                'booms': booms,
                'isMultiBoom': is_multi,
                'pkgCount': 9,
                'userId': self.user_id,
                'nickname': self.nickname,
            })

    async def recv(self):

        SERV_DIC = {
            'AUTH.SYNC_USER_INFO': self.sync_user_info,
            'GAME.NEW_REDPACK': self.on_new_redpack,
        }

        while True:

            msg = await self.ws_conn.recv()
            msg = json.loads(msg)
            logging.info(msg)
            key = f'USER_INFO:{self.token}'
            user_cache = self.redis.hgetall(key)
            user_id = user_cache['user_id']
            key = self.redis.get(f"aes_key:{user_id}")
            iv = self.redis.get(f"aes_iv:{user_id}")
            msg = json.loads(
                aes.decrypt_cbc(msg.get('data'), key, iv)
            )
            service_name = msg.get('service')
            func = SERV_DIC.get(service_name, self.do_default)
            is_async = inspect.iscoroutinefunction(func)
            if is_async:
                await func(msg)
            else:
                func(msg)

    def do_default(self, msg):
        pass

    async def _grab(self, redpack):
        delay = random.randrange(0, 20)
        print(f'{self.nickname}决定{delay}秒后抢')
        await asyncio.sleep(delay)

        # print(redpack)

        data = {
            'userId': self.user_id,
            'redpackId': redpack['id']
        }

        game_id = redpack['gameId']
        sv = self._get_sv_name(game_id)

        print(f'{self.nickname} 抢红包')
        serv = f'GAME_{sv}'
        await self.send_msg(f'{serv}.GRAB_REDPACK', data)

    async def on_new_redpack(self, msg):
        # print(f'new redpack {msg}')
        rp = msg['data']['redpack']
        # 决定是否抢
        print(msg)
        if self.grab_prob >= random.randrange(0, 100):
            asyncio.create_task(self._grab(rp))

    def sync_user_info(self, msg):
        self.user_id = msg['data']['userId']
        self.nickname = msg['data']['nickname']
        self.gold = msg['data']['gold']
        self.head = msg['data']['head']

    async def start(self):
        delay = random.randint(1000, 5000)/1000
        await asyncio.sleep(delay)
        self.login()
        await self.connect()
