from datetime import datetime

from solid import Mongo

mongo = Mongo.instance().client
redpack = mongo.redpack

def add():
    pac_list = list(redpack.package.find({'used':False}))
    pac_len = len(pac_list)
    if pac_len > 1000:
        return
    new_len = 1000 - pac_len
    package = redpack.package.find_one(sort=[('channel', -1)])
    if package:
        ch = package.get('channel')
        for i in range(0,new_len):
            ch += 1
            redpack.package.insert({
                'channel': ch,
                'used':False,
                'create_time':datetime.utcnow(),
                'player_id':'0',
                'used_time':datetime.utcnow()
            })


if __name__ == '__main__':
    add()
