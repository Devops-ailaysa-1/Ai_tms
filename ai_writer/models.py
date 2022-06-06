from django.db import models
from django.conf import settings
# from django.core.files.storage import FileSystemStorage
# import os
from ai_auth.models import AiUser

# class OverwriteStorage(FileSystemStorage):
#     def get_available_name(self, name, max_length=None):
#         if self.exists(name):
#             os.remove(os.path.join(settings.MEDIA_ROOT, name))
#         return name
 
# def json_upload_path(instance, filename):
#     return 'user_{0}/{1}'.format(instance.user_name, filename)

class FileDetails(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(AiUser , on_delete=models.CASCADE, related_name="ai_writer_file_user")
    file_name = models.CharField(max_length=100 )
    
    store_quill_data = models.TextField()
    store_quill_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    


    def save(self, *args, **kwargs):
        if self.id:
            count = FileDetails.objects.filter(file_name__contains=self.file_name).exclude(id=self.id).count()
        else:
            count = FileDetails.objects.filter(file_name__contains=self.file_name).count()
        print(count)
        if count!=0:
            self.file_name = str(self.file_name) + "(" + str(count) + ")"
        return super().save()



# class verbset_tense_form(models.Model):
#     verbs = models.CharField(max_length=100)
#     third_person_singular_simple_present = models.CharField(max_length=100)
#     present_participle = models.CharField(max_length=100)
#     simple_past = models.CharField(max_length=100)
#     past_participle = models.CharField(max_length=100)
 


#     def __str__(self) -> str:
#         return f"{self.verbs , self.third_person_singular_simple_present , self.present_participle , self.simple_past  , self.past_participle}"

# class synonyms(models.Model):
#     verbs = models.CharField(max_length=100)
#     synonyms = models.CharField(max_length=100)

#     def __str__(self) -> str:
#         return f"{self.verbs , self.synonyms}"
    



# class Nounset(models.Model):
#     nouns = models.CharField(max_length=100)
#     synonyms = models.CharField(max_length=100)
