
import asyncio
import logging

from solid.mongo import get_db
from solid.redisCache import get_pub, get_redis, get_redis_conn
from solid.utils import gold, ed_code


async def example_func(**kwargs):
    """
    示例： 查询数据，发送至消息队列
    """
    db = get_db("example")

    model_ex = db.example_model.find(**kwargs)
    async with get_redis_conn() as pub:
        pub.publish(
            f'chan:room:1',
            ed_code.dict2json(
                {
                    "service": "GAME.SV",
                    "data": {"example":'example'},
                }
            ),
        )