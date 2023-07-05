import os

from django.core.validators import FileExtensionValidator
from django.db import models
from ai_auth.models import AiUser
from ai_workspace.models import Project, Job, Task


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
    # threshold = models.IntegerField(null=True, blank=True, default=85)
    # max_hits = models.IntegerField(null=True, blank=True, default=5)

    @property
    def filename(self):
        return  os.path.basename(self.tmx_file.file.name)

    @property
    def owner_pk(self):
        return self.project.owner_pk
    
    @property
    def proj_obj(self):
        return self.project


class WordCountGeneral(models.Model):
    project = models.ForeignKey(Project, related_name="project_wc_general", null=False, blank=False, \
                                on_delete=models.CASCADE)
    tasks =  models.ForeignKey(Task, related_name="task_wc_general", null=False, blank=False, \
                                on_delete=models.CASCADE)
    new_words = models.IntegerField(null=True, blank=True,default=0)
    repetition = models.IntegerField(null=True, blank=True,default=0)
    cross_file_rep = models.IntegerField(null=True, blank=True,default=0)
    tm_100 = models.IntegerField(null=True, blank=True,default=0)
    tm_95_99 = models.IntegerField(null=True, blank=True,default=0)
    tm_85_94 = models.IntegerField(null=True, blank=True,default=0)
    tm_75_84 = models.IntegerField(null=True, blank=True,default=0)
    tm_50_74 = models.IntegerField(null=True, blank=True,default=0)
    tm_101 = models.IntegerField(null=True,blank=True,default=0)
    tm_102 = models.IntegerField(null=True,blank=True,default=0)
    raw_total = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.project.project_name + "_wwc"

class CharCountGeneral(models.Model):
    project = models.ForeignKey(Project, related_name="project_cc_general", null=False, blank=False, \
                                on_delete=models.CASCADE)
    tasks =  models.ForeignKey(Task, related_name="task_cc_general", null=False, blank=False, \
                                on_delete=models.CASCADE)
    new_words = models.IntegerField(null=True, blank=True,default=0)
    repetition = models.IntegerField(null=True, blank=True,default=0)
    cross_file_rep = models.IntegerField(null=True, blank=True,default=0)
    tm_100 = models.IntegerField(null=True, blank=True,default=0)
    tm_95_99 = models.IntegerField(null=True, blank=True,default=0)
    tm_85_94 = models.IntegerField(null=True, blank=True,default=0)
    tm_75_84 = models.IntegerField(null=True, blank=True,default=0)
    tm_50_74 = models.IntegerField(null=True, blank=True,default=0)
    tm_101 = models.IntegerField(null=True,blank=True,default=0)
    tm_102 = models.IntegerField(null=True,blank=True,default=0)
    raw_total = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.project.project_name + "_wcc"

class UserDefinedRate(models.Model):
    user = models.ForeignKey(AiUser, related_name="analysis_default", null=True, blank=True, \
                                     on_delete=models.CASCADE)
    base_rate = models.DecimalField(max_digits=5,decimal_places=2,blank=True, null=True)
    #currency
    tm_100_percentage = models.IntegerField(null=True,blank=True,default=30)
    tm_95_99_percentage = models.IntegerField(null=True,blank=True,default=60)
    tm_85_94_percentage = models.IntegerField(null=True,blank=True,default=60)
    tm_75_84_percentage = models.IntegerField(null=True,blank=True,default=60)
    tm_50_74_percentage = models.IntegerField(null=True,blank=True,default=100)
    tm_101_percentage = models.IntegerField(null=True,blank=True,default=30)#Need to confirm
    tm_102_percentage = models.IntegerField(null=True,blank=True,default=30)#Need to confirm
    tm_repetition_percentage = models.IntegerField(null=True,blank=True,default=30)
    is_default = models.BooleanField(default=False)

class WordCountTmxDetail(models.Model):
    word_count = models.ForeignKey(WordCountGeneral, related_name="wc_general", null=False, blank=False, \
                                on_delete=models.CASCADE)
    tmx_file = models.ForeignKey(TmxFileNew, null=True, blank=True, related_name="tmx_file_included",
                                on_delete=models.SET_NULL)
    tmx_file_obj_id = models.IntegerField(null=True, blank=True)
# class WordCountGeneral(models.Model):
#     project = models.ForeignKey(Project, related_name="project_wc_general", null=False, blank=False, \
#                                 on_delete=models.CASCADE)
#     tasks =  models.ForeignKey(Task, related_name="task_wc_general", null=False, blank=False, \
#                                 on_delete=models.CASCADE)
#     new_words = models.IntegerField(null=True, blank=True)
#     repetition = models.IntegerField(null=True, blank=True)
#     cross_file_rep = models.IntegerField(null=True, blank=True)
#     tm_101 = models.IntegerField(null=True,blank=True)
#     tm_102 = models.IntegerField(null=True,blank=True)
#     raw_total = models.IntegerField(null=True, blank=True)
#
#     def __str__(self):
#         return self.project.project_name + "_wwc"
#
# class ProjectAnalysisTemplate(models.Model):
#     user = models.ForeignKey(AiUser, related_name="analysis_template", null=True, blank=True, \
#                                 on_delete=models.CASCADE)
#     template_name = models.CharField(max_length=500, null=True, blank=True,)
#     base_rate = models.DecimalField(max_digits=5,decimal_places=2,blank=True, null=True)
#     is_default = models.BooleanField(default=False)
#
# class DefinedRange(models.Model):
#     start = models.IntegerField(null=True,blank=True)
#     end = models.IntegerField(null=True,blank=True)
#     percentage =  models.IntegerField(null=True,blank=True)
#     template =  models.ForeignKey(ProjectAnalysisTemplate, related_name="template", null=True, blank=True, \
#                                 on_delete=models.CASCADE)
#
# class WordCount(models.Model):
#     project = models.ForeignKey(Project, related_name="project_wc", null=False, blank=False, \
#                                 on_delete=models.CASCADE)
#     tasks =  models.ForeignKey(Task, related_name="task_wc", null=False, blank=False, \
#                                 on_delete=models.CASCADE)
#     defined_range =  models.ForeignKey(DefinedRange, related_name="range", null=False, blank=False, \
#                                 on_delete=models.CASCADE)
#     words = models.IntegerField(null=True, blank=True)
