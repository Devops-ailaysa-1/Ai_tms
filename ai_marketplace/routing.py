from django.urls import path
from . import consumers,notification_consumers
from .views import stream


websocket_urlpatterns = [
    path('marketplace/messages/', consumers.ChatConsumer.as_asgi()),
    path('stream/', consumers.StreamConsumer.as_asgi()),
]
