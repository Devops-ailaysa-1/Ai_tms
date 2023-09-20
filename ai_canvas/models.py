from django.db import models

# Create your models here.
from ai_workspace.models import Project,Job
from ai_staff.models import Languages ,LanguagesLocale,SocialMediaSize
from ai_auth.models import AiUser
from ai_staff.models import ImageCategories  
class CanvasCatagories(models.Model):
    catagory_name = models.CharField(max_length=50,null=True,blank=True)
    def __str__(self) -> str:
        return self.catagory_name


class CanvasTemplates(models.Model):
    file_name =  models.CharField(max_length=2000,null=True,blank=True) 
    template_json = models.JSONField()
    thumbnail=models.FileField(upload_to='aidesign_templates/thumbnails/',blank=True,null=True)
    width = models.IntegerField(null=True,blank=True)
    height = models.IntegerField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at= models.DateTimeField(auto_now=True,null=True,blank=True)


def user_directory_path_canvas_source_json_thumbnails(instance, filename):
    return '{0}/{1}/{2}'.format(instance.canvas_design.user.uid, "aidesign/design/aidesign_templates_source/thumbnails/",filename)

def user_directory_path_canvas_source_json_exports(instance, filename):
    return '{0}/{1}/{2}'.format(instance.canvas_design.user.uid, "aidesign/design/aidesign_exports_source/exports/",filename)

def user_directory_path_canvas_image_assets(instance, filename): ###
    return '{0}/{1}/{2}'.format(instance.user.uid, "aidesign/assets/aidesign_assets/images/",filename)

def user_directory_path_canvas_target_json_thumbnails(instance, filename):
    return '{0}/{1}/{2}'.format(instance.canvas_trans_json.canvas_design.user.uid, "aidesign/design/aidesign_exports_target/thumbnails/",filename)

def user_directory_path_canvas_target_json_exports(instance, filename):
    return '{0}/{1}/{2}'.format(instance.canvas_trans_json.canvas_design.user.uid, "aidesign/design/aidesign_exports_target/exports/",filename)

def user_directory_path_canvas_user_imageassets(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "aidesign/assets/aidesign_assets/thumbnail",filename)


