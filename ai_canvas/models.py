from django.db import models

# Create your models here.
from ai_staff.models import Languages ,LanguagesLocale
from ai_auth.models import AiUser



class CanvasCatagories(models.Model):
    catagory_name = models.CharField(max_length=50,null=True,blank=True)
    def __str__(self) -> str:
        return self.catagory_name


class CanvasTemplates(models.Model):
    file_name =  models.CharField(max_length=50,null=True,blank=True) 
    template_json = models.JSONField()
    thumbnail=models.FileField(upload_to='canva_templates/thumbnails/',blank=True,null=True)
    width = models.IntegerField(null=True,blank=True)
    height = models.IntegerField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at= models .DateTimeField(auto_now=True,null=True,blank=True)


def user_directory_path_canvas_source_json_thumbnails(instance, filename):
    return '{0}/{1}/{2}'.format(instance.canvas_design.user.uid, "canvas/design/canvas_templates_source/thumbnails/",filename)

def user_directory_path_canvas_source_json_exports(instance, filename):
    return '{0}/{1}/{2}'.format(instance.canvas_design.user.uid, "canvas/design/canvas_exports_source/exports/",filename)

def user_directory_path_canvas_image_assets(instance, filename): ###
    return '{0}/{1}/{2}'.format(instance.user.uid, "canvas/assets/canva_assets/images/",filename)

def user_directory_path_canvas_target_json_thumbnails(instance, filename):
    return '{0}/{1}/{2}'.format(instance.canvas_trans_json.canvas_design.user.uid, "canvas/design/canvas_exports_target/thumbnails/",filename)

def user_directory_path_canvas_target_json_exports(instance, filename):
    return '{0}/{1}/{2}'.format(instance.canvas_trans_json.canvas_design.user.uid, "canvas/design/canvas_exports_target/exports/",filename)

class CanvasUserImageAssets(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    image_name =  models.CharField(max_length=50,null=True,blank=True)
    image= models.FileField(upload_to=user_directory_path_canvas_image_assets,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at= models .DateTimeField(auto_now=True,null=True,blank=True)

class CanvasDesign(models.Model):
    user=models.ForeignKey(AiUser, on_delete=models.CASCADE)
    file_name=models.CharField(max_length=50,null=True,blank=True) 
    width=models.IntegerField(null=True,blank=True)
    height=models.IntegerField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at=models .DateTimeField(auto_now=True,null=True,blank=True)

    class Meta:
        ordering = ('updated_at',)

class CanvasSourceJsonFiles(models.Model):
    canvas_design=models.ForeignKey(CanvasDesign,related_name='canvas_json_src', on_delete=models.CASCADE)
    thumbnail=models.FileField(upload_to=user_directory_path_canvas_source_json_thumbnails,blank=True,null=True)
    export_file=models.FileField(upload_to=user_directory_path_canvas_source_json_exports,blank=True,null=True)
    json=models.JSONField(null=True)
    page_no=models.IntegerField()
    updated_at=models.DateTimeField(auto_now=True,null=True,blank=True)
    undo_hide_src=models.BooleanField(default=False)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['canvas_design', 'page_no'], name="%(app_label)s_%(class)s_unique")]
        ordering = ('page_no',)


class CanvasTranslatedJson(models.Model):
    canvas_design=models.ForeignKey(CanvasDesign,related_name='canvas_translate', on_delete=models.CASCADE)
    source_language=models.ForeignKey(LanguagesLocale,related_name='source_locale' , on_delete=models.CASCADE) 
    target_language=models.ForeignKey(LanguagesLocale,related_name='target', on_delete=models.CASCADE)
    #canvas_translate_json = models.JSONField(blank=True,null=True)
    #thumbnail_target=models.FileField(upload_to='canva_templates/thumbnails/',blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at=models .DateTimeField(auto_now=True,null=True,blank=True)
    undo_hide_tar=models.BooleanField(default=False)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['canvas_design', 'source_language','target_language'], name="%(app_label)s_%(class)s_unique")]


class CanvasTargetJsonFiles(models.Model):
    canvas_trans_json=models.ForeignKey(CanvasTranslatedJson,related_name='canvas_json_tar', on_delete=models.CASCADE)
    thumbnail=models.FileField(upload_to=user_directory_path_canvas_target_json_thumbnails,blank=True,null=True)
    export_file=models.FileField(upload_to=user_directory_path_canvas_target_json_exports,blank=True,null=True)
    json=models.JSONField(null=True)
    page_no=models.IntegerField()

    class Meta:
        ordering = ('page_no',)

