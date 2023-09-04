import requests
from allauth.socialaccount.providers.oauth2.views import (OAuth2Adapter, OAuth2LoginView, OAuth2CallbackView)
from .provider import ProzProvider
from django.conf import settings


class ProzAdapter(OAuth2Adapter):
    provider_id = ProzProvider.id
    
    # Fetched programmatically, must be reachable from container
    access_token_url = '{}/oauth/token/'.format('https://www.proz.com')
    profile_url = '{}/user'.format("https://api.proz.com/v2")
    
    # Accessed by the user browser, must be reachable by the host
    authorize_url = '{}/oauth/authorize/'.format('https://www.proz.com')

    # NOTE: trailing slashes in URLs are important, don't miss it

    def complete_login(self, request, app, token, **kwargs):
        headers = {'Authorization': 'Bearer {0}'.format(token.token)}
        resp = requests.get(self.profile_url, headers=headers)
        extra_data = resp.json()
        print("request_data --> ",extra_data)
        return self.get_provider().sociallogin_from_response(request, extra_data)
    

oauth2_login = OAuth2LoginView.adapter_view(ProzAdapter)
oauth2_callback = OAuth2CallbackView.adapter_view(ProzAdapter)