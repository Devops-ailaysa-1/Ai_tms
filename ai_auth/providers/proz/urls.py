from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns
from .provider import ProzProvider

urlpatterns = default_urlpatterns(ProzProvider)
