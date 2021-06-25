


import asyncio
import json
import traceback
import uuid
import random
import inspect
import pdb
import logging

import requests
import pytz
import pymongo

import websockets

from models import Session
from liquid.models import User,Redpack,Grab,GoldLog
from liquid.robot import Robot
from liquid import config
from solid import init_log

#init_log()


client = pymongo.MongoClient('mongodb://127.0.0.1:27017/?tz_aware=true&readPreference=secondaryPreferred',tzinfo=pytz.timezone('Asia/Shanghai'))
db = client['redpack']

NUM = 5

WS_URL = 'ws://127.0.0.1:8001/ws/app/service'
HTTP_URL = 'http://127.0.0.1:8001/http/app/service'

def init_robots(num:int,session=None):
    print('init robots')
    for n in range(num):

        userid = str(800000+n)
        phone = str(19900000000+n)
        user = User(
            user_id=userid,
            phone=phone,
            head='/assets/img/wx_head.jpeg',
            nickname = f'测试机器人_{n}',
            gold = 80000000,
            password ='11111111',
            channel="000001",
            is_robot = True
        )
        session.add(user)
        print('add user')

async def setup_new_data():
    

    session = Session()
    session.query(GoldLog).filter().delete()
    session.query(Grab).filter().delete()
    session.query(Redpack).filter().delete()
    session.query(User).filter(User.is_robot==True,User.channel=='000001').delete()
    #session.delete(users)
    session.commit()
    #return

    init_robots(200,session=session)
    session.commit()

    go_room = 3
    for i in range(100):
        phone = 19900000000 + i
        #await asyncio.sleep(0.2)
        asyncio.create_task(
            Robot(phone=str(phone),
                password="11111111",
                go_room=go_room,
                max_send_amount=50,
                min_send_amount=10,
                send_prob=300,
                grab_prob=100)\
            .start()) 

    for i in range(100):
        phone = 19900000100 + i
        #await asyncio.sleep(0.2)
        asyncio.create_task(
            Robot(phone=str(phone),
                password="11111111",
                go_room=go_room,
                max_send_amount=50,
                min_send_amount=10,
                send_prob=300,
                grab_prob=0)\
            .start())


def test_robots():
    asyncio.get_event_loop().run_until_complete(setup_new_data())
    asyncio.get_event_loop().run_forever()

