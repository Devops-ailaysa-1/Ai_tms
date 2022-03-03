from django.db import models

class DownloadBase(models.Model):

    project = models.OneToOneField("ai_workspace.Project", on_delete=models.CASCADE,
                related_name="project_%(app_label)s%(class)s", null=True)
    controller = models.OneToOneField("controller.DownloadController",
                on_delete=models.CASCADE, related_name="controller_%(app_label)s%(class)s", null=True)
    commit_hash = models.TextField(null=True)


    class Meta:
        abstract = True

    def download(self):
        raise NotImplementedError("You should derive "
            "the function in child class")





