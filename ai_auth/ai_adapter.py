from django.conf import settings
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.sites.shortcuts import get_current_site
from urllib.parse import urljoin
from os.path import join
from django.utils.encoding import force_str
from allauth.account import app_settings
import logging
from ai_auth.models import AiUser
logger = logging.getLogger('django')

class MyAccountAdapter(DefaultAccountAdapter):

    # def get_login_redirect_url(self, request):
    #     path = "/accounts/{username}/"
    #     return path.format(username=request.user.username)



    def get_email_confirmation_url(self, request, emailconfirmation):
        """Constructs the email confirmation (activation) url.

        Note that if you have architected your system such that email
        confirmations are sent outside of the request context `request`
        can be `None` here.
        """
        "Build  Absoulute Uri can be Used after domain is included in Sites"
        url = join(settings.SIGNUP_CONFIRM_URL, emailconfirmation.key)
 
        #ret = build_absolute_uri(request, url
        return url

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        current_site = get_current_site(request)
        activate_url = self.get_email_confirmation_url(request, emailconfirmation)
        ctx = {
            "user": emailconfirmation.email_address.user,
            "activate_url": activate_url,
            "current_site": current_site,
            "key": emailconfirmation.key,
        }
        if signup:
            email_template = "account/email/email_confirmation_signup"
        else:
            email_template = "account/email/email_confirmation"

        self.send_mail(email_template, emailconfirmation.email_address.email, ctx)


    # def format_email_subject(self, subject):
    #     prefix = app_settings.EMAIL_SUBJECT_PREFIX
    #     if prefix is None:
    #         site = get_current_site(self.request)
    #         prefix = "{name}".format(name=site.name)
    #     return prefix + force_str(subject)


class SocialAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """Get called after a social login. check for data and save what you want."""
        try:
            user = AiUser.objects.get(id=request.user.id)  # Error: user not available
            name = sociallogin.account.extra_data.get('name', None)
            user.fullname=name
            user.save()
        except AiUser.DoesNotExist:
            logger.warning("User not found:",user.email)
        except AttributeError:
            logger.warning("User fullname not found:",user.email)