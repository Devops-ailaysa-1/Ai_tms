from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm

from ai_auth.models import AiUser


from github import Github
from django.shortcuts import get_object_or_404

from datetime import datetime
import pytz


class IntegerationOAuthToken(models.Model):
    oauth_token = models.CharField(max_length=255,)
    ai_user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    username = models.CharField(max_length=255)
    created_on = models.DateTimeField(auto_now_add=True, )
    accessed_on =  models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True, )

    class Meta:
        abstract = True
        constraints = [models.UniqueConstraint(fields=("ai_user", "username"), \
            name="Duplicate github usernames not allowed for one ai-user ...")]

        permissions = (
            ('assign_task', 'Assign task'),
        )

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

@receiver(post_save, sender=GithubOAuthToken)
def githubtoken_post_save(sender, **kwargs):
    """
    Create a Profile instance for all newly created User instances. We only
    run on user creation to avoid having to check for existence on each call
    to User.save.
    """
    print("signals received----")
    obj, created = kwargs["instance"], kwargs["created"]
    if created :
        assign_perm("change_githuboauthtoken", obj.ai_user, obj)
