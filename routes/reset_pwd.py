from flask import (
    render_template,
    request,
    redirect,
    url_for,
    Blueprint,
)

from models.message import Messages
from routes import *

main = Blueprint('reset', __name__)



@main.route('/send', methods=['POST'])
def reset_send():
    form = request.form.to_dict()
    username = form['username']
    u = User.one(username=username)
    token = str(uuid.uuid4())
    cache.set(token, u.id)
    # csrf_tokens[token] = u.id

    link = 'https://www.fengfan620.com/reset/view?token={}'.format(token)
    Messages.send(
        title='小破站重置密码',
        content='点击链接重置密码啦~~点击<br>{}'.format(link),
        sender_id=1,
        receiver_id=u.id
    )
    return redirect(url_for('index.index'))


@main.route('/view')
def reset_view():
    token = request.args.get('token')
    if token is not None:
        return render_template('reset_pwd.html', token=token)


@main.route('/view/update', methods=['POST'])
def reset_update():
    form = request.form.to_dict()
    password = User.salted_password(form['password'])
    token = str(form['token'])

    if token is not None:
        # id = csrf_tokens[token]
        id = cache.get(token)
        User.update(id, password=password)
    return redirect(url_for('index.index'))
