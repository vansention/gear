
import re

r_h2u = re.compile(r'([a-z]|\d)([A-Z])')

def h2u(h_str):
    return re.sub(r_h2u, r'\1_\2', h_str).lower()

def u2h(u_str):
    return re.sub(r'(_\w)',lambda x:x.group(1)[1].upper(),u_str)


def h2u_dic(obj):

    if isinstance(obj,list):
        ret = []
        for i in obj:
            ret.append(h2u_dic(i))
        return ret
    if isinstance(obj,dict):
        ret = {}
        for k,v in obj.items():
            k = h2u(k)
            if isinstance(v,dict):
                v = h2u_dic(v)
            ret[k] = v
        return ret
    return obj

def u2h_dic(obj):
    if isinstance(obj,list):
        ret = []
        for i in obj:
            ret.append(u2h_dic(i))
        return ret
    if isinstance(obj,dict):
        ret = {}
        for k,v in obj.items():
            k = u2h(k)
            if isinstance(v,dict) or isinstance(v,list):
                v = u2h_dic(v)
            ret[k] = v 
        return ret
    return obj 
