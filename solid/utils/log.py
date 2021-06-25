import datetime
import logging

from liquid.models import UserRegisterLog,UserLoginLog

def log_register(service, user_id:str, user_name:str, channel:str, ctime:datetime, ip:str,  device:str, status:bool,union_id:str):
    session = service.session
    register_log = UserRegisterLog(user_id=user_id,nickname=user_name,union_id=union_id,channel=channel,last_time=ctime,last_device=device,last_ip=ip,status=status)
    logging.debug(register_log)
    session.add(register_log)
    session.commit()
    logging.info(f'insert login log success:\n{register_log}')


def log_login(service, user_id:str, user_name:str, channel:str, ctime:datetime, ip:str,  device:str, status:bool,union_id:str):
    session = service.session
    login_log = UserLoginLog(user_id=user_id,nickname=user_name,union_id=union_id,channel=channel,last_time=ctime,last_device=device,last_ip=ip,status=status)
    logging.debug(login_log)
    session.add(login_log)
    session.commit()
    logging.info(f'insert login log success:\n{login_log}')
