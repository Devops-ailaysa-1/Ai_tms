from os import path

from allauth.account.forms import (
    EmailAwarePasswordResetTokenGenerator,
    ResetPasswordForm,
)
from allauth.account.utils import user_pk_to_url_str
from django.conf import settings
#from django.contrib.auth import forms as admin_forms
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
# from .tasks import email_send_task
from django.contrib.sites.shortcuts import get_current_site
from datetime import date

from ai_auth import models as auth_models

from django.utils.translation import ugettext_lazy as _




class SendInviteForm(ResetPasswordForm):
    """
    used to send an invitation to onboard the platform and reset the password
    """

    default_token_generator = EmailAwarePasswordResetTokenGenerator()

    def send_email_invite(self, email, uri, uid, token,current_site,user):
        context = {
            "uri": uri,
            "uid": uid,
            "token": token,
            "user":user,
            "current_site": current_site,
        }
        msg_plain = render_to_string("account/email/password_reset_email.txt", context)
        msg_html = render_to_string("account/email/password_reset_email.html", context)
        send_mail(
            "Password Reset",
            msg_plain,
           settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=msg_html,
        )


    def save(self, request, **kwargs):
        email = self.cleaned_data["email"]
        token_generator = kwargs.get("token_generator", self.default_token_generator)
        for user in self.users:
            temp_key = token_generator.make_token(user)
            uri = path.join(settings.CLIENT_BASE_URL, settings.PASSWORD_RESET_URL)
            current_site = get_current_site(request)
            self.send_email_invite(email, uri, user_pk_to_url_str(user), temp_key,current_site,user)

        return self.cleaned_data["email"]



# class AiPasswordResetForm(ResetPasswordForm):
#     def clean_email(self):
#         """
#         Invalid email should not raise error, as this would leak users
#         for unit test: test_password_reset_with_invalid_email
#         """
#         email = self.cleaned_data["email"]
#         email = get_adapter().clean_email(email)
#         self.users = filter_users_by_email(email, is_active=True)
#         return self.cleaned_data["email"]

#     def save(self, request, **kwargs):
#         if 'allauth' not in settings.INSTALLED_APPS:
#             return super().save(request, **kwargs)
#         # for allauth
#         current_site = get_current_site(request)
#         email = self.cleaned_data['email']
#         token_generator = kwargs.get('token_generator', default_token_generator)

#         for user in self.users:

#             temp_key = token_generator.make_token(user)

#             # save it to the password reset model
#             # password_reset = PasswordReset(user=user, temp_key=temp_key)
#             # password_reset.save()

#             # send the password reset email
#             path = reverse(
#                 'password_reset_confirm',
#                 args=[user_pk_to_url_str(user), temp_key],
#             )
#             url = build_absolute_uri(request, path)

#             context = {
#                 'current_site': current_site,
#                 'user': user,
#                 'password_reset_url': url,
#                 'request': request,
#             }
#             if app_settings.AUTHENTICATION_METHOD != app_settings.AuthenticationMethod.EMAIL:
#                 context['username'] = user_username(user)
#             get_adapter(request).send_mail(
#                 'account/email/password_reset_key', email, context
#             )
#         return self.cleaned_data['email']


def send_welcome_mail(current_site,user):
    context = {
        "user":user,
        "current_site": current_site,
    }
    email =user.email
    msg_plain = render_to_string("account/email/welcome.txt", context)
    msg_html = render_to_string("account/email/welcome.html", context)
    send_mail(
        "Welcome to Ailaysa!",
        msg_plain,
        settings.CEO_EMAIL,
        [email],
        html_message=msg_html,
    )

def send_password_change_mail(current_site,user):
    today = date.today()
    d1 = today.strftime("%d/%m/%Y")
    context = {
        "user":user,
        "current_site": current_site,
        "date" : d1,
    }
    email =user.email
    msg_plain = render_to_string("account/email/password_change.txt", context)
    msg_html = render_to_string("account/email/password_change.html", context)
    send_mail(
        "Password change",
        msg_plain,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=msg_html,
    )


def user_trial_end(user,sub):
    date1 = sub.trial_start.strftime("%B %d, %Y")
    date2 = sub.trial_end.strftime("%B %d, %Y")
    time1= sub.trial_start.strftime("%I:%M:%S %p")
    time2= sub.trial_end.strftime("%I:%M:%S %p")
    context = {
        "user":user,
        "start_date" : date1,
        "start_time": time1,
        "end_date" : date2,
        "end_time":time2
        }
    print("inside trial form")
    email =user.email
   # msg_plain = render_to_string("account/email/password_change.txt", context)
    msg_html = render_to_string("account/email/trial_ending.html", context)
    try:      
        from .block_list import ven_blocklist
        block_list=ven_blocklist
    except Exception as e:
        block_list=[]
    if user.email not in block_list:
        ms =send_mail(
            " Your Trial Ends Soon",None,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            html_message=msg_html,
        )
        print("mailsent>>",ms)
    else:
        print("user in block list")



def vendor_status_mail(email,status):
    context = {
        "user":email,
        "status": status,
    }
    if status == "Accepted":
        msg_html = render_to_string("account/email/vendor_status.html", context)
    else:
        msg_html = render_to_string("account/email/vendor_status_fail.html", context)
    send_mail(
        "Become an Editor application status with Ailaysa",None,
        # msg_plain,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=msg_html,
    )
    print("mailsent>>")


def vendor_request_admin_mail(instance):
    today = date.today()
    context = {'email': instance.email,'name':instance.name,'date':today,'message':instance.message}
    msg_html = render_to_string("vendor_onboarding_email.html", context)
    send_mail(
        "Regarding Vendor Onboarding",None,
        settings.DEFAULT_FROM_EMAIL,
        ['support@ailaysa.com'],
        html_message=msg_html,
    )
    print("mailsent>>")

def vendor_accepted_freelancer_mail(user):
    # print("User----<>",user)
    today = date.today()
    context = {'email': user.email,'name':user.fullname,'date':today}
    msg_html = render_to_string("vendor_accepted_freelancer_mail.html", context)
    send_mail(
        "Regarding Vendor Joining Freelancers Marketplace",None,
        settings.DEFAULT_FROM_EMAIL,
        ['support@ailaysa.com'],
        html_message=msg_html,
    )
    print("mailsent>>")

def vendor_renewal_mail(link,email):
    context = {'link':link}
    msg_html = render_to_string("vendor_renewal.html",context)
    send_mail(
        "Ailaysa has become a translators marketplace. Please update your account",None,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=msg_html,
    )
    print("mailsent>>")


def internal_user_credential_mail(context):
    context = context
    email = context.get('email')
    msg_html = render_to_string("Internal_member_credential_email.html",context)
    send_mail(
        "Regarding Login Credentials",None,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=msg_html,
    )
    print("mailsent>>")


def external_member_invite_mail(context,email):
    context = context
    msg_html = render_to_string("External_member_invite_email.html",context)
    send_mail(
        'Ailaysa MarketPlace Invite',None,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=msg_html,
    )
    print("mailsent>>")
