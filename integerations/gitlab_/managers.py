from django.db import models
from github import Github

from ..base.managers import BaseIntegerationManager

class AppManager(BaseIntegerationManager, models.Manager):

    def get_invalid_token_objects(self):
        raise ValueError("Not implemented properly in child class")