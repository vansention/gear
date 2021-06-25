import logging
import json
import uuid
import traceback
import pdb
import asyncio
import time
import base64
from abc import ABC

from models import Session
import tornado.web
import tornado.websocket
from liquid.models import App, Order
from solid.sign import aes

from solid.server import start_tornado_server
from solid import init_log
from solid.service import WebSocketService, AppService, ws_message_filter
from solid.redisCache import get_aio_redis, get_redis
from solid.sign import md5_signature
from solid import format as fmt

from solid.ws_conn import WSConnMixin, check_online_connection

from liquid.models import User

import settings

cdn_download_prefix = ""


class BaseHandler(tornado.web.RequestHandler, ABC):
    def set_default_headers(self):
        origin = self.request.headers.get('Origin', '')
        self.set_header("Access-Control-Allow-Origin", origin or "http://localhost:8100")
        self.set_header("Access-Control-Allow-Headers", "content-type,token,id")
        self.set_header("Access-Control-Allow-Methods", "*")
        self.set_header("Access-Control-Allow-Credentials", "true")
        self.set_header(
            "Access-Control-Request-Headers",
            "Origin, X-Requested-With, content-Type, Accept, Authorization",
        )

    def options(self):
        # no body
        self.set_status(204)
        self.finish()


class AppServiceHandler(BaseHandler, ABC):
    """
    HTTP协议接口
    """
    def post(self):
        logging.debug(self.request.body)
        redis = get_redis()
        user_id = ''
        try:
            data = json.loads(self.request.body.decode("utf-8"))
            key = f'USER_INFO:{data["token"]}'
            user_cache = redis.hgetall(key)
            user_id = user_cache['user_id']
            key = redis.get(f"aes_key:{user_id}")
            iv = redis.get(f"aes_iv:{user_id}")
            if data.get('data'):
                data['data'] = json.loads(
                    aes.decrypt_cbc(data.get('data'), key, iv)
                )
        except:
            data = json.loads(
                aes.decrypt_cbc(
                    self.request.body.decode("utf-8"), settings.AESKEY, settings.AESIV
                )
            )
        logging.info(data)
        ip = self.request.headers.get("X-Forwarded-For", self.request.remote_ip)
        # logging.debug(data)
        serv_name = data["service"]
        serv = AppService(self, serv_name, **{"ip": ip})
        ret = serv.serv(data)
        logging.info(ret)
        logging.info(f'user_id:{user_id}')
        if serv_name in [
            "auth.wx_login",
            "auth.login",
            "auth.send_code",
            "auth.get_wx_user_info",
            "auth.robot_login",
            "auth.device_login"
        ]:
            aesdata = aes.encrypt_cbc(ret, settings.AESKEY, settings.AESIV).decode(
                "utf-8"
            )
        else:
            key = redis.get(f"aes_key:{user_id}")
            iv = redis.get(f"aes_iv:{user_id}")
            aesdata = aes.encrypt_cbc(ret, key, iv).decode("utf-8")
            logging.info(aesdata)
        self.write({"data": aesdata})

