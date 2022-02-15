
from django.db import models
from django.apps import apps

class DownloadController(models.Model):
    project = models.OneToOneField("ai_workspace.Project", on_delete=models.CASCADE,
                    related_name="project_download")
    related_model_string = models.TextField()

    @property
    def get_download(self):
        return apps.get_model(self.related_model_string).objects\
            .filter(**{"controller": self}).first()

class FileController(models.Model):
    file = models.OneToOneField("ai_workspace.File", on_delete=models.CASCADE,
                    related_name="file_filecontroller")
    related_model_string = models.TextField()

    @property
    def get_file(self):
        return apps.get_model(self.related_model_string).objects\
            .filter(**{"controller": self}).first()






