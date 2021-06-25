import hashlib
from datetime import datetime

import settings
from models import Session, Admin, Perm, Role
from solid import Mongo
from liquid.models import App
from solid import oss
from solid.utils import tuiguang_api

session = Session()

rel_role_perm = {
    'role1': 'base',
    'role2': ['base', 'do_issue'],
    'role3': ['base', 'do_issue', 'do_auth'],
}


def init_perm_system():
    perms = [
        Perm(name='管理员基础', slug='base'),
        Perm(name='下发操作', slug='do_issue'),
        Perm(name='权限操作', slug='do_auth'),
    ]

    roles = [
        Role(name='普通管理员', slug='role1'),
        Role(name='下发管理员', slug='role2'),
        Role(name='超级管理员', slug='role3'),
    ]

    session.add_all(perms)
    session.add_all(roles)
    session.commit()

    for role in roles:
        for perm in perms:
            if perm.slug in rel_role_perm[role.slug]:
                role.perms.append(perm)

    hex_password = hashlib.sha256(('123456' + settings.SECRET).encode('utf-8')).hexdigest()
    admin = Admin(username='admin', password=hex_password)
    session.add(admin)

    r = session.query(Role).filter(Role.slug == 'role3').one()
    admin.roles.append(r)

    session.commit()


def add_admin():
    session = Session()
    hex_password = hashlib.sha256((settings.PASSWORD + settings.SECRET).encode('utf-8')).hexdigest()
    user = Admin(username=settings.USERNAME, password=hex_password)
    session.add(user)
    session.commit()
    session.close()

def package():
    mongo = Mongo.instance().client
    redpack = mongo.redpack
    ch = 300000
    for i in range(0, 1000):
        ch += 1
        redpack.package.insert_one({
            'channel': str(ch),
            'used': False,
            'create_time': datetime.utcnow(),
            'user_id': 0,
            'used_time': datetime.utcnow()
        })

if __name__ == '__main__':
    init_perm_system()
    add_admin()
    package()