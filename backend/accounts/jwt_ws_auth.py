import urllib.parse
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from accounts.models import User


@database_sync_to_async
def get_user_from_token(token_string):
    try:
        token = AccessToken(token_string)
        user_id = token.get("user_id")
        user = User.objects.select_related("organisation").filter(id=user_id, is_active=True).first()
        return user or AnonymousUser()
    except Exception:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    Channels ASGI middleware that authenticates WebSocket connections
    using a JWT token passed in the query string (?token=...) or Sec-WebSocket-Protocol.
    """

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = urllib.parse.parse_qs(query_string)
        token_list = query_params.get("token", [])

        if token_list:
            token_string = token_list[0]
            scope["user"] = await get_user_from_token(token_string)
        else:
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
