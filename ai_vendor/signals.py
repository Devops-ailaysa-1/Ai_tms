from locale import currency
from django.db.models.signals import post_save, pre_save
# from ai_auth.api_views import subscribe_vendor
from ai_auth import models as auth_models
from django.conf import settings
from ai_auth.utils import get_plan_name
from djstripe.models import Price,Customer
# from ai_auth.api_views import subscribe,subscribe_vendor
#
#
users_list=[0,0]  


def user_update(sender, instance, *args, **kwargs):
    user = auth_models.AiUser.objects.get(id = instance.lang_pair.user.id)
    if instance.lang_pair.user.id in users_list:
        if user.is_vendor == False:
            user.is_vendor = True
            user.save()


def user_update_1(sender, instance, *args, **kwargs):
    user = auth_models.AiUser.objects.get(id = instance.lang_pair.user.id)
    if instance.lang_pair.user.id in users_list:
        if user.is_vendor == False:
            user.is_vendor = True
            user.save()
