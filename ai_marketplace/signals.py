from django.db.models.signals import post_save
from notifications.signals import notify
from ai_marketplace.models import ChatMessage

# import random

def my_handler(sender, instance, created, **kwargs):
    notify.send(instance, verb='was saved')

post_save.connect(my_handler, sender=ChatMessage)


# def create_postjob_id(sender, instance, *args, **kwargs):
#     if instance.postjob_id == None:
#         instance.postjob_id = str(random.randint(1,10000))+"j"+str(instance.id)
#         instance.save()
