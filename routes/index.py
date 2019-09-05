import os
import uuid

from flask import (
    render_template,
    request,
    redirect,
    session,
    url_for,
    Blueprint,
    abort,
    send_from_directory,
    current_app)
from werkzeug.datastructures import FileStorage

from models.reply import Reply
from models.topic import Topic
from models.user import User
from routes import current_user, cache
# from routes import current_user

import json

from utils import log

main = Blueprint('index', __name__)

"""
用户在这里可以
    访问首页
    注册
    登录

用户登录后, 会写入 session, 并且定向到 /profile
"""

# import gevent
import time



@main.route("/")
def index():
    # t = threading.Thread()
    # t.start()
    # gevent.spawn()

    print('time type')

    # print('time type', time.sleep, gevent.sleep)

    return render_template("user_login.html")


@main.route("/resume")
def resume():
    return render_template("resume.html")


@main.route("/register_view")
def register_view():

    return render_template("user_regiser.html")

@main.route("/forget_pwd")
def forget_pwd():

    return render_template("forget_pwd.html")


@main.route("/register", methods=['POST'])
def register():
    form = request.form.to_dict()
    # 用类函数来判断
    u = User.register(form)
    return redirect(url_for('.index'))


@main.route("/login", methods=['POST'])
def login():
    form = request.form
    u = User.validate_login(form)
    print('login user <{}>'.format(u))
    if u is None:
        return redirect(url_for('.index'))
    else:
        # session 中写入 user_id
        session_id = str(uuid.uuid4())
        key = 'session_id_{}'.format(session_id)
        log('index login key <{}> user_id <{}>'.format(key, u.id))
        cache.set(key, u.id)

        redirect_to_index = redirect(url_for('topic.index'))
        response = current_app.make_response(redirect_to_index)
        response.set_cookie('session_id', value=session_id)
        # 转到 topic.index 页面
        return response
        # session['user_id'] = u.id
        # return redirect(url_for('topic.index'))


def created_topic(user_id):
    # O(n)
    ts = Topic.all(user_id=user_id)

    return ts
    #
    # k = 'created_topic_{}'.format(user_id)
    # if cache.exists(k):
    #     v = cache.get(k)
    #     ts = json.loads(v)
    #     return ts
    # else:
    #     ts = Topic.all(user_id=user_id)
    #     v = json.dumps([t.json() for t in ts])
    #     cache.set(k, v)
    #     return ts


def replied_topic(user_id):
    # O(k)+O(m*n)
    # rs = Reply.all(user_id=user_id)
    # ts = []
    # for r in rs:
    #     t = Topic.one(id=r.topic_id)
    #     ts.append(t)
    # return ts
    #
    #     sql = """
    # select * from topic
    # join reply on reply.topic_id=topic.id
    # where reply.user_id=1
    # """
    # k = 'replied_topic_{}'.format(user_id)
    # if cache.exists(k):
    #     v = cache.get(k)
    #     ts = json.loads(v)
    #     return ts
    # else:
    #     # ts = Topic.select()
    #     #   .join(Reply, 'id', 'topic_id')
    #     #   .where(user_id=user_id)
    #     #   .all()
    #     rs = Reply.all(user_id=user_id)
    #     ts = []
    #     for r in rs:
    #         t = Topic.one(id=r.topic_id)
    #         ts.append(t)
    #
    #     v = json.dumps([t.json() for t in ts])
    #     cache.set(k, v)
    #
    #     return ts
    ts = Topic.query\
        .join(Reply, Topic.id == Reply.topic_id)\
        .filter(Reply.user_id == user_id)\
        .all()
    return ts


@main.route('/setting')
def setting():
    u = current_user()
    if u is None:
        return redirect(url_for('.index'))
    else:

        return render_template(
            'setting.html',
            user=u,
        )


@main.route('/setting/change', methods=['POST'])
def setting_change():
    form = request.form.to_dict()
    u = current_user()
    username = form['username']
    quote = form['quote']
    User.update(u.id, username=username, quote=quote)

    return redirect(url_for('.setting'))


@main.route('/setting/pwd_change', methods=['POST'])
def setting_pwd_change():
    form = request.form.to_dict()
    u = current_user()
    old_pass = form['old_pass']
    if u.password == User.salted_password(old_pass):
        new_pass = User.salted_password(form['new_pass'])

        User.update(u.id, password=new_pass)
    else:
        print('mimacuowu')

    return redirect(url_for('.setting'))


@main.route('/user/<name>')
def user_index(name):
    u = User.one(username=name)
    if u is None:
        abort(404)
    else:
        tss= Topic.all(user_id=u.id)
        ts = sorted(tss, key=lambda s: s.created_time, reverse=True)

        rs = Reply.all(user_id=u.id)
        rtss = []
        for r in rs:
            rtss.append(Topic.one(id=r.topic_id))
        rts = sorted(rtss, key=lambda s: s.created_time, reverse=True)

        return render_template('user_index.html', user=u, topics=ts, rtopics=rts)


@main.route('/profile')
def profile():
    print('running profile route')
    u = current_user()
    if u is None:
        return redirect(url_for('.index'))
    else:
        created = created_topic(u.id)
        replied = replied_topic(u.id)
        return render_template(
            'profile.html',
            user=u,
            created=created,
            replied=replied
        )


@main.route('/user/<int:id>')
def user_detail(id):
    u = User.one(id=id)
    if u is None:
        abort(404)
    else:
        return render_template('profile.html', user=u)


@main.route('/image/add', methods=['POST'])
def avatar_add():
    file: FileStorage = request.files['avatar']
    # file = request.files['avatar']
    # filename = file.filename
    # ../../root/.ssh/authorized_keys
    # images/../../root/.ssh/authorized_keys
    # filename = secure_filename(file.filename)
    suffix = file.filename.split('.')[-1]
    if suffix not in ['gif', 'jpg', 'jpeg']:
        abort(400)
        log('不接受的后缀, {}'.format(suffix))
    else:
        filename = '{}.{}'.format(str(uuid.uuid4()), suffix)
        path = os.path.join('static/images', filename)
        file.save(path)

        u = current_user()
        User.update(u.id, image='/static/images/{}'.format(filename))

        return redirect(url_for('.setting'))


@main.route('/images/<filename>')
def image(filename):
    # 不要直接拼接路由，不安全，比如
    # http://localhost:3000/images/..%5Capp.py
    # path = os.path.join('images', filename)
    # print('images path', path)
    # return open(path, 'rb').read()
    # if filename in os.listdir('images'):
    #     return
    return send_from_directory('images', filename)
