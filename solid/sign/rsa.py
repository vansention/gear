
import base64

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Signature import PKCS1_v1_5 as Signature_pkcs1_v1_5
from Crypto import Random
from Crypto.Hash import SHA,SHA256
#import OpenSSL



def encrypt_rsa(txt,key_path):
    with open(key_path) as f:
        key = f.read()
        rsa_key = RSA.importKey(key)
        cipher = PKCS1_v1_5.new(rsa_key)
        cipher_text = base64.b64encode(cipher.encrypt(txt.encode('utf-8')))
    return cipher_text

def decrypt_rsa(txt,key_path):
    with open(key_path) as f:
        key = f.read()
        rsa_key = RSA.importKey(key)
        cipher = PKCS1_v1_5.new(rsa_key)
        cipher_text = cipher.decrypt(base64.b64decode(txt),
                Random.new().read)
    return cipher_text


def sign_rsa(txt,key_path, sha=SHA):
    with open(key_path) as f:
        key = f.read().encode('utf-8').strip()
        #import pdb
        #pdb.set_trace()
        rsa_key = RSA.importKey(key)
        signer = Signature_pkcs1_v1_5.new(rsa_key)
        digest = sha.new()
        digest.update(txt.encode('utf-8'))
        sign = signer.sign(digest)
    return base64.b64encode(sign)

def sign_rsa_str(txt,key, sha=SHA):
    rsa_key = RSA.importKey(base64.b64decode(key.encode('utf-8')))
    signer = Signature_pkcs1_v1_5.new(rsa_key)
    digest = sha.new()
    digest.update(txt.encode('utf-8'))
    sign = signer.sign(digest)
    return base64.b64encode(sign).decode('utf-8')



def verify_rsa(txt,signature,key_path):
    with open(key_path) as f:
        key = f.read()
        rsa_key = RSA.importKey(key)
        signer = Signature_pkcs1_v1_5.new(rsa_key)
        digest = SHA.new()
        digest.update(txt)
        is_verify = signer.verify(digest,base64.b64decode(signature))
        return is_verify


def opensslSign(txt,key_path):
    with open(key_path) as f:
        priKey = f.read().encode('utf-8').strip()
    private_key = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, priKey)
    return base64.b64encode(OpenSSL.crypto.sign(private_key, txt, 'sha256'))


def rsa_long_encrypt(msg, key_path, length=100):
    """
    单次加密串的长度最大为 (key_size/8)-11
    1024bit的证书用100， 2048bit的证书用 200
    """
    with open(key_path) as f:
        key = f.read()
        rsa_key = RSA.importKey(key)
        cipher = PKCS1_v1_5.new(rsa_key)
        txt = b''
        for i in range(0, len(msg), length):
            txt += cipher.encrypt(msg[i:i+length].encode('utf-8'))
        cipher_text = base64.b64encode(txt)
    return cipher_text


def rsa_long_decrypt(msg, key_path, length=128):
    """
    1024bit的证书用128，2048bit证书用256位
    """
    with open(key_path) as f:
        key = f.read()
        rsa_key = RSA.importKey(key)
        cipher = PKCS1_v1_5.new(rsa_key)
        res = []
        for i in range(0, len(msg), length):
            res.append(cipher.decrypt(msg[i:i+length], 'xyz'))
        txt = "".join(res)
        cipher_text = base64.b64encode(txt)
    return cipher_text