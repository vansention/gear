import json
import logging
import logging.config
import types
import traceback

from datetime import date, datetime

import pytz
from flask import request, abort
from flask_login import current_user
from pymongo import MongoClient
from tornado.util import import_object
from solid.utils import make_mongo_filter,make_mongo_sort,makeQueryFields,makeOrderByField
from solid.utils.ed_code import dict2json

#import models
import models
import settings


def init_log():
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d : %(message)s'
            },
        },

        'handlers':
            {
                'console': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'formatter': 'verbose'
                },
            },
        'root': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    }

    logging.config.dictConfig(LOGGING)


# ################ api service #####################
SERVICE_MESSAGE_SUCCESS = {'status': 'success', 'message': '提交成功'}
SERVICE_MESSAGE_ERROR = {'status': 'success', 'message': '提交失败'}


def json_serial(obj):
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(obj, date):
        return obj.strftime('%Y-%m-%d')

    return str(obj)


class Mongo(object):
    __mongo__ = None

    def __init__(self):
        self.client = MongoClient(settings.MONGO,
                unicode_decode_error_handler='ignore',
                connect=False,
                tz_aware=True,
                tzinfo=pytz.timezone('Asia/Shanghai'))

    @classmethod
    def instance(cls):
        if cls.__mongo__:
            return cls.__mongo__
        else:
            cls.__mongo__ = Mongo()
            return cls.__mongo__

    @classmethod
    def get_db(cls,dbname:str):
        return cls.instance().client[dbname]

def check_perms(session, perms):
    if not perms:
        perms = ['base']

    if current_user.__tablename__ != 'admin':
        abort(403)

    current_admin = session.query(models.Admin).filter(models.Admin.id == current_user.id).one()
    perm_slugs = set([slug for slug, name in current_admin.get_perms()])

    return perm_slugs >= set(perms)


def ApiService(perms=None):
    session = models.Session()
    mongo = Mongo.instance().client

    def func_wapper(func):

        def _wapper(*args, **kwargs):
            if current_user.__tablename__ == 'admin':
                if not check_perms(session, perms):
                    abort(403)
            if current_user.__tablename__ == 'account':
                # perms is not None and perms unequal to base
                logging.debug(perms)
                if not (perms == ['base'] or perms is None):
                    abort(403)
            try:
                serv = Service(session,mongo)
                ret = func(serv, *args, **kwargs)
                return json.dumps(ret, default=json_serial)
            except:
                logging.error(traceback.format_exc())
            finally:
                session.close()
        return _wapper

    return func_wapper


def service_view(slug):
    module_name, func_name = slug.split('.')
    logging.debug(request.args)

    if request.method == 'GET':
        module = f'services.admin.{module_name}.get_{func_name}'
        service_obj = import_object(module)
        ret = service_obj(**request.args.to_dict())

    if request.method == 'POST':
        module = f'services.admin.{module_name}.post_{func_name}'
        service_obj = import_object(module)
        if request.content_type.find("form-data") >= 0:
            ret = service_obj(request.files)
        else:
            ret = service_obj(json.loads(request.data.decode('utf-8')))

    return ret


all_models = {}

def sqlalchemy_webquery_view(model_name):

    Model = all_models.get(model_name)
    if not Model:
        for path in settings.SQLALCHEMY_MODEL_PATH:
            try:
                Model = import_object(f'{path}.{model_name}')
            except ImportError:
                continue
            all_models[model_name] = Model
    
    if not Model:
        raise Exception(f'Model {model_name} not found')

    
    session = models.Session()

    try:
        find_args = request.args.to_dict()
        _sort = find_args.get('_sort','id.desc')
        _limit = find_args.get('_limit',100)
        _start = find_args.get('_start',0)
        _rels = find_args.get('_rels')
        _one = find_args.get('_one')

        filters = makeQueryFields(find_args,Model)
        query = session.query(Model).filter(*filters)
        order_by = makeOrderByField(_sort,Model)
        if _rels:
            _rels = _rels.split('.')

        if _one:
            result = query.one()
            return result.toDic(rels=_rels)

        _count = query.count()
        queryset = query.order_by(order_by).offset(_start).limit(_limit)

            #breakpoint()
        
        return {
            '_count':_count,
            '_start':_start,
            '_limit':_limit,
            'queryset':[q.toDic(rels=_rels) for q in queryset],
        }
    except Exception:
        logging.error(traceback.format_exc())
    finally:
        session.close()


def mongo_webquery_view(db_name:str,col_name:str):
    db = Mongo.get_db(db_name)
    table = db[col_name]
    find_args = request.args.to_dict()
    _sort = find_args.get('_sort','_id.desc')
    _limit = find_args.get('_limit',100)
    _start = find_args.get('_start',0)
    _one = find_args.get('_one')


    filters = make_mongo_filter(find_args)
    if _one:
        result = table.find_one(filters)
        return dict2json({
            col_name:result
        })

    query = table.find(filters)

    cur = query.sort(*make_mongo_sort(_sort))\
        .skip(int(_start))\
        .limit(int(_limit))

    _count = cur.count()
    result = list(cur)

    return dict2json({
        '_count':_count,
        '_start':_start,
        '_limit':_limit,
        'queryset':result,
    })



class Service(object):

    def __init__(self, session,mongo):
        self.session = session
        self.mongo = mongo


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]