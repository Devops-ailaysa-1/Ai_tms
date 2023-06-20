from django.urls import path
from . import consumers,notification_consumers
from .views import stream


websocket_urlpatterns = [
    path('marketplace/messages/', consumers.ChatConsumer.as_asgi()),
    path('stream/', consumers.StreamConsumer.as_asgi()),
    # path("marketplace/stream/", stream),
    # path('marketplace/notify/', notification_consumers.NotificationConsumer.as_asgi())
    # path("notifications/", consumers.NotificationConsumer.as_asgi()),
]


# from channels.routing import ProtocolTypeRouter, URLRouter
# from django.urls import path
# from .views import stream

# application = ProtocolTypeRouter({
#     "websocket": URLRouter([
#         path("stream/", stream),
#     ]),
# })