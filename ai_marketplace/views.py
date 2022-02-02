from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes

# Create your views here.
from .models import Thread
from notifications.signals import notify
from notifications.models import Notification
from django.db.models import OuterRef, Subquery
from ai_auth.models import Professionalidentity


@api_view(['GET',])
def messages_page(request):
    user=request.user
    bid_id =request.GET.get('bid_id')
    threads = Thread.objects.by_user(user=request.user).filter(bid_id=bid_id).prefetch_related('chatmessage_thread').order_by('timestamp')
    count = user.notifications.filter(verb='Message').unread().count()
    # notifications = user.notifications.unread().filter(verb='Message').filter(pk__in=Subquery(
            # user.notifications.unread().filter(verb='Message').order_by("data").distinct("data").values('id'))).order_by("-timestamp")
    # print("NN--->",notifications)
    context = {
        'Threads': threads,
        'count':count,
        # 'notifications':notifications
    }
    return render(request, 'messages.html', context)
