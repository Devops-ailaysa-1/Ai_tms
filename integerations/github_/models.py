from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm

from ai_auth.models import AiUser
from .managers import GithubTokenManager

from github import Github
from django.shortcuts import get_object_or_404

from .utils import GithubUtils
from datetime import datetime
import pytz


# custom lokalize_user models should have
# last github repo fetch timestamp
# periodically fetch


class GithubOAuthToken(models.Model):
    oauth_token = models.CharField(max_length=255,)
    ai_user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    # username should be fetched from github library
    # don't set
    username = models.CharField(max_length=255)
    created_on = models.DateTimeField(auto_now_add=True, )
    accessed_on =  models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True, )

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

class FetchInfo(models.Model):
    github_token = models.OneToOneField(GithubOAuthToken,\
        on_delete=models.CASCADE, related_name="github_fetch_info")
    last_fetched_on=models.DateTimeField(auto_now=True,)

class Repository(models.Model):
    github_token = models.ForeignKey(GithubOAuthToken,\
        on_delete=models.CASCADE, related_name="github_repository_set")
    repository_name = models.TextField()
    repository_fullname = models.TextField()
    is_localize_registered = models.BooleanField(default=False)
    is_alive_in_github = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True,)
    accessed_on =  models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True, )

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.accessed_on = datetime.now(tz=pytz.UTC)
    #     self.save()


    def get_last_obj():
        return  Repository.objects.last()

    @property
    def get_repo_obj(self):

        git_user, repo_name = self.repository_fullname.split("/")
        return GithubUtils.get_repo(
            self.github_token.oauth_token,
            git_user,
            repo_name)

    def create_all_repositories_of_github(github_token_id):
        # Should be called from API's
        gt = get_object_or_404(GithubOAuthToken.objects.all(),
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

@receiver(post_save, sender=Repository)
def repository_post_save(sender, **kwargs):

    obj, created = kwargs["instance"], kwargs["created"]
    if created :
        assign_perm("change_repository",
            obj.github_token.ai_user, obj)

class Branch(models.Model):
    branch_name = models.CharField(max_length=255)
    is_localize_registered = models.BooleanField(default=False)
    repo = models.ForeignKey(Repository, on_delete=models.CASCADE,
            related_name="repo_branches_set")
    created_on = models.DateTimeField(auto_now_add=True,)
    accessed_on =  models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True, )

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.accessed_on = datetime.now(tz=pytz.UTC)
    #     self.save()

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

@receiver(post_save, sender=Branch)
def branch_post_save(sender, **kwargs):

    obj, created = kwargs["instance"], kwargs["created"]
    if created :
        assign_perm("change_branch",
            obj.repo.github_token.ai_user, obj)

@receiver(post_save, sender=Branch)
def branch_localize_register_update(sender, **kwargs):
    obj = kwargs["instance"]
    if obj.is_localize_registered == True:
        repo = obj.repo
        if not repo.is_localize_registered:
            repo.is_localize_registered = True
            repo.save()


class ContentFile(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE,
                related_name="branch_contentfiles_set")
    is_localize_registered = models.BooleanField(default=False)
    file = models.CharField(max_length=255)
    file_path = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True,)
    accessed_on =  models.DateTimeField(blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True, )

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.accessed_on = datetime.now(tz=pytz.UTC)
    #     self.save()

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
            )

@receiver(post_save, sender=ContentFile)
def contentfile_post_save(sender, **kwargs):

    obj, created = kwargs["instance"], kwargs["created"]
    if created :
        assign_perm("change_contentfile",
            obj.branch.repo.github_token.ai_user, obj)

@receiver(post_save, sender=ContentFile)
def contentfile_localize_register_update(sender, **kwargs):
    obj = kwargs["instance"]
    if obj.is_localize_registered == True:
        branch = obj.branch
        if not branch.is_localize_registered:
            branch.is_localize_registered = True
            branch.save()



