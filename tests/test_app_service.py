

import logging
import asyncio

import pymongo
from nose import with_setup

#from liquid.models import Redpack,Grab
from solid import mongo
from solid.log import init_log

from models import Session
from services import game_niu,game_boom,game_bao
from liquid.models import Redpack,Grab,User
from liquid import config
from liquid import gold_utils

from .tools import async_test,setup_users,clean_users,in_loop

init_log()

redpack_id_list = []


class MockService:
    
    pass

@with_setup(setup_users,clean_users)
@in_loop
def test_send_redpack_niu():

    service = MockService()
    service.session = Session()
    logging.debug(gold_utils.get_user_frozen_gold('900001'))

    # 验证缓存初始化
    assert gold_utils.get_user_frozen_gold("900001") == 0

    #余额不足
    ret = game_niu.send_redpack(service,'900000','测试脚本',9800,1,3)
    assert ret is None

    #余额足够
    ret = game_niu.send_redpack(service,'900001','测试脚本',9800,1,3)
    logging.debug(ret)

    # 数据是否插入
    grab = service.session.query(Grab).filter(Grab.user_id=="900001",Grab.redpack_id==ret['id']).one()

    logging.debug(grab.toDic())
    assert '900001' in ret['grab_user_id_list']
    assert ret['gold'] == 9800

    # 冻结逻辑
    logging.debug(gold_utils.get_user_frozen_gold('900001'))
    assert gold_utils.get_user_frozen_gold('900001') == 9800 * 8 * 2

@with_setup(setup_users,clean_users)
@in_loop
def test_grab_redpack_niu():
    
    # 余额不足
    service = MockService()
    service.session = Session()

    game_niu.send_redpack(service,'900002','很多钱',9800,1,3)

    redpack = service.session.query(Redpack)\
        .filter(Redpack.status=='created',Redpack.user_id=='900002')\
        .order_by(Redpack.id.desc()).first()

    #breakpoint()
    ret = game_niu.grab_redpack(service,redpack_id=redpack.id,
            user_id="900000",
            nickname="没钱",
            game_id=redpack.game_id,
            room_id=redpack.room_id)
    assert ret is None

    
    # 余额足够，已抢。
    logging.debug('测试余额足够的正常流程')
    ret = game_niu.grab_redpack(service,redpack_id=redpack.id,
        user_id="900001",
        nickname="有钱",
        game_id=redpack.game_id,
        room_id=redpack.room_id)

    logging.debug(ret)
    assert ret['grab_status'] == 1
    assert ret['niu'] >= 0
    assert ret['grab_gold'] > 0
    assert ret['frozen_gold'] > 0

    logging.debug("把红包抢完")

    logging.debug("测试000000用户发包")

    rp_data = game_niu.send_redpack(service,'000000','sam',1000,1,3)

    for i in range(20):
        user_id = 900002 + i
        grab_data = game_niu.grab_redpack(service,redpack_id=rp_data['id'],
            user_id=str(user_id),
            nickname=f"有钱{user_id}",
            game_id=redpack.game_id,
            room_id=redpack.room_id)
        
        if i < 8:
            assert grab_data['grab_status'] == 1
            assert grab_data['niu'] != None
        else:
            assert grab_data is None

@async_test
async def test_settle_redpack():
    
    # niu
    session = Session()
    redpack = session.query(Redpack).filter(Redpack.status=='settled').order_by(Redpack.id.desc()).first()
    logging.debug(redpack.toDic())
    logging.debug([grab.toDic() for grab in redpack.grab_list])
    assert len(redpack.grab_list) == 9


@with_setup(setup_users,clean_users)
@in_loop
async def test_send_redpack_boom():
    
    service = MockService()
    service.session = Session()
  
    logging.debug("单雷测试")

    #user_00 = service.session.query(User).filter(User.user_id=='900000').one()
    user_01 = service.session.query(User).filter(User.user_id=='900001').one()
    #breakpoint()
    start_gold = gold_utils.get_user_avail_gold('900001')

    #余额不足
    ret = game_boom.send_redpack(service,'900000','测试脚本',9800,2,1,[1],False)
    assert ret is None

    #余额足够
    ret = game_boom.send_redpack(service,'900001','测试脚本',9800,2,1,[1],False)
    logging.debug(ret)

    service.session.refresh(user_01)

    assert ret['gold'] == 9800
    assert start_gold - ret['gold'] == gold_utils.get_user_avail_gold("900001")

    logging.debug("多雷测试")
    ret = game_boom.send_redpack(service,'900001','测试脚本',9800,2,1,[1,2,3],True)
    logging.debug(ret)
    #breakpoint()


@with_setup(setup_users,clean_users)
@in_loop
async def test_grab_redpack_boom():
    
    service = MockService()
    service.session = Session()

    logging.debug("抢单雷")
    send_ret = game_boom.send_redpack(service,'000000','sam',9800,2,1,[1],False)

    for i in range(20):
        user_id = str(900002 + i)
        grab_ret = game_boom.grab_redpack(service,
            user_id=user_id,
            nickname=f"有钱{user_id}",
            redpack_id=send_ret['id'],
            game_id=send_ret['game_id'],
            room_id=send_ret['room_id'])

        if grab_ret is not None and grab_ret['is_hit_boom'] and grab_ret['grab_status'] == 1:

            assert grab_ret['frozen_gold'] > 0


@with_setup(setup_users,clean_users)
@async_test
async def test_grab_multi_boom():
    
    service = MockService()
    service.session = Session()

    logging.debug("抢单雷")
    send_ret = game_boom.send_redpack(service,'000000','sam',9800,2,1,[1,2,3],True)

    for i in range(20):
        user_id = 900002 + i
        grab_ret = game_boom.grab_redpack(service,
            user_id=user_id,
            nickname=f"有钱{user_id}",
            redpack_id=send_ret['id'],
            game_id=send_ret['game_id'],
            room_id=send_ret['room_id'])

        if grab_ret['is_hit_boom'] and grab_ret['grab_status'] == 1:

            assert grab_ret['boom_gold'] > 0


@with_setup(setup_users,clean_users)
@in_loop
def test_send_redpack_bao():

    service = MockService()
    service.session = Session()
    logging.debug(gold_utils.get_user_frozen_gold('900001'))

    # 验证缓存初始化
    assert gold_utils.get_user_frozen_gold("900001") == 0

    #余额不足
    ret = game_bao.send_redpack(service,user_id='900000',gold=88,pkg_count=4,game_id=3,room_id=4)
    logging.debug(ret)
    assert ret.get('send_error') != None

    #余额足够
    #ret = game_niu.send_redpack(service,'900001','测试脚本',9800,1,3)
    ret = game_bao.send_redpack(service,user_id='900001',gold=88,pkg_count=4,game_id=3,room_id=4)
    logging.debug(ret)

    # 数据是否插入
    grab = service.session.query(Grab).filter(Grab.user_id=="900001",Grab.redpack_id==ret['id']).one()

    logging.debug(grab.toDic())
    assert '900001' in ret['grab_user_id_list']
    assert ret['gold'] == 9800

    # # 冻结逻辑
    # logging.debug(gold_utils.get_user_frozen_gold('900001'))
    # assert gold_utils.get_user_frozen_gold('900001') == 9800 * 8 * 2