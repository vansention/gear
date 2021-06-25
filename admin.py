"""
Admin管理系统模块
"""

import hashlib
import logging
import datetime
import redis
import json
import os

from flask import Flask, request, redirect, render_template, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from sqlalchemy.orm.exc import NoResultFound

import settings
from models import Session, Admin, AdminLoginLog
from solid import service_view,mongo_webquery_view,sqlalchemy_webquery_view
from solid.redisCache import get_redis
from solid.utils import model2dict, get_random_char
from solid.log import init_log
from solid import goole_authentication

init_log()

app = Flask(__name__)
app.secret_key = settings.SECRET
app.debug = settings.DEBUG

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.refresh_view = 'login'
redis_cli = get_redis()


@login_manager.user_loader
def load_user(admin_id):
    session = Session()
    try:
        return session.query(Admin).filter(Admin.id == admin_id).one()
    except NoResultFound:
        return None
    finally:
        session.close()


@login_manager.unauthorized_handler
def unauthorized_callback():
    current_path = request.path
    return redirect('/login')


@app.route('/login/', methods=['GET', 'POST'])
@app.route('/')
def login():
    if request.method == 'GET':
        return render_template('admin_login.html')

    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        form_authentication_code = request.form.get('authentication_code')
        # ############### 邮箱登陆验证 ##################
        # email = request.form.get('email')
        # form_verify_code = request.form.get('verify_code')
        #
        # verify_key = str(email) + '_verify_key'
        # redis_verify_code = redis_cli.get(verify_key)
        # if redis_verify_code is not None:
        #     redis_verify_code = redis_verify_code.decode()
        # else:
        #     logging.warning('verify_code not find')
        #
        # if form_verify_code != redis_verify_code:
        #     if redis_verify_code is not None:
        #         return render_template('admin_login.html', messages='验证码不正确，请仔细核对')
        #     else:
        #         return render_template('admin_login.html')
        # redis_cli.delete(verify_key)
        # ############### 邮箱登陆验证 ##################

        hex_password = hashlib.sha256((password + settings.SECRET).encode('utf-8')).hexdigest()
        logging.debug(hex_password)
        session = Session()
        try:
            admin = session.query(Admin).filter(Admin.username == username, Admin.password == hex_password).one()
            #admin = session.query(Admin).filter(Admin.username == username).one()
            if admin.active is False:
                return render_template('admin_login.html', messages='账号未激活')

        except NoResultFound:
            logging.warn('login error')
            session.close()
            return render_template('admin_login.html', messages='账号或密码错误，请重新登陆')
        # ################### 谷歌验证码 ##############################
        # user_authentication_key = admin.goole_authentication_key
        # if user_authentication_key is not None:
        #     real_authentication_code = goole_authentication.generate_otp(user_authentication_key)
        #     if real_authentication_code != form_authentication_code:
        #         return render_template('admin_login.html', messages='动态验证码有误')
        # ################### 谷歌验证码 ##############################

        login_user(admin, remember=True)
        app.permanent_session_lifetime = datetime.timedelta(hours=1)
        session.close()

        admin = model2dict(admin)
        ip = request.environ.get('HTTP_FORWARDED_FOR', request.remote_addr)

        login_log = AdminLoginLog(
            admin_id=admin['id'],
            admin_name=admin['username'],
            login_ip=ip,
            create_time=datetime.datetime.today()
        )

        session.add(login_log)
        session.commit()
        session.close()

    return redirect(f'/index/?v={settings.VERSION}')


@app.route('/admin_update_password/', methods=['GET', 'POST'])
@login_required
def update_password():
    session = Session()
    user = session.query(Admin).get(current_user.id)

    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')

    if user.password != hashlib.sha256((current_password + settings.SECRET).encode('utf-8')).hexdigest():
        res = {
            'tip': '原密码有误, 请重新登陆'
        }
        return render_template('admin_login.html', **res)

    user.password = hashlib.sha256((new_password + settings.SECRET).encode('utf-8')).hexdigest()
    session.commit()

    return redirect('/login/')


@app.route('/user_info/', methods=['GET', 'POST'])
def user_info():
    session = Session()
    user = session.query(Admin).get(current_user.id)
    session.close()
    res = {
        'result': True,
        'username': user.username,
        'create_time': user.create_time,
    }

    return jsonify(res)



@app.route('/logout/')
def logout():
    logout_user()
    return redirect('/login/')


@app.route('/index/')
@login_required
def index():
    return app.send_static_file('admin.html')

@app.route('/api/webquery/model.<model_name>/')
@login_required
def sqlalchemy_webquery(model_name:str):
    #breakpoint()
    ret = sqlalchemy_webquery_view(model_name)
    return json.dumps(ret)

@app.route('/api/webquery/<db>.<col>/')
@login_required
def webquery(db:str,col:str):
    return mongo_webquery_view(db,col)


@app.route('/api/service/<slug>/', methods=['POST', 'GET'])
@login_required
def service(slug):
    return service_view(slug)


if __name__ == '__main__':
    from tornado.wsgi import WSGIContainer
    from tornado.httpserver import HTTPServer
    from tornado.ioloop import IOLoop

    if settings.DEBUG:
        app.run(host='127.0.0.1', port=settings.ADMIN_PORT)
    else:
        http_server = HTTPServer(WSGIContainer(app))
        http_server.bind(settings.ADMIN_PORT, address=settings.LISTEN)
        http_server.start(4)
        IOLoop.current().start()
