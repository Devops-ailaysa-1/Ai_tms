from django.urls import path
from . import consumers


websocket_urlpatterns = [
    path('marketplace/messages/', consumers.ChatConsumer.as_asgi()),
    # path("notifications/", consumers.NotificationConsumer.as_asgi()),
]
