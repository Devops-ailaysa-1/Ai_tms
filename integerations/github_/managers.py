from django.db import models
from github import Github

class GithubTokenManager(models.Manager):

    def get_invalid_token_objects(self):
        objects = []
        for obj in self.all():
            if not obj.github_repository_set.all():

                g = Github(obj.oauth_token)

                try:
                    g.get_user().login
                except:
                    objects.append(obj)

        return objects