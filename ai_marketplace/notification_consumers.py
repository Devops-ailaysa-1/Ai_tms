import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.consumer import AsyncConsumer
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from notifications.signals import notify
from notifications.models import Notification
from .models import Thread, ChatMessage
from ai_auth.models import AiUser
from django.db.models import Q
User = get_user_model()


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # """
        # Called when the websocket is handshaking as part of initial connection.
        # """
        print("NotificationConsumer: connect: " + str(self.scope["user"]) )
        await self.accept()


    async def disconnect(self, code):
        # """
        # Called when the WebSocket closes for any reason.
        # """
        print("NotificationConsumer: disconnect")

    async def receive_json(self, content):
        # """
        # Called when we get a text frame. Channels will JSON-decode the payload
        # for us and pass it as the first argument.
        # """
        command = content.get("command", None)
        try:
            if command == "get_unread_chat_notifications_count":
                try:
                    payload = await self.get_unread_chat_notification_count(self.scope["user"])
                    if payload != None:
                        payload = json.loads(payload)
                        await self.send_unread_chat_notification_count(payload['count'])
                except Exception as e:
                    print("UNREAD CHAT MESSAGE COUNT EXCEPTION: " + str(e))
                    pass
        except ClientError as e:
            print("EXCEPTION: receive_json: " + str(e))
            pass


    @database_sync_to_async
    def get_unread_chat_notification_count(user):
        payload = {}
        if user.is_authenticated:
            chatmessage_ct = ContentType.objects.get_for_model(UnreadChatRoomMessages)
            notifications = Notification.objects.filter(target=user, content_type__in=[chatmessage_ct])

            unread_count = 0
            if notifications:
                unread_count = len(notifications.all())
            payload['count'] = unread_count
            return json.dumps(payload)
        else:
            raise ClientError("AUTH_ERROR", "User must be authenticated to get notifications.")
        return None



    async def send_unread_chat_notification_count(self, count):
        """
        Send the number of unread "chat" notifications to the template
        """
        await self.send_json(
        {
        "chat_msg_type": CHAT_MSG_TYPE_GET_UNREAD_NOTIFICATIONS_COUNT,
        "count": count,
        },
    )
