import logging
from solid.log import init_log

from models import Session

from liquid.models import User,Redpack,Grab

init_log()

def test_cache():

    session = Session()

    session.query(User).filter(User.user_id=='00000a').delete()
    session.commit()

    user = User(
            user_id='00000a',
            phone='1300000000a',
            head='/assets/img/wx_head.jpeg',
            nickname = f'测试用例A',
            gold = 80000000,
            password ='11111111',
            is_robot = False
        )

    session.add(user)
    session.commit()

    cache_data = User.cache.get('00000a')
    logging.debug(cache_data)
    assert cache_data['gold'] == 80000000
    cache_gold = User.cache.get_val('00000a','gold')
    
    assert cache_gold == 80000000


def test_set_cache_val():
    
    session = Session()
    user = session.query(User).filter().first()
    user.set_ext_cache(test=1)

    test_cache = User.cache.get_ext_cache(user.user_id,'test')
    logging.debug(test_cache)
    assert test_cache == 1

    #user.set_cache_val(some='some')

