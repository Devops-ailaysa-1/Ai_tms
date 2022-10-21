from django.db import models
from django.db.models.signals import pre_save, post_save
from django.shortcuts import get_object_or_404
from django.apps import apps
from controller.bases import DownloadBase, FileBase

from ai_auth.models import AiUser
from gitlab import Gitlab

import os, re
from .enums import APP_NAME

from ..base.models import IntegerationAppBase, FetchInfoBase,\
    RepositoryBase, BranchBase, ContentFileBase
from .utils import GitlabUtils
from .managers import ContentFileManager



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

        repo_name = self.repository_fullname
        return GitlabUtils.get_repo(
            self.gitlab_token.oauth_token,
            repo_name)

    def create_all_repositories(gitlab_token_id):
        # Should be called from API's
        gl = get_object_or_404(GitlabApp.objects.all(),
            id=gitlab_token_id)

        g = Gitlab("http://gitlab.com", gl.oauth_token)
        g.auth()

        exist, fresh = 0, 0

        for repo in g.projects.list(owned=True): # repo=project
            repository_fullname = f'{g.user.username}/{repo.name.replace(" ", "-")}'
            obj, created = Repository.objects.get_or_create(
                repository_name = repo.name,
                repository_fullname = repository_fullname, # May be need to change in future
                gitlab_token_id = gitlab_token_id
            )

            if created:
                fresh += 1
            else:
                exist += 1

        return exist, fresh

post_save.connect(RepositoryBase.permission_signal(f"owner_repository"),
                  sender=Repository)

class Branch(BranchBase):

    repo = models.ForeignKey(Repository, on_delete=models.CASCADE,
            related_name="repo_branches_set")

    @property
    def get_branch_gh_obj(self):
        return self.repo.get_repo_obj.branches.get(self.branch_name)

    def create_all_branches(repo):
        exist, fresh_created = 0, 0
        repo_obj = repo.get_repo_obj

        for branch_name in GitlabUtils.get_branches(repo=repo_obj):
            obj, created = Branch.objects.get_or_create(
                branch_name = branch_name,
                repo = repo,
            )
            if created:
                fresh_created += 1
            else:
                exist += 1

        return exist, fresh_created

    get_branch_gl_obj = get_branch_gh_obj

post_save.connect(BranchBase.permission_signal(), sender=Branch)


class ContentFile(ContentFileBase):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE,
                related_name="branch_contentfiles_set")

    objects = ContentFileManager()

    def update_file(self, file):
        self.uploaded_file = file
        fc = apps.get_model("controller.FileController")\
            (file = file, related_model_string="gitlab_.ContentFile")
        fc.save()
        self.controller = fc
        self.save()

    @property
    def get_contentfile_obj(self):
        return self.branch.repo.get_repo_obj.files.get(
            file_path=self.file_path, ref=self.branch.branch_name)

    @property
    def get_content_of_file(self):
        return self.get_contentfile_obj.decode()

    def create_all_contentfiles(branch):
        repo_obj = branch.repo.get_repo_obj
        branch_name = branch.branch_name

        for file_content, size in GitlabUtils.get_file_contents(
            repo=repo_obj, ref_branch=branch_name):

            ContentFile.objects.get_or_create(
                branch=branch, file=file_content.get("name"),
                file_path=file_content.get("path"),
                size_of_file=size)

post_save.connect(ContentFileBase.permission_signal(),
                  sender=ContentFile)


class DownloadProject(DownloadBase):
    branch = models.OneToOneField(Branch, on_delete=models.CASCADE, null=True)

    serializer_class_str = "gitlab__contentfile_serializer"

    def save(self, *args, **kwargs):
        # print("project---->", self.project)
        return super().save(*args, **kwargs)

    def push_to_gitlab(self):
        pass

    def download(self):
        self.push_to_gitlab()

    def update_project(self, project):
        self.project = project
        dc = apps.get_model("controller.DownloadController")\
            (project = project, related_model_string="gitlab_.DownloadProject")
        dc.save()
        self.controller = dc
        self.save()


class FileConnector(FileBase):
    contentfile = models.OneToOneField(ContentFile, on_delete=models.SET_NULL,
        null=True)


