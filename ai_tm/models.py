import os

from django.core.validators import FileExtensionValidator
from django.db import models

from ai_workspace.models import Project, Job


def tmx_file_path(instance, filename):
    return os.path.join(instance.project.ai_user.uid,instance.project.ai_project_id, "tmx", filename)

class TmxFile(models.Model):
    project = models.ForeignKey(Project, null=False, blank=False, related_name="tmx_file_project",
                                on_delete=models.CASCADE)
    job = models.ForeignKey(Job, null=True, blank=True, related_name="tmx_file_job", on_delete=models.CASCADE)
    tmx_file = models.FileField(upload_to=tmx_file_path,
                            validators=[FileExtensionValidator(allowed_extensions=["tmx"])])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    @property
    def filename(self):
        return  os.path.basename(self.tmx_file.file.name)
