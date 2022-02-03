import json
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from notifications.signals import notify
from notifications.models import Notification
from .models import Thread, ChatMessage
from ai_auth.models import AiUser
from django.db.models import Q
User = get_user_model()

class ChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        print('connected', event)
        user = self.scope['user']
        chat_room = f'user_chatroom_{user.id}'
        self.chat_room = chat_room
        await self.channel_layer.group_add(
            chat_room,
            self.channel_name
        )
        await self.send({
            'type': 'websocket.accept'
        })

    async def websocket_receive(self, event):
        print('receive', event)
        message_type = event.get('type', None)
        # is_notify = 'chat_message' if self.room_group_name == room else 'notification'
        # message_type = json.loads(event.get('text')).get('type')
        print("MSG TYPE-------->",message_type)
        if message_type == "notification_read":
            data = json.loads(event['text'])
            user = self.scope['user']
            id =data.get('id')
            thread_id = data.get('thread_id')
            user = AiUser.objects.filter(id = id)
            # id = id if user.is_authenticated else 'default'
            # Update the notification read status flag in Notification model.
            list = Notification.objects.filter(Q(data={'thread_id':thread_id})&Q(recipient=user))

            print("notification read")

        received_data = json.loads(event['text'])
        msg = received_data.get('message')
        sent_by_id = received_data.get('sent_by')
        send_to_id = received_data.get('send_to')
        thread_id = received_data.get('thread_id')

        if not msg:
            print('Error:: empty message')
            return False

        sent_by_user = await self.get_user_object(sent_by_id)
        send_to_user = await self.get_user_object(send_to_id)
        thread_obj = await self.get_thread(thread_id)
        if not sent_by_user:
            print('Error:: sent by user is incorrect')
        if not send_to_user:
            print('Error:: send to user is incorrect')
        if not thread_obj:
            print('Error:: Thread id is incorrect')

        await self.create_chat_message(thread_obj, sent_by_user, msg)
        tt = await self.create_chat_notification(thread_id, sent_by_user,send_to_user, msg)


        other_user_chat_room = f'user_chatroom_{send_to_id}'
        self_user = self.scope['user']
        response = {
            'message': msg,
            'sent_by': self_user.id,
            'thread_id': thread_id,
            # 'notification': tt,
        }

        await self.channel_layer.group_send(
            other_user_chat_room,
            {
                'type': 'chat_message',
                'text': json.dumps(response)
            },
            )
        # await self.channel_layer.group_send(
        #     other_user_chat_room,
        #     {
        #         "type":"send_notification",
        #         "text":json.dumps(tt)
        #     }
        # )

        await self.channel_layer.group_send(
            self.chat_room,
            {
                'type': 'chat_message',
                'text': json.dumps(response)
            }
        )



    async def websocket_disconnect(self, event):
        print('disconnect', event)

    async def chat_message(self, event):
        print('chat_message', event)
        await self.send({
            'type': 'websocket.send',
            'text': event['text']
        })

    async def send_notification(self,event):
        print("In")
        await self.send(json.dumps({
            "type":"websocket.send",
            "data":event
        }))
        print('I am here')
        print(event)

    @database_sync_to_async
    def get_user_object(self, user_id):
        qs = AiUser.objects.filter(id=user_id)
        if qs.exists():
            obj = qs.first()
        else:
            obj = None
        return obj

    @database_sync_to_async
    def get_thread(self, thread_id):
        qs = Thread.objects.filter(id=thread_id)
        if qs.exists():
            obj = qs.first()
        else:
            obj = None
        return obj

    @database_sync_to_async
    def create_chat_message(self, thread, user, msg):
        ChatMessage.objects.create(thread=thread, user=user, message=msg)

    @database_sync_to_async
    def create_chat_notification(self, thread, sender, receiver, msg):
        res = notify.send(sender, recipient=receiver, verb='Message', description=msg, thread_id=int(thread))
        return res[0][1][0].id
