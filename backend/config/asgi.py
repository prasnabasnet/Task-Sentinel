import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from apps.projects.middleware import TokenAuthMiddleware
from apps.projects.routing import websocket_urlpatterns as project_ws_urls
from apps.tasks.routing import websocket_urlpatterns as task_ws_urls
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application



django_asgi_app = get_asgi_application()


combined_websocket_urlpatterns = task_ws_urls + project_ws_urls

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": TokenAuthMiddleware(URLRouter(combined_websocket_urlpatterns)),
    }
)
