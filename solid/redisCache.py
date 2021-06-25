import redis
import aioredis
import asyncio
import logging

import settings

TOKEN_SET = 'TOKEN_SET'

pool = redis.ConnectionPool(host=settings.REDIS_HOST,max_connections=256,decode_responses=True)

def get_redis():
    return redis.Redis(connection_pool=pool)

async def get_sub():
    sub = await aioredis.create_redis(f'redis://{settings.REDIS_HOST}')
    return sub

async def get_pub():
    pub = await aioredis.create_redis(f'redis://{settings.REDIS_HOST}')
    return pub

async def get_aio_redis():
    redis = await aioredis.create_redis(f'redis://{settings.REDIS_HOST}')
    return redis



class AioRedisConnection(object):

    async def __aenter__(self):

        self.redis_client = await get_aio_redis()
        return self.redis_client

    async def __aexit__(self, exc_type, exc_value, trace):
        #logging.debug(f'{exc_type},{exc_value},{trace}')
        self.redis_client.close()

def get_redis_conn():
    return AioRedisConnection()

