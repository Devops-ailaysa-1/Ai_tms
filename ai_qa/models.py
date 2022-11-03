from django.db import models
from django.core.validators import FileExtensionValidator
from ai_workspace.models import Project,Job
import os
from .signals import delete_words_from_ForbiddenWords,update_words_from_forbidden_file,update_words_from_untranslatable_file,delete_words_from_Untranslatable
from django.db.models.signals import post_save, pre_save, post_delete

class Forbidden(models.Model):
    def forbidden_file_path(instance, filename):
        return os.path.join(instance.project.ai_user.uid,instance.project.ai_project_id,\
            "forbidden", filename)
    forbidden_file = models.FileField(upload_to=forbidden_file_path,
                    validators=[FileExtensionValidator(allowed_extensions=["txt"])])
    project = models.ForeignKey(Project, on_delete=models.CASCADE,related_name="proj_forbidden_file",null=True,blank=True)
    job     = models.ForeignKey(Job, on_delete=models.CASCADE,related_name='job_forbidden_file',null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

post_save.connect(update_words_from_forbidden_file, sender=Forbidden)
post_delete.connect(delete_words_from_ForbiddenWords, sender=Forbidden)


class ForbiddenWords(models.Model):
    words = models.CharField(max_length=500, null=True, blank=True)
    file = models.ForeignKey(Forbidden, on_delete=models.CASCADE, related_name='forbidden_word_file',null=True,blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE,related_name="word_proj",null=True,blank=True)
    job     = models.ForeignKey(Job, on_delete=models.CASCADE,related_name='word_job',null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)


class Untranslatable(models.Model):
    def untranslatable_file_path(instance, filename):
        return os.path.join(instance.project.ai_user.uid,instance.project.ai_project_id,\
            "untranslatable", filename)
    untranslatable_file = models.FileField(upload_to=untranslatable_file_path,
                    validators=[FileExtensionValidator(allowed_extensions=["txt"])])
    project = models.ForeignKey(Project, on_delete=models.CASCADE,related_name="proj_untranslatable_file",null=True,blank=True)
    job     = models.ForeignKey(Job, on_delete=models.CASCADE,related_name='job_untranslatable_file',null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

post_save.connect(update_words_from_untranslatable_file, sender=Untranslatable)
post_delete.connect(delete_words_from_Untranslatable, sender=Untranslatable)


class UntranslatableWords(models.Model):
    words = models.CharField(max_length=500, null=True, blank=True)
    file = models.ForeignKey(Untranslatable, on_delete=models.CASCADE, related_name='untranslatable_word_file',null=True,blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE,related_name="untrans_word_proj",null=True,blank=True)
    job     = models.ForeignKey(Job, on_delete=models.CASCADE,related_name='untrans_word_job',null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

#
# # class UserFile(models.Model):
# #     file    = models.FileField(null=True )
# #     Letterfile = models.FileField(null=True)
#
# class Untranslatables(models.Model):
#     untranslatables = models.CharField ( max_length=1000, null= False, blank = False)
#
# class Untranslatable(models.Model):
#     doc_id  = models.CharField(max_length=10)
#     file    = models.FileField(upload_to='untranslatable_words')
#     created_at = models.DateTimeField(auto_now_add=True)
#
# class LetterCase(models.Model):
#     doc_id  = models.CharField(max_length=10)
#     file    = models.FileField(upload_to='lettercase_words')
#     created_at = models.DateTimeField(auto_now_add=True)
