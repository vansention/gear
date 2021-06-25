import hashlib

from solid import ApiService, SERVICE_MESSAGE_SUCCESS
from solid.redisCache import get_redis
from solid.utils import makeOrderByField, makeQueryFields, model2dict
from models import Admin
from liquid.models import User
import settings


@ApiService(perms=['base'])
def get_list(service, _sort='id.desc', _start=0, _limit=30, **kwargs):
    """
    获取所有用户信息
    :param service:
    :param _sort:
    :param _start:
    :param _limit:
    :param kwargs:
    :return:
    """
    session = service.session

    filters = makeQueryFields(kwargs,User)
    order_by = makeOrderByField(_sort,User)

    query = session.query(User).filter(*filters)
    count = query.count()
    
    queryset = query.order_by(order_by)\
        .offset(_start)\
        .limit(_limit)\
        .all()

    ret = {
        'user_list': [i.toDic() for i in queryset],
        '_count': count,
        '_start': _start,
        '_limit': _limit
    }

    return ret

@ApiService(perms=['base'])
def get_frozen_gold(service,_sort='id.desc', _start=0, _limit=100,**kwargs):
    
    #return [ conn for conn in get_online_cache()]
    ret = []
    redis = get_redis()
    # user_query = service.session.query(User).filter().offset(_start).limit(_limit)
    key_list = redis.keys("frozen_gold:user_id:*")
    user_id_list = [ key.split(":")[-1] for key in key_list]
    user_query = service.session.query(User).filter(User.user_id.in_(user_id_list))

    users = user_query.all()
    for user in users:
        user_data = user.toDic()
        info = redis.hgetall(f'frozen_gold:user_id:{user.user_id}')
        user_data['frozen_gold'] =  {}
        re = {}
        for k,v in info.items():
            redpack_id = k[k.index(':')+1:]
            re.update({redpack_id:v})
        user_data['frozen_gold'].update(re)
        user_data['total_frozen_gold'] = sum([int(float(v)) for v in info.values()])
        ret.append(user_data)
    return {'frozen_gold_list': ret,'_count': user_query.count(),'_start': _start,'_limit': _limit}
    


@ApiService(perms=['base'])
def post_info_modify(service, data):
    """
    修改用户信息
    :param service:
    :param _sort:
    :param _start:
    :param _limit:
    :param kwargs:
    :return:
    """
    session = service.session
    user_id = data.get('user_id')
    phone = data.get('phone')
    nickname = data.get('nickname')
    alipay = data.get('alipay')
    realname = data.get('realname')
    password = data.get('password')

    user = session.query(User).filter(User.user_id==user_id).one()
    user.phone = phone
    user.nickname = nickname
    user.alipay = alipay
    user.realname = realname
    user.password = password
    session.commit()

    return SERVICE_MESSAGE_SUCCESS

@ApiService(perms=['base'])
def get_details(service,user_id):
    session = service.session
    user = session.query(User).filter(User.user_id==user_id).one()
    return {'user':model2dict(user)}

@ApiService(perms=['base'])
def post_admin_add(service, data):
    """
    添加管理员
    :param service:
    :param data:
    :return:
    """
    session = service.session

    username = data.get('username')
    password = data.get('password', str(123456))
    hex_password = hashlib.sha256((password + settings.SECRET).encode('utf-8')).hexdigest()

    admin = Admin(username=username, password=hex_password)
    session.add(admin)
    session.commit()

    return {'status': 'success', 'message': '管理员添加成功'}


@ApiService(perms=['base'])
def post_admin_password_modify(service, data):
    """
    修改管理员密码
    :param service:
    :param data:
    :return:
    """
    session = service.session
    password = data.get('password')
    hex_password = hashlib.sha256((password + settings.SECRET).encode('utf-8')).hexdigest()

    admin = session.query(Admin).get(data.get('id'))
    admin.password = hex_password

    return {'status': 'success', 'message': '密码修改成功'}


@ApiService(perms=['base'])
def post_admin_active_modify(service, data):
    """
    修改管理员状态
    :param service:
    :param data:
    :return:
    """
    session = service.session
    active = data.get('active')

    admin = session.query(Admin).get(data.get('id'))
    admin.active = active

    session.commit()

    return {'status': 'success', 'message': '状态修改成功'}