class CanvasUserImageAssets(models.Model):
    user=models.ForeignKey(AiUser, on_delete=models.CASCADE)
    image_name=models.CharField(max_length=2000,null=True,blank=True)
    image= models.FileField(upload_to=user_directory_path_canvas_image_assets,blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at=models.DateTimeField(auto_now=True,null=True,blank=True)
    height=models.IntegerField(null=True,blank=True)
    width=models.IntegerField(null=True,blank=True)
    thumbnail=models.FileField(upload_to=user_directory_path_canvas_user_imageassets,blank=True,null=True)
    # status=models.BooleanField(default=False)

class CanvasDesign(models.Model):
    project = models.OneToOneField(Project, null=True, blank=True, on_delete=models.CASCADE, related_name="designer_project")
    user=models.ForeignKey(AiUser, on_delete=models.CASCADE)
    # task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="task_designer_details")
    file_name=models.CharField(max_length=50,null=True,blank=True) 
    width=models.IntegerField(null=True,blank=True)
    height=models.IntegerField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at=models.DateTimeField(auto_now=True,null=True,blank=True)
    project_category=models.ForeignKey(SocialMediaSize,on_delete=models.CASCADE,null=True)

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
    # 
    # canvas_src_json=models.ForeignKey(CanvasSourceJsonFiles,related_name='canvas_src',on_delete=models.CASCADE,null=True,blank=True)
    canvas_design=models.ForeignKey(CanvasDesign,related_name='canvas_translate', on_delete=models.CASCADE)
    source_language=models.ForeignKey(LanguagesLocale,related_name='source_locale' , on_delete=models.CASCADE) 
    target_language=models.ForeignKey(LanguagesLocale,related_name='target', on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True,related_name="canvas_job")
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

# #########global template design##############

class TemplateGlobalDesign(models.Model):
    template_name=models.CharField(max_length=50,null=True,blank=True)
    category=models.ForeignKey(SocialMediaSize,related_name='template_global_categoty', on_delete=models.CASCADE)
    width=models.IntegerField(null=True,blank=True)
    height=models.IntegerField(null=True,blank=True)
    # user_name=models.CharField(max_length=100,null=True,blank=True)
    is_pro=models.BooleanField()
    is_published=models.BooleanField()
    description=models.CharField(max_length=600,blank=True,null=True)
    thumbnail_page=models.FileField(upload_to='templates_page/thumbnails/',blank=True,null=True)
    export_page=models.FileField(upload_to='templates_page/exports/',blank=True,null=True)
    json=models.JSONField(blank=True,null=True)
    template_lang=models.ForeignKey(Languages,related_name='template_page_lang', on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at=models.DateTimeField(auto_now=True,null=True,blank=True)


class TemplateTag(models.Model):
    tag_name=models.CharField(max_length=500,null=True,blank=True)
    global_template=models.ForeignKey(TemplateGlobalDesign,related_name='template_global_page', on_delete=models.CASCADE)
    def __str__(self) -> str:
        if self.tag_name:
            return self.tag_name
        else:
            return ""


def user_directory_path_canvas_mytemplatedesign_thumbnails(instance, filename):
    return '{0}/{1}/{2}'.format(instance.my_template_design.user.uid, "aidesign/mytemplatedesign/aidesign_thumbnails_target/thumbnails/",filename)

def user_directory_path_canvas_mytemplatedesign_exports(instance, filename):
    return '{0}/{1}/{2}'.format(instance.my_template_design.user.uid, "aidesign/mytemplatedesign/aidesign_exports_target/exports/",filename)




class MyTemplateDesign(models.Model):
    user=models.ForeignKey(AiUser, on_delete=models.CASCADE)
    file_name=models.CharField(max_length=50,null=True,blank=True) 
    width=models.IntegerField(null=True,blank=True)
    height=models.IntegerField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at=models.DateTimeField(auto_now=True,null=True,blank=True)
    project_category=models.ForeignKey(SocialMediaSize,on_delete=models.CASCADE,null=True,related_name='project_cat_mytemplate')
     


class MyTemplateDesignPage(models.Model):
    my_template_design=models.ForeignKey(MyTemplateDesign,related_name='my_template_page', on_delete=models.CASCADE)
    my_template_thumbnail=models.FileField(upload_to=user_directory_path_canvas_mytemplatedesign_thumbnails,blank=True,null=True)
    my_template_export=models.FileField(upload_to=user_directory_path_canvas_mytemplatedesign_exports,blank=True,null=True)
    my_template_json=models.JSONField(null=True,default=dict)

    # page_no=models.IntegerField()
    # class Meta:
    #     constraints = [
    #     models.UniqueConstraint(fields=['my_template_design','page_no'], name="%(app_label)s_%(class)s_unique")
    #     ]

def user_directory_path_canvas_source_image_assets(instance, filename):
    return '{0}/{1}/{2}'.format(instance.canvas_design_img.user.uid, "aidesign/assets/sourceimage/",filename)





class SourceImageAssetsCanvasTranslate(models.Model):
    canvas_design_img=models.ForeignKey(CanvasDesign , related_name='aidesign_design_image_assets', on_delete=models.CASCADE,blank=True,null=True)
    img = models.FileField(upload_to=user_directory_path_canvas_source_image_assets,blank=True,null=True)

class TextTemplate(models.Model):
    text_thumbnail=models.FileField(upload_to = 'text_template' ,blank = True , null = True)
    text_template_json=models.JSONField(blank = True , null = True)

class TemplateKeyword(models.Model):
    text_template=models.ForeignKey(TextTemplate, on_delete = models.CASCADE ,related_name= 'txt_temp')
    text_keywords=models.CharField(max_length=100)

def user_directory_path_font_file(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "aidesign/font_file/fonts/",filename)




class FontFile(models.Model):
    user=models.ForeignKey(AiUser,on_delete=models.CASCADE)
    name=models.CharField(max_length=2000,blank=True,null=True)
    font_family=models.FileField(upload_to=user_directory_path_font_file,blank=True,null=True)

    def __str__(self) -> str:
        return self.name
    
class ThirdpartyImageMedium(models.Model):
    image = models.FileField(upload_to="aidesign/thirdpartyimage",blank=True,null=True)

def user_directory_path_canvas_image_medium(filename):
    return "aidesign/assets/image_medium/"+filename



class CanvasDownloadFormat(models.Model):
    format_name=models.CharField(max_length=200,null=True,blank=True)

    def __str__(self) -> str:
        return self.format_name
    



class CanvasSourceUpdate(models.Model):
    text_id=models.CharField(max_length=300,null=True,blank=True)
    # translate_text=models.CharField(max_length=2000,null=True,blank=True)
    source_text=models.CharField(max_length=2000,null=True,blank=True)
    prev_text=models.CharField(max_length=2000,null=True,blank=True)

    def __str__(self) -> str:
        prev_text= "" if not self.prev_text else self.prev_text
        source_text= "" if not self.source_text else self.source_text
        # translate_text= "" if not self.translate_text else self.translate_text
        return self.text_id+"--"+source_text+"--"+prev_text



class TextboxUpdate(models.Model):
    canvas=models.ForeignKey(CanvasDesign,related_name='canvas_text_box', on_delete=models.CASCADE)
    # canvas_src=models.ForeignKey(CanvasSourceJsonFiles,related_name='canvas_text_box_src', on_delete=models.CASCADE,default=1)
    text_id=models.CharField(max_length=1000,null=True,blank=True)
    text=models.CharField(max_length=1000,null=True,blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['canvas', 'text_id'], name="%(app_label)s_%(class)s_unique")]

    def __str__(self) -> str:
        if self.text and self.text_id:
            return self.text and self.text_id
        else:
            return ""

class EmojiCategory(models.Model):
    name=models.CharField(max_length=200,null=True,blank=True)
    def __str__(self) -> str:
        if self.name:
            return self.name
        else:
            return ""



class EmojiData(models.Model):
    emoji_cat=models.ForeignKey(EmojiCategory,on_delete=models.CASCADE,related_name='emoji_cat_data')
    emoji_name=models.CharField(max_length=300,null=True,blank=True)
    data=models.TextField()
    def __str__(self) -> str:
        return self.emoji_name
    

class ImageListCategory(models.Model):
    imageurl=models.CharField(max_length=3000,null=True,blank=True)
    preview_img=models.CharField(max_length=3000,null=True,blank=True)
    tags=models.CharField(max_length=300,null=True,blank=True)
    type=models.CharField(max_length=200,null=True,blank=True)
    user=models.CharField(max_length=200,null=True,blank=True)

    def __str__(self) -> str:
        return self.type


# class ImageListMedium(models.Model):
    
#     image_name=models.CharField(max_length=200,blank=True,null=True)
#     api_name=models.CharField(max_length=200,blank=True,null=True)
#     preview_image=models.FileField(upload_to="canvas/assets/image_medium/",blank=True,null=True)
#     image_url=models.URLField()
#     tags=models.CharField(max_length=100,blank=True,null=True)
#     def __str__(self) -> str:
#         return self.image_name+" "+self.api_name


# class GlobalTemplateTags(models.Model):
#     tag_name=models.ForeignKey(TemplateTag,related_name='template_global_tag_name', on_delete=models.CASCADE)
#     template_design=models.ForeignKey(TemplateGlobalDesign,related_name='template_global_tag', on_delete=models.CASCADE)

#     created_at=models.DateTimeField(auto_now_add=True,blank=True,null=True)
#     updated_at=models.DateTimeField(auto_now=True,null=True,blank=True)
 


# class TemplatePage(models.Model):
#     template_page=models.ForeignKey(TemplateGlobalDesign,related_name='template_globl_pag', on_delete=models.CASCADE)
#     thumbnail_page=models.FileField(upload_to='templates_page/thumbnails/',blank=True,null=True)
#     export_page=models.FileField(upload_to='templates_page/exports/',blank=True,null=True)
#     json_page=models.JSONField(null=True,default=dict)
#     template_lang=models.ForeignKey(Languages,related_name='template_page_lang', on_delete=models.CASCADE)
    # page_no=models.IntegerField()
    # class Meta:
    #     constraints = [
    #     models.UniqueConstraint(fields=['template_page', 'page_no'], name="%(app_label)s_%(class)s_unique")]
    
# class PromptCategory(models.Model):
#     name=models.CharField(max_length=256)

#     def __str__(self):
#         return self.name

# class TemplateBackground(models.Model):
#     prompt_category=models.ForeignKey(PromptCategory,related_name='prompt_background', on_delete=models.CASCADE)
#     bg_image=models.FileField(upload_to="backround-template",blank=True,null=True)
#     height=models.IntegerField(blank=True,null=True)
#     width=models.IntegerField(blank=True,null=True)

# class PromptEngine(models.Model):
#     prompt_category=models.ForeignKey(PromptCategory,related_name='prompt_category', on_delete=models.CASCADE)
#     prompt=models.CharField(max_length=256)
#     key_words=models.JSONField(null=True,blank=True,default=dict)
#     image=models.FileField(upload_to="prompt-image",blank=True,null=True)
#     mask_image=models.FileField(upload_to="prompt-mask-image",blank=True,null=True)
#     height=models.IntegerField(blank=True,null=True)
#     width=models.IntegerField(blank=True,null=True)

#     def __str__(self):
#         return self.prompt
    
#     @property
#     def background_img(self):
#         return self.prompt_category.prompt_background.all()
    
# class PromptMaskImage(models.Model):
#     mask_image=models.ForeignKey(PromptEngine,on_delete=models.CASCADE,related_name="prompt_image")
#     image_url=models.URLField(blank=True,null=True)

#     def __str__(self):
#         return self.image_url

class AiAssertscategory(models.Model):
    name=models.CharField(max_length=256)

    def __str__(self):
        return self.name
    

class AiAsserts(models.Model):
    imageurl=models.FileField(upload_to="Ai-assert",blank=True,null=True)
    preview_img=models.FileField(upload_to="Ai-assert",blank=True,null=True)
    tags=models.TextField(blank=True, null=True)
    positive_prompt=models.TextField(blank=True, null=True)
    negative_prompt=models.TextField(blank=True, null=True)
    category=models.ForeignKey(ImageCategories, on_delete=models.CASCADE)
    type=models.ForeignKey(AiAssertscategory, on_delete=models.CASCADE)
    user=models.CharField(max_length=2000,null=True,blank=True)
    status=models.BooleanField(default=False)

    # def __str__(self):
    #     return str(self.type)


class AssetCategory(models.Model):
    cat_name=models.CharField(max_length=300,null=True,blank=True)

class AssetImage(models.Model):
    user_asset = models.ForeignKey(CanvasUserImageAssets,on_delete=models.CASCADE,related_name='user_asset_image')
    image_category=models.ForeignKey(AssetCategory, on_delete=models.CASCADE,related_name='cat_asset_image')
    imageurl=models.FileField(upload_to="asset-image",blank=True,null=True)
    blob = models.FileField(upload_to="asset-blob",blank=True,null=True)
    preview_img=models.FileField(upload_to="asset_thumbnail",blank=True,null=True)
    tags = models.TextField(blank=True, null=True)
    positive_prompt=models.TextField(blank=True, null=True)
    negative_prompt=models.TextField(blank=True, null=True)
    country=models.CharField(max_length=300,blank=True, null=True)
    is_store=models.BooleanField(default=False)
    category = models.ForeignKey(ImageCategories, on_delete=models.CASCADE,related_name='image_asset_cat',null=True,blank=True)


    

