from django.db import models
from ai_staff.models import Languages ,LanguagesLocale

from ai_auth.models import AiUser





class Imageload(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    image = models.FileField(upload_to='media/image' , blank=True ,null=True)
    file_name = models.CharField(max_length=200 , blank=True,null=True)
    types = models.CharField(max_length=10 , blank=True,null=True)
    height = models.CharField(max_length=10,blank=True,null=True)
    width = models.CharField(max_length=10,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at= models .DateTimeField(auto_now=True,null=True,blank=True)
    
    
class ImageUpload(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    image = models.FileField(upload_to='media/inpaint' , blank=True ,null=True)
    project_name = models.CharField(max_length=200 , blank=True,null=True)
    types = models.CharField(max_length=10 , blank=True,null=True)
    height = models.CharField(max_length=10,blank=True,null=True)
    width = models.CharField(max_length=10,blank=True,null=True)
    mask = models.FileField(upload_to = 'inpaint' ,blank = True , null = True)
    mask_json = models.JSONField(blank = True , null = True)
    inpaint_image = models.FileField(upload_to = 'inpaint' ,blank = True , null = True)

    create_inpaint_pixel_location = models.FileField(upload_to = 'inpaint' ,blank = True , null = True)
    source_canvas_json =  models.JSONField(blank = True , null = True)
    source_bounding_box = models.JSONField(blank = True , null = True)
    source_language = models.ForeignKey(to=LanguagesLocale , on_delete=models.CASCADE,blank=True ,null=True, related_name='s_lang')
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at= models .DateTimeField(auto_now=True,null=True,blank=True)
 
    
 

class ImageInpaintCreation(models.Model):
    source_image=models.ForeignKey(to=ImageUpload, blank=True,null=True,on_delete=models.CASCADE,related_name='s_im')
    target_language=models.ForeignKey(to=LanguagesLocale,on_delete=models.CASCADE,related_name='t_lang')
    target_canvas_json=models.JSONField(blank=True,null=True)
    target_bounding_box=models.JSONField(blank = True , null = True)
    thumbnail=models.FileField(upload_to = 'inpaint/thumbnail' ,blank = True , null = True )
    export=models.FileField(upload_to = 'inpaint/export' ,blank = True , null = True ) 
    created_at=models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at=models .DateTimeField(auto_now=True,null=True,blank=True)