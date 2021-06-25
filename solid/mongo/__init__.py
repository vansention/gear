import pytz
import pymongo
from pymongo import MongoClient,collection

import settings


class Mongo(object):

    __mongo__ = None
    
    def __init__(self):
        self.client = MongoClient(settings.MONGO_URL,tzinfo=pytz.timezone('Asia/Shanghai'))

    @classmethod
    def instance(cls):
        if not cls.__mongo__:
            cls.__mongo__ = Mongo()
        return cls.__mongo__


def get_db(db_name:str):

    mongo = Mongo.instance().client
    return mongo[db_name]



