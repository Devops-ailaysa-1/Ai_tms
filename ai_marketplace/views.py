from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes

# Create your views here.
from .models import Thread
from ai_auth.models import Professionalidentity


@api_view(['GET',])
def messages_page(request):
    user=request.user
    bid_id =request.GET.get('bid_id')
    threads = Thread.objects.by_user(user=request.user).filter(bid_id=bid_id).prefetch_related('chatmessage_thread').order_by('timestamp')
    context = {
        'Threads': threads
    }
    return render(request, 'messages.html', context)