# #########template design##############

class TemplateGlobalDesign(models.Model):
    file_name=models.CharField(max_length=50,null=True,blank=True) 
    width=models.IntegerField(null=True,blank=True)
    height=models.IntegerField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at=models .DateTimeField(auto_now=True,null=True,blank=True)
    user_name=models.CharField(max_length=100,null=True,blank=True)

class TemplatePage(models.Model):
    template_page=models.ForeignKey(TemplateGlobalDesign,related_name='template_globl_pag', on_delete=models.CASCADE)
    thumbnail_page=models.FileField(upload_to='templates_page/thumbnails/',blank=True,null=True)
    export_page=models.FileField(upload_to='templates_page/exports/',blank=True,null=True)
    json_page=models.JSONField(null=True,default=dict)
    page_no=models.IntegerField()
    class Meta:
        constraints = [
        models.UniqueConstraint(fields=['template_page', 'page_no'], name="%(app_label)s_%(class)s_unique")]


def user_directory_path_canvas_mytemplatedesign_thumbnails(instance, filename):
    return '{0}/{1}/{2}'.format(instance.my_template_design.user.uid, "canvas/mytemplatedesign/canvas_thumbnails_target/thumbnails/",filename)

def user_directory_path_canvas_mytemplatedesign_exports(instance, filename):
    return '{0}/{1}/{2}'.format(instance.my_template_design.user.uid, "canvas/mytemplatedesign/canvas_exports_target/exports/",filename)

class MyTemplateDesign(models.Model):
    user=models.ForeignKey(AiUser, on_delete=models.CASCADE)
    file_name=models.CharField(max_length=50,null=True,blank=True) 
    width=models.IntegerField(null=True,blank=True)
    height=models.IntegerField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at=models.DateTimeField(auto_now=True,null=True,blank=True)
     
class MyTemplateDesignPage(models.Model):
    my_template_design=models.ForeignKey(MyTemplateDesign,related_name='my_template_page', on_delete=models.CASCADE)
    my_template_thumbnail=models.FileField(upload_to=user_directory_path_canvas_mytemplatedesign_thumbnails,blank=True,null=True)
    my_template_export=models.FileField(upload_to=user_directory_path_canvas_mytemplatedesign_exports,blank=True,null=True)
    my_template_json=models.JSONField(null=True,default=dict)
    page_no=models.IntegerField()
    class Meta:
        constraints = [
        models.UniqueConstraint(fields=['my_template_design','page_no'], name="%(app_label)s_%(class)s_unique")
        ]

def user_directory_path_canvas_source_image_assets(instance, filename):
    return '{0}/{1}/{2}'.format(instance.canvas_design_img.user.uid, "canvas/assets/sourceimage/",filename)


class SourceImageAssetsCanvasTranslate(models.Model):
    canvas_design_img=models.ForeignKey(CanvasDesign , related_name='canvas_design_image_assets', on_delete=models.CASCADE,blank=True,null=True)
    img = models.FileField(upload_to=user_directory_path_canvas_source_image_assets,blank=True,null=True)

class TextTemplate(models.Model):
    text_thumbnail=models.FileField(upload_to = 'text_template' ,blank = True , null = True)
    text_template_json=models.JSONField(blank = True , null = True)

class TemplateKeyword(models.Model):
    text_template=models.ForeignKey(TextTemplate, on_delete = models.CASCADE ,related_name= 'txt_temp')
    text_keywords=models.CharField(max_length=100)



def user_directory_path_font_file(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "canvas/font_file/fonts/",filename)

class FontFile(models.Model):
    user=models.ForeignKey(AiUser,on_delete=models.CASCADE)
    name=models.CharField(max_length=200,blank=True,null=True)
    font_family=models.FileField(upload_to=user_directory_path_font_file,blank=True,null=True)

    def __str__(self) -> str:
        return self.name
    





def user_directory_path_canvas_image_medium(filename):
    return "canvas/assets/image_medium/"+filename

# class ImageListMedium(models.Model):
    
#     image_name=models.CharField(max_length=200,blank=True,null=True)
#     api_name=models.CharField(max_length=200,blank=True,null=True)
#     preview_image=models.FileField(upload_to="canvas/assets/image_medium/",blank=True,null=True)
#     image_url=models.URLField()
#     tags=models.CharField(max_length=100,blank=True,null=True)
#     def __str__(self) -> str:
#         return self.image_name+" "+self.api_name


