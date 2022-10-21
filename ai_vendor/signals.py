from django.db.models import Q
from locale import currency
from django.db.models.signals import post_save, pre_save
# from ai_auth.api_views import subscribe_vendor
from ai_auth import models as auth_models
from ai_vendor import models as vendor_models
from django.conf import settings
from ai_auth.utils import get_plan_name
from djstripe.models import Price,Customer
from ai_auth.vendor_onboard_list import users_list
# from ai_auth.api_views import subscribe,subscribe_vendor
#
#
# users_list=[0,0]


def user_update(sender, instance, *args, **kwargs):
    user = auth_models.AiUser.objects.get(id = instance.lang_pair.user.id)
    if vendor_models.VendorServiceInfo.objects.filter(lang_pair__user = user).filter(lang_pair__deleted_at = None).count() == 1:
        if instance.lang_pair.user.email in users_list:
            if user.is_vendor == False:
                user.is_vendor = True
                # user.vendor_onboard_info.onboarded_as_vendor = True
                user.save()


def user_update_1(sender, instance, *args, **kwargs):
    user = auth_models.AiUser.objects.get(id = instance.lang_pair.user.id)
    if vendor_models.VendorServiceTypes.objects.filter(lang_pair__user = user).filter(lang_pair__deleted_at = None).count() == 1:
        if instance.lang_pair.user.email in users_list:
            if user.is_vendor == False:
                user.is_vendor = True
                # user.vendor_onboard_info.onboarded_as_vendor = True
                user.save()
