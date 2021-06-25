from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import random

def encrypt(data,key):
    if len(key) < 16:
        raise Exception('Invalid AES key length (must be 16 bytes)')
    else:
        key = key[:16]

    cipher = AES.new(key.encode('utf-8'), AES.MODE_ECB)
    encrypted = cipher.encrypt(pad(data.encode('utf-8'), 16))
    return base64.b64encode(encrypted)

def encrypt_cbc(data,key,iv):
    if len(key) < 16:
        raise Exception('Invalid AES key length (must be 16 bytes)')
    else:
        key = key[:16]

    cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
    encrypted = cipher.encrypt(pad(data.encode('utf-8'), 16))
    return base64.b64encode(encrypted)

def decrypt_cbc(data, key, iv):
    if len(key) < 16:
        raise Exception('Invalid AES key length (must be 16 bytes)')
    else:
        key = key[:16]

    if len(key) < 16:
        raise Exception('Invalid AES key length (must be 16 bytes)')
    else:
        key = key[:16]
    cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
    decrypted = unpad(cipher.decrypt(base64.b64decode(data)), 16).decode('utf-8')
    return decrypted



def genRandom(length):
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_ []{}<>~`+=,.;:/?|"
    randm_chars = random.sample(chars, length)
    return "".join(randm_chars)