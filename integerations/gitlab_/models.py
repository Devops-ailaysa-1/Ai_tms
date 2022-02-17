from django.db import models
from django.db.models.signals import pre_save, post_save
from django.shortcuts import get_object_or_404

from ai_auth.models import AiUser
from gitlab import Gitlab

import os, re
from .enums import APP_NAME

from ..base.models import IntegerationAppBase, FetchInfoBase,\
    RepositoryBase


CRYPT_PASSWORD = os.environ.get("CRYPT_PASSWORD")


class GitlabApp(IntegerationAppBase):
    #
    # def validate_oauth_token(value):
    #     raise ValueError("Not implemented in child class!!!")
    #     # return value

    oauth_token = models.CharField(max_length=255)
    ai_user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    # username should be fetched from github library
    # don't set
    username = models.CharField(max_length=255)
    created_on = models.DateTimeField(auto_now_add=True, )
    accessed_on =  models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True, )

    class Meta:
        constraints = [models.UniqueConstraint(fields=("ai_user", "username"), \
            name="Duplicate gitlab usernames not allowed for one ai-user ...")]

    @property
    def is_token_expired(self):
        gl = Gitlab("http://gitlab.com",self.oauth_token)
        try:
            gl.auth()
            return False
        except:
            return True

    @property
    def check_username_correct(self):
        raise ValueError("Not implemented in child class!!!")

    @property
    def get_app_obj(self):
        raise ValueError("Not implemented in child class!!!")


post_save.connect(IntegerationAppBase.permission_signal(APP_NAME), sender=GitlabApp)


class FetchInfo(FetchInfoBase):
    github_token = models.OneToOneField(GitlabApp,\
        on_delete=models.CASCADE, related_name="gitlab_fetch_info")

class Repository(RepositoryBase):
    gitlab_token = models.ForeignKey(GitlabApp,\
        on_delete=models.CASCADE, related_name="gitlab_repository_set")


    class Meta:
        permissions = (
            ('owner_repository', 'Owner'),
        )

    def get_last_obj():
        return Repository.objects.last()

    @property
    def get_token(self):
        return self.gitlab_token

    @property
    def get_repo_obj(self): # get_repo_gh_obj
        raise ValueError("You should implement in child class!!!")

    def create_all_repositories(gitlab_token_id):
        # Should be called from API's
        gl = get_object_or_404(GitlabApp.objects.all(),
            id=gitlab_token_id)

        g = Gitlab("http://gitlab.com", gl.oauth_token)
        g.auth()

        exist, fresh = 0, 0

        for repo in g.projects.list(owned=True): # repo=project
            obj, created = Repository.objects.get_or_create(
                repository_name = repo.name,
                repository_fullname = repo.name, # May be need to change in future
                gitlab_token_id = gitlab_token_id
            )

            if created:
                fresh += 1
            else:
                exist += 1

        return exist, fresh

post_save.connect(RepositoryBase.permission_signal(f"owner_repository"),
                  sender=Repository)
