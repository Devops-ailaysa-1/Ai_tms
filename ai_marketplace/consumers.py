import json
from django.db.models import OuterRef, Subquery,Q,Max
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from notifications.signals import notify
from notifications.models import Notification
from .models import Thread, ChatMessage
from ai_auth.models import AiUser,Professionalidentity
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
        print("user--->",self.scope["user"])
        # print('receive', event)
        command = json.loads(event.get('text')).get('command')
        print("command---->",command)
        if command == "get_unread_chat_notifications":
            try:
                # user = json.loads(event.get('text')).get('user')
                payload = await self.get_unread_chat_notification(self.scope["user"])
                if payload != None:
                    payload = json.dumps(payload,default=str)
                    print("payload---->",payload)
                    await self.channel_layer.group_send(
                        self.chat_room,
                        {
                            'type': 'notification',
                            'text': payload
                        },
                        )
            except Exception as e:
                print("UNREAD CHAT MESSAGE COUNT EXCEPTION: " + str(e))
                pass

        elif command == "mark_messages_read":
            data = json.loads(event['text'])
            user = self.scope['user']
            thread_id = data.get('thread_id')
            # Update the notification read status flag in Notification model.
            await self.mark_all_read(thread_id,user)
            print("notification read")

        elif command == "get_available_threads":
            try:
                res = await self.get_available_threads(self.scope["user"])
                print("re--->",res)
                result = json.dumps(res,default=str)
                await self.channel_layer.group_send(
                    self.chat_room,
                    {
                        'type': 'threads',
                        'text': result
                    },
                    )
            except Exception as e:
                print("Available thread EXCEPTION: " + str(e))
                pass

        elif command == "message":
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

            chat = await self.create_chat_message(thread_obj, sent_by_user, msg)
            await self.create_chat_notification(thread_id, sent_by_user,send_to_user, msg)


            other_user_chat_room = f'user_chatroom_{send_to_id}'
            self_user = self.scope['user']
            response = {
                'message': msg,
                'sent_by': self_user.id,
                'thread_id': thread_id,
                'id':chat.id,
                'user':chat.user.id,
                'user_name':chat.user.fullname,
                'timestamp':chat.timestamp,
                'date':chat.timestamp.date().strftime('%Y-%m-%d')
            }

            await self.channel_layer.group_send(
                other_user_chat_room,
                {
                    'type': 'chat_message',
                    'text': json.dumps(response,default=str)
                },
                )

            await self.channel_layer.group_send(
                self.chat_room,
                {
                    'type': 'chat_message',
                    'text': json.dumps(response,default=str)
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

    async def notification(self, event):
        print('notification', event)
        await self.send({
            'type': 'websocket.send',
            'text': event['text']
        })

    async def threads(self, event):
        print('threads', event)
        await self.send({
            'type': 'websocket.send',
            'text': event['text']
        })

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
        obj = ChatMessage.objects.create(thread=thread, user=user, message=msg)
        return obj

    @database_sync_to_async
    def create_chat_notification(self, thread, sender, receiver, msg):
        res = notify.send(sender, recipient=receiver, verb='Message', description=msg, thread_id=int(thread))
        # return res[0][1][0].id

    @database_sync_to_async
    def mark_all_read(self,thread_id,user):
        list = Notification.objects.filter(Q(data={'thread_id':thread_id})&Q(recipient=user))
        list.mark_all_as_read()
        print("done")

    @database_sync_to_async
    def get_available_threads(self,user):
        threads = Thread.objects.by_user(user=user).filter(chatmessage_thread__isnull = False).annotate(last_message=Max('chatmessage_thread__timestamp')).order_by('-last_message')
        receivers_list =[]
        for i in threads:
            receiver = i.second_person_id if i.first_person_id == user.id else i.first_person_id
            Receiver = AiUser.objects.get(id = receiver)
            try:profile = Receiver.professional_identity_info.avatar_url
            except:profile = None
            data = {'thread_id':i.id}
            chats = Notification.objects.filter(Q(data=data) & Q(verb='Message'))
            count = user.notifications.filter(Q(data=data) & Q(verb='Message')).unread().count()
            try:
                notification = chats.order_by('-timestamp').first()
                message = notification.description
                time = notification.timestamp
            except:
                message,time = None,None
            receivers_list.append({'thread_id':i.id,'receiver':Receiver.fullname,'receiver_id':receiver,'avatar':profile,\
                                    'message':message,'timestamp':time,'unread_count':count})
        return {"receivers_list":receivers_list}

    @database_sync_to_async
    def get_unread_chat_notification(self,user):
        # if user.is_authenticated:
            # user = AiUser.objects.get(pk=request.user.id)
        count = user.notifications.filter(verb='Message').unread().count()
        notification_details=[]
        notification=[]
        notification.append({'total_count':count})
        # notifications = user.notifications.unread().filter(verb='Message').order_by('data','-timestamp').distinct()
        notifications = user.notifications.unread().filter(verb='Message').filter(pk__in=Subquery(
                user.notifications.unread().filter(verb='Message').order_by("data",'-timestamp').distinct("data").values('id'))).order_by("-timestamp")
        for i in notifications:
            count = user.notifications.filter(Q(data=i.data) & Q(verb='Message')).unread().count()
            sender = AiUser.objects.get(id =i.actor_object_id)
            try:profile = sender.professional_identity_info.avatar_url
            except:profile = None
            notification_details.append({'thread_id':i.data.get('thread_id'),'avatar':profile,'sender':sender.fullname,'sender_id':sender.id,'message':i.description,'timestamp':i.timestamp,'count':count})
        print("NNNN------->",notification_details)
        return {'notifications':notification,'notification_details':notification_details}
        # else:
        #     raise ClientError("AUTH_ERROR", "User must be authenticated to get notifications.")
        # return None


    # async def send_unread_chat_notification(self,payload):
    #     await self.send(
    #     {
    #     'type': 'unread_chat_notification',
    #     "res": payload,
    #     },
    #     print("Done")
    # )

from channels.generic.websocket import AsyncWebsocketConsumer

class StreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        pass

    async def stream_data(self, data):
        await self.send(data)