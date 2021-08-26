from ai_staff.serializer import AiSupportedMtpeEnginesSerializer
from ai_auth.utils import get_unique_pid
from django.db import models, IntegrityError
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import User
from django.db.models.base import Model
from django.utils.text import slugify
from datetime import datetime
from enum import Enum
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.contrib.auth import settings
import os
from ai_auth.models import AiUser
from ai_staff.models import AilaysaSupportedMtpeEngines, AssetUsageTypes,\
    ContentTypes, Languages, SubjectFields
from ai_staff.models import ContentTypes, Languages, SubjectFields
from ai_workspace_okapi.models import Document, Segment
from ai_staff.models import ParanoidModel
from django.shortcuts import reverse
from django.core.validators import FileExtensionValidator
from ai_workspace_okapi.utils import get_processor_name, get_file_extension
from django.db.models import Q

from .manager import AilzaManager
from .utils import create_dirs_if_not_exists
from .signals import (create_allocated_dirs, create_project_dir, \
    create_pentm_dir_of_project,set_pentm_dir_of_project, \
    check_job_file_version_has_same_project)
from .manager import ProjectManager, FileManager, JobManager,\
    TaskManager

def set_pentm_dir(instance):
    path = os.path.join(instance.project.project_dir_path, ".pentm")
    create_dirs_if_not_exists(path)
    return path

class TempProject(models.Model):
    temp_proj_id =  models.CharField(max_length=50 , null=False, blank=True)

    def save(self, *args, **kwargs):
        if not self.temp_proj_id:
            self.temp_proj_id = get_unique_pid(TempProject)
        return super().save(*args, **kwargs)

def get_temp_file_upload_path(instance, filename):
    file_path = os.path.join("temp_projects",instance.temp_proj.temp_proj_id,\
            "source")
    return os.path.join(file_path, filename)

class TempFiles(models.Model):
    temp_proj = models.ForeignKey(TempProject, on_delete=models.CASCADE,
        related_name="temp_proj_file")
    files_temp = models.FileField(upload_to=get_temp_file_upload_path,\
        null=False, blank=False, max_length=1000)

class Templangpair(models.Model):
    temp_proj = models.ForeignKey(TempProject, on_delete=models.CASCADE,
                        related_name="temp_proj_langpair")
    temp_src_lang = models.ForeignKey(Languages, null=False, blank=False, on_delete=\
        models.CASCADE, related_name="temp_source_lang")
    temp_tar_lang = models.ForeignKey(Languages, null=False, blank=False, on_delete=\
        models.CASCADE, related_name="temp_target_lang")

class PenseiveTM(models.Model):
    penseive_tm_dir_path = models.FilePathField(max_length=1000, null=True,\
        path=settings.MEDIA_ROOT, blank=True, allow_folders=True, allow_files=False)
    source_tmx_dir_path = models.FilePathField(max_length=1000, null=True, \
        path=settings.MEDIA_ROOT, blank=True, allow_folders=True, allow_files=False)
    project = models.OneToOneField("Project", null=False, blank=False, on_delete=models.\
        CASCADE, related_name="project_penseivetm")

    class Meta:
        managed = False

pre_save.connect(set_pentm_dir_of_project, sender=PenseiveTM)

class Project(ParanoidModel):
    project_name = models.CharField(max_length=50, null=True, blank=True,)
    project_dir_path = models.FilePathField(max_length=1000, null=True,\
        path=settings.MEDIA_ROOT, blank=True, allow_folders=True, allow_files=False)
    created_at = models.DateTimeField(auto_now=True)
    ai_user = models.ForeignKey(AiUser, null=False, blank=False, on_delete=models.CASCADE)
    ai_project_id = models.TextField()
    mt_engine = models.ForeignKey(AilaysaSupportedMtpeEngines, null=True, blank=True, \
        on_delete=models.CASCADE, related_name="proj_mt_engine")

    class Meta:
        unique_together = ("project_name", "ai_user")
        managed = False

    objects = ProjectManager()

    def __str__(self):
        return self.project_name

    __repr__ = __str__

    penseive_tm_klass = PenseiveTM


    def save(self, *args, **kwargs):
        ''' try except block created for logging the exception '''
        if not self.ai_project_id:
            # self.ai_user shoould be set before save
            self.ai_project_id = self.ai_user.uid+"p"+str(Project.\
            objects.filter(ai_user=self.ai_user).count()+1)
        if not self.project_name:
            self.project_name = self.ai_project_id
        super().save()

    @property
    def progress(self):
        docs = Document.objects.filter(job__project_id=self.id).all()
        total_segments = 0
        if not docs:
            return "Yet to start"
        else:
            for doc in docs:
                total_segments+=doc.total_segment_count

        status_count = Segment.objects.filter(Q(text_unit__document__job__project_id=self.id) &
            Q(status_id__in=[102,104,106])).all().count()

        if total_segments == status_count:
            return "Completed"

        else:
            return "In Progress"

    @property
    def files_and_jobs_set(self):
        return  \
            ( # jobs will not exceed 100nos, and files will not exceed 10nos,
            # so all() functionality used...
            self.project_jobs_set.all(),
            self.project_files_set.all()
            )

    @property
    def _assign_tasks_url(self):
        return reverse("", kwargs={"project_id":self.id})

    @property
    def get_tasks(self):
        return [task for job in self.project_jobs_set.all() for task \
            in job.job_tasks_set.all()\
                ]

    @property
    def files_jobs_choice_url(self):
        return reverse("get-files-jobs-by-project_id", kwargs={"project_id": self.id})

    @property
    def source_language(self):
        return self.project_jobs_set.first().source_language_code

    @property
    def _source_language(self):
        lang = self.project_jobs_set.first().source__language
        return {"id": lang.id, "language": lang.language}

    @property
    def _target_languages(self):
        return [{"id":job.target__language.id, "language": job.target__language.language} \
            for job in self.project_jobs_set.all()]

    @property
    def source_language_code(self):
        return self.project_jobs_set.first().source_language_code

    @property
    def target_language_codes(self):
        return [job.target_language_code for job in self.project_jobs_set.all()]

    @property
    def pentm_path(self):
        return self.project_penseivetm.penseive_tm_dir_path

    @property
    def tmx_files_path(self):
        return [tmx_file.tmx_file.path for tmx_file in self.project_tmx_files.all()]

    @property
    def tmx_files_path_not_processed(self):
        return {tmx_file.id:tmx_file.tmx_file.path for tmx_file in self.project_tmx_files\
            .filter(is_processed=False).all()\
                }

