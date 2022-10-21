from django.db import models

# class forbidden_file_model(models.Model):
#     doc_id  = models.CharField(max_length=10, default=10)
#     file    = models.FileField(upload_to='forbidden_words')
#     # created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
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
