import os
import base64
import random
import asyncio
import logging
import uuid
import json

from solid.redisCache import get_redis
from solid.oss import upload_file
from liquid.models import User
from models import Session

import settings

from liquid.models import User
from liquid.robot import Robot
from liquid import config



HEAD_PATH = '/tmp/heads'    # 初始化的头像文件夹在 assets/head

def set_head_cache(key,path):
    '''
    设置头像缓存
    '''
    with open(path,'rb') as fd:
        buff = fd.read()
        b64img = base64.b64encode(buff).decode('utf-8')
        redis_cli = get_redis()
        redis_cli.hset(f'{settings.APP_NAME}:HEAD',key,b64img)

def create_all(**kwargs):
    """
    初始化机器人头像
    """
    head_path = '/Users/sam/Documents/work/redpack/src/assets/heads/'
    path_list = os.listdir(head_path)
    redis = get_redis()
    session = Session()
    logging.debug(path_list)
    for path in path_list:
        if not '.jpg' in path:
            continue
        
        nickname = path.split('.')[0]
        full_path = os.path.join(head_path,path)
        logging.debug(full_path)

        user_id = redis.spop(f'{settings.APP_NAME}:USER_ID_LIST')
        key = uuid.uuid1().hex
        head_url = f'https://{settings.BUCKET_NAME}.{settings.ENDPOINT}/{key}.jpg'
        logging.debug(head_url)
        upload_file(full_path,f'{key}.jpg')

        user = User(
            phone=f"14000{user_id}",
            password=f'password_{user_id}',
            user_id=user_id,
            nickname=nickname,
            gold=1000,
            head=head_url,
            channel='000000',
            device='robot',   
            is_robot=True
        )
        session.add(user)
    
    session.commit()

async def run(num=10,
    go_room=0,
    send_prob=100,
    grab_prob=100):

    room_choices = [ i['id'] for i in config.ROOM_INIT]

    print('run robot')
    go_room = int(go_room)
    session = Session()
    robots = session.query(User).filter(User.is_robot==True,User.channel=='000000',User.phone.startswith('14'))\
        .order_by(User.gold.desc())\
        .limit(num).all()
    logging.info(robots)
    for robot in robots:

        if go_room == 0:
            robot_go_room = random.choice(room_choices)
            logging.debug(robot_go_room)
        else:
            robot_go_room = go_room

        logging.info(f'start robot [{robot.nickname}]')
        asyncio.create_task(
            Robot(phone=robot.phone,
                password=robot.password,
                go_room=robot_go_room,
                max_send_amount=100,
                min_send_amount=30,
                send_prob=send_prob,
                grab_prob=grab_prob)\
            .start()
        )

def landingJS(num=100,output=None):

    session = Session()
    queryset = session.query(User).filter(User.is_robot==True,User.channel=='000000',User.phone.startswith('14'))\
        .order_by(User.gold.desc())\
        .limit(num).all()

    users = [q.toDic(exclude=['password','alipay','phone']) for q in queryset]
    out_str = json.dumps(users,indent=4, sort_keys=True)
    if output:
        open(output,'w').write(out_str)

def update_gold(gold=1000):
    session = Session()
    robots = session.query(User).filter(User.is_robot==True,User.channel=='000000',User.phone.startswith('14')).all()
    for robot in robots:
        robot.frozen_gold = 0
        robot.gold = gold
    session.commit()
    session.close()