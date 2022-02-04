from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes

# Create your views here.
from .models import Thread
from notifications.signals import notify
from notifications.models import Notification
from django.db.models import OuterRef, Subquery,Q,Max
from ai_auth.models import Professionalidentity,AiUser


def get_available_threads(user):
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
        notification = chats.order_by('-timestamp').first()
        message = notification.description
        time = notification.timestamp
        receivers_list.append({'thread_id':i.id,'receiver':Receiver.fullname,'avatar':profile,\
                                'message':message,'timestamp':time,'unread_count':count})
    return {"threads":threads,"receivers_list":receivers_list}


@api_view(['GET',])
def messages_page(request):
    user=request.user
    # tt = get_available_threads(user)
    # threads = tt.get('threads')
    # receivers_list = tt.get('receivers_list')
    threads = Thread.objects.by_user(user=request.user).prefetch_related('chatmessage_thread').order_by('timestamp')
    context = {
        'Threads': threads,
        #'receivers_list':receivers_list
    }
    return render(request, 'messages.html', context)
