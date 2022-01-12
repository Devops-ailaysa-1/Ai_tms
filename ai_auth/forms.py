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

# from ai_auth import models as auth_models
# from django.contrib.auth.forms import UserCreationForm, UserChangeForm
# from django.utils.translation import ugettext_lazy as _



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
       settings.DEFAULT_FROM_EMAIL,
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



# class AiUserCreationForm(UserCreationForm):
#     """
#     A form that creats a custom user with no privilages
#     form a provided email and password.
#     """

#     def __init__(self, *args, **kargs):
#         super(AiUserCreationForm, self).__init__(*args, **kargs)
#         del self.fields['username']

#     class Meta:
#         model = auth_models.AiUser
#         fields = ('email',)

# class AiUserChangeForm(UserChangeForm):
#     """
#     A form for updating users. Includes all the fields on
#     the user, but replaces the password field with admin's
#     password hash display field.
#     """

#     def __init__(self, *args, **kargs):
#         super(AiUserChangeForm, self).__init__(*args, **kargs)
#         del self.fields['username']

#     class Meta:
#         model = auth_models.AiUser
#         fields = '__all__'



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
    ms =send_mail(
        " Your Trial Ends Soon",None,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        html_message=msg_html,
    )
    print("mailsent>>",ms)