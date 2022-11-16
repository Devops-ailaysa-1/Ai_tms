from django.db import models
from django.utils.text import slugify
from ai_auth.models import AiUser

def user_directory_path(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "pdf_file",filename)

class Ai_PdfUpload(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    pdf_file = models.FileField(upload_to=user_directory_path  , blank=False, null=False)
    docx_url_field = models.URLField(null=True, blank=True)
    pdf_file_name = models.CharField(max_length=200 , null=True, blank=True)
    pdf_task_id = models.CharField(max_length=200 , null=True, blank=True)
    pdf_conversion_sec = models.IntegerField(null=True, blank=True)
    pdf_language = models.CharField(max_length=200 , null=True, blank=True)
    pdf_format_option = models.CharField(max_length=200 , null=True, blank=True)
    pdf_api_use =models.CharField(max_length=200 , null=True, blank=True)
    pdf_no_of_page =  models.IntegerField(null=True, blank=True)
    counter = models.IntegerField(null=True, blank=True )
    status = models.CharField(max_length=200 , null=True, blank=True)
    slug = models.SlugField(default="", blank=True, null=True, db_index=True)



    def save(self, *args, **kwargs):
        if self.id:
            count = Ai_PdfUpload.objects.filter(pdf_file_name__contains=self.pdf_file_name).exclude(id=self.id).count()
        else:
            count = Ai_PdfUpload.objects.filter(pdf_file_name__contains=self.pdf_file_name).count()
        print(count)
        if count!=0:
            self.pdf_file_name = str(self.pdf_file_name).split(".pdf")[0] + "(" + str(count) + ").pdf" 
        return super().save()