from django.db import models
from ai_staff.models import Languages ,LanguagesLocale
from ai_auth.models import AiUser
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from ai_workspace.models import Project,Job

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
    height=models.IntegerField(blank=True,null=True)
    width=models.IntegerField(blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at=models.DateTimeField(auto_now=True,null=True,blank=True)
    thumbnail=models.FileField(upload_to=user_directory_path_image_load_thumbnail,blank=True ,null=True)

class ImageTranslate(models.Model):
    user=models.ForeignKey(AiUser,on_delete=models.CASCADE)
    project = models.OneToOneField(Project, null=True, blank=True, on_delete=models.CASCADE, related_name="image_translate_project")
    image_load=models.ForeignKey(Imageload,on_delete=models.SET_NULL,blank=True,null=True, related_name='s_lang')
    image=models.FileField(upload_to=user_directory_path_image_translate_image,blank=True,null=True)
    project_name=models.CharField(max_length=2000,blank=True,null=True)
    types=models.CharField(max_length=10,blank=True,null=True)
    height=models.IntegerField(blank=True,null=True)
    width=models.IntegerField(blank=True,null=True)
    mask=models.FileField(upload_to=user_directory_path_image_translate_process,blank=True,null=True)
    mask_json=models.JSONField(blank=True,null=True)
    inpaint_image=models.FileField(upload_to=user_directory_path_image_translate_result,blank=True,null=True)
    create_inpaint_pixel_location=models.FileField(upload_to=user_directory_path_image_translate_process,blank=True,null=True)
    source_canvas_json=models.JSONField(blank=True,null=True)
    source_bounding_box=models.JSONField(blank=True,null=True)
    source_language_for_translate=models.ForeignKey(to=LanguagesLocale,on_delete=models.CASCADE,blank=True,null=True, related_name='s_lang')
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
    source_language=models.ForeignKey(to=LanguagesLocale,on_delete=models.CASCADE,blank=True,null=True, related_name='s_lang_inpaint')
    target_language=models.ForeignKey(to=LanguagesLocale,on_delete=models.CASCADE,related_name='t_lang')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True,related_name="image_translation_job")
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
    original_image=models.FileField(upload_to=user_directory_path_image_background_removel,blank=True,null=True)
    image=models.FileField(upload_to=user_directory_path_image_background_removel,blank=True,null=True)
    mask=models.FileField(upload_to=user_directory_path_image_background_removel,blank=True,null=True)
    eraser_transparent_mask=models.FileField(upload_to=user_directory_path_image_background_removel,blank=True,null=True)
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
    generated_image=models.FileField(upload_to='stable-diffusion-image-gen',blank=True,null=True)
    image=models.FileField(upload_to='stable-diffusion-image',blank=True,null=True)
    used_api=models.CharField(max_length=200,blank=True,null=True)
    model_name=models.CharField(max_length=200,blank=True,null=True)
    prompt=models.CharField(max_length=3000,blank=True,null=True)
    negative_prompt=models.CharField(max_length=3000,blank=True,null=True)
    style=models.CharField(max_length=100,blank=True,null=True)
    height=models.IntegerField(blank=True,null=True)
    width=models.IntegerField(blank=True,null=True)
    steps=models.IntegerField(blank=True,null=True)
    thumbnail=models.FileField(upload_to='stable-diffusion-image-thumbnail',blank=True,null=True)
    celery_id=models.CharField(max_length=100,blank=True,null=True)
    status=models.CharField(max_length=100,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at= models.DateTimeField(auto_now=True,null=True,blank=True)
    def __str__(self) -> str:
        return self.used_api
    

# class CustomImageGenerationStyle(models.Model):
#     style_name=models.CharField(max_length=200,blank=True,null=True)
#     image=models.FileField(upload_to="custom_image_gen",blank=True,null=True)


# class ImageStyleCategories(models.Model):
#     style_name=models.ManyToManyField(CustomImageGenerationStyle,related_name="style")
#     style_category_name=models.CharField(max_length=200,blank=True,null=True)

# class ImageModificationTechnique(models.Model):
#     custom_image_style=models.ForeignKey(ImageStyleCategories,on_delete=models.CASCADE,related_name="style_category")
#     custom_style_name=models.CharField(max_length=200,blank=True,null=True)
#     image=models.FileField(upload_to="custom_image_gen",blank=True,null=True)




class GeneralPromptList(models.Model):
    prompt=models.TextField()
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at= models.DateTimeField(auto_now=True,null=True,blank=True)


class CustomImageGenerationStyle(models.Model):
    style_name=models.CharField(max_length=200,blank=True,null=True)
    image=models.FileField(upload_to="custom_image_gen",blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at= models.DateTimeField(auto_now=True,null=True,blank=True)
    def __str__(self) -> str:
        return self.style_name

class ImageStyleCategories(models.Model):
    style_name=models.ForeignKey(CustomImageGenerationStyle,on_delete=models.CASCADE,related_name="style")
    style_category_name=models.CharField(max_length=200,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at= models.DateTimeField(auto_now=True,null=True,blank=True)
    def __str__(self) -> str:
        return self.style_category_name +"--"+ self.style_name.style_name


class ImageModificationTechnique(models.Model):
    custom_image_style=models.ForeignKey(ImageStyleCategories,on_delete=models.CASCADE,related_name="style_category")
    custom_style_name=models.CharField(max_length=200,blank=True,null=True)
    image=models.FileField(upload_to="custom_image_gen",blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at= models.DateTimeField(auto_now=True,null=True,blank=True)
    default_prompt=models.CharField(max_length=700,blank=True,null=True)

    def __str__(self) -> str:
        known_info=self.custom_style_name +"--"+ self.custom_image_style.style_category_name +"--"+ self.custom_image_style.style_name.style_name 
        if self.default_prompt:
            known_info+= "--"+self.default_prompt
        return known_info


class AIimageCategory(models.Model):
    image_category=models.CharField(max_length=200,blank=True,null=True)


class ImageStyleSD(models.Model):
    # category=models.ForeignKey(AIimageCategory,on_delete=models.CASCADE,related_name="ai-image-cat")
    style_name=models.CharField(max_length=200,blank=True,null=True)
    image=models.FileField(upload_to="custom_image_gen",blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at=models.DateTimeField(auto_now=True,null=True,blank=True)
    default_prompt=models.CharField(max_length=700,blank=True,null=True)
    negative_prompt=models.CharField(max_length=700,blank=True,null=True)


class Color(models.Model):
    color_name=models.CharField(max_length=200,blank=True,null=True)
    image=models.FileField(upload_to="custom_image_gen",blank=True,null=True)

class Lighting(models.Model):
    lighting_name=models.CharField(max_length=200,blank=True,null=True)
    image=models.FileField(upload_to="custom_image_gen",blank=True,null=True)

class Composition(models.Model):
    composition_name=models.CharField(max_length=200,blank=True,null=True)
    image=models.FileField(upload_to="custom_image_gen",blank=True,null=True)


class AspectRatio(models.Model):
    resolution=models.CharField(max_length=200,blank=True,null=True)
    image=models.FileField(upload_to="aspect-ratio",blank=True,null=True)
    # height=models.IntegerField(blank=True,null=True)
    # width=models.IntegerField(blank=True,null=True)

    def __str__(self) -> str:
        return self.resolution

class StableDiffusionVersion(models.Model):
    version_name=models.CharField(max_length=200,blank=True,null=True)
    cfg=models.IntegerField(blank=True,null=True)
    

    def __str__(self) -> str:
        return self.version_name 


class SDImageResolution(models.Model):
    # sd_image_version=models.ForeignKey(StableDiffusionVersion,on_delete=models.CASCADE,related_name="sd_image_ver")
    sd_image_resolution=models.ForeignKey(AspectRatio,on_delete=models.CASCADE,related_name="sd_image_res")
    resolution=models.CharField(max_length=200,blank=True,null=True)
    width=models.IntegerField(blank=True,null=True)
    height=models.IntegerField(blank=True,null=True)
    steps=models.IntegerField(blank=True,null=True)
    def __str__(self) -> str:
        return str(self.width)+"--"+str(self.height) +"--"+str(self.id) 





