from django.db import models
from github import Github

from ..base.managers import BaseIntegerationManager

class AppManager(BaseIntegerationManager, models.Manager):

    def get_invalid_token_objects(self):
        raise ValueError("Not implemented properly in child class")



class ContentFileManager(models.Manager):
    def size_of_file_null_reset(self):
        counts = self.filter(size_of_file=None).count()
        if counts> 1000:
            raise OverflowError("content file records having null size_of_file "
                    "count is more than 1000...")

        for obj in self.filter(size_of_file=None).all():
            if not obj.size_of_file:
                try:
                    obj.size_of_file = obj.get_contentfile_obj.size
                    obj.save()
                except:
                    print(f"{obj.branch.repo.gitlab_token.oauth_token} is expired...")




