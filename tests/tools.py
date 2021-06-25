
import asyncio
import logging

from models import Session

from liquid.models import User,GoldLog,Redpack,Grab
from liquid import gold_utils

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

def async_test(func):

    def wapper(*args,**kwargs):
        loop.run_until_complete(func(*args,**kwargs))
        pending = asyncio.Task.all_tasks()
        loop.run_until_complete(asyncio.gather(*pending))

    return wapper

def in_loop(func):

    def wapper(*args,**kwargs):
        logging.debug('run func')
        async_func = asyncio.coroutine(func)
        loop.run_until_complete(async_func(*args,**kwargs))
        pending = asyncio.Task.all_tasks()
        loop.run_until_complete(asyncio.gather(*pending))

    return wapper


def clean_users():
    session = Session()
    session.query(User).filter(User.user_id.startswith('900')).delete(synchronize_session=False)
    session.query(Redpack).filter(Redpack.user_id.startswith('90')).delete(synchronize_session=False)
    session.query(Grab).filter(Grab.user_id.startswith('90')).delete(synchronize_session=False)
    session.commit()


def setup_users():
    
    # 创建一个没有余额的用户,和一个余额足够的用户

    clean_users()

    session = Session()
    session.add(User(
        phone="13100000000",
        user_id='900000',
        nickname='余额不足',
        password='password',
        gold=0
    ))


    for i in range(30):
        phone = 13100000001 + i
        user_id = 900001 + i
        gold_utils.unfreeze_user_all(user_id)
        session.query(GoldLog).delete()
        session.add(User(
            phone=str(phone),
            user_id=str(user_id),
            nickname=f"很多钱{i}",
            password="password",
            gold=9999999,
        ))

    session.commit()