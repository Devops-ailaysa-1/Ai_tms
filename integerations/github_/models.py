from django.db import models
from ai_auth.models import AiUser
from .managers import GithubTokenManager

from github import Github

# custom lokalize_user models should have
# last github repo fetch timestamp
# periodically fetch


class GithubOAuthToken(models.Model):
    oauth_token = models.CharField(max_length=255,)
    ai_user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    # username should be fetched from github library
    # don't set
    username = models.CharField(max_length=255)


    class Meta:
        constraints = [models.UniqueConstraint(fields=("ai_user", "username"), \
            name="Duplicate github usernames not allowed for one ai-user ...")]

    objects = GithubTokenManager()

    @property
    def is_token_expired(self):
        g = Github(self.oauth_token)

        try:
            g.get_user().login
            return False
        except:
            return True

    @property
    def check_username_correct(self):
        g = Github(self.oauth_token)
        return g.get_user().login == self.username

class FetchInfo(models.Model):
    github_token = models.OneToOneField(GithubOAuthToken,\
        on_delete=models.CASCADE, related_name="github_fetch_info")
    last_fetched_on=models.DateTimeField(auto_now=True,)

class Repository(models.Model):
    github_token = models.ForeignKey(GithubOAuthToken,\
        on_delete=models.CASCADE, related_name="github_repository_set")
    repository_name = models.TextField()
    is_localize_registered = models.BooleanField(default=False)
    is_alive_in_github = models.BooleanField(default=True)

