from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm

from ai_auth.models import AiUser
from .managers import GithubTokenManager, HookDeckManager,\
    ContentFileManager
from .enums import GITHUB_PREFIX_NAME, HOOK_PREFIX_NAME,\
    HOOK_DESTINATION_GITHUB_PREFIX_NAME, APP_NAME, DJ_APP_NAME,\
    HOOK_LISTEN_ADDRESS


from github import Github
from django.shortcuts import get_object_or_404, reverse
from django.utils.crypto import get_random_string

from .utils import GithubUtils
from controller.bases import DownloadBase, FileBase
from datetime import datetime
import pytz
import cryptocode
import os, re
import uuid
import requests
from requests.auth import HTTPBasicAuth
from django.apps import apps
from django import forms
from ..base.models import IntegerationAppBase, RepositoryBase, FetchInfoBase,\
    BranchBase, ContentFileBase

CRYPT_PASSWORD = os.environ.get("CRYPT_PASSWORD")

# custom lokalize_user models should have
# last github repo fetch timestamp
# periodically fetch

class GithubApp(IntegerationAppBase):

    # def validate_oauth_token(value):
    #     print("value--->", value)
    #     g = Github(value)
    #     try:
    #         g.get_user().login
    #     except:
    #         raise forms.ValidationError({"detail":"Token is invalid!!!"})
    #     return value

    oauth_token = models.CharField(max_length=255, )#validators=[validate_oauth_token])

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.accessed_on = datetime.now(tz=pytz.UTC)
        # self.save()

    # @property
    # def update_accessed(self):
    #     print("-----property----")
    #     self.accessed_on = datetime.now(tz=pytz.UTC)
    #     self.save()

    class Meta:
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

    @property
    def get_github_obj(self):
        gh = Github(self.oauth_token)
        return gh

    get_app_obj = get_github_obj

post_save.connect(IntegerationAppBase.permission_signal(APP_NAME), sender=GithubApp)

# @receiver(post_save, sender=GithubApp)
# def githubtoken_post_save(sender, **kwargs):
#     """
#     Create a Profile instance for all newly created User instances. We only
#     run on user creation to avoid having to check for existence on each call
#     to User.save.
#     """
#     print("signals received----")
#     obj, created = kwargs["instance"], kwargs["created"]
#     if created :
#         assign_perm("change_githuboauthtoken", obj.ai_user, obj)

class FetchInfo(FetchInfoBase):
    github_token = models.OneToOneField(GithubApp,\
        on_delete=models.CASCADE, related_name="github_fetch_info")

class Repository(RepositoryBase):
    github_token = models.ForeignKey(GithubApp,\
        on_delete=models.CASCADE, related_name="github_repository_set")

    class Meta:

        permissions = (
            ('owner_repository', 'Owner'),
        )

    def get_last_obj():
        return  Repository.objects.last()

    @property
    def get_token(self):
        return self.github_token

    @property
    def get_repo_obj(self): # get_repo_gh_obj

        git_user, repo_name = self.repository_fullname.split("/")
        return GithubUtils.get_repo(
            self.github_token.oauth_token,
            git_user,
            repo_name)

    def create_all_repositories_of_github(github_token_id):
        # Should be called from API's
        gt = get_object_or_404(GithubApp.objects.all(),
            id=github_token_id)

        g = Github(gt.oauth_token)

        exist, fresh = 0, 0

        for repo in g.get_user().get_repos():
            obj, created = Repository.objects.get_or_create(
                repository_name = repo.name,
                repository_fullname = repo.full_name,
                github_token_id = github_token_id
            )

            if created:
                fresh += 1
            else:
                exist += 1

        return exist, fresh

    create_all_repositories = create_all_repositories_of_github

post_save.connect(RepositoryBase.permission_signal(f"owner_repository"),
                  sender=Repository)

class Branch(BranchBase):

    repo = models.ForeignKey(Repository, on_delete=models.CASCADE,
            related_name="repo_branches_set")

    @property
    def get_branch_gh_obj(self):
        return self.repo.get_repo_obj.get_branch(self.branch_name)

    def create_all_branches(repo):
        exist, fresh_created = 0, 0
        repo_obj = repo.get_repo_obj

        for branch_name in GithubUtils.get_branches(repo=repo_obj):
            obj, created = Branch.objects.get_or_create(
                branch_name = branch_name,
                repo = repo,
            )
            if created:
                fresh_created += 1
            else:
                exist += 1

        return exist, fresh_created

post_save.connect(BranchBase.permission_signal(),
                  sender=Branch)

@receiver(post_save, sender=Branch)
def branch_localize_register_update(sender, **kwargs):
    obj = kwargs["instance"]
    if obj.is_localize_registered == True:
        repo = obj.repo
        if not repo.is_localize_registered:
            repo.is_localize_registered = True
            repo.save()

