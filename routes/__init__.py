import uuid
from functools import wraps

import redis
from flask import session, request, abort

from models.user import User
from utils import log


def current_user():
    if 'session_id' in request.cookies:
        session_id = request.cookies['session_id']
        # s = Session.one_for_session_id(session_id=session_id)
        key = 'session_id_{}'.format(session_id)
        if cache.exists(key):
            user_id = int(cache.get(key))
            u = User.one(id=user_id)
            return u
        else:
            return None
    else:
        return None

# def current_user():
#     uid = session.get('user_id', '')
#     u: User = User.one(id=uid)
#     # type annotation
#     # User u = User.one(id=uid)
#     return u


def csrf_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.args['token']
        u = current_user()
        k = token
        if cache.exists(k) and int(cache.get(k)) == u.id:
            cache.delete(token)
            return f(*args, **kwargs)

        else:
            abort(401)
        # if token in csrf_tokens and csrf_tokens[token] == u.id:
        #     csrf_tokens.pop(token)
        #     return f(*args, **kwargs)
        # else:
        #     abort(401)

    return wrapper


def new_csrf_token():
    u = current_user()
    token = str(uuid.uuid4())
    cache.set(token, u.id)
    # csrf_tokens[token] = u.id
    return token


cache = redis.StrictRedis()