from django.db import models
from ai_auth.models import AiUser
import os
from ai_workspace.models import MyDocuments
from ai_staff.models import ( Languages,PromptCategories,PromptStartPhrases,
                              PromptSubCategories,PromptTones,ModelGPTName,AiCustomize,ImageGeneratorResolution)

class TokenUsage(models.Model):
    user_input_token = models.CharField(max_length=10, null=True, blank=True)
    prompt_tokens =  models.CharField(max_length=10, null=True, blank=True)
    total_tokens =  models.CharField(max_length=10, null=True, blank=True)
    completion_tokens = models.CharField(max_length=10, null=True, blank=True)
    no_of_outcome = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self) -> str:
        return self.user_input_token+"--"+self.completion_tokens
# class ContentCatagories(models.Model):
#     pass



class AiPrompt(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    prompt_string = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    document = models.ForeignKey(to= MyDocuments, on_delete = models.SET_NULL, blank=True, null=True,related_name='prompt_doc')
    model_gpt_name = models.ForeignKey(to= ModelGPTName, on_delete = models.CASCADE,related_name='gpt_model',default=1)
    catagories = models.ForeignKey(to= PromptCategories, on_delete = models.CASCADE ,blank=True,null=True )
    sub_catagories = models.ForeignKey(to= PromptSubCategories, on_delete = models.CASCADE,blank=True,null=True)
    source_prompt_lang = models.ForeignKey(Languages, on_delete = models.CASCADE,related_name='prompt_lang')
    Tone = models.ForeignKey(PromptTones,on_delete = models.CASCADE,related_name='prompt_tone',blank=True,null=True,default=1)
    response_copies = models.IntegerField(null=True, blank=True,default=1)
    product_name = models.CharField(max_length = 1000, null=True, blank=True)
    product_name_mt = models.CharField(max_length = 1000, null=True, blank=True)
    keywords = models.CharField(max_length = 1000, null=True, blank=True)
    description_mt = models.TextField(null=True, blank=True)
    keywords_mt = models.TextField(null=True, blank=True)
    prompt_string_mt = models.TextField(null=True, blank=True)
    response_charecter_limit =  models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # def __str__(self) -> str:
    #     return self.description

    @property
    def source_prompt_lang_code(self):
        return self.source_prompt_lang.locale.first().locale_code


class AiPromptResult(models.Model):
    prompt = models.ForeignKey(AiPrompt, on_delete=models.CASCADE, related_name = 'ai_prompt')
    start_phrase =  models.ForeignKey(to= PromptStartPhrases, on_delete = models.CASCADE,null=True, blank=True)
    response_id =  models.CharField(max_length = 50, null=True, blank=True)
    copy = models.IntegerField(null=True, blank=True)
    result_lang = models.ForeignKey(Languages, on_delete = models.CASCADE,related_name='prompt_result_lang_src',null=True, blank=True)  
    token_usage =  models.ForeignKey(to= TokenUsage, on_delete = models.CASCADE,related_name='used_tokens',null=True, blank=True)
    response_created = models.CharField(max_length = 50, null=True, blank=True)
    prompt_generated = models.TextField(null=True, blank=True)
    api_result = models.TextField(null=True, blank=True) 
    translated_prompt_result = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def result_lang_code(self):
        return self.result_lang.locale.first().locale_code

class BlogCreation(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    user_title = models.CharField(max_length = 100, null=True, blank=True)
    keywords = models.CharField(max_length = 200, null=True, blank=True)
    categories = models.ForeignKey(to= PromptCategories, on_delete = models.CASCADE,related_name = 'blog_categories' ,blank=True,null=True )
    sub_categories = models.ForeignKey(to= PromptSubCategories, on_delete = models.CASCADE,related_name = 'blog_sub_categories',blank=True,null=True)
    user_language = models.ForeignKey(Languages, on_delete = models.CASCADE,related_name='user_test_lang_src',null=True, blank=True)  
    user_title_mt = models.CharField(max_length = 100, null=True, blank=True)
    keywords_mt = models.CharField(max_length = 200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def user_language_code(self):
        return self.user_language.locale.first().locale_code

class BlogKeywordGenerate(models.Model):
    blog_creation =  models.ForeignKey(BlogCreation, on_delete=models.CASCADE, related_name = 'blogcreate')
    blog_keyword = models.CharField(max_length = 200, null=True, blank=True)
    token_usage =  models.ForeignKey(to= TokenUsage, on_delete = models.CASCADE,related_name='blog_creation_used_tokens',null=True, blank=True)
    selected_field = models.BooleanField()
    blog_keyword_mt = models.CharField(max_length = 200, null=True, blank=True)

class Blogtitle(models.Model):
    blog_keyword_gen = models.ForeignKey(BlogKeywordGenerate, on_delete=models.CASCADE, related_name = 'blogtitle_keygen')
    blog_title = models.CharField(max_length = 2000 , null=True, blank=True)
    blog_title_mt =  models.CharField(max_length = 2000 , null=True, blank=True)
    token_usage =  models.ForeignKey(to= TokenUsage, on_delete=models.CASCADE,related_name='blogtitle_used_tokens',null=True, blank=True)
    selected_field = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class BlogOutline(models.Model):
    blog_title_gen = models.ForeignKey(Blogtitle, on_delete=models.CASCADE, related_name = 'blogoutline_title')
    blog_outline =  models.TextField()
    blog_outline_mt =  models.TextField()
    tone = models.ForeignKey(PromptTones,on_delete = models.CASCADE,related_name='blog_tone',blank=True,null=True,default=1)
    token_usage =  models.ForeignKey(to= TokenUsage, on_delete = models.CASCADE,related_name='blogoutline_used_tokens',null=True, blank=True)
    selected_field = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class BlogArticle(models.Model):
    blog_outline_gen = models.ForeignKey(BlogOutline, on_delete=models.CASCADE, related_name = 'blogarticle_outline')
    blog_article=  models.TextField()
    blog_article_mt =  models.TextField()
    token_usage =  models.ForeignKey(to= TokenUsage, on_delete = models.CASCADE,related_name='blogarticle_used_tokens',null=True, blank=True)
    selected_field = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class TextgeneratedCreditDeduction(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    credit_to_deduce = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class AiPromptCustomize(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    document = models.ForeignKey(MyDocuments, on_delete=models.SET_NULL, null=True, blank=True,related_name = 'ai_doc')
    customize = models.ForeignKey(AiCustomize, on_delete=models.CASCADE, related_name = 'ai_cust')
    user_text = models.TextField(null=True, blank=True)
    tone = models.ForeignKey(PromptTones,on_delete = models.CASCADE,related_name='customize_tone',blank=True,null=True,default=1)
    user_text_mt = models.TextField(null=True, blank=True)
    credits_used = models.IntegerField(null=True, blank=True)
    api_result = models.TextField(null=True, blank=True) 
    user_text_lang = models.ForeignKey(Languages, on_delete = models.CASCADE,related_name='text_lang')
    prompt_generated = models.TextField(null=True, blank=True)
    prompt_result = models.TextField(null=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)


def user_directory_path_image_gen_result(instance, filename):
    return '{0}/{1}/{2}'.format(instance.user.uid, "image_generation_result",filename)

 # document = models.ForeignKey(MyDocuments, on_delete=models.SET_NULL, null=True, blank=True,related_name = 'img_doc')
class ImageGeneratorPrompt(models.Model):
    prompt = models.TextField(null=True, blank=True)
    prompt_mt = models.TextField(null=True, blank=True)
    image_resolution = models.ForeignKey(ImageGeneratorResolution , on_delete= models.CASCADE)
    credits_used = models.IntegerField(null=True, blank=True)
    no_of_image = models.IntegerField(null=True, blank=True)
 
class ImageGenerationPromptResponse(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    created_id = models.CharField(max_length = 50, null=True, blank=True)
    generated_image =models.FileField(upload_to=user_directory_path_image_gen_result,blank=False, null=False)
    image_generator_prompt = models.ForeignKey(ImageGeneratorPrompt , on_delete= models.CASCADE,related_name='gen_img')



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
    



 
 



    
    