class AppWebSocketHandler(tornado.websocket.WebSocketHandler, WSConnMixin):
    """
    Websocket协议接口
    """

    running = False
    chan = None
    chan_name = ""
    redis = None
    token = ''

    async def _recv_chan(self, chan_name: str):

        logging.debug(f"recv {chan_name}")

        if self.chan_name == chan_name:
            return

        if self.chan:
            self.chan.close()

        if self.redis:
            self.redis.close()

        try:
            self.redis = await get_aio_redis()
        except OSError:
            logging.error(traceback.format_exc())
            self.close()
        chan_list = await self.redis.subscribe(chan_name)
        logging.debug(chan_list)
        chan = chan_list[0]

        self.chan = chan
        self.chan_name = chan_name
        while await chan.wait_message() and self.running and chan.is_active:
            msg = await chan.get_json()
            filter_name = msg.get("filter")
            if filter_name:
                del msg["filter"]
                is_send = ws_message_filter(self, filter_name, msg)
                if not is_send:
                    continue

            msg = fmt.u2h_dic(msg)
            msg = json.dumps(msg)
            redis = get_redis()
            key = f'USER_INFO:{self.token}'
            user_cache = redis.hgetall(key)
            user_id = user_cache['user_id']
            key = redis.get(f"aes_key:{user_id}")
            iv = redis.get(f"aes_iv:{user_id}")
            aesdata = aes.encrypt_cbc(msg, key, iv).decode("utf-8")
            self.write_message({"data": aesdata})
        logging.debug("stop subscribe")

    def recv(self, chan_name: str):
        # breakpoint()
        asyncio.create_task(self._recv_chan(chan_name))

    def un_recv(self, chan_name: str):

        if self.chan_name == chan_name and self.redis:
            self.chan.close()
            self.redis.close()
            self.redis = None
            self.chan = None

    async def _check_connect_auth(self, delay):
        await asyncio.sleep(delay)
        if self.is_auth == False:
            self.close()

    async def open(self):
        """
        TODO 
        * ws连接需要通过登陆服务下发的ticket，链接建立后3s内未收到tikcet 则断开ws链接
        * 一个deviceId 只能维持一个链接
        """
        self.running = True
        self.init_connection_cache()
        asyncio.create_task(self._check_connect_auth(1))

    async def on_message(self, message):
        redis = get_redis()
        try:
            data = json.loads(message)
            self.token = data["userToken"]
            key = f'USER_INFO:{self.token}'
            user_cache = redis.hgetall(key)
            user_id = user_cache.get('user_id')
            key = redis.get(f"aes_key:{user_id}")
            iv = redis.get(f"aes_iv:{user_id}")
            if data.get('data'):
                data['data'] = json.loads(
                    aes.decrypt_cbc(data.get('data'), key, iv)
                )
        except:
            logging.error(traceback.format_exc())
            return

        if data.get("service") == "CONN_AUTH":
            logging.debug("CONN_AUTH")
            if not self.auth(data["userToken"]):
                self.close()
                return
            self.recv("chan:index")
            aesdata = aes.encrypt_cbc(json.dumps(data), key, iv).decode("utf-8")
            return self.write_message({"data": aesdata})

        if self.is_auth == False:
            return

        # logging.debug(data)
        serv_name = data["service"]
        ip = self.request.headers.get("X-Forwarded-For", self.request.remote_ip)
        ws_service = WebSocketService(self, serv_name.lower(), **{"ip": ip})

        try:
            ret = await ws_service.serv(data)
        except:
            logging.error(traceback.format_exc())
            # breakpoint()
            return

        if ret:
            aesdata = aes.encrypt_cbc(ret, key, iv).decode("utf-8")
            self.write_message({"data": aesdata})

    def on_close(self):
        # logging.info(f'{self.conn_id} close')
        self.running = False
        self.clear_connection()

        if self.redis:
            self.redis.close()

    def check_origin(self, origin):
        return True


class OrderNotifyHandler(tornado.web.RequestHandler):
    def post(self):
        logging.info(self.request.body)
        session = Session()
        data = json.loads(self.request.body.decode("utf-8"))
        status = data.get("status")
        appid = data.get("appid")
        orderid = data.get("orderid")
        rsp_sign = data.get("sign")
        del data["sign"]
        try:
            order = session.query(Order).filter(Order.order_id == orderid).one()
        except:
            self.write("error")
        app_key = settings.VAMP_KEY
        sign = md5_signature(data, app_key)
        ret = False
        if sign == rsp_sign and status == "success":
            order.status = 3
            session.commit()
            if ret:
                self.write("success")
            else:
                order.status = 6
                session.commit()
                self.write("error")
        else:
            order.status = 4
            session.commit()
            self.write("error")

urlpatterns = [
    (r"/http/app/service", AppServiceHandler),
    (r"/ws/app/service", AppWebSocketHandler),
    (r"/recharge/api/order/notify", OrderNotifyHandler),
]

if __name__ == "__main__":
    init_log()

    start_tornado_server(
        urlpatterns,
        debug=settings.DEBUG,
        port=settings.WEB_PORT,
        task_list=[check_online_connection],
        listen=settings.LISTEN,
    )

