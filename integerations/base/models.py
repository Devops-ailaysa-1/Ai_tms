from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm

from ai_auth.models import AiUser
from .utils import pretty_size
from ai_workspace_okapi.okapi_configs import CURRENT_SUPPORT_FILE_EXTENSIONS_LIST as csfel

from github import Github
from django.shortcuts import get_object_or_404

from datetime import datetime
import pytz, os



class IntegerationAppBase(models.Model):
    oauth_token = models.CharField(max_length=255,)
    ai_user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    username = models.CharField(max_length=255)
    created_on = models.DateTimeField(auto_now_add=True, )
    accessed_on =  models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True, )

    class Meta:
        abstract = True
        constraints = [models.UniqueConstraint(fields=("ai_user", "username"), \
            name="Duplicate app usernames not allowed for one user ...")]

        permissions = (
            ('assign_task', 'Assign task'),
        )

    def validate_oauth_token(value):
        raise ValueError("You should implement in child class")

    @property
    def is_token_expired(self):
        raise ValueError("You should implement in child class")

    @property
    def check_username_correct(self):
        raise ValueError("You should implement in child class")

    @property
    def get_app_obj(self):
        raise ValueError("You should implement in child class")

    def permission_signal(app_name="github"):
        def githubtoken_post_save(sender, **kwargs):
            obj, created = kwargs["instance"], kwargs["created"]
            if created:
                assign_perm(f"change_{app_name}app", obj.ai_user, obj)
        return githubtoken_post_save

class FetchInfoBase(models.Model):
    last_fetched_on = models.DateTimeField(auto_now=True,)

    class Meta:
        abstract = True

class RepositoryBase(models.Model):
    repository_name = models.TextField()
    repository_fullname = models.TextField()
    is_localize_registered = models.BooleanField(default=False)
    is_alive_in_github = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True,)
    accessed_on =  models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True, )

    class Meta:
        abstract = True

    @property
    def get_repo_obj(self): # get_repo_gh_obj
        raise ValueError("You should implement in child class!!!")

    def create_all_repositories_of_github(github_token_id):
        raise ValueError("You should implement in child class!!!")

    def permission_signal(app_name):
        def repository_post_save(sender, **kwargs):
            obj, created = kwargs["instance"], kwargs["created"]
            if created:
                assign_perm(app_name,
                            obj.get_token.ai_user, obj)

        return repository_post_save

class BranchBase(models.Model):

    branch_name = models.CharField(max_length=255)
    is_localize_registered = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True,)
    accessed_on =  models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True, )
    is_archived = models.BooleanField(default=False)

    class Meta:
        abstract = True

    @property
    def get_branch_gh_obj(self):
        raise ValueError("You should implement in child class!!!")

    def create_all_branches(repo):
        raise ValueError("You should implement in child class!!!")

    def permission_signal(app_name="change_branch"):
        def branch_post_save(sender, **kwargs):

            obj, created = kwargs["instance"], kwargs["created"]
            if created :
                assign_perm(app_name,
                    obj.repo.get_token.ai_user, obj)
        return branch_post_save



class ContentFileBase(models.Model):

    is_localize_registered = models.BooleanField(default=False)
    file = models.CharField(max_length=255)
    file_path = models.TextField() #github file stored path
    size_of_file = models.BigIntegerField(null=True) # in bytes
    created_on = models.DateTimeField(auto_now_add=True,)
    accessed_on =  models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True, )
    uploaded_file = models.OneToOneField("ai_workspace.File",
            on_delete=models.SET_NULL, null=True, default=None,
            related_name="%(app_label)s%(class)s")
    controller = models.OneToOneField("controller.FileController",
            on_delete=models.SET_NULL, null=True, default=None,
            related_name="%(app_label)s%(class)s")

    class Meta:
        abstract = True

    @property
    def is_translatable(self):
        return os.path.splitext(self.file)[-1]  in csfel

    @property
    def is_file_size_exceeded(self):
        return 100*1000*1000 < self.size_of_file

    @property
    def get_size_of_file_with_units(self):
        return pretty_size(self.size_of_file)

    size_of_file_with_units = get_size_of_file_with_units

    def update_file(self, file):
        raise ValueError("You should implement in child class!!!")

    @property
    def get_content_of_file(self):
        raise ValueError("You should implement in child class!!!")

    def create_all_contentfiles(branch):
        raise ValueError("You should implement in child class!!!")

    def permission_signal(app_name="change_contentfile"):
        def contentfile_post_save(sender, **kwargs):
            obj, created = kwargs["instance"], kwargs["created"]
            if created:
                assign_perm(app_name,
                            obj.branch.repo.get_token.ai_user, obj)
        return contentfile_post_save






