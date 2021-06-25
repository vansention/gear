
import logging
import traceback
import uuid
import asyncio
from datetime import datetime

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application
import tornado.websocket

import  aioredis

from solid.redisCache import get_redis,get_aio_redis
import solid


ALL_WS_CONN = 'ALL_WS_CONN'
WS_CONN_KEY = 'WS_CONN_{0}'


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def start_tornado_server(urlpatterns,
        listen='127.0.0.1',
        port=8080,
        fork=8,
        task_list:list = None,
        debug=True):
   
    app = Application(urlpatterns,
            autoreload=debug,
            debug=debug,cookie_secret="42ecbb5a603ba54ff4f7d82a415901e4")

    #SolidContext.instance().init_env()

    if debug:
        app.listen(port,address=listen)
        logging.info(f'stat app {listen}:{port}')
        #IOLoop.current().start()
    else:
        http_server = HTTPServer(app)
        http_server.bind(port,address=listen)
        http_server.start(fork)
    
    loop = IOLoop.current()
    #breakpoint()
    #loop.instance()
    for task_func in task_list:
        loop.add_callback(task_func)

    IOLoop.current().start()

