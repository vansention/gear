


import json
from datetime import datetime

from sqlalchemy import event

from solid.redisCache import get_redis
from sqlalchemy.orm.collections import InstrumentedList

import settings

convert_dic = {
    datetime: lambda x: x.timestamp()
}



class AppMixin(object):
    """
    继承AppMixin或者缓存功能
    """

    def get_one(self,**kwargs):
        pass

    def toDic(self,exclude:list=None,rels:list=None):

        ret = {}
        if not exclude: exclude=[]
        if not rels: rels=[]
        for col in self.__table__.columns:
            if col.name in exclude:
                continue
            val = getattr(self,col.name)
            if hasattr(val,'toDic'):
                val = val.toDic()

            convert_func = convert_dic.get(type(val))
            if convert_func:
                val = convert_func(val)
            ret[col.name] = val

        for rel in rels:
            #breakpoint()
            rel_obj = getattr(self,rel)
            if isinstance(rel_obj,InstrumentedList):
                ret[rel] = [item.toDic() for item in rel_obj]
            else:
                ret[rel] = rel_obj.toDic()

        return ret

    def toJson(self):
        return json.dumps(self.toDic())

    def set_ext_cache(self,**kwargs):
        """
        设置额外的缓存数据（未在model中定义，不存入数据库），
        """
        cache = self.__class__.cache
        key = getattr(self,cache.key_field)
        cache.set_ext_cache(key,**kwargs)
        
    def get_ext_cache(self,field):
        """
        取得额外的缓存数据
        """
        cache = self.__class__.cache
        key = getattr(self,cache.key_field)
        cache.get_ext_cache(key,field)

    def get_ext_cache_multi(self,*fields):
        cache = self.__class__.cache
        key = getattr(self,cache.key_field)
        cache.get_ext_cache_multi(key,*fields)

    def flush_cache(self):
        """
        更新缓存
        """
        cache_inst = self.__class__.cache
        cache_inst.flush_cache(self)


def _jsonb(x):
    try:
        return json.loads(x)
    except:
        return eval(x)

class RedisCacheModel(object):
    
    redis_type_mapper = {
        'Integer':lambda x: int(float(x)),
        'DateTime':float,
        'DateTime':float,
        #'Boolean':int,
        'JSONB': _jsonb
    }

    key_field = None # 缓存键


    def __init__(self,ModelClass,key_field):
        self.ModelClass = ModelClass
        if not key_field:
            key_field = 'id'

        self.key_field = key_field
        self.key_prefix = f'{settings.APP_NAME}:MODEL_CACHE:{self.ModelClass.__name__}'

        self._map_redis_field()

        event.listens_for(ModelClass,'after_insert')(self._after_insert)
        event.listens_for(ModelClass,'after_update')(self._after_update)
        event.listens_for(ModelClass,'load')(self._after_load)
        # event.listens_for(ModelClass,'save')(self._save)
        event.listens_for(ModelClass,'after_delete')(self._after_delete)

    def _map_redis_field(self):
        '''
        通过配置，生成转换字典
        '''

        model_redis_mapper ={}

        for column in self.ModelClass.__table__.columns:
            func = self.redis_type_mapper.get(column.type.__class__.__name__)
            if func:
                model_redis_mapper[column.name]= func
        #logging.debug(model_redis_mapper)
        # breakpoint()
        self.model_redis_mapper = model_redis_mapper

    def _after_insert(self,mapper, connection, target):
        self.flush_cache(target)

    def _after_update(self,mapper,connection,target):
        self.flush_cache(target)

    def _after_load(self,target, context):
        self.flush_cache(target)

    def _save(self,target, context):
        pass

    def flush_cache(self,target):
        redis = get_redis()
        key = f'{settings.APP_NAME}:MODEL_CACHE:{self.ModelClass.__name__}:{getattr(target,self.key_field)}'
        redis.hmset(key,target.toDic())

    def flush_cache_by_key(self,primary_key,**kwargs):
        redis = get_redis()
        key = f'{settings.APP_NAME}:MODEL_CACHE:{self.ModelClass.__name__}:{primary_key}'
        redis.hmset(key,kwargs)

    def _after_delete(self,mapper, connection, target):
        '''
        清空user缓存，
        清空user frozen gold
        '''
        redis = get_redis()
        key = f'{settings.APP_NAME}:MODEL_CACHE:{self.ModelClass.__name__}:{getattr(target,self.key_field)}'
        redis.delete(key)
        # 清空frozen gold
        redis.delete(f'frozen_gold:user_id:{target.user_id}')

    def get_val(self,key,field) -> list:
        '''
        将redis存储的str转化为model class 定义的类型
        '''

        redis = get_redis()
        cache_key = f'{self.key_prefix}:{key}'

        val = redis.hget(cache_key,field)
        func = self.model_redis_mapper.get(field,lambda x:x)
        return func(val)

    def set_ext_cache(self,key,**kwargs):
        """设置额外缓存（model中未定义）
        
        Arguments:
            key {缓存主键} -- 缓存主键
        """
        redis = get_redis()
        cache_key = f'{self.key_prefix}:{key}'
        redis.hmset(cache_key,kwargs)

    def get_ext_cache(self,key,field):
        redis = get_redis()
        cache_key = f'{self.key_prefix}:{key}'
        return redis.hget(cache_key,field)

    def get_ext_cache_multi(self,key,*fields):
        redis = get_redis()
        cache_key = f'{self.key_prefix}:{key}'
        return redis.hmget(cache_key,*fields)

    def get_multi_val(self,key,*fields):
        redis = get_redis()
        cache_key = f'{self.key_prefix}:{key}'

        for field in fields:
            val = redis.hget(cache_key,field)            
            func = self.model_redis_mapper.get(field,lambda x:x)
            yield func(val)

    def get(self,key:str) -> dict:
        redis = get_redis()
        cache_key = f'{self.key_prefix}:{key}'
        data = redis.hgetall(cache_key)

        if not data:
            #breakpoint()
            raise Exception("未取得缓存")

        ret = {}

        for k,v in data.items():
            if v is None:
                ret[k] = v
            else:
                ret[k] = self.model_redis_mapper.get(k,lambda x:x)(v) 

        return ret
        # return { 
        #         k:self.model_redis_mapper.get(k,lambda x:x)(v) 
        #         for k,v in data.items()
        #     }

    def clear(self,key):
        """
        清除缓存
        """
        redis = get_redis()
        cache_key = f'{self.key_prefix}:{key}'
        redis.delete(cache_key)


def cache_model(ModelClass,
        key_field=None):
    
    """
    key_field 缓存主键
    """

    cache = RedisCacheModel(ModelClass,key_field)
    setattr(ModelClass,'cache',cache)
