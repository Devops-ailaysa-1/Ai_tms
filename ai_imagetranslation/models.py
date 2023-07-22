from django.db import models
from ai_staff.models import Languages ,LanguagesLocale
from ai_auth.models import AiUser
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
def user_directory_path_image_load(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "image_translate/image_load/",filename)


def user_directory_path_image_translate_image(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "image_translate/image_upload/image_translate/image",filename)


def user_directory_path_image_translate_process(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "image_translate/image_upload/image_translate/mask",filename)

def user_directory_path_image_translate_result(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "image_translate/image_upload/image_translate/inpaint_res",filename)


def user_directory_path_image_load_thumbnail(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "image_load/thumbnail",filename)


def user_directory_path_image_translate_image_temp_resize(instance, filename):
    return '{0}/{1}/{2}'.format(instance.image_translate.user.uid, "image_translate/image_upload/image_translate/temp_resize",filename)

class Imageload(models.Model):
    user=models.ForeignKey(AiUser,on_delete=models.CASCADE)
    image=models.FileField(upload_to=user_directory_path_image_load,blank=True ,null=True,validators=[FileExtensionValidator(allowed_extensions=["svg","jpeg","jpg","png"])])
    file_name=models.CharField(max_length=2000,blank=True,null=True)
    types=models.CharField(max_length=10,blank=True,null=True)
    height=models.CharField(max_length=10,blank=True,null=True)
    width=models.CharField(max_length=10,blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at=models.DateTimeField(auto_now=True,null=True,blank=True)
    thumbnail=models.FileField(upload_to=user_directory_path_image_load_thumbnail,blank=True ,null=True)
    
class ImageTranslate(models.Model):
    user=models.ForeignKey(AiUser,on_delete=models.CASCADE)
    image=models.FileField(upload_to=user_directory_path_image_translate_image,blank=True,null=True)
    project_name=models.CharField(max_length=2000,blank=True,null=True)
    types=models.CharField(max_length=10,blank=True,null=True)
    height=models.CharField(max_length=10,blank=True,null=True)
    width=models.CharField(max_length=10,blank=True,null=True)
    mask=models.FileField(upload_to=user_directory_path_image_translate_process,blank=True,null=True)
    mask_json=models.JSONField(blank=True,null=True)
    inpaint_image=models.FileField(upload_to=user_directory_path_image_translate_result,blank=True,null=True)
    create_inpaint_pixel_location=models.FileField(upload_to=user_directory_path_image_translate_process,blank=True,null=True)
    source_canvas_json=models.JSONField(blank=True,null=True)
    source_bounding_box=models.JSONField(blank=True,null=True)
    source_language=models.ForeignKey(to=LanguagesLocale,on_delete=models.CASCADE,blank=True,null=True, related_name='s_lang')
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at= models.DateTimeField(auto_now=True,null=True,blank=True)
    # thumbnail=models.FileField(upload_to=user_directory_path_image_load_thumbnail,blank=True ,null=True)


class ImageTranslateResizeImage(models.Model):
    image_translate=models.ForeignKey(ImageTranslate,on_delete=models.CASCADE,related_name='image_translate_resize')
    resize_image=models.FileField(upload_to=user_directory_path_image_translate_image_temp_resize,blank=True,null=True)
    resize_mask=models.FileField(upload_to=user_directory_path_image_translate_image_temp_resize,blank=True,null=True)
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
    
    # def validate_unique(self, exclude=None):
    #     im_tr=ImageTranslate.objects.filter(user=self.source_image.user,source_language=self.source_image.source_language,
    #                                         s_im__target_language=self.target_language)
    #     if im_tr.exists():
    #         raise ValidationError({'msg':"source and target pair already exist"})
    
def user_directory_path_image_background_removel(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid,"background_removel",filename)

class BackgroundRemovel(models.Model):
    user=models.ForeignKey(AiUser,on_delete=models.CASCADE)
    image_json_id=models.CharField(max_length=100,blank=True,null=True)
    image_url=models.URLField(blank=True,null=True)
    canvas_json=models.JSONField(blank=True,null=True)
    image=models.FileField(upload_to=user_directory_path_image_background_removel,blank=True,null=True)
    preview_json=models.JSONField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at= models.DateTimeField(auto_now=True,null=True,blank=True)
    def __str__(self) -> str:
        return self.image_json_id+'----'+self.image_url
    
class BackgroundRemovePreviewimg(models.Model):
    back_ground_remove=models.ForeignKey(BackgroundRemovel,on_delete=models.CASCADE,related_name="back_ground_rm_preview_im")
    image_url=models.URLField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at= models.DateTimeField(auto_now=True,null=True,blank=True)

    def __str__(self) -> str:
        return self.image_url

# def user_directory_path_image_object_removel(instance, filename):
#     return '{0}/{1}/{2}'.format(instance.user.uid,"object_removel",filename)

# class ObjectRemovel(models.Model):
#     user=models.ForeignKey(AiUser,on_delete=models.CASCADE)
#     image_json_id=models.CharField(max_length=100,blank=True,null=True)
#     image_url=models.URLField(blank=True,null=True)
#     canvas_json=models.JSONField(blank=True,null=True)
#     image=models.FileField(upload_to=user_directory_path_image_object_removel,blank=True,null=True)
#     created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
#     updated_at= models.DateTimeField(auto_now=True,null=True,blank=True)
#     resultant_image=models.FileField(upload_to=user_directory_path_image_object_removel,blank=True,null=True)


#     def __str__(self) -> str:
#         return self.image_json_id+'----'+self.image_url



class StableDiffusionAPI(models.Model):
    user=models.ForeignKey(AiUser,on_delete=models.CASCADE)
    image=models.FileField(upload_to='stable-diffusion-image',blank=True,null=True)
    used_api=models.CharField(max_length=200,blank=True,null=True)
    model_name=models.CharField(max_length=200,blank=True,null=True)
    prompt=models.CharField(max_length=3000,blank=True,null=True)
    negative_prompt=models.CharField(max_length=3000,blank=True,null=True)
    style=models.CharField(max_length=100,blank=True,null=True)
    height=models.IntegerField(blank=True,null=True)
    width=models.IntegerField(blank=True,null=True)
    sampler=models.CharField(max_length=100,blank=True,null=True)
    def __str__(self) -> str:
        return self.used_api