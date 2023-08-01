from django.db import models
from ai_staff.models import Languages, AilaysaSupportedMtpeEngines
from ai_auth.models import AiUser
from django.db.models.fields.files import FieldFile, FileField
from ai_workspace.models import Project,Job,Task
import os
from .manager import GlossaryTasksManager
from ai_staff.models import AssetUsageTypes
from django.contrib.auth import settings
from django.core.validators import FileExtensionValidator
from django.db.models.signals import post_save, pre_save, post_delete
from ai_glex.signals import update_words_from_template,delete_words_from_term_model
# Create your models here.
##########  GLOSSARY GENERAL DETAILS #############################
class Glossary(models.Model):
    class GlossaryObjects(models.Manager):
        def get_queryset(self):
            return super().get_queryset().filter(usage_permission='Public')
    options =(
        ('Public', 'Public'),
        ('Private', 'Private'),
    )
    project = models.OneToOneField(Project, null=False, blank=False, on_delete=models.CASCADE, related_name="glossary_project")
    primary_glossary_source_name = models.CharField(max_length=20, null=True, blank=True)
    details_of_PGS          = models.TextField(null=True, blank=True)
    source_Copyright_owner  = models.CharField(max_length=50, null=True, blank=True)
    notes                   = models.TextField(verbose_name = "Glossary General Notes", null=True, blank=True)
    usage_permission        = models.CharField(max_length=30, verbose_name = "Usage Permission", choices=options, default='Private', null=True, blank=True)
    public_license          = models.CharField(max_length=30, verbose_name = "Public License", null=True, blank=True)
    created_date            = models.DateTimeField(auto_now_add=True)
    modified_date           = models.DateTimeField(auto_now=True)
    objects = models.Manager() # default built-in manager
    glossaryobjects = GlossaryObjects() # object manager for Glossary model
    def __str__(self):
        return self.project.project_name
    
    @property
    def owner_pk(self):
        return self.project.owner_pk


def get_file_upload_path(instance, filename):
    file_path = os.path.join(instance.project.ai_user.uid,instance.project.ai_project_id,\
            instance.usage_type.type_path)
    print("Upload file path ----> ", file_path)
    instance.filename = filename
    return os.path.join(file_path, filename)

use_spaces = os.environ.get("USE_SPACES")



######### GLOSSARY & FILES MODEL ###############
class GlossaryFiles(models.Model):
    usage_type = models.ForeignKey(AssetUsageTypes,null=False, blank=False,\
                on_delete=models.CASCADE, related_name="glossary_project_usage_type")
    file = FileField(upload_to=get_file_upload_path, null=False,\
                blank=False, max_length=1000,validators=[FileExtensionValidator(allowed_extensions=["xlsx"])] )
    project = models.ForeignKey(Project, null=False, blank=False, on_delete=models.\
                CASCADE, related_name="project_files")
    filename = models.CharField(max_length=200,null=True)
    fid = models.TextField(null=True, blank=True)
    job = models.ForeignKey(Job,on_delete=models.CASCADE,related_name="job")
    source_only = models.BooleanField(default=False)
    deleted_at = models.BooleanField(default=False)
    upload_date = models.DateTimeField(auto_now_add=True)

    # def __str__(self):
    #     return self.file_name

post_save.connect(update_words_from_template, sender=GlossaryFiles)
post_delete.connect(delete_words_from_term_model, sender=GlossaryFiles)
###############################################################################

