import os
import os.path
import time
import uuid
import logging
import traceback
from datetime import datetime
from dataclasses import dataclass

from sqlalchemy.dialects.postgresql import JSONB

from solid.redisCache import get_redis

from sqlalchemy import Column, func, Float, Integer
from sqlalchemy.orm.exc import NoResultFound
from tornado.util import import_object

from models import Session, Order, App, Vendor, PayConfig

from solid.mongo import Mongo
from solid.server import Singleton

import settings


class PayVendorMessage:
    TIMEOUT = 1
    SIGN_ERROR = 2
    FORMAT_ERROR = 3
    PAY_INDEX_ERROR = 4


class NotifyMessage:
    pass


@dataclass
class PayResult:
    msg: str = ""
    resp: str = ""
    url: str = settings.SUCCESS_PAGE
    status: str = 'failed'


class PayVendor(metaclass=Singleton):
    pay_modules = {}

    def __init__(self):
        logging.warn('new PayVendor instance')
        self._init_vendors()

    def _import_vendor(self, file_name):

        if not file_name.endswith('.py'):
            logging.warning(f'ignore file {file_name}')
            return

        module_name, _ = file_name.split('.')

        try:
            module = import_object(f'services.vendor.{module_name}')
            self.pay_modules[module_name] = module
        except:
            logging.error(traceback.format_exc())
            logging.warning('import file {file_name} error')

    def _init_vendors(self):

        vendor_dir = os.path.join(settings.BASE_PATH, settings.VENDOR_DIR)
        logging.debug(vendor_dir)
        [self._import_vendor(d) for d in os.listdir(vendor_dir)]

    def load_vendor(self, name):

        module = import_object(f'service.vendor.{name}')
        self.module[name] = module

    def get_orderid(self):

        return uuid.uuid1().hex

    @staticmethod
    def current():
        return PayVendor()

    def pay(self, post_args) -> PayResult:

        # vamp.vendor 为支付类型，指定例如 支付宝使用何种pay module
        # vamp.vendor_config 为指定 pay module 的各项参数，例如 appid，appkey 等。以供 module 使用

        amount = float(post_args['amount'])
        appid = post_args['appid']
        pay_index = post_args['pay_index']
        notifyURL = post_args.get('notifyURL')
        redirectURL = post_args.get('redirectURL', settings.SUCCESS_PAGE)
        orderid = post_args.get('order_id', '')
        tax = post_args.get('tax',0)
        ip = post_args['ip']
        session = Session()
        logging.warning(appid)
        val = Column('value', type_=JSONB)
        configs = session.query(val). \
            select_from(PayConfig,
                        func.jsonb_array_elements(PayConfig.data).alias()). \
            filter(val.contains({"pay_type": pay_index}), val['amount_min'].astext.cast(Float) <= amount,
                   val['amount_max'].astext.cast(Float) >= amount,PayConfig.status == True).order_by(val['priority'].astext.cast(Integer).desc()). \
            first()

        logging.warning(configs[0])
        r = get_redis()
        if r.exists('order_id'):
            if len(r.get('order_id').decode('utf-8')) > settings.COVERAGE:
                r.set('order_id', 1)
        r.incr('order_id')
        s = r.get("order_id").decode("utf-8").zfill(settings.COVERAGE)
        order_id = time.strftime("%Y%m%d%H%M%S", time.localtime()) + f'{s}'
        order = Order(
            order_id=order_id,
            app_order_id=orderid,
            create_time=datetime.today(),
            app_id=post_args.get('appid', 'test'),
            bindID='',
            amount=amount,
            status='created',
            resp_html="",
            notify_url=notifyURL,
            redirect_url=redirectURL,
            vendor_type=pay_index,
            vendor_name='')
        session.add(order)
        session.commit()
        try:
            vendor = session.query(Vendor).filter(Vendor.module_name == configs[0].get('vendor')).one()
            config = vendor.config
            module_name = configs[0].get('vendor')
        except NoResultFound:
            error_info = traceback.format_exc()
            order.status = 'failed'
            order.resp_html = error_info
            logging.warning(f'AppPayType not found: appid:{appid} pay_index:{pay_index}')
            session.commit()
            session.close()
            raise

        order.vendor_name = module_name

        order.app_real_amount = order.amount - order.amount * (tax * 0.01)
        order.vendor_real_amount = order.amount - order.amount * (vendor.tax * 0.01)

        pay_module = self.pay_modules[module_name]

        try:
            pay_info = pay_module.createOrder(orderid, amount, ip=ip, config=config, postArgs=post_args)
            order.status = pay_info.status
            order.resp_html = pay_info.url
            return pay_info
        except:
            error_info = traceback.format_exc()
            logging.error(error_info)
            order.status = 'failed'
            order.resp_html = error_info
            raise
        finally:
            session.commit()
            session.close()

