from django.db import transaction
import logging
from django.dispatch import receiver,Signal
from django.db.models.signals import post_save


bi_user_details= Signal()

@receiver(bi_user_details)
def _bi_user_details(sender, instance, created, *args, **kwargs):
    # from ai_pay.api_views import po_generate_pdf
    # if instance.po_file == None:
    #     pass
    #     # po_generate_pdf(instance)

    instance.save(using="bi")   
