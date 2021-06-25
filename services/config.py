
from liquid import config

def get_app_config(service):
    
    app_config = {
        'ROOM_LIST': config.ROOM_INIT,
        'SIG_BOOM_ODDS': config.SIG_BOOM_ODDS,
        'MULTI_BOOM_ODDS': config.MULTI_BOOM_ODDS,
    }

    return app_config