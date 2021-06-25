import logging

from flask_login import current_user
from sqlalchemy.orm.exc import NoResultFound

import settings
from solid import ApiService
from models import Admin, Role, Perm
from solid.utils import model2dict, makeOrderByField, makeQueryFields


@ApiService(perms=['base'])
def get_current_perms(service):
    current_admin = service.session.query(Admin).filter(Admin.id == current_user.id).one()
    perms = current_admin.get_perms()
    return {k: v for k, v in perms}


@ApiService(perms=['do_auth'])
def get_perm_list(service):
    """
    获取权限列表
    :param service:
    :return:
    """
    perms = service.session.query(Perm).all()

    return [model2dict(p) for p in perms]


@ApiService(perms=['do_auth'])
def get_role_list(service):
    """
    获取角色列表
    :param service:
    :return:
    """

    roles = service.session.query(Role).all()
    return [{
        'id': r.id,
        'name': r.name,
        'slug': r.slug,
        'perms': [model2dict(perm) for perm in r.perms]
    } for r in roles]


@ApiService(perms=['do_auth'])
def get_admin_list(service, _sort='create_time.desc', _start=0, _limit=50, **kwargs):
    """
    获取管理员列表
    :param service:
    :param _sort:
    :param _start:
    :param _limit:
    :param kwargs:
    :return:
    """
    ret = {}
    session = service.session
    order_by = makeOrderByField(_sort, Admin)
    filters = makeQueryFields(kwargs, Admin)
    admins_query = session.query(Admin).filter(*filters)

    admin_list = session.query(Admin).order_by(order_by).offset(_start).limit(_limit).all()

    ret['admin_list'] = [
        {
            'id': a.id,
            'username': a.username,
            'create_time': a.create_time,
            'roles': [model2dict(r) for r in a.roles],
            'perms': [perm for perm in a.get_perms()],
            'active': a.active
        }
        for a in admin_list
    ]

    ret['_count'] = admins_query.count()
    ret['_start'] = _start
    ret['_limit'] = _limit

    return ret


@ApiService(perms=['do_auth'])
def post_add_perm(service, data):
    """
    添加权限
    :param service:
    :param data:
    :return:
    """
    perm = Perm(**data)
    service.session.add(perm)
    service.session.commit()

    return {'status': 'success', 'message': '添加成功'}


@ApiService(perms=['do_auth'])
def post_delete_perm(service, data):
    """
    删除权限
    :param service:
    :param data:
    :return:
    """
    try:
        perm = service.session.query(Perm).filter(Perm.slug == data['slug']).one()
    except NoResultFound:
        return {'status': 'error', 'message': '未找到记录'}

    service.session.delete(perm)
    service.session.commit()

    return {'status': 'success', 'message': '删除成功'}


@ApiService(perms=['do_auth'])
def post_add_role(service, data):
    """
    添加角色
    :param service:
    :param data:
    :return:
    """
    role = Role(**data)
    service.session.add(role)
    service.session.commit()

    return {'status': 'success', 'message': '添加成功'}


@ApiService(perms=['do_auth'])
def post_delete_role(service, data):
    """
    删除角色
    :param service:
    :param data:
    :return:
    """
    try:
        role = service.session.query(Role).filter(Role.slug == data['slug']).one()
    except NoResultFound:
        return {'status': 'error', 'message': '未找到记录'}

    service.session.delete(role)
    service.session.commit()

    return {'status': 'success', 'message': '删除成功'}


@ApiService(perms=['do_auth'])
def post_role_perm(service, data):
    """
    配置权限
    :param service:
    :param data:
    :return:
    """

    # 所有的权限以及权限选中的情况 / 当前 role 对象以及其所有的权限
    perms = data['perms']
    role = data['role']

    current_perms = [p['slug'] for p in role['perms']]
    add_perms = [p['slug'] for p in perms if p.get('selected') is True and p['slug'] not in current_perms]
    remove_perms = [p['slug'] for p in perms if p.get('selected') is False and p['slug'] in current_perms]

    try:
        role = service.session.query(Role).filter(Role.slug == role['slug']).one()
    except NoResultFound:
        return {'status': 'error', 'message': 'no role was found'}

    objs = service.session.query(Perm).filter(Perm.slug.in_(add_perms)).all()
    for o in objs:
        role.perms.append(o)

    objs = service.session.query(Perm).filter(Perm.slug.in_(remove_perms)).all()
    for o in objs:
        role.perms.remove(o)

    service.session.commit()

    return {'status': 'success', 'message': '权限设置成功'}


@ApiService(perms=['do_auth'])
def post_admin_role(service, data):
    """
    管理员角色分配
    :param service:
    :param data:
    :return:
    """
    roles = data['roles']
    admin = data['admin']

    logging.debug(data)

    current_roles = [p['slug'] for p in admin['roles']]
    add_roles = [p['slug'] for p in roles if p.get('selected') is True and p['slug'] not in current_roles]
    remove_roles = [p['slug'] for p in roles if p.get('selected') is False and p['slug'] in current_roles]

    try:
        admin = service.session.query(Admin).filter(Admin.id == admin['id']).one()
    except NoResultFound:
        return {'status': 'error', 'message': 'no role was found'}

    objs = service.session.query(Role).filter(Role.slug.in_(add_roles)).all()
    for o in objs:
        admin.roles.append(o)

    objs = service.session.query(Role).filter(Role.slug.in_(remove_roles)).all()
    for o in objs:
        admin.roles.remove(o)

    service.session.commit()

    return {'status': 'success', 'message': '管理员权限设置成功'}


@ApiService(perms=['base'])
def get_nav_list(service):
    """
    获取用户权限内的导航
    :param service:
    :return:
    """
    current_admin = service.session.query(Admin).filter(Admin.id == current_user.id).one()
    perms = current_admin.get_perms()
    nav_list = settings.NAV_LIST

    return [nav for nav in nav_list if set(nav['perms']) <= set([p[0] for p in perms])]
