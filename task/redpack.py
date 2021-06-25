import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)
import logging
import json
import pdb
import uuid
import pdb
import time
import traceback
from datetime import datetime,timedelta
import asyncio
from functools import reduce
from tornado.util import import_object
import pymongo

import pymongo

from solid.redisCache import get_redis_conn,get_redis
from solid.service import MockService

from liquid import gold_utils
from liquid import config
from liquid.models import Redpack,Grab,GoldLog,User
from models import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler

setttle = {
    1:'game_niu',
    2:'game_boom',
    3:'game_bao'
}

def unfreeze():
    session = Session()
    redis = get_redis()
    key_list = redis.keys("frozen_gold:user_id:*")
    user_id_list = [ key.split(":")[-1] for key in key_list]
    user_query = session.query(User).filter(User.user_id.in_(user_id_list))

    users = user_query.all()
    for user in users:
        user_data = user.toDic()
        info = redis.hgetall(f'frozen_gold:user_id:{user.user_id}')
        for k,v in info.items():
            redpack_id = k[k.index(':')+1:]
            redpack = session.query(Redpack).filter(Redpack.status=='settled',Redpack.id==redpack_id).first()
            if redpack:
                gold_utils.unfreeze_user_gold(user.user_id,redpack.id)

async def setttled():
    # await asyncio.sleep(60)
    session = Session()
    redpack_list = session.query(Redpack).filter(Redpack.status!='settled').all()
    for redpack in redpack_list:
        if int((redpack.end_time - datetime.today()).total_seconds())< 0:
            print(redpack.id)
            module = f'services.{setttle[redpack.game_id]}.redpack_settle'
            redpack_settle = import_object(module)
            asyncio.create_task(redpack_settle(redpack.id,0))

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    scheduler = AsyncIOScheduler(event_loop=loop)
    scheduler.add_job(setttled, 'interval', seconds=2, id='setttled')
    scheduler.start()
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass