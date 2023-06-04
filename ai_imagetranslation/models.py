from django.db import models
from ai_staff.models import Languages ,LanguagesLocale
from ai_auth.models import AiUser

def user_directory_path_image_load(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "image_translate/image_load/",filename)


def user_directory_path_image_translate_image(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "image_translate/image_upload/image_translate/image",filename)


def user_directory_path_image_translate_process(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "image_translate/image_upload/image_translate/mask",filename)

def user_directory_path_image_translate_result(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "image_translate/image_upload/image_translate/inpaint_res",filename)


class Imageload(models.Model):
<<<<<<< HEAD
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    image = models.FileField(upload_to="image_translate/image_load/", blank=True ,null=True)#user_directory_path_image_load
    file_name = models.CharField(max_length=200 , blank=True,null=True)
    types = models.CharField(max_length=10 , blank=True,null=True)
    height = models.CharField(max_length=10,blank=True,null=True)
    width = models.CharField(max_length=10,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at= models .DateTimeField(auto_now=True,null=True,blank=True)
=======
    user=models.ForeignKey(AiUser,on_delete=models.CASCADE)
    image=models.FileField(upload_to=user_directory_path_image_load,blank=True ,null=True)
    file_name=models.CharField(max_length=200,blank=True,null=True)
    types=models.CharField(max_length=10,blank=True,null=True)
    height=models.CharField(max_length=10,blank=True,null=True)
    width=models.CharField(max_length=10,blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at=models.DateTimeField(auto_now=True,null=True,blank=True)
>>>>>>> origin/canvas_staging
    
    
class ImageTranslate(models.Model):
    user=models.ForeignKey(AiUser,on_delete=models.CASCADE)
<<<<<<< HEAD
    image=models.FileField(upload_to="image_translate/image_load/",blank=True,null=True)#user_directory_path_image_translate_image
    project_name=models.CharField(max_length=200 , blank=True,null=True)
    types=models.CharField(max_length=10,blank=True,null=True)
    height=models.CharField(max_length=10,blank=True,null=True)
    width=models.CharField(max_length=10,blank=True,null=True)
    
    mask=models.FileField(upload_to="image_translate/image_load/",blank=True,null=True)#user_directory_path_image_translate_process
    mask_json=models.JSONField(blank=True,null=True)
    inpaint_image=models.FileField(upload_to="image_translate/image_load/",blank=True,null=True)#user_directory_path_image_translate_result
    create_inpaint_pixel_location=models.FileField(upload_to="image_translate/image_load/",blank=True,null=True) #user_directory_path_image_translate_process
=======
    image=models.FileField(upload_to=user_directory_path_image_translate_image,blank=True,null=True)
    project_name=models.CharField(max_length=200,blank=True,null=True)
    types=models.CharField(max_length=10,blank=True,null=True)
    height=models.CharField(max_length=10,blank=True,null=True)
    width=models.CharField(max_length=10,blank=True,null=True)
    mask=models.FileField(upload_to=user_directory_path_image_translate_process,blank=True,null=True)
    mask_json=models.JSONField(blank=True,null=True)
    inpaint_image=models.FileField(upload_to=user_directory_path_image_translate_result,blank=True,null=True)
    create_inpaint_pixel_location=models.FileField(upload_to=user_directory_path_image_translate_process,blank=True,null=True)
>>>>>>> origin/canvas_staging
    source_canvas_json=models.JSONField(blank=True,null=True)
    source_bounding_box=models.JSONField(blank=True,null=True)
    source_language=models.ForeignKey(to=LanguagesLocale,on_delete=models.CASCADE,blank=True,null=True, related_name='s_lang')
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at= models.DateTimeField(auto_now=True,null=True,blank=True)
 

def user_directory_path_image_translate_thumbnail(instance, filename):
    return '{0}/{1}/{2}'.format(instance.source_image.user.uid,"image_translate/thumbnail",filename) 


def user_directory_path_image_translate_export(instance, filename):
    return '{0}/{1}/{2}'.format(instance.source_image.user.uid,"image_translate/export",filename) 

def user_directory_path_inpaint_image(instance, filename):
    return '{0}/{1}/{2}'.format(instance.source_image.user.uid,"image_translate/image_upload/image_translate/inpaint_res",filename)

def user_directory_path_image_translate_process_target(instance, filename):
    return '{0}/{1}/{2}'.format(instance.source_image.user.uid,"image_translate/image_upload/image_translate/mask",filename)




class ImageInpaintCreation(models.Model):
    source_image=models.ForeignKey(to=ImageTranslate,blank=True,null=True,on_delete=models.CASCADE,related_name='s_im')
<<<<<<< HEAD
    target_language=models.ForeignKey(to=LanguagesLocale,on_delete=models.CASCADE,related_name='t_lang')   
    # export=models.FileField(upload_to=user_directory_path_image_translate_export,blank=True,null=True) 
    created_at=models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at=models.DateTimeField(auto_now=True,null=True,blank=True)
 
    class Meta:
        ordering = ['id']

def image_translate_process_target(instance, filename):
    return '{0}/{1}/{2}'.format(instance.inpaint_creation.source_image.user.uid, "image_translate/image_upload/image_translate/mask",filename)
=======
    target_language=models.ForeignKey(to=LanguagesLocale,on_delete=models.CASCADE,related_name='t_lang')
    target_canvas_json=models.JSONField(blank=True,null=True) ############
    target_bounding_box=models.JSONField(blank=True,null=True)  ################
    thumbnail=models.FileField(upload_to=user_directory_path_image_translate_thumbnail,blank=True,null=True) ############
    export=models.FileField(upload_to=user_directory_path_image_translate_export,blank=True,null=True)  ##################
    created_at=models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at=models.DateTimeField(auto_now=True,null=True,blank=True)
    # mask=models.FileField(upload_to=user_directory_path_image_translate_process_target,blank=True,null=True)
    # inpaint_image=models.FileField(upload_to=user_directory_path_inpaint_image,blank=True,null=True)
    # mask_json=models.JSONField(blank=True,null=True)
    create_inpaint_pixel_location=models.FileField(upload_to=user_directory_path_image_translate_process_target,blank=True,null=True)


    class Meta:
        ordering = ['id']

# class TargetInpaintimage(models.Model):
#     inpaint_create=models.ForeignKey(to=ImageInpaintCreation,blank=True,null=True,on_delete=models.CASCADE,related_name='tar_im_create')
#     mask_json=models.JSONField(blank=True,null=True)
#     inpaint_image=models.FileField(upload_to=user_directory_path_inpaint_image,blank=True,null=True)
#     target_canvas_json=models.JSONField(blank=True,null=True)
#     thumbnail=models.FileField(upload_to=user_directory_path_image_translate_thumbnail,blank=True,null=True)
#     export=models.FileField(upload_to=user_directory_path_image_translate_export,blank=True,null=True) 

    



>>>>>>> origin/canvas_staging

def image_translate_result_target(instance, filename):
    return '{0}/{1}/{2}'.format(instance.inpaint_creation.source_image.user.uid, "image_translate/image_upload/image_translate/inpaint_res",filename)


def image_translate_thumbnail_target(instance, filename):
    return '{0}/{1}/{2}'.format(instance.inpaint_creation.source_image.user.uid,"image_translate/thumbnail",filename) 

class TargetInpaintaImage(models.Model):
    inpaint_creation=models.ForeignKey(ImageInpaintCreation,blank=True,null=True,on_delete=models.CASCADE,related_name='t_inpaint_creation')
    mask=models.FileField(upload_to='image_translate/thumbnail',blank=True,null=True)
    mask_json=models.JSONField(blank=True,null=True)
    inpaint_image=models.FileField(upload_to='image_translate/thumbnail',blank=True,null=True)
    target_canvas_json=models.JSONField(blank=True,null=True)
    target_bounding_box=models.JSONField(blank=True,null=True)
    thumbnail=models.FileField(upload_to='image_translate/thumbnail',blank=True,null=True)
    create_inpaint_pixel_location=models.FileField(upload_to='image_translate/thumbnail',blank=True,null=True)