pre_save.connect(create_project_dir, sender=Project)
post_save.connect(create_pentm_dir_of_project, sender=Project,)


class ProjectContentType(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE,
                        related_name="proj_content_type")
    content_type = models.ForeignKey(ContentTypes, on_delete=models.CASCADE,
                        related_name="proj_content_type_name")

class ProjectSubjectField(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE,
                        related_name="proj_subject")
    subject = models.ForeignKey(SubjectFields, on_delete=models.CASCADE,
                        related_name="proj_sub_name")

class Job(models.Model):
    source_language = models.ForeignKey(Languages, null=False, blank=False, on_delete=models.CASCADE,\
        related_name="source_language")
    target_language = models.ForeignKey(Languages, null=False, blank=False, on_delete=models.CASCADE,\
        related_name="target_language")
    project = models.ForeignKey(Project, null=False, blank=False, on_delete=models.CASCADE,\
        related_name="project_jobs_set",)
    job_id =models.TextField(null=True, blank=True)
    deleted_at = models.BooleanField(default=False)

    class Meta:
        unique_together = [("project", "source_language", "target_language")]

    objects = JobManager()

    def save(self, *args, **kwargs):
        ''' try except block created for logging the exception '''
        if not self.job_id:
            # self.ai_user shoould be set before save
            self.job_id = self.project.ai_project_id+"j"+str(Job.objects.filter(project=self.project)\
                .count()+1)
        super().save()

    @property
    def source_target_pair(self): # code repr
        return "%s-%s"%(self.source_language.locale.first().locale_code,\
            self.target_language.locale.first().locale_code)

    @property
    def source_target_pair_names(self):
        return "%s->%s"%(
            self.source_language.language,
            self.target_language.language
        )

    @property
    def source_language_code(self):
        return self.source_language.locale.first().locale_code

    @property
    def target_language_code(self):
        return self.target_language.locale.first().locale_code

    @property
    def source__language(self):
        return self.source_language.locale.first().language

    @property
    def target__language(self):
        return self.target_language.locale.first().language

    def __str__(self):
        return self.source_language.language+"->"+self.target_language.language

class FileTypes(models.Model):
    TERMBASE = "termbase"
    QA_UNTRANSLATABLE = "untranslatable"
    QA_BLOCKEDTEXT= "blockedtext"
    TRANSLATION_MEMORY="translation_memory"
    SOURCE = "source"
    REFERENCE = "reference"
    FILETYPES = [
        (SOURCE, 'Src'),
        (REFERENCE, 'Ref'),
        (TRANSLATION_MEMORY, 'TM'),
        (QA_BLOCKEDTEXT, 'qa_BT'),
        (QA_UNTRANSLATABLE, 'qa_UT'),
        (TERMBASE, 'TB'),
    ]
    file_type_name = models.CharField(
    max_length=100,
    choices=FILETYPES,
    )
    file_type_path = models.CharField(max_length=100)

def get_file_upload_path(instance, filename):
    file_path = os.path.join(instance.project.ai_user.uid,instance.project.ai_project_id,instance.usage_type.type_path)
    instance.filename = filename
    # print("path--->", os.path.join(instance.project.project_dir_path.replace( settings.MEDIA_ROOT, ""), file_path, filename))
    # project Directory Should be Relative Path
    return os.path.join(file_path, filename)

