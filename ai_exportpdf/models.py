from django.db import models
from django.utils.text import slugify
from ai_auth.models import AiUser
from ai_workspace.models import Task
import os
from django.core.files.storage import FileSystemStorage
from ai_staff.models import ( Languages,PromptCategories,PromptStartPhrases,
                              PromptSubCategories,PromptTones,ModelGPTName)
from ai_workspace.signals import invalidate_cache_on_save,invalidate_cache_on_delete
from django.db.models.signals import post_save, pre_save, post_delete, pre_delete



def user_directory_path(instance, filename):
    count = Ai_PdfUpload.objects.filter(file_name__contains=filename).count()
    if count!=0:
        filename = str(filename).split(".pdf")[0] + "_" + str(count) + ".pdf"
    return '{0}/{1}/{2}'.format(instance.user.uid, "pdf_file",filename)


def user_directory_path_image_gen(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "image_generation",filename)

def user_directory_path_image_gen_result(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "image_generation_result",filename)

def edited_file_path(instance, filename):
    if instance.task:
        file_path = os.path.join(instance.task.job.project.ai_user.uid,instance.task.job.project.ai_project_id,instance.task.file.usage_type.type_path,\
                "Edited", filename)
    else:
        file_path = os.path.join(instance.user.uid,"Edited", filename)
    return file_path

def pdf_converted_file_path(instance, filename):
    file_path = os.path.join(instance.user.uid,"pdf_file", filename)
    return file_path



class Ai_PdfUpload(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    pdf_file = models.FileField(upload_to=user_directory_path,blank=False, null=False)#,storage=MyStorage())
    docx_url_field = models.URLField(null=True, blank=True)
    #docx_file = models.FileField(upload_to=pdf_converted_file_path,null=True,blank=True)
    pdf_file_name = models.CharField(max_length=200 , null=True, blank=True)
    pdf_task_id = models.CharField(max_length=200 , null=True, blank=True)
    pdf_conversion_sec = models.IntegerField(null=True, blank=True)
    pdf_language = models.CharField(max_length=200 , null=True, blank=True)
    pdf_format_option = models.CharField(max_length=200 , null=True, blank=True)
    pdf_api_use =models.CharField(max_length=200 , null=True, blank=True)
    pdf_no_of_page =  models.IntegerField(null=True, blank=True)
    counter = models.IntegerField(null=True, blank=True )
    status = models.CharField(max_length=200 , null=True, blank=True)
    #slug = models.SlugField(default="", blank=True, null=True, db_index=True)
    docx_file_name = models.CharField(max_length=200 , null=True, blank=True)
    updated_count = models.IntegerField(blank=True,null=True)
    file_name = models.CharField(max_length=200 , null=True, blank=True)
    task = models.ForeignKey(to = Task, on_delete = models.CASCADE , null=True, blank=True, related_name = 'pdf_task' )
    docx_file_from_writer = models.FileField(upload_to=edited_file_path  , blank=True, null=True)
    html_data =  models.TextField(null=True,blank=True)
    translation_task_created = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    created_by = models.ForeignKey(AiUser, null=True, blank=True, on_delete=models.SET_NULL,related_name = 'pdf_created_by')

    def save(self, *args, **kwargs):
        # if self.id:
        #     count = Ai_PdfUpload.objects.filter(file_name__contains=self.file_name).exclude(id=self.id).count()
        # else:
        #     count = Ai_PdfUpload.objects.filter(file_name__contains=self.file_name).count()
        # print(count)
        # if count!=0:
        #     self.pdf_file_name = str(self.file_name).split(".pdf")[0] + "(" + str(count) + ").pdf"
        return super().save()
    @property
    def filename(self):
        return  os.path.basename(self.pdf_file.file.name)


    def generate_cache_keys(self):
        cache_keys = [
            f'task_translated_{self.task.pk}',
            f'task_converted_{self.task.pk}',
        ]
        return cache_keys
    # def __str__(self):
    #     return self.name
post_save.connect(invalidate_cache_on_save, sender=Ai_PdfUpload)
pre_delete.connect(invalidate_cache_on_delete, sender=Ai_PdfUpload) 

# class MyStorage(FileSystemStorage):

#     def get_available_name(self, name, max_length=None):
#         if self.exists(name):
#             print("Name------->",name)
#             #count = Ai_PdfUpload.objects.filter(file_name__contains=name).count()
#             #name = str(name).split(".pdf")[0] + "(" + str(count) + ").pdf"
#             # dir_name, file_name = os.path.split(name)
#             # file_root, file_ext = os.path.splitext(file_name)            

#             # my_chars = 'abcde'  # The characters you want to append

#             # name = os.path.join(dir_name, '{}_{}{}'.format(file_root, my_chars, file_ext))
#         return name