from os import path

from allauth.account.forms import (
    EmailAwarePasswordResetTokenGenerator,
    ResetPasswordForm,
)
from allauth.account.utils import user_pk_to_url_str
from django.conf import settings
from django.contrib.auth import forms as admin_forms
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from django.contrib.sites.shortcuts import get_current_site



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
        msg_plain = render_to_string("email/password_reset_email.txt", context)
        # msg_html = render_to_string("users/invite_with_password_reset.html", context)
        send_mail(
            "Password Reset",
            msg_plain,
            'noreply@ailaysa.com',
            [email],
            # html_message=msg_html,
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