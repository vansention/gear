import logging
import string
import random
from datetime import timedelta,datetime
import time

from sqlalchemy.orm import class_mapper,aliased
from sqlalchemy import cast,Date,func,extract

import models

try:
    import pymongo
except:
    pass

import settings

FUNC_DIC = {
    'date': lambda x, y: cast(x, Date) == y,
    'date_gt': lambda x, y: cast(x, Date) > y,
    'date_lt': lambda x, y: cast(x, Date) < y,
    'date_gte': lambda x, y: cast(x, Date) >= y,
    'date_lte': lambda x, y: cast(x, Date) <= y
}

filter_func = {}
filter_func['gt']=lambda x,y:x>y
filter_func['lt']=lambda x,y:x<y
filter_func['date_gt']=lambda x,y:cast(x,Date)>y
filter_func['date_lt']=lambda x,y:cast(x,Date)<y
filter_func['date_gte']=lambda x,y:cast(x,Date)>=y
filter_func['date_lte']=lambda x,y:cast(x,Date)<=y

filter_func['date'] = lambda x,y: cast(x,Date)==y
filter_func['month'] = lambda x,y: extract('month',x)==y
filter_func['week'] = lambda x,y: extract('week',x)==y
filter_func['not'] = lambda x,y: x!=y

group_func = {}
group_func['date'] = lambda x: cast(x,Date) 
group_func['month'] = lambda x: func.date_trunc('month',x)

def convert_kwargs(kwargs,**type_dic):
    for k,v in kwargs.items():
        if k in type_dic.keys():
            kwargs[k] = type_dic[k](kwargs[k])

def make_mongo_sort(sort):
    key,order = sort.split('.')
    return key, {'desc':pymongo.DESCENDING,'asc':pymongo.ASCENDING}[order]


def make_mongo_filter(kwargs,**convert_args):
    filter_dic = {}
    for k,v in kwargs.items():
        if k.startswith('_'): continue
        if '__' in k:
            field, func = k.split('__')
            if func == 'in':
                values = v.split(',')
                convert_func = convert_args.get(field)
                if convert_func:
                    values = map(convert_func,values)
                f = {field:{'$in':values}}
                filter_dic.update(f)
        else:
            filter_dic[k] = v
    return filter_dic

def get_between(dt,days):

    end = dt.strftime(settings.SHOW_DATE_FMT+' 00:00:00')
    start = (dt-timedelta(days=days)).strftime(settings.SHOW_DATE_FMT+' 00:00:00')
    return start,end

def makeOrderByField(order_by,Table):
    field, order = order_by.split('.')
    order_by_field = getattr(Table,field)
    return getattr(order_by_field,order)() 

def makeCountKey(key,Table):
    key_list = key.split('__')
    real_key = key_list[0]
    func_list = key_list[1:]

    real_key = getattr(Table,real_key)
    for func_name in func_list:
        real_key = getattr(func,func_name)(real_key)

    return real_key


def makeGroupByFields(group,Table):
    if '__' in group:
        field,func_name = group.split('__')
        ret = group_func[func_name](getattr(Table,field))
    else:
        ret = getattr(Table,group)
    return ret

# def makeFilterFields(kwargs,Table):
    
#     filter_field = []
#     for k,v in kwargs.items():
#         if '.' in k:
#             t_name,t_field = k.split('.')
#             filter_field.append( getattr(getattr(db,t_name),t_field)==v )
#         else:
#             if '__' in k:
#                 field,cp = k.split('__')
#                 f = filter_func[cp](getattr(Table,field),v)
#                 filter_field.append(f)
#             else:
#                 filter_field.append(getattr(Table,k) == v)
#     return filter_field

def makeQueryFields(kwargs, Table):
    def _get_field(slug):
        if '.' in k:
            rel_table_name, rel_field_name = slug.split('.')
            RelTable = getattr(models, rel_table_name)
            return getattr(RelTable, rel_field_name)
        else:
            return getattr(Table, slug)

    filters = []
    for k, v in kwargs.items():

        if k.startswith('_'):
            continue

        if '__' in k:
            f_name, func_name = k.split('__')
            field = _get_field(f_name)
            filters.append(FUNC_DIC[func_name](field, v))
        else:
            field = _get_field(k)
            filters.append(field == v)
    return filters


def makeUpdateFields(kwargs,Table):
    logging.debug('make update kwargs: {0},{1}'.format(kwargs,Table))
    fields = {}
    for k,v in kwargs.items():
        fields[getattr(Table,k)]=v
    return fields

def makeOrderDateByField(order_by, Table):
    field, order = order_by.split('.')
    order_by_field = getattr(Table, field)
    return getattr(func.date(order_by_field), order)()

def makeOrderSumByField(order_by, Table):
    field, order = order_by.split('.')
    order_by_field = getattr(Table, field)
    return getattr(func.sum(order_by_field), order)()

def model2dict(model):

    def _(model, c):
        r = getattr(model, c)
        # logging.debug(r)
        if isinstance(r, datetime):
            return r.strftime('%Y-%m-%d %H:%M:%S')
        return r

    columns = [c.key for c in class_mapper(model.__class__).columns]
    data = {c: _(model, c) for c in columns}
    # data = { c:getattr(model,c) for c in columns}
    return data 


def model2list(model):
    columns = [c.key for c in class_mapper(model.__class__).columns]
    data = [getattr(model,c) for c in columns]
    return data 


def utc2local(utc_datetime):
    pass
    now_timestamp = time.time()
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    return utc_datetime + offset

def hour_range(start_date, end_date):
    """
    获取时间区间小时列表
    :param start_date:
    :param end_date:
    :return:
    """
    dhours = []
    dhour = datetime.strptime(start_date, "%Y-%m-%d %H")
    date = start_date[:]
    while date <= end_date:
        dhours.append(date)
        dhour = dhour + timedelta(hours=1)
        date = dhour.strftime("%Y-%m-%d %H")
    logging.debug(dhours)
    return dhours


def get_random_char(count=6):
    """
    随机产生验证码 格式: 字母 + 数字 共六位
    :param count:
    :return:
    """
    ran = string.ascii_lowercase + string.ascii_uppercase + string.digits
    char = ''
    for i in range(count):
        char += random.choice(ran)
    return char


def get_res(money):
    level = settings.AGENT_LEVEL
    for le in level:
        min, max = le.get('range').replace('万', '0000').split('-')
        if int(min) == 10000000:
            return money / 10000 * le.get('res')
        if int(min) <= money < int(max):
            return money / 10000 * le.get('res')
