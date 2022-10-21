from django.db import models
from abc import ABC, abstractmethod

class DownloadBase(models.Model):

    # project = models.ManyToManyField("ai_workspace.Project", null=True,
    #     related_name="project_%(app_label)s%(class)s")
    controller = models.ManyToManyField("controller.DownloadController",
        # on_delete=models.CASCADE,
        related_name="controller_%(app_label)s%(class)s", null=True)
    commit_hash = models.TextField(null=True)

    class Meta:
        abstract = True

    def download(self):
        raise NotImplementedError("You should derive "
            "the function in child class")

class FileBase(models.Model):

    # file = models.ManyToManyField("ai_workspace.File", null=True,
    #     related_name="project_%(app_label)s%(class)s", )
    controller = models.ManyToManyField("controller.FileController",
        related_name="controller_%(app_label)s%(class)s", null=True)

    class Meta:
        abstract = True

    # def (self):
    #     raise NotImplementedError("You should derive "
    #         "the function in child class")
    #







