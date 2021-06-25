

import logging
import hashlib
from hashlib import md5

try:
    from urllib import urlencode
except:
    from urllib.parse import urlencode

def md5_signature(args,key,upper=False,key_with_prefix="&key="):
    argsList = [ (k,v) for k,v in args.items()]
    argsList.sort(key=lambda x:x[0])
    sign_str = '&'.join([ '{0}={1}'.format(k,v) for k,v in argsList])
    sign_str = '{0}{1}{2}'.format(sign_str, key_with_prefix, key)

    logging.debug(sign_str)
    sign =  hashlib.md5(sign_str.encode('utf-8')).hexdigest()
    if upper:
        sign = sign.upper()

    return sign

def rc4(lyst, keyid, encode_std='utf-8'):
    # 不同平台的string指定编码格式不同,如php为"ISO-8859-1", 编码格式错误会导致验签失败.
    data = md5(''.join(lyst).encode()).hexdigest()
    key = {}
    box = {}
    plen = len(keyid)
    dlen = len(data)
    for i in range(256):
        key[i] = ord(keyid[i % plen])
        box[i] = i
    for i in range(256):
        if i == 0:
            j = 0
        j = (j + box[i] + key[i]) % 256
        tmp = box[i]
        box[i] = box[j]
        box[j] = tmp
        cipher = ''
    for i in range(dlen):
        if i == 0:
            a = 0
            j = 0
        a = (a + 1) % 256
        j = (j + box[a]) % 256
        tmp = box[a]
        box[a] = box[j]
        box[j] = tmp
        k = box[((box[a] + box[j]) % 256)]
        cipher += str(chr(ord(data[i]) ^ k))
    return md5(cipher.encode(encode_std)).hexdigest()
