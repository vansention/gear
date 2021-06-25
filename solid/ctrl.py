import argparse
import sys
import logging
import inspect
import asyncio

from solid.log import init_log

from tornado.util import import_object

SCRIPT_ROOT = 'script'

def run():
    
    init_log()

    parser = argparse.ArgumentParser(description='运行脚本')
    parser.add_argument('-f','--function', help='指定脚本函数，例如： -f init_playerid.insert2db')
    parser.add_argument('-l','--loop', help='是否为循环程序',default=False,nargs="?")
    parser.add_argument('args',nargs="+",help="运行函数的参数，例如：-f some_file.some_function  1 2 a=3 b=4",default=[])

    parse_args = parser.parse_args()
    #breakpoint()
    function_path = f'{SCRIPT_ROOT}.{parse_args.function}'
    is_loop = parse_args.loop
    func = import_object(function_path)

    args = []
    kwargs = {}

    #breakpoint()

    for item in parse_args.args:
        if '=' in item:
            k,v = item.split('=')
            kwargs[k] = v
        else:
            args.append(item)

    if is_loop:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(func(*args,**kwargs))
        loop.run_forever()


    else:
        func(*args,**kwargs)