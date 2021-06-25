from sqlalchemy import Column, Integer, String, DateTime, func, Float, Text, Boolean
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import JSONB,ARRAY

from models import Model
from solid.app_model import AppMixin,cache_model

import settings


class User(Model,AppMixin):

    __tablename__ = 'app_user'
    id = Column(Integer, primary_key=True,autoincrement=True)

    user_id = Column(String(6),unique=True)
    union_id = Column(String(64),nullable=True)

    phone = Column(String(13),nullable=False,unique=True)
    password = Column(String(32),nullable=False)
    nickname = Column(String(32),nullable=False)
    gold = Column(Integer,default=0)
    frozen_gold = Column(Integer,default=0)
    channel = Column(String(16),default="000000")
    device = Column(String(64),nullable=False,default="")
    head = Column(String(256),default=settings.DEFAULT_HEAD)
    register_time = Column(DateTime,default=func.now())
    last_login_time = Column(DateTime,default=func.now())

    alipay = Column(String(32),nullable=False,default="") #支付宝账户
    realname = Column(String(32),nullable=False,default="") #支付宝账号真实姓名
    is_robot = Column(Boolean,default=False)
    is_active = Column(Boolean,default=True)
    is_nickname_award = Column(Boolean,default=False)
    is_head_award = Column(Boolean,default=False)

cache_model(User,key_field='user_id')

class UserLoginLog(Model):
    """
    user 登陆记录
    """

    __tablename__ = 'user_login_log'

    id = Column(Integer, primary_key=True)
    user_id = Column(String(6),nullable=False)
    nickname =  Column(String(32),nullable=False,default='')
    user = relationship("User", 
        primaryjoin='foreign(UserLoginLog.user_id) == remote(User.user_id)',
        backref=backref('user_login_log_list', lazy=True))
    union_id = Column(String(64), nullable=False,default='')
    channel = Column(String(16),default="000000")
    last_time = Column(DateTime, default=func.now())
    last_device = Column(String(64),nullable=False,default="")
    last_ip = Column(String(16),default="127.0.0.1")
    status = Column(Boolean,default=True)

class UserRegisterLog(Model):
    """
    user 注册记录
    """

    __tablename__ = 'user_register_log'

    id = Column(Integer, primary_key=True)
    user_id = Column(String(6),nullable=False)
    nickname =  Column(String(32),nullable=False,default='')
    user = relationship("User", 
        primaryjoin='foreign(UserRegisterLog.user_id) == remote(User.user_id)',
        backref=backref('user_register_log_list', lazy=True))
    union_id = Column(String(64), nullable=False,default='')
    channel = Column(String(16),default="000000")
    last_time = Column(DateTime, default=func.now())
    last_device = Column(String(64),nullable=False,default="")
    last_ip = Column(String(16),default="127.0.0.1")
    status = Column(Boolean,default=True)


class App(Model):
    __tablename__ = 'app'

    id = Column(Integer,primary_key=True, nullable=False)
    name = Column(String(32), nullable=False, default='')
    app_id = Column(String(32), unique=True, nullable=False, default='')
    app_key = Column(String(32), nullable=False)
    description = Column(String(256), nullable=False)
    tax = Column(JSONB, default={}, nullable=False)
    app_balance = Column(Float, default=0, nullable=False)  # 余额
    create_time = Column(DateTime, nullable=False, default=func.now())
    status = Column(Boolean,default=True)

# 游戏配置表
class Game(Model):
    __tablename__ = 'game'

    id = Column(Integer, primary_key=True)
    name = Column(String(32), nullable=False) # 游戏名
    status = Column(String(6),nullable=False,default='open') #游戏状态, 开启状态, "open"开启, "close"关闭
    discription = Column(String(32), nullable=False,default='') # 游戏描述
    create_time = Column(DateTime, nullable=False, default=func.now())  # 创建时间

