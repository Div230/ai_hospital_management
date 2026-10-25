"""
ASGI config for config project — serves both regular HTTP (Django views/DRF)
and WebSocket connections (real-time ambulance tracking + video call
signaling) through Django Channels.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

from channels.security.websocket import OriginValidator
from django.conf import settings
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from realtime.middleware import JwtAuthMiddlewareStack  # noqa: E402
from realtime.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': OriginValidator(JwtAuthMiddlewareStack(URLRouter(websocket_urlpatterns)), settings.CORS_ALLOWED_ORIGINS),
})
