

#from liquid.models import User
# for(let img of document.querySelectorAll('.j_user_card>.p_author_face>img') ){ console.log(img.attributes.username.nodeValue,img.src) }

import shutil
import requests

save_path = '/Users/sam/Downloads/heads'
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

def save_file(nickname,url):
    resp = requests.get(url,stream=True,headers=headers)
    if resp.status_code == 200:
        open(f'{save_path}/{nickname}.jpg','wb').write(resp.content)

def fetch():

    with open('/tmp/head') as fd:
        for line in fd:
            ret = line.split(' ')
            if len(ret) == 2:
                nickname = ret[0]
                url = ret[1].strip()
                print(line)
                save_file(nickname,url)




if __name__ == '__main__':
    fetch()
