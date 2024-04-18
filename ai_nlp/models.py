from django.db import models

# Create your models here.

from ai_auth.models import AiUser
from ai_staff.models import Languages  

# class ChatEmbeddingLLMModel(models.Model):
#     model_name = models.CharField(max_length=200,null=True,blank=True)
    # embedding_name = models.CharField(max_length=200,null=True,blank=True)

def user_directory_path_pdf_upload(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "pdf_chat_doc/semantic_search_file",filename)

def user_directory_path_pdf_thumbnail(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "pdf_chat_doc/thumbnail",filename)

# class PdfUsageThreshold(models.Model):
#     user = models.ForeignKey(AiUser,on_delete=models.CASCADE)
#     question_threshold = models.PositiveIntegerField(null=True,blank=True,default=0)
#     no_of_question_remaining= models.PositiveIntegerField(null=True,blank=True,default=0)
#     add_on_subscribed =  models.BooleanField(null=True,blank=True,default=False)
#     created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
#     updated_at= models.DateTimeField(auto_now=True,null=True,blank=True)



class PdffileUpload(models.Model):
    user = models.ForeignKey(AiUser,on_delete=models.CASCADE)
    # pdf_usage = models.ForeignKey(PdfUsageThreshold,on_delete=models.CASCADE,related_name="pdf_threshold_file")
    file = models.FileField(upload_to=user_directory_path_pdf_upload,null=True,blank=True)
    file_name = models.CharField(max_length=200,null=True,blank=True)
    pdf_thumbnail = models.FileField(upload_to=user_directory_path_pdf_thumbnail,blank=True ,null=True)
    vector_embedding_path = models.CharField(max_length=200,null=True,blank=True)
    is_train=models.BooleanField(default=False)
    vector_id= models.CharField(max_length=200,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    created_by = models.ForeignKey(AiUser,null=True, blank=True, on_delete=models.SET_NULL,related_name='pdfchat_created_by')
    updated_at= models.DateTimeField(auto_now=True,null=True,blank=True)
    celery_id = models.CharField(max_length=200,null=True,blank=True)
    status = models.CharField(max_length=200,null=True,blank=True)
    text_file =  models.FileField(upload_to=user_directory_path_pdf_upload,null=True,blank=True)
    website = models.TextField(null=True,blank=True)
    
    # embedding_name = models.ForeignKey(ChatEmbeddingLLMModel,on_delete=models.CASCADE,related_name="pdf_embed_chat",null=True,blank=True)




class PdffileChatHistory(models.Model):
    pdf_file = models.ForeignKey(PdffileUpload,on_delete=models.CASCADE,related_name="pdf_file_chat")
    question = models.CharField(max_length=2000,null=True,blank=True)
    answer = models.CharField(max_length=2000,null=True,blank=True)
    question_mt = models.CharField(max_length=2000,null=True,blank=True)
    answer_mt = models.CharField(max_length=2000,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at= models.DateTimeField(auto_now=True,null=True,blank=True)
    token_usage = models.CharField(max_length=2000,null=True,blank=True)
    language  = models.ForeignKey(Languages,related_name='pdf_chat_lang', on_delete=models.CASCADE,null=True,blank=True)


class ContentPageReference(models.Model):
    pdf_chat =  models.ForeignKey(PdffileChatHistory,on_delete=models.CASCADE,related_name="pdf_chat_page_ref")
    page_no = models.IntegerField(null=True,blank=True)


class PdfQustion(models.Model):
    pdf_file_chat = models.ForeignKey(PdffileUpload,on_delete=models.CASCADE,related_name="pdf_file_question",null=True,blank=True)
    question = models.CharField(max_length=500,null=True,blank=True)
    

def user_directory_path_public_pdf(filename):
    return '{0}/{1}'.format("public_pdf_book/semantic_search_file",filename)


def user_directory_pdf_publicbook_thumbnail(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "pdf_public_book_chat_doc/thumbnail",filename)


class PublicBook(models.Model):
    user = models.ForeignKey(AiUser,on_delete=models.CASCADE)
    file =  models.FileField(upload_to=user_directory_path_public_pdf,null=True,blank=True)
    file_name = models.CharField(max_length=200,null=True,blank=True) ###title
    author = models.CharField(max_length=500,null=True,blank=True)
    isbn =  models.CharField(max_length=14,null=True,blank=True)
    pdf_thumbnail = models.FileField(upload_to=user_directory_pdf_publicbook_thumbnail,blank=True ,null=True)
    vector_embedding_path = models.CharField(max_length=200,null=True,blank=True)
    text_file =  models.FileField(upload_to=user_directory_path_pdf_upload,null=True,blank=True)
    publisher = models.CharField(max_length=200,null=True,blank=True)
    created_by = models.ForeignKey(AiUser,null=True, blank=True, on_delete=models.SET_NULL,related_name='pdf_public_created_by')
    # book_category = models.ForeignKey(BookCategory,on_delete=models.CASCADE,related_name="pdf_public_file",null=True,blank=True)
 
    celery_id = models.CharField(max_length=200,null=True,blank=True)
    status = models.CharField(max_length=200,null=True,blank=True)

    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at= models.DateTimeField(auto_now=True,null=True,blank=True)

    def __str__(self) -> str:
        return str(self.author)+'----'+str(self.file_name)+'----'+str(self.isbn)
    

 
# class PdfPublicChatHistory(models.Model):
#     user = models.ForeignKey(AiUser,on_delete=models.CASCADE)
#     pdf_file = models.ForeignKey(PublicBook,on_delete=models.CASCADE,related_name="pdf_file_chat")
#     question = models.CharField(max_length=2000,null=True,blank=True)
#     answer = models.CharField(max_length=2000,null=True,blank=True)
#     question_mt = models.CharField(max_length=2000,null=True,blank=True)
#     answer_mt = models.CharField(max_length=2000,null=True,blank=True)
#     created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
#     updated_at= models.DateTimeField(auto_now=True,null=True,blank=True)