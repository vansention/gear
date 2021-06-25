import asyncio
import logging

#from liquid import gold, frozen_gold
from liquid.redpack import get_niu,get_bao
from solid.log import init_log
from solid.redisCache import get_redis

init_log()

# def test_frozen():
    
#     redis = get_redis()
#     redis.delete(f'frozen_gold:user_id:000000')
        
#     frozen_gold.freeze_user_gold("000000",1,100)
#     frozen_gold.freeze_user_gold("000000",2,100)
#     frozen_gold.freeze_user_gold("000000",3,100)
#     frozen_gold.freeze_user_gold("000000",4,100)
#     frozen_gold.freeze_user_gold("000000",5,100)

#     gold_000000 = frozen_gold.get_user_frozen_gold("000000")
#     logging.debug(gold_000000)
#     assert gold_000000 == 500

#     frozen_gold.un_frozen_gold("000000",1)

#     assert frozen_gold.get_user_frozen_gold("000000") == 400

def test_niu():
    
    assert get_niu(231) == 6
    assert get_niu(445) == 3
    assert get_niu(999) == 7
    assert get_niu(668) == 10

def test_bao():
    
    assert get_bao(123) == 5
    assert get_bao(33) == 23
    assert get_bao(98) == 17 
