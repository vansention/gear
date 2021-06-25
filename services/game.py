
import logging

from liquid import config



def get_room_list(service):
    
    return {'room_list':config.ROOM_INIT}

def enter_room(service,room_id:int):
    logging.debug('enter room')
    service.handler.set_conn_val(room_id=room_id)
    service.handler.recv(f'chan:room:{room_id}')
    return {'room_id':room_id}

def leave_room(service,room_id:int):
    logging.debug('leave room')
    service.handler.un_recv(f'chan:room:{room_id}')
    service.handler.set_conn_val(room_id=0)
    service.handler.recv('chan:index')
    return {'room_id':room_id}


