
from django.apps import AppConfig


class GithubAppConfig(AppConfig):
    name = 'integerations.github_'
    label = 'github_'
    verbose_name = 'Github'

    def ready(self):
        import integerations.github_.signals
        #conduit.apps.articles.signals

default_app_config = 'integerations.github_.GithubAppConfig'