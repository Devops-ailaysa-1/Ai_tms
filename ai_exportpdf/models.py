from django.db import models
from django.utils.text import slugify
from ai_auth.models import AiUser
from ai_workspace.models import Task
import os
from ai_staff.models import ( Languages,PromptCategories,PromptStartPhrases,
                              PromptSubCategories,PromptTones,ModelGPTName)

def user_directory_path(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "pdf_file",filename)

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
    pdf_file = models.FileField(upload_to=user_directory_path  , blank=False, null=False)
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
    # def __str__(self):
    #     return self.name


class TokenUsage(models.Model):
    user_input_token = models.CharField(max_length=10, null=True, blank=True)
    prompt_tokens =  models.CharField(max_length=10, null=True, blank=True)
    total_tokens =  models.CharField(max_length=10, null=True, blank=True)
    completion_tokens = models.CharField(max_length=10, null=True, blank=True)
    no_of_outcome = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self) -> str:
        return self.user_input_token+"--"+self.completion_tokens
# class ContentCatagories(models.Model):
#     pass

class AiPrompt(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    prompt_string = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    model_gpt_name = models.ForeignKey(to= ModelGPTName, on_delete = models.CASCADE,related_name='gpt_model',default=1)
    catagories = models.ForeignKey(to= PromptCategories, on_delete = models.CASCADE ,blank=True,null=True )
    sub_catagories = models.ForeignKey(to= PromptSubCategories, on_delete = models.CASCADE,blank=True,null=True)
    source_prompt_lang = models.ForeignKey(Languages, on_delete = models.CASCADE,related_name='prompt_lang')
    Tone = models.ForeignKey(PromptTones,on_delete = models.CASCADE,related_name='prompt_tone',blank=True,null=True,default=1)
    response_copies = models.IntegerField(null=True, blank=True,default=1)
    product_name = models.CharField(max_length = 1000, null=True, blank=True)
    product_name_mt = models.CharField(max_length = 1000, null=True, blank=True)
    keywords = models.CharField(max_length = 1000, null=True, blank=True)
    description_mt = models.TextField(null=True, blank=True)
    keywords_mt = models.TextField(null=True, blank=True)
    prompt_string_mt = models.TextField(null=True, blank=True)
    response_charecter_limit =  models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.prompt_string

    @property
    def source_prompt_lang_code(self):
        return self.source_prompt_lang.locale.first().locale_code

class AiPromptResult(models.Model):
    prompt = models.ForeignKey(AiPrompt, on_delete=models.CASCADE, related_name = 'ai_prompt')
    start_phrase =  models.ForeignKey(to= PromptStartPhrases, on_delete = models.CASCADE,null=True, blank=True)
    response_id =  models.CharField(max_length = 50, null=True, blank=True)
    copy = models.IntegerField(null=True, blank=True)
    result_lang = models.ForeignKey(Languages, on_delete = models.CASCADE,related_name='prompt_result_lang_src',null=True, blank=True)  
    token_usage =  models.ForeignKey(to= TokenUsage, on_delete = models.CASCADE,related_name='used_tokens',null=True, blank=True)
    response_created = models.CharField(max_length = 50, null=True, blank=True)
    prompt_generated = models.TextField(null=True, blank=True)
    api_result = models.TextField(null=True, blank=True) 
    translated_prompt_result = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def result_lang_code(self):
        return self.result_lang.locale.first().locale_code

    # def __str__(self) -> str:
    #     return self.prompt_result

# class AiPromptMulti(models.Model):
#     prompt = models.ForeignKey(AiPrompt, on_delete=models.CASCADE, related_name = 'ai_prompt_src')
#     prompt_result = models.ForeignKey(AiPromptResult, on_delete=models.CASCADE, related_name = 'ai_prompt_result_src') 
#     result_lang = models.ForeignKey(Languages, on_delete = models.CASCADE,related_name='prompt_result_lang')  
#     translated_prompt_result = models.TextField(null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)


class TextgeneratedCreditDeduction(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    cerdit_to_deduce = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)