class TermsModel(models.Model):
    sl_term         = models.CharField(max_length=200, null=False, blank=False)
    tl_term         = models.CharField(max_length=200, null=True, blank=True)
    pos             = models.CharField(max_length=200, null=True, blank=True)
    sl_definition   = models.TextField(max_length=1000, blank=True, null=True)
    tl_definition   = models.TextField(max_length=1000, blank=True, null=True)
    context         = models.TextField(max_length=1000, blank=True, null=True)
    note            = models.TextField(max_length=1000, blank=True, null=True)
    sl_source       = models.CharField(max_length=200, null=True, blank=True)
    tl_source       = models.CharField(max_length=200, null=True, blank=True)
    gender          = models.CharField(max_length=200, null=True, blank=True)
    termtype        = models.CharField(max_length=200, null=True, blank=True)
    geographical_usage = models.CharField(max_length=200, null=True, blank=True)
    usage_status    = models.CharField(max_length=200, null=True, blank=True)
    term_location   = models.CharField(max_length=200, null=True, blank=True)
    created_date    = models.DateTimeField(auto_now_add=True)
    modified_date   = models.DateTimeField(auto_now=True)
    glossary        = models.ForeignKey(Glossary, null=True, on_delete=models.CASCADE,related_name='term')
    file            = models.ForeignKey(GlossaryFiles, null=True, on_delete=models.CASCADE,related_name='term_file')
    job             = models.ForeignKey(Job, null=True, on_delete=models.CASCADE,related_name='term_job')
    #tl_term_mt      = models.CharField(max_length=200, null=True, blank=True)
    # user            = models.ForeignKey(User, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.sl_term

    def save(self, *args, **kwargs):
        super().save()
        cache_key = f'audio_file_exists_{self.pk}'
        cache.delete(cache_key)
    # @property
    # def source_language(self):
    #     return str(self.job.source_language)
    #
    # @property
    # def target_language_script(self):
    #     target_lang_id = self.job.target_language.id
    #     return LanguageMetaDetails.objects.get(language_id=target_lang_id).lang_name_in_script
class GlossaryMt(models.Model):
    task        = models.ForeignKey(Task, null=True, on_delete=models.CASCADE,related_name='term_task')
    source      = models.CharField(max_length=200, null=True, blank=True)
    target_mt   = models.CharField(max_length=200, null=True, blank=True)
    mt_engine   = models.ForeignKey(AilaysaSupportedMtpeEngines,on_delete=models.CASCADE,related_name='term_mt_engine',null=True, blank=True)



##############Glossary Tasks Model###################
class GlossaryTasks(models.Model):
    glossary = models.ForeignKey(Glossary, on_delete=models.CASCADE, related_name='task')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='job_task')
    # terms = models.ForeignKey(TermsModel, on_delete=models.CASCADE, null=True, blank=True, related_name='job_terms')
    objects = GlossaryTasksManager()
#####################################################################################

class Tbx_Download(models.Model):
    user                    = models.ForeignKey(AiUser, on_delete=models.CASCADE, null=True)
    glossary                = models.ForeignKey(Glossary, null=True, on_delete=models.CASCADE)
    termbase_Name           = models.CharField(max_length=20, null=False)
    customer                = models.TextField()
    project                 = models.TextField()
    note                    = models.TextField()

    def __str__(self):
        return self.termbase_Name


class GlossarySelected(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project')
    glossary = models.ForeignKey(Glossary,on_delete=models.CASCADE,related_name='glossary')

    class Meta:
        unique_together = ("project", "glossary")


class MyGlossary(models.Model):######Default Glossary For Each User###################
    user            = models.ForeignKey(AiUser, on_delete=models.CASCADE, related_name='default_glossary')
    sl_term         = models.CharField(max_length=200, null=True, blank=False)
    tl_term         = models.CharField(max_length=200, null=True, blank=True)
    sl_language     = models.ForeignKey(Languages, null=True, blank=True, on_delete=models.CASCADE,\
                      related_name="my_glossary_source_language")
    tl_language     = models.ForeignKey(Languages, null=True, blank=True, on_delete=models.CASCADE,\
                      related_name="my_glossary_target_language")
    # job             = models.ForeignKey(Job, null=True, on_delete=models.SET_NULL,related_name='my_glossary_job')
    project         = models.ForeignKey(Project, null=True, on_delete=models.SET_NULL,related_name = 'my_glossary_project')
    created_at      = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at      = models.DateTimeField(auto_now=True,blank=True, null=True)
    deleted_at      = models.DateTimeField(blank=True, null=True)
