from django.db import models

# Create your models here.

from ai_auth.models import AiUser

def user_directory_path_pdf_upload(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "pdf_chat_doc/semantic_search_file",filename)

def user_directory_path_pdf_thumbnail(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "pdf_chat_doc/thumbnail",filename)

class PdffileUpload(models.Model):
    user = models.ForeignKey(AiUser,on_delete=models.CASCADE)
    file = models.FileField(upload_to=user_directory_path_pdf_upload,null=False,blank=True)
    file_name = models.CharField(max_length=200,null=True,blank=True)
    pdf_thumbnail = models.FileField(upload_to=user_directory_path_pdf_thumbnail,blank=True ,null=True)
    vector_embedding_path = models.CharField(max_length=200,null=True,blank=True)
    is_train=models.BooleanField(default=False)
    vector_id= models.CharField(max_length=200,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    created_by = models.ForeignKey(AiUser,null=True, blank=True, on_delete=models.SET_NULL,related_name='pdfchat_created_by')
    updated_at= models.DateTimeField(auto_now=True,null=True,blank=True)


class PdffileChatHistory(models.Model):
    pdf_file =models.ForeignKey(PdffileUpload,on_delete=models.CASCADE,related_name="pdf_file_chat")
    question =models.CharField(max_length=2000,null=True,blank=True)
    answer = models.CharField(max_length=2000,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at= models.DateTimeField(auto_now=True,null=True,blank=True)