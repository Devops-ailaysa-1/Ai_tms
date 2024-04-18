from django.db.models.signals import post_save
from notifications.signals import notify
from ai_marketplace.models import ChatMessage

# import random

def my_handler(sender, instance, created, **kwargs):
    notify.send(instance, verb='was saved')

post_save.connect(my_handler, sender=ChatMessage)


