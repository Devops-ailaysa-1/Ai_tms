
from django.db import models
from django.apps import apps

class DownloadController(models.Model):
    # project = models.OneToOneField("ai_workspace.Project", on_delete=models.CASCADE,
    #                 related_name="project_download")
    project = models.OneToOneField("ai_workspace.Project", null=True, on_delete=models.CASCADE,
        related_name="project_%(class)s")
    related_model_string = models.TextField()

    @property
    def get_download(self):
        return apps.get_model(self.related_model_string).objects\
            .filter(**{"controller__in": self}).first()

    def update_project(self, project, related_model_string, branch_id):
        self.project = project
        self.related_model_string = related_model_string
        self.save()
        obj, created = apps.get_model(self.related_model_string).objects.\
            get_or_create(branch_id=branch_id)
        obj.controller.add(self)

        return self

class FileController(models.Model):
    file = models.OneToOneField("ai_workspace.File", null=True, on_delete=models.CASCADE,
                    related_name="file_filecontroller")
    related_model_string = models.TextField()

    def update_file(self, file, related_model_string, contentfile_id):
        self.file = file
        self.related_model_string = related_model_string
        self.save()
        obj, created = apps.get_model(self.related_model_string).objects.\
            get_or_create(contentfile_id=contentfile_id)
        obj.controller.add(self)
        return self

    @property
    def get_file(self):
        return apps.get_model(self.related_model_string).objects\
            .filter(**{"controller__in": self}).first()






