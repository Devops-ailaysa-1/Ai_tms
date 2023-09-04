from decimal import localcontext
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from ai_auth.providers.proz.views import ProzAdapter
from dj_rest_auth.registration.serializers import SocialLoginSerializer
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
import logging
logger = logging.getLogger('django')

class GoogleLogin(SocialLoginView): # if you want to use Authorization Code Grant, use this
    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.GOOGLE_CALLBACK_URL
    client_class = OAuth2Client

    #print("request session",self.request.session)

#from django.template.defaulttags import token_kwargs


class ProzLogin(SocialLoginView): # if you want to use Authorization Code Grant, use this
    adapter_class = ProzAdapter
    callback_url = settings.PROZ_CALLBACK_URL
    client_class = OAuth2Client





# class AiSocialAuth:
#     # def get_soc_adapter(provider):
#     #     match argument:
#     #         case 0:
#     #             return "zero"
#     #             return "one"
#     #         case 2:
#     #             return "two"
#     #         case default:
#     #             return "something"

#     def __init__(self, request=None):
#         from allauth.socialaccount.adapter import get_adapter
#         # Explicitly passing `request` is deprecated, just use:
#         # `allauth.core.context.request`.
#         self.adapter = get_adapter()
#         self.request = request


    

#     def list_providers(self, request):
#         from allauth.socialaccount.providers import registry

#         ret = []
#         provider_classes = registry.get_class_list()
#         apps = self.adapter.list_apps(request)
#         apps_map = {}
#         for app in apps:
#             apps_map.setdefault(app.provider, []).append(app)
#         for provider_class in provider_classes:
#             provider_apps = apps_map.get(provider_class.id, [])
#             if not provider_apps:
#                 if provider_class.uses_apps:
#                     continue
#                 provider_apps = [None]
#             for app in provider_apps:
#                 provider = provider_class(request=request, app=app)
#                 ret.append(provider)
#         return ret

#     def get_provider(self, request, provider):
#         """Looks up a `provider`, supporting subproviders by looking up by
#         `provider_id`.
#         """
#         from allauth.socialaccount.providers import registry

#         provider_class = registry.get_class(provider)
#         if provider_class is None or provider_class.uses_apps:
#             app = self.get_app(request, provider=provider)
#             if not provider_class:
#                 # In this case, the `provider` argument passed was a
#                 # `provider_id`.
#                 provider_class = registry.get_class(app.provider)
#             if not provider_class:
#                 logger.error(f"unknown provider: {app.provider}")
#             return provider_class(request, app=app)
#         elif provider_class:
#             assert not provider_class.uses_apps
#             return provider_class(request, app=None)
#         else:
#              logger.error(f"unknown provider: {app.provider}")