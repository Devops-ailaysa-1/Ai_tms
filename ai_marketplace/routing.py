from django.urls import path
from . import consumers,notification_consumers


websocket_urlpatterns = [
    path('marketplace/messages/', consumers.ChatConsumer.as_asgi()),
    # path('marketplace/notify/', notification_consumers.NotificationConsumer.as_asgi())
    # path("notifications/", consumers.NotificationConsumer.as_asgi()),
]
