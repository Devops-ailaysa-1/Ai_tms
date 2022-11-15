import os

from django.core.validators import FileExtensionValidator
from django.db import models

from ai_workspace.models import Project, Job


def tmx_file_path(instance, filename):
    return os.path.join(instance.project.ai_user.uid,instance.project.ai_project_id, "tmx", filename)

class TmxFileNew(models.Model):
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


class ProjectAnalysis(models.Model):
    project = models.ForeignKey(Project, related_name="projectanalysis", null=False, blank=False, \
                                on_delete=models.CASCADE)
    new_words = models.IntegerField(null=True, blank=True)
    repetition = models.IntegerField(null=True, blank=True)
    cross_file_rep = models.IntegerField(null=True, blank=True)
    tm_100 = models.IntegerField(null=True, blank=True)
    tm_95_99 = models.IntegerField(null=True, blank=True)
    tm_85_94 = models.IntegerField(null=True, blank=True)
    tm_75_84 = models.IntegerField(null=True, blank=True)
    tm_50_74 = models.IntegerField(null=True, blank=True)
    tm_102 = models.IntegerField(null=True, blank=True)
    tm_101 = models.IntegerField(null=True, blank=True)
    raw_total = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.project.project_name + "_wwc"
