# -*- coding:utf-8 -*-

import re, time, json, logging, hashlib, base64, asyncio

from webframe import get, post

from models import User, Comment, Blog, next_id



# -----------------------------------------------------------------------------------

from config import configs

COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret

# @asyncio.coroutine        # 此处不能添加异步方式，不然返回一个generator，导致后续无法判断len(L)!=3永远成立，即永远无法进入登录状态
def user2cookie(user, max_age):
    '''
    Generate cookie str by user.
    '''
    # build cookie string by: id-expires-sha1
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

# @asyncio.coroutine
def cookie2user(cookie_str):
    '''
    Parse cookie and load user if cookie is valid.
    '''
    logging.info('check cookies')
    if not cookie_str:
        logging.info('no cookies')
        return None
    try:
        L = cookie_str.split('-')
        logging.info('L：%s'%L)
        if len(L) != 3:
            logging.info('invalid lenth of cookies_str')
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time():
            logging.info('invalid time of cookies_str')
            return None
        user = yield from User.find(uid)
        if user is None:
            logging.info('invalid user in database')
            return None
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None
# ----------------------------------------------------------------------------------


# @get('/')
# @asyncio.coroutine
# def index(request):
#     users = yield from User.findAll()
#     return {
#         '__template__': 'test.html',
#         'users': users
#     }


@get('/')                                           #主页
@asyncio.coroutine
def index(request):
    summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    blogs = [
        Blog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120),
        Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
        Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200)
    ]
    return {
        '__template__': 'blogs.html',
        'blogs': blogs,
        '__user__': request.__user__                          #added in day10
    }


# -----------------------------------------------------------------------------------


# @get('/api/users')
# @asyncio.coroutine
# def api_get_users():
#     users = yield from User.findAll(orderBy='created_at desc')
#     for u in users:
#         u.passwd = '******'
#     return dict(users=users)


from aiohttp import web
from apis import APIError,APIValueError, APIResourceNotFoundError

@get('/register')                                          #注册页面
@asyncio.coroutine
def register():
    return {
        '__template__': 'register.html'
    }


_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')


@post('/api/users')                                        #注册表单提交功能接口
@asyncio.coroutine
def api_register_user(*, email, name, passwd):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')
    users = yield from User.findAll('email=?', [email])
    if len(users) > 0:
        raise APIError('register:failed', 'email', 'Email is already in use.')
    uid = next_id()
    sha1_passwd = '%s:%s' % (uid, passwd)
    user = User(id=uid, name=name.strip(), email=email, passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(), image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email.encode('utf-8')).hexdigest())
    yield from user.save()
    # make session cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


@get('/signin')                                                  #登录页面
@asyncio.coroutine
def signin():
    return {
        '__template__': 'signin.html'
    }


@post('/api/authenticate')                                       #发出请求的用户身份校对接口
@asyncio.coroutine
def authenticate(*, email, passwd):
    if not email:
        raise APIValueError('email', 'Invalid email.')
    if not passwd:
        raise APIValueError('passwd', 'Invalid password.')
    users = yield from User.findAll('email=?', [email])
    if len(users) == 0:
        raise APIValueError('email', 'Email not exist.')
    user = users[0]
    # check passwd:
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest():
        raise APIValueError('passwd', 'Invalid password.')
    # authenticate ok, set cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


@get('/signout')                                                      #登出页面，清除cookies
@asyncio.coroutine
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out.')
    return r
