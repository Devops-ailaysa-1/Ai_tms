from django.db import models
from ai_auth.models import AiUser
import os
from ai_workspace.models import MyDocuments,Task
from ai_staff.models import ( Languages,PromptCategories,PromptStartPhrases,AilaysaSupportedMtpeEngines,
                              PromptSubCategories,PromptTones,ModelGPTName,AiCustomize,ImageGeneratorResolution,
                              BackMatter,FrontMatter,BodyMatter,Levels,Genre,)
from django.contrib.postgres.fields import ArrayField

class TokenUsage(models.Model):
    user_input_token = models.CharField(max_length=10, null=True, blank=True)
    prompt_tokens =  models.CharField(max_length=10, null=True, blank=True)
    total_tokens =  models.CharField(max_length=10, null=True, blank=True)
    completion_tokens = models.CharField(max_length=10, null=True, blank=True)
    no_of_outcome = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self) -> str:
        return str(self.user_input_token)+"--"+str(self.completion_tokens)


class AiPrompt(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    prompt_string = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    document = models.ForeignKey(to= MyDocuments, on_delete = models.SET_NULL, blank=True, null=True,related_name='prompt_doc')
    task = models.ForeignKey(Task,null=True, blank=True,on_delete=models.SET_NULL,related_name = 'prompt_task')
    pdf = models.ForeignKey("ai_exportpdf.Ai_PdfUpload",null=True, blank=True,on_delete=models.SET_NULL,related_name = 'prompt_pdf')
    model_gpt_name = models.ForeignKey(to= ModelGPTName, on_delete = models.CASCADE,related_name='gpt_model',default=1)
    catagories = models.ForeignKey(to= PromptCategories, on_delete = models.SET_NULL ,blank=True,null=True )
    sub_catagories = models.ForeignKey(to= PromptSubCategories, on_delete = models.SET_NULL,blank=True,null=True)
    source_prompt_lang = models.ForeignKey(Languages, on_delete = models.CASCADE,related_name='prompt_lang')
    Tone = models.ForeignKey(PromptTones,on_delete = models.SET_NULL,related_name='prompt_tone',blank=True,null=True,default=1)
    response_copies = models.IntegerField(null=True, blank=True,default=1)
    product_name = models.CharField(max_length = 1000, null=True, blank=True)
    product_name_mt = models.CharField(max_length = 1000, null=True, blank=True)
    keywords = models.CharField(max_length = 1000, null=True, blank=True)
    description_mt = models.TextField(null=True, blank=True)
    keywords_mt = models.TextField(null=True, blank=True)
    prompt_string_mt = models.TextField(null=True, blank=True)
    response_charecter_limit =  models.IntegerField(null=True, blank=True)
    created_by = models.ForeignKey(AiUser,null=True, blank=True, on_delete=models.SET_NULL,related_name='prompt_created_by')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # def __str__(self) -> str:
    #     return self.description

    @property
    def source_prompt_lang_code(self):
        return self.source_prompt_lang.locale.first().locale_code

class AiPromptResult(models.Model):
    prompt = models.ForeignKey(AiPrompt, on_delete=models.CASCADE, related_name = 'ai_prompt')
    start_phrase =  models.ForeignKey(to= PromptStartPhrases, on_delete = models.SET_NULL,null=True, blank=True)
    response_id =  models.CharField(max_length = 50, null=True, blank=True)
    copy = models.IntegerField(null=True, blank=True)
    result_lang = models.ForeignKey(Languages, on_delete = models.SET_NULL,related_name='prompt_result_lang_src',null=True, blank=True)  
    token_usage =  models.ForeignKey(to= TokenUsage, on_delete = models.SET_NULL,related_name='used_tokens',null=True, blank=True)
    response_created = models.CharField(max_length = 50, null=True, blank=True)
    prompt_generated = models.TextField(null=True, blank=True)
    api_result = models.TextField(null=True, blank=True) 
    translated_prompt_result = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def result_lang_code(self):
        return self.result_lang.locale.first().locale_code
    
def user_directory_path_image_gen_result(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "image_generation_result",filename)

 # document = models.ForeignKey(MyDocuments, on_delete=models.SET_NULL, null=True, blank=True,related_name = 'img_doc')
# class ImageGeneratorPrompt(models.Model):
#     prompt = models.TextField(null=True, blank=True)
#     prompt_mt = models.TextField(null=True, blank=True)
#     image_resolution = models.ForeignKey(ImageGeneratorResolution , on_delete= models.CASCADE)
#     credits_used = models.IntegerField(null=True, blank=True)
#     no_of_image = models.IntegerField(null=True, blank=True)
 
# class ImageGenerationPromptResponse(models.Model):
#     user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
#     created_id = models.CharField(max_length = 50, null=True, blank=True)
#     generated_image =models.FileField(upload_to=user_directory_path_image_gen_result,blank=False, null=False)
#     image_generator_prompt = models.ForeignKey(ImageGeneratorPrompt , on_delete= models.CASCADE,related_name='gen_img')
    
class BlogCreation(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    document = models.ForeignKey(MyDocuments, on_delete=models.CASCADE, blank=True, null=True,related_name='blog_doc')
    user_title = models.CharField(max_length=100,null=True,blank=True)
    user_title_mt = models.CharField(max_length = 100, null=True, blank=True)
    keywords = models.CharField(max_length=1000,null=True,blank=True)
    keywords_mt = models.CharField(max_length = 1000, null=True, blank=True)
    prompt_user_title_mt = models.CharField(max_length = 200, null=True, blank=True)
    prompt_keyword_mt = models.CharField(max_length = 200, null=True, blank=True)
    categories = models.ForeignKey(to= PromptCategories, on_delete = models.CASCADE,related_name = 'blog_categories' ,blank=True,null=True )
    sub_categories = models.ForeignKey(to= PromptSubCategories, on_delete = models.CASCADE,related_name = 'blog_sub_categories',blank=True,null=True)
    user_language = models.ForeignKey(Languages, on_delete = models.CASCADE,related_name='user_test_lang_src',null=True, blank=True)  
    tone = models.ForeignKey(PromptTones,on_delete = models.CASCADE,related_name='blog_tone',blank=True,null=True,default=1)
    response_copies_keyword = models.IntegerField(null=True, blank=True,default=10)
    steps =  models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.ForeignKey(AiUser, on_delete=models.CASCADE,null=True, blank=True,related_name='blog_created_by')
    
    @property
    def user_language_code(self):
        return self.user_language.locale.first().locale_code

class BlogKeywordGenerate(models.Model):
    blog_creation =  models.ForeignKey(BlogCreation, on_delete=models.CASCADE, related_name='blog_key_create')
    blog_keyword = models.CharField(max_length=200,null=True,blank=True)
    blog_keyword_mt = models.CharField(max_length=200,null=True,blank=True)
    token_usage =  models.ForeignKey(to= TokenUsage,on_delete=models.CASCADE,related_name='blog_creation_used_tokens',null=True, blank=True)
    selected_field = models.BooleanField(null=True,blank=True)
 

class Blogtitle(models.Model):
    blog_creation_gen = models.ForeignKey(BlogCreation,on_delete=models.CASCADE,related_name='blog_title_create')
    sub_categories = models.ForeignKey(PromptSubCategories,on_delete=models.CASCADE,related_name='blog_title_sub_categories')
    blog_title = models.TextField(null=True,blank=True) 
    blog_title_mt =  models.TextField(null=True,blank=True)  
    token_usage =  models.ForeignKey(to=TokenUsage, on_delete=models.CASCADE,related_name='blogtitle_used_tokens',null=True, blank=True)
    selected_field = models.BooleanField(null=True,blank=True)
    response_copies = models.IntegerField(null=True, blank=True,default=3)

class BlogOutline(models.Model):
    blog_title_gen = models.ForeignKey(Blogtitle,on_delete=models.CASCADE,related_name='blogoutline_title')
    user_selected_title = models.TextField(null=True,blank=True)
    user_selected_title_mt = models.TextField(null=True,blank=True)
    sub_categories = models.ForeignKey(PromptSubCategories,on_delete=models.CASCADE,related_name='blog_outline_sub_categories')
    token_usage =  models.ForeignKey(to= TokenUsage, on_delete = models.CASCADE,related_name='blogoutline_used_tokens',null=True, blank=True)
    selected_group_num = models.IntegerField(null=True,blank=True)
    response_copies = models.IntegerField(null=True,blank=True,default=2)
    # blog_outline_json=models.JSONField(null=True,blank=True)
    # blog_outline_json_mt=models.JSONField(null=True,blank=True)
 

class BlogOutlineSession(models.Model):
    blog_title = models.ForeignKey(Blogtitle,on_delete=models.CASCADE,related_name='blogoutlinesession_title')
    blog_outline_gen = models.ForeignKey(BlogOutline,on_delete=models.CASCADE,related_name='blog_outline_session')
    blog_outline =  models.TextField(null=True,blank=True)
    blog_outline_mt =  models.TextField(null=True,blank=True)
    selected_field = models.BooleanField(null=True,blank=True,default=False)
    custom_order = models.IntegerField(null=True,blank=True) 
    temp_order = models.IntegerField(null=True,blank=True) 
    group = models.IntegerField(null=True,blank=True)

    # class Meta:
    #     unique_together = ('group', 'custom_order',)
    def save(self, *args, **kwargs):
        
        self.order = self.temp_order
        super().save()

class BlogArticle(models.Model):
    blog_creation =  models.ForeignKey(BlogCreation, on_delete=models.CASCADE, related_name='blog_article_create')
    blog_article=  models.TextField(null=True, blank=True)
    blog_article_mt =  models.TextField(null=True, blank=True)
    token_usage =  models.ForeignKey(to= TokenUsage,on_delete = models.CASCADE,related_name='blogarticle_used_tokens',null=True, blank=True)
    sub_categories = models.ForeignKey(PromptSubCategories,on_delete=models.CASCADE,related_name='blog_article_sub_categories')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    document = models.ForeignKey(MyDocuments, on_delete=models.CASCADE, null=True, blank=True,related_name = 'ai_doc_blog')
    # blog_intro = models.TextField(null=True, blank=True)
    # blog_intro_mt = models.TextField(null=True, blank=True)
    # blog_conclusion = models.TextField(null=True, blank=True)
    # blog_conclusion_mt=models.TextField(null=True, blank=True)
    #blog_outline_article_gen = models.ForeignKey(BlogOutline,on_delete=models.CASCADE, related_name = 'blogarticle_outline',null=True,blank=True)
    # blog_title=  models.TextField(null=True, blank=True)
    # selected_field = models.BooleanField()
    # blog_keyword =  models.TextField(null=True, blank=True)
    # blog_outlines = ArrayField(models.TextField(), blank=True, null=True)
    # tone = models.ForeignKey(PromptTones,on_delete = models.CASCADE,related_name='article_tone',blank=True,null=True,default=1)



class TextgeneratedCreditDeduction(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    credit_to_deduce = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class AiPromptCustomize(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    document = models.ForeignKey(MyDocuments, on_delete=models.SET_NULL, null=True, blank=True,related_name = 'ai_doc')
    task = models.ForeignKey(Task,null=True, blank=True,on_delete=models.SET_NULL,related_name = 'ai_task')
    pdf = models.ForeignKey("ai_exportpdf.Ai_PdfUpload",null=True, blank=True,on_delete=models.SET_NULL,related_name = 'ai_pdf')
    customize = models.ForeignKey(AiCustomize, on_delete=models.CASCADE, related_name = 'ai_cust')
    user_text = models.TextField(null=True, blank=True)
    tone = models.ForeignKey(PromptTones,on_delete = models.CASCADE,related_name='customize_tone',blank=True,null=True,default=1)
    user_text_mt = models.TextField(null=True, blank=True)
    credits_used = models.IntegerField(null=True, blank=True)
    api_result = models.TextField(null=True, blank=True) 
    user_text_lang = models.ForeignKey(Languages, on_delete = models.CASCADE,related_name='text_lang')
    prompt_generated = models.TextField(null=True, blank=True)
    prompt_result = models.TextField(null=True, blank=True) 
    created_by = models.ForeignKey(AiUser,null=True, blank=True, on_delete=models.SET_NULL , related_name='customize_created_by')
    created_at = models.DateTimeField(auto_now_add=True)

class TranslateCustomizeDetails(models.Model):
    customization = models.ForeignKey(AiPromptCustomize, on_delete=models.CASCADE, null=True, blank=True,related_name = 'customization')
    #source_language = models.ForeignKey(Languages, on_delete = models.CASCADE,related_name='source_lang')
    target_language = models.ForeignKey(Languages, on_delete = models.CASCADE,related_name='target_lang')
    mt_engine = models.ForeignKey(AilaysaSupportedMtpeEngines,null=True, blank=True, \
        on_delete=models.CASCADE, related_name="customization_mt_engine")
    credits_used = models.IntegerField(null=True, blank=True)
    result = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


def user_directory_path_image_gen_result(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "image_generation_result",filename)

 # document = models.ForeignKey(MyDocuments, on_delete=models.SET_NULL, null=True, blank=True,related_name = 'img_doc')
class ImageGeneratorPrompt(models.Model):
    prompt = models.TextField(null=True, blank=True)
    prompt_mt = models.TextField(null=True, blank=True)
    image_resolution = models.ForeignKey(ImageGeneratorResolution,on_delete= models.CASCADE, default=1)
    credits_used = models.IntegerField(null=True, blank=True)
    no_of_image = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
 
class ImageGenerationPromptResponse(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    created_by = models.ForeignKey(AiUser,null=True, blank=True, on_delete=models.SET_NULL, related_name='img_created_by')
    created_id = models.CharField(max_length = 50, null=True, blank=True)
    generated_image =models.FileField(upload_to=user_directory_path_image_gen_result,blank=False, null=False)
    image_generator_prompt = models.ForeignKey(ImageGeneratorPrompt,on_delete= models.CASCADE,related_name='gen_img')

class CustomizationSettings(models.Model):
    user = models.OneToOneField(AiUser, on_delete=models.CASCADE,related_name = 'custom_setting')
    mt_engine = models.ForeignKey(AilaysaSupportedMtpeEngines,default=1, \
        on_delete=models.CASCADE, related_name="customization_mt_engine_setting")
    append = models.BooleanField(default=True)
    new_line = models.BooleanField(default=True)
    

class BookCreation(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    document = models.ForeignKey(MyDocuments, on_delete=models.CASCADE, blank=True, null=True,related_name='book_doc')
    description = models.TextField(null=True,blank=True)
    description_mt = models.TextField(null=True,blank=True)
    author_info = models.TextField(null=True,blank=True)
    author_info_mt = models.TextField(null=True,blank=True)
    genre = models.ForeignKey(Genre, on_delete = models.CASCADE,related_name='book_genre',null=True, blank=True)
    level = models.ForeignKey(Levels, on_delete = models.CASCADE,related_name='book_level',null=True, blank=True) 
    title = models.TextField(null=True,blank=True)
    title_mt = models.TextField(null=True,blank=True)
    categories = models.ForeignKey(PromptCategories, on_delete = models.CASCADE,related_name = 'book_categories' ,blank=True,null=True )
    sub_categories = models.ForeignKey(PromptSubCategories, on_delete = models.CASCADE,related_name = 'book_sub_categories',blank=True,null=True)
    book_language = models.ForeignKey(Languages, on_delete = models.CASCADE,related_name='book_lang_src',null=True, blank=True)  
    
    @property
    def book_language_code(self):
        return self.book_language.locale.first().locale_code

class BookTitle(models.Model):
    book_creation = models.ForeignKey(BookCreation,on_delete=models.CASCADE,related_name='book_title_create')
    sub_categories = models.ForeignKey(PromptSubCategories,on_delete=models.CASCADE,related_name='book_title_sub_categories')
    html_data = models.TextField(null=True,blank=True)
    book_title = models.TextField(null=True,blank=True) 
    book_title_mt =  models.TextField(null=True,blank=True)  
    token_usage =  models.ForeignKey(to=TokenUsage, on_delete=models.CASCADE,related_name='booktitle_used_tokens',null=True, blank=True)
    selected_field = models.BooleanField(null=True,blank=True)
    response_copies = models.IntegerField(null=True, blank=True,default=3) 


class BookFrontMatter(models.Model):
    book_creation = models.ForeignKey(BookCreation,on_delete=models.CASCADE,related_name='book_fm_create')
    front_matter = models.ForeignKey(FrontMatter,on_delete=models.CASCADE,related_name='book_front_matter')
    sub_categories = models.ForeignKey(PromptSubCategories,on_delete=models.CASCADE,related_name='book_fm_sub_categories')
    html_data = models.TextField(null=True,blank=True)
    name = models.CharField(max_length = 250, null=True, blank=True)
    generated_content = models.TextField(null=True,blank=True) 
    generated_content_mt = models.TextField(null=True,blank=True) 
    token_usage =  models.ForeignKey(to=TokenUsage, on_delete=models.CASCADE,related_name='book_fm_tokens',null=True, blank=True)
    selected_field = models.BooleanField(null=True,blank=True)
    custom_order = models.IntegerField(null=True,blank=True) 
    temp_order = models.IntegerField(null=True,blank=True) 

class BookBody(models.Model):
    book_creation = models.ForeignKey(BookCreation,on_delete=models.CASCADE,related_name='book_bdy_create',null=True,blank=True)
    book_title = models.ForeignKey(BookTitle,on_delete=models.CASCADE,related_name='book_title_bdy',null=True,blank=True)
    body_matter = models.ForeignKey(BodyMatter,on_delete=models.CASCADE,related_name='book_body_matter')
    sub_categories = models.ForeignKey(PromptSubCategories,on_delete=models.CASCADE,related_name='book_bdy_sub_categories')
    generated_content = models.TextField(null=True,blank=True) 
    token_usage =  models.ForeignKey(to=TokenUsage, on_delete=models.CASCADE,related_name='bookbdy_tokens',null=True, blank=True)
    name = models.CharField(max_length = 250, null=True, blank=True)
    html_data = models.TextField(null=True,blank=True)
    generated_content_mt = models.TextField(null=True,blank=True) 
    selected_field = models.BooleanField(null=True,blank=True)
    response_copies = models.IntegerField(null=True, blank=True,default=1)
    custom_order = models.IntegerField(null=True,blank=True) 
    temp_order = models.IntegerField(null=True,blank=True) 
    group = models.IntegerField(null=True,blank=True)

class BookBodyDetails(models.Model):
    book_bm = models.ForeignKey(BookBody,on_delete=models.CASCADE,related_name='book_bdy_det_create')
    html_data = models.TextField(null=True,blank=True)
    generated_chapter = models.TextField(null=True,blank=True)
    generated_chapter_mt = models.TextField(null=True,blank=True)
    chapter_summary = models.TextField(null=True,blank=True)
    token_usage =  models.ForeignKey(to=TokenUsage, on_delete=models.CASCADE,related_name='bookbdy_det_tokens',null=True, blank=True)


class BookBackMatter(models.Model):
    book_creation = models.ForeignKey(BookCreation,on_delete=models.CASCADE,related_name='book_bm_create')
    back_matter = models.ForeignKey(BackMatter,on_delete=models.CASCADE,related_name='book_back_matter')
    sub_categories = models.ForeignKey(PromptSubCategories,on_delete=models.CASCADE,related_name='book_bm_sub_categories')
    name = models.CharField(max_length = 250, null=True, blank=True)
    html_data = models.TextField(null=True,blank=True)
    generated_content = models.TextField(null=True,blank=True) 
    generated_content_mt = models.TextField(null=True,blank=True) 
    selected_field = models.BooleanField(null=True,blank=True)
    custom_order = models.IntegerField(null=True,blank=True) 
    temp_order = models.IntegerField(null=True,blank=True) 
    token_usage =  models.ForeignKey(to=TokenUsage, on_delete=models.CASCADE,related_name='book_bm_tokens',null=True, blank=True)


# class InstantTranslation(models.Model):
#     # InstantChoice=[
#     #     ('Shorten' , 'Shorten'),
#     #     ('Simplify' ,'Simplify')
#     # ]
#     user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
#     instant_text = models.CharField(max_length=800)
#     source_lang = models.ForeignKey(Languages, on_delete = models.CASCADE,related_name='insta_trans_src_lang')
#     target_lang = models.ForeignKey(Languages, on_delete = models.CASCADE,related_name='insta_trans_tar_lang') 
#     # instance_choice = models.CharField(max_length=30, choices=InstantChoice)
#     customize = models.ForeignKey(AiCustomize, on_delete=models.CASCADE, related_name = 'insta_cust')
#     insta_usage = models.IntegerField()
#     instant_result = models.CharField(max_length=800)
    






    
