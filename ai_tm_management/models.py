from django.db import models
from ai_auth.models import AiUser
from ai_staff.models import Languages, SubjectFields

# Create your models here.


class UploadedTMinfo(models.Model):

    def get_file_name(instance, filename):
        return instance.uploaded_by.userattribute.allocated_dir.split("/")[-1] + f"/tmx/{filename}"

    uploaded_by = models.ForeignKey(AiUser, on_delete=models.CASCADE,
                        related_name="user_tm")
    tm_file = models.FileField(upload_to=get_file_name)
    source_language = models.ForeignKey(Languages, on_delete=models.CASCADE,
                        related_name="source_language_uploadedtminfo_set")
    target_languages = models.ManyToManyField(Languages,
                        related_name="target_languages_uploadedtminfo_set")
    subject_fields = models.ManyToManyField(SubjectFields,
                        related_name="subject_fields_uploadedtminfo_set")
    owned_by = models.ForeignKey(AiUser, on_delete=models.CASCADE,
                        related_name="owner_tm")

# class SubjectFieldsOfTM(models.Model):
#     subject_field = models.ForeignKey(SubjectFields, on_delete=models.CASCADE)
#     tm_info = models.ForeignKey(UploadedTMinfo, on_delete=models.CASCADE,
#                                 related_name="tm_subjct_fields_set")
#
# class TargetLanguagesOfTM(models.Model):
#     target_language = models.ForeignKey(Languages, on_delete=models.CASCADE)
#     tm_info = models.ForeignKey(UploadedTMinfo, on_delete=models.CASCADE,
#                 related_name="tm_target_languages_set")
#
# class TM(models.Model):
#     target_language = models.ForeignKey(TargetLanguagesOfTM, on_delete=models.CASCADE)
#     source_content = models.TextField()
#     target_content = models.TextField()
#
#     @property
#     def get_upload_tm_info(self):
#         return self.target_language.tm_info
#
#     @property
#     def get_source_language(self):
#         return self.get_upload_tm_info.source_language
#
#     @property
#     def get_target_language(self):
#         return self.target_language.target_language


'''
pip install translate-toolkit
>>> from translate.storage.tmx import tmxfile
>>>
>>> with open("sample.tmx", 'rb') as fin:
...     tmx_file = tmxfile(fin, 'en', 'ar')
>>>
>>> for node in tmx_file.unit_iter():
...     print(node.source, node.target)
Hello world! اهلا بالعالم!
'''

