from django.db import models, IntegrityError
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import User
from django.utils.text import slugify
from datetime import datetime
from enum import Enum
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.contrib.auth import settings
import os
from ai_auth.models import AiUser
from ai_staff.models import Languages

from .manager import AilzaManager
from .utils import create_dirs_if_not_exists
from .signals import (create_allocated_dirs, create_project_dir, create_pentm_dir_of_project,
    set_pentm_dir_of_project)

# class AilzaUser(AbstractBaseUser):
#     email = models.EmailField(unique=True, null=False)
#     username = models.CharField(max_length=255, null=True, blank=True)
#     created_at = models.DateTimeField(auto_now=True)
#     deleted_at = models.DateTimeField(null=True, blank=True)
#     allocated_dir = models.CharField(max_length=255, null=True, blank=True)
#     # role = models.ForeignKey(Role)

#     USERNAME_FIELD = "email"
#     objects = AilzaManager()

#     def delete(self):
#         self.deleted_at = datetime.now()
#         return self.save()

#     def hard_delete(self):
#         return super(AilzaUser, self).delete()

# pre_save.connect(create_allocated_dirs, sender=AilzaUser)
            
class PenseiveTM(models.Model):
    penseive_tm_dir_path = models.CharField(max_length=1000, null=True, blank=True)  # Common for a project 
    project = models.OneToOneField("Project", null=False, blank=False, on_delete=models.CASCADE)

pre_save.connect(set_pentm_dir_of_project, sender=PenseiveTM)

class Project(models.Model):
    project_name = models.CharField(max_length=50, null=False, blank=False,)
    project_dir_path = models.CharField(max_length=1000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True)
    ai_user = models.ForeignKey(AiUser, null=False, blank=False, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("project_name", "ai_user")

    penseive_tm_klass = PenseiveTM

    def save(self, *args, **kwargs):
        try:
            return super().save(*args, **kwargs)
        except Exception as e:
            print("error--->", e)
            raise ValueError("project name should be unique")

pre_save.connect(create_project_dir, sender=Project)
post_save.connect(create_pentm_dir_of_project, sender=Project,)

# class Language(models.Model):
#     language_name = models.CharField(max_length=50, null=False, blank=False)
#     language_code = models.CharField(max_length=20, null=False, blank=False)

class Job(models.Model):
    source_language = models.ForeignKey(Languages, null=False, blank=False, on_delete=models.CASCADE, 
                        related_name="source_lang")
    target_language = models.ForeignKey(Languages, null=False, blank=False, on_delete=models.CASCADE, 
                        related_name="target_language")
    project = models.ForeignKey(Project, null=False, blank=False, on_delete=models.CASCADE, 
                related_name="project_jobs_set")

    class Meta:
        unique_together = ("project", "source_language", "target_language")

class FileSubTypes(Enum):
    RESOURCES = "resources"
    REFERENCES = "references"

class FileTypes(Enum):
    TRANSLATABLE = "translatable"
    UNTRANSLATABLE = "untranslatable"

    def get_path(self, sub_dir=""):
        if self == FileTypes.TRANSLATABLE:
            return os.path.join(self.value, sub_dir)
        if self == FileTypes.UNTRANSLATABLE:
            if not isinstance(sub_dir, FileSubTypes):
                sub_dir = FileSubTypes.RESOURCES    
                #raise ValueError("sub directory name required!!!")
            return os.path.join(self.value, sub_dir.value)

def get_file_upload_path(instance, filename):
    file_path = FileTypes(instance.file_type.lower()).get_path()
    return os.path.join(instance.project.project_dir_path, file_path, filename)

class File(models.Model):
    file_type = models.CharField(max_length=100, choices=[(file_type.name, file_type.value) 
                    for file_type in FileTypes], null=False, blank=False)
    file = models.FileField(upload_to=get_file_upload_path, null=False, blank=False, max_length=1000)
    project = models.ForeignKey(Project, null=False, blank=False, on_delete=models.CASCADE, 
                related_name="project_files_set")

class VersionChoices(Enum):
    POST_EDITING = "post_editing"

class Version(models.Model):
    version_name = models.CharField(max_length=100, choices=[(version.name, version.value) 
                        for version in VersionChoices], null=False, blank=False)
    project = models.ForeignKey(Project, null=False, blank=False, on_delete=models.CASCADE, 
                related_name="project_versions_set")   


class Task(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE, null=False, blank=False,
            related_name="file_tasks_set")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=False, blank=False,
            related_name="job_tasks_set")
    version = models.ForeignKey(Version, on_delete=models.CASCADE, null=False, blank=False,
            related_name="version_tasks_set")
    assign_to = models.ForeignKey(AiUser, on_delete=models.CASCADE, null=False, blank=False,
            related_name="user_tasks_set")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['file', 'job', 'version'], name=\
                'file, job, version combination unique'), 
        ]


# /////////////////////// References \\\\\\\\\\\\\\\\\\\\\\\\
# 
# from django.core.validators import EmailValidator
# EmailValidator().validate_domain_part(".com")  ---> False
# EmailValidator().validate_domain_part("l.com")  ---> True

