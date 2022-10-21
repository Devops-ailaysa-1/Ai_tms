"""
ASGI config for myproject project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_tms.settings')
django.setup()
django_asgi_app = get_asgi_application()

import ai_marketplace.routing
from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
from ai_marketplace.channels_auth import QueryAuthMiddleware

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': QueryAuthMiddleware(
        URLRouter(
            ai_marketplace.routing.websocket_urlpatterns
        )
    )
})
# import os
#
# from channels.auth import AuthMiddlewareStack
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.security.websocket import AllowedHostsOriginValidator
# from django.conf.urls import url
# from django.urls import path
# from django.core.asgi import get_asgi_application
#
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_tms.settings")
# # Initialize Django ASGI application early to ensure the AppRegistry
# # is populated before importing code that may import ORM models.
# django_asgi_app = get_asgi_application()
#
# from ai_marketplace.consumers import ChatConsumer
#
# application = ProtocolTypeRouter({
#     # Django's ASGI application to handle traditional HTTP requests
#     "http": django_asgi_app,
#
#     # WebSocket chat handler
#     "websocket":  AllowedHostsOriginValidator(
#     AuthMiddlewareStack(
#         URLRouter([
#             path('marketplace/messages/', ChatConsumer.as_asgi()),
#             # url(r"^chat/admin/$", AdminChatConsumer.as_asgi()),
#             # url(r"^chat/$", PublicChatConsumer.as_asgi()),
#         ])
#     )
# ),
# })
