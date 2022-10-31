from django.apps import AppConfig


class AiAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_auth'
    def ready(self):
        from ai_auth.models import AiUser
        from django_oso.oso import Oso
        from rest_framework.request import Request
        from django.contrib.auth.models import AnonymousUser
        Oso.register_class(Request)
        # Oso.register_class(AiUser)
        # Oso.register_class(AnonymousUser)

