from sqlalchemy import Column, Integer, String, DateTime, func, Boolean, ForeignKey, \
    Table
from sqlalchemy.orm import relationship, backref

from solid.database import SqlalchemyConfig

import settings

sqlalchemy_config = SqlalchemyConfig(db_url=settings.DB_URL)
Model = sqlalchemy_config.Model
Session = sqlalchemy_config.Session
get_session = sqlalchemy_config.get_session

# 管理员对应的角色
rel_object_role = Table(
    'rel_object_role', Model.metadata,
    Column('admin_id', Integer, ForeignKey('admin.id')),
    Column('role_id', Integer, ForeignKey('auth_role.id'))
)

# 角色对应的权限
rel_role_perm = Table(
    'rel_role_perm', Model.metadata,
    Column('role_id', Integer, ForeignKey('auth_role.id')),
    Column('perm_id', Integer, ForeignKey('perm.id'))
)


# 角色表
class Role(Model):
    __tablename__ = 'auth_role'

    id = Column(Integer, primary_key=True)
    name = Column(String(32), unique=True, nullable=False)  # 显示的中文名称
    slug = Column(String(32), unique=True, nullable=False)

    admins = relationship("Admin", secondary=rel_object_role, back_populates="roles")
    perms = relationship('Perm', secondary=rel_role_perm, back_populates="roles")

    def __repr__(self):
        return f'<Role: {self.name}|{self.slug}>'


# 权限表
class Perm(Model):
    __tablename__ = 'perm'

    id = Column(Integer, primary_key=True)
    name = Column(String(32), unique=True, nullable=False)  # 显示的中文名称
    slug = Column(String(32), unique=True, nullable=False)

    roles = relationship("Role", secondary=rel_role_perm, back_populates="perms")


class Admin(Model):
    __tablename__ = 'admin'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(32), nullable=False)
    password = Column(String(256), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    create_time = Column(DateTime, nullable=False, default=func.now())

    roles = relationship("Role", secondary=rel_object_role, back_populates="admins")

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.active

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def __repr__(self):
        return f'<Admin {self.username}>'

    def get_perms(self):
        perms = []
        for role in self.roles:
            for perm in role.perms:
                perms.append((perm.slug, perm.name))
        return list(set(perms))


class AdminLoginLog(Model):
    """
    Admin 登陆记录
    """

    __tablename__ = 'admin_loginlog'

    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey('admin.id'), nullable=False)
    admin_name = Column(String(32), nullable=False)
    login_ip = Column(String(16), default="127.0.0.1")
    create_time = Column(DateTime, default=func.now())

    admin = relationship('Admin', backref=backref('loginlogs', lazy=True))


if __name__ == '__main__':
    from liquid.models import *
    Model.metadata.create_all()
