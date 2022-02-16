from django.db import models
from django.db.models.signals import pre_save, post_save

from ai_auth.models import AiUser
from gitlab import Gitlab

import os, re
from .enums import APP_NAME

from ..base.models import IntegerationAppBase

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

