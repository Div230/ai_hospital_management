"""
JWT auth for WebSocket connections. Browsers can't send custom Authorization
headers during a WebSocket handshake, so the frontend passes the access
token as a query param: wss://.../ws/ambulance/<id>/?token=<jwt>
This middleware resolves that token to request.scope['user'], same as
DRF's JWTAuthentication does for regular HTTP requests.
"""
from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def get_user_from_token(token):
    from rest_framework_simplejwt.tokens import AccessToken
    from accounts.models import User
    try:
        validated = AccessToken(token)
        user_id = validated['user_id']
        return User.objects.get(id=user_id, is_active=True)
    except Exception:
        return AnonymousUser()


class JwtAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        params = parse_qs(query_string)
        token = params.get('token', [None])[0]

        scope['user'] = await get_user_from_token(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)


def JwtAuthMiddlewareStack(inner):
    return JwtAuthMiddleware(inner)
