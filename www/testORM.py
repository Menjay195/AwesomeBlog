# -*- coding:utf-8 -*-

import asyncio
import sys
import orm
from models import User, Blog, Comment

def testOrm(loop):
    yield from orm.create_pool(loop=loop,user='www-data', password='www-data', db='awesome')

    u = User(name='Test', email='test@example.com', passwd='1234567890', image='about:blank')
    # print(u.name,u.email,u.passwd,u.image)
    yield from u.save()
    yield from orm.destory_pool()


loop = asyncio.get_event_loop()
loop.run_until_complete(testOrm(loop))
loop.close()
# if loop.is_closed():
#     sys.exit(0)