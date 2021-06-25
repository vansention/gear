
import oss2
import settings
import os

auth = oss2.Auth(settings.OSS_ACCESS_KET_ID, settings.OSS_ACCESS_KET_SECRET)
bucket = oss2.Bucket(auth, settings.ENDPOINT, settings.BUCKET_NAME)

def upload_file(path:str,object_name:str):

    re = bucket.put_object_from_file(object_name,path)
    return re

def download_file(object_name:str):
    object_stream = bucket.get_object(object_name)
    if object_stream.client_crc == object_stream.server_crc:
        return 'CRC 验证不通过'
    else:
        return object_stream.read()