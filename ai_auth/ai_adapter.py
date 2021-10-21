from django.conf import settings
from allauth.account.adapter import DefaultAccountAdapter
from django.contrib.sites.shortcuts import get_current_site
from urllib.parse import urljoin
from os.path import join

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
        # print("Entered Get email uri",url)
        # print("Setting link>",settings.SIGNUP_CONFIRM_URL)
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
        print("Entered Confirmation Mail")
        if signup:
            email_template = "account/email/email_confirmation_signup"
        else:
            email_template = "account/email/email_confirmation"

        self.send_mail(email_template, emailconfirmation.email_address.email, ctx)