class ContentFile(ContentFileBase):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE,
                related_name="branch_contentfiles_set")

    objects = ContentFileManager()


    def update_file(self, file):
        self.uploaded_file = file
        fc = apps.get_model("controller.FileController")\
            (file = file, related_model_string="github_.ContentFile")
        fc.save()
        self.controller = fc
        self.save()

    @property
    def get_contentfile_obj(self):
        return self.branch.repo.get_repo_obj.get_contents(self.file_path,
            ref=self.branch.branch_name)

    @property
    def get_content_of_file(self):
        repo = self.branch.repo.get_repo_obj
        ref_branch = self.branch.branch_name

        contents = GithubUtils.get_content_of_file(
            repo=repo, ref_branch=ref_branch, file_path=self.file_path)

        return contents

    def create_all_contentfiles(branch):
        repo_obj = branch.repo.get_repo_obj
        branch_name = branch.branch_name

        for file_content in GithubUtils.get_file_contents(
            repo=repo_obj, ref_branch=branch_name
        ) :
            ContentFile.objects.get_or_create(
                branch=branch, file=file_content.name,
                file_path=file_content.path,
                size_of_file=file_content.size
            )

post_save.connect(ContentFileBase.permission_signal(),
                  sender=ContentFile)

@receiver(post_save, sender=ContentFile)
def contentfile_localize_register_update(sender, **kwargs):
    obj = kwargs["instance"]
    if obj.is_localize_registered == True:
        branch = obj.branch
        if not branch.is_localize_registered:
            branch.is_localize_registered = True
            branch.save()

class HookDeck(models.Model):

    def get_password():
        return HookDeck.objects.get_password()

    def get_hook_ref_token():
        return HookDeck.objects.get_hook_unique_token()

    project = models.OneToOneField("ai_workspace.Project",
        on_delete=models.CASCADE, related_name="project_hookdeck_set")
    password = models.TextField(default=get_password)
    hook_url = models.TextField() #Programmatically to be setted
    hook_ref_token = models.TextField(default=get_hook_ref_token)

    objects = HookDeckManager()

    def save(self, *args, **kwargs):
        self.hook_url = HOOK_LISTEN_ADDRESS + reverse("hooks-listen",
                    kwargs={"token": self.hook_ref_token})
        print("You may need to call set fields function before save. please ensure")
        return super().save(*args, **kwargs)
    #
    # def set_source_name(self):
    #
    #     if not self.source_name:
    #         self.source_name = "github"
    #             # HookDeck.objects. \
    #             # get_hookdeck_source_name_for_user(user= \
    #             # self.project.ai_user)

    # def set_hookname_and_destname(self):
    #     if not self.hook_name and (not self.destination_name):
    #         base_name = HookDeck.objects.\
    #             get_unique_base_name()
    #         self.hook_name, self.destination_name = \
    #             HOOK_PREFIX_NAME +base_name, HOOK_DESTINATION_GITHUB_PREFIX_NAME+\
    #             base_name
    #
    #     elif not self.hook_name:
    #         raise ValueError(
    #             "Something went to wrong.Destination name setted already and hookname"
    #             "not setted")
    #     else:
    #         raise ValueError(
    #             "Something went to wrong.Hook name setted already and destination name"
    #             "not setted")

    # def set_clipath_and_password(self):
    #
    #     if not self.password:
    #         self.password = uuid.uuid4().__str__().split("-")[-1]
    #
    # @staticmethod
    # def get_hook_url():
    #     res = requests.post("http://api.hookdeck.com/2021-08-01/connections",
    #         data=data, headers= {'Content-Type': 'application/json'
    #         }, auth=HTTPBasicAuth('0uiz4mw193y0'
    #         'bp52b177rch275878cbnbsr60uleytgdv1gzo6', ''))
    #     try:
    #         return res.json()
    #     except:
    #         raise ValueError("hookdeck new connection create or get api failed!!!")

class DownloadProject(DownloadBase):

    branch = models.OneToOneField(Branch, on_delete=models.CASCADE, null=True)

    serializer_class_str = "github__contentfile_serializer"

    def save(self, *args, **kwargs):
        self.commit_hash = self.branch.get_branch_gh_obj.commit.sha
        # print("project---->", self.project)
        return super().save(*args, **kwargs)

    def push_to_github(self):
        pass

    def download(self):
        self.push_to_github()

    def update_project(self, project):
        self.project.add(project)
        print("here----")
        dc = apps.get_model("controller.DownloadController")\
            (project = project, related_model_string="github_.DownloadProject")
        dc.save()
        self.controller = dc
        self.save()

    def get_content_files_set(self):
        return self.branch.branch_contentfiles_set

class FileConnector(FileBase):
    contentfile = models.OneToOneField(ContentFile, on_delete=models.SET_NULL,
        null=True)
