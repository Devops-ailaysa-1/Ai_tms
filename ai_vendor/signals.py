from django.db.models.signals import post_save, pre_save
from ai_auth.models import AiUser


def user_update(sender, instance, *args, **kwargs):
    user = AiUser.objects.get(id = instance.user_id)
    if user.is_vendor == False:
        user.is_vendor = True
        user.save()
