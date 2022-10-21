from django.db import models
from github import Github
from django.utils.crypto import get_random_string
import uuid

from ..base.managers import BaseIntegerationManager
from .enums import HOOK_DESTINATION_GITHUB_PREFIX_NAME, \
    HOOK_PREFIX_NAME, GITHUB_PREFIX_NAME
import re

class GithubTokenManager(BaseIntegerationManager, models.Manager):

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

class HookDeckManager(models.Manager):
    def get_hookdeck_source_name_for_user(self, user):
        url_regex = "^[a-z0-9-_]+$"
        MAX_ITER = 1000
        hook_deck = self.filter(project__ai_user=user).first()

        if hook_deck:
            return hook_deck.source_name

        for i in range(MAX_ITER):
            code = get_random_string(5).lower()
            if (not self.filter(
                source_name=GITHUB_PREFIX_NAME + code).first() ) and\
                (re.match(url_regex, GITHUB_PREFIX_NAME + code)):
                return GITHUB_PREFIX_NAME + code

        raise ValueError("Hookdeck Api Source name create Max iteration "
                         "reached to find unique source_name. Try Again once!!!")

    def get_unique_base_name(self):
        MAX_ITER = 1000
        for i in range(MAX_ITER):
            code = uuid.uuid4().__str__().split("-")[-1]

            if not self.filter(
                hook_name = HOOK_PREFIX_NAME + code
            ).first():
                return code

        raise ValueError("Hookdeck Api Hook and destination name create Max iteration "
                         "reached to find unique base name. Try Again once!!!")

    def get_hook_unique_token(self):
        MAX_ITER = 1000
        for i in range(MAX_ITER):
            unique_token = uuid.uuid4().__str__()
            if not self.filter(hook_ref_token=unique_token):
                return unique_token

        raise ValueError("Hook url token create Max iteration "
                         "reached to find unique base name. Try Again once!!!")

    def get_password(self):
        return  uuid.uuid4().__str__().split("-")[-1]

class ContentFileManager(models.Manager):
    def size_of_file_null_reset(self):
        counts = self.filter(size_of_file=None).count()
        if counts> 1000:
            raise OverflowError("content file records having null size_of_file count is more than 1000...")

        for obj in self.filter(size_of_file=None).all():
            if not obj.size_of_file:
                try:
                    obj.size_of_file = obj.get_contentfile_obj.size
                    obj.save()
                except:
                    print(f"{obj.branch.repo.github_token.oauth_token} is expired...")
