from os import path
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from datetime import date
from ai_auth import models as auth_models
from django.utils.translation import ugettext_lazy as _


def external_member_invite_mail_after_bidding(context,email):
    context = context
    msg_html = render_to_string("External_member_invite_email_with_bid_detail.html",context)
    send_mail(
        'Ailaysa MarketPlace Invite',None,
        settings.DEFAULT_FROM_EMAIL,
        #['thenmozhivijay20@gmail.com'],
        [email],
        html_message=msg_html,
    )
    print("bid detail mailsent>>")
