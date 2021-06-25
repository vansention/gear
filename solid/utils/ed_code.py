
import json
from datetime import datetime

from bson import json_util


def json_encode_wapper(func):
    def _(obj,*args,**kwargs):
        return func(obj,*args,**kwargs)
    return _



def dict2json(val):

    return json.dumps(val,default=json_encode_wapper(json_util.default))
