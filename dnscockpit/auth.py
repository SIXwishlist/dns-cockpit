from functools import wraps

from aiohttp import web
from aiohttp_security.abc import AbstractAuthorizationPolicy
from aiohttp_security import authorized_userid
from aiohttp_session import get_session


class DatabaseAuthorizationPolicy(AbstractAuthorizationPolicy):

    def __init__(self, app):
        self.app = app

    async def authorized_userid(self, identity):
        async with self.app['db'].acquire() as conn:
            stmt = await conn.prepare("SELECT * FROM `users` WHERE `email` = $1 AND `is_active` = true")
            ret = await stmt.fetchval(identity)
            if ret:
                return identity
            else:
                return None

    async def permits(self, identity, permission, context=None):
        if identity is None:
            return False
        return True


def login_required(fn):
    @wraps(fn)
    async def wrapped(*args, **kwargs):
        request = args[-1]
        session = await get_session(request)
        router = request.app.router
        if 'user_id' not in session:
            return web.HTTPFound(router['login'].url_for())
        ret = await fn(*args, **kwargs)
        return ret

    return wrapped