class File(models.Model):
    # file_type = models.CharField(max_length=100, choices=[(file_type.name, file_type.value)
    #                 for file_type in FileTypes], null=False, blank=False)
    usage_type = models.ForeignKey(AssetUsageTypes,null=False, blank=False,\
                on_delete=models.CASCADE, related_name="project_usage_type")
    file = models.FileField(upload_to=get_file_upload_path, null=False,\
                blank=False, max_length=1000)
    project = models.ForeignKey(Project, null=False, blank=False, on_delete=models.\
                CASCADE, related_name="project_files_set")
    filename = models.CharField(max_length=200,null=True)
    fid = models.TextField(null=True, blank=True)
    deleted_at = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        ''' try except block created for logging the exception '''
        if not self.fid:
            # self.ai_user shoould be set before save
            self.fid = str(self.project.ai_project_id)+"f"+str(File.objects\
                .filter(project=self.project.id).count()+1)
        super().save()

    objects = FileManager()

    def __str__(self):
        return self.filename

    @property
    def use_type(self):
        return self.usage_type.use_type

    @property
    def owner(self):
        return self.project.ai_user # created by

    @property
    def get_source_file_path(self):
        return self.file.path

    @property
    def output_file_path(self):
        return '.out'.join( os.path.splitext(self.get_source_file_path))

    @property
    def get_file_name(self):
        return self.filename

    @property
    def get_source_tmx_path(self):
        prefix, ext = os.path.splitext(self.filename)
        return os.path.join(self.project.project_penseivetm.source_tmx_dir_path, prefix+".tmx")

    @property
    def source_language(self):
        return self.project.source_language

    @property
    def target_language(self):
        return "ta"

class VersionChoices(Enum):# '''need to discuss with senthil sir, what are the choices?'''

    POST_EDITING = "post_editing"

class Version(models.Model):
    # 'n' number versions can be set to a specific project...it cannot be a job specific or file specific
    version_name = models.CharField(max_length=100, choices=[(version.name, version.value)
                        for version in VersionChoices], null=False, blank=False)
    # project = models.ForeignKey(Project, null=False, blank=False, on_delete=models.CASCADE,
    #             related_name="project_versions_set")

    def __str__(self):
        return self.version_name

class Task(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE, null=False, blank=False,
            related_name="file_tasks_set")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=False, blank=False,
            related_name="job_tasks_set")
    version = models.ForeignKey(Version, on_delete=models.CASCADE, null=False, blank=False,
            related_name="version_tasks_set")
    assign_to = models.ForeignKey(AiUser, on_delete=models.CASCADE, null=False, blank=False,
            related_name="user_tasks_set")
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True,)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['file', 'job', 'version'], name=\
                'file, job, version combination unique'),
        ]

    objects = TaskManager()

    @property
    def get_document_url(self):
        return reverse("ws_okapi:document", kwargs={"task_id": self.id})

    @property
    def extension(self):
        try:ret=get_file_extension(self.file.file.path)
        except:ret=''
        return ret 

    @property
    def processor_name(self):
        return  get_processor_name(self.file.file.path).get("processor_name", None)

    @property
    def get_progress(self):
        confirm_list = [102, 104, 106]
        total_segment_count = self.document.total_segment_count
        segments_confirmed_count = self.document.segments.filter(
            status__status_id__in=confirm_list
        ).count()
        return {"total_segments":total_segment_count,\
                "confirmed_segments":segments_confirmed_count}

    def __str__(self):
        return "file=> "+ str(self.file) + ", job=> "+ str(self.job)

pre_save.connect(check_job_file_version_has_same_project, sender=Task)

class TmxFile(models.Model):

    def tmx_file_path(instance, filename):
        return os.path.join(instance.project.ai_user.uid,instance.project.ai_project_id, "tmx", filename)

    tmx_file = models.FileField(upload_to=tmx_file_path,
                    validators=[FileExtensionValidator(allowed_extensions=["tmx"])])
    project = models.ForeignKey(Project, on_delete=models.CASCADE,
                related_name="project_tmx_files")
    is_processed = models.BooleanField(default=False)
    is_failed = models.BooleanField(default=False)

# /////////////////////// References \\\\\\\\\\\\\\\\\\\\\\\\
#
# from django.core.validators import EmailValidator
# EmailValidator().validate_domain_part(".com")  ---> False
# EmailValidator().validate_domain_part("l.com")  ---> True
# p1 = Project.objects.last()
# In [8]: p1.penseivetm.penseive_tm_dir_path
# Out[8]: '/ai_home/media/user_2/p14/.pentm'

def tbx_file_upload_path(instance, filename):
    file_path = os.path.join(instance.project.project_dir_path,"tbx",filename)
    return file_path

class Tbxfiles(models.Model):
    # tbx_files = models.FileField(upload_to=tbx_file_upload_path, null=False, blank=False, max_length=1000)  # Common for a project
    tbx_file = models.FileField(upload_to="uploaded_tbx_files", null=False,\
            blank=False, max_length=1000)  # Common for a project
    project = models.ForeignKey("Project", null=False, blank=False,\
            on_delete=models.CASCADE)
