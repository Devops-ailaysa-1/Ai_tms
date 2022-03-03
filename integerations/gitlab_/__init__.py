
from django.apps import AppConfig


class GitlabAppConfig(AppConfig):
    name = 'integerations.gitlab_'
    label = 'gitlab_'
    verbose_name = 'Gitlab'

    def ready(self):
        import integerations.gitlab_.signals
        #conduit.apps.articles.signals

default_app_config = 'integerations.gitlab_.GitlabAppConfig'