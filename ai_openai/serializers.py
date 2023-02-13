from rest_framework.response import Response
from rest_framework import serializers
from .models import (AiPrompt ,AiPromptResult,TokenUsage,TextgeneratedCreditDeduction,
                    AiPromptCustomize ,ImageGeneratorPrompt ,ImageGenerationPromptResponse ,
                    ImageGeneratorResolution,BlogKeywordGenerate,BlogCreation ,Blogtitle )
from ai_staff.models import PromptCategories,PromptSubCategories ,AiCustomize, LanguagesLocale ,PromptStartPhrases
from .utils import get_prompt ,get_consumable_credits_for_openai_text_generator,get_prompt_freestyle ,get_prompt_image_generations ,get_img_content_from_openai_url
from ai_workspace_okapi.utils import get_translation
import math
from ai_workspace.api_views import UpdateTaskCreditStatus ,get_consumable_credits_for_text
from ai_tms.settings import  OPENAI_MODEL

class AiPromptSerializer(serializers.ModelSerializer):
    targets = serializers.ListField(allow_null=True,required=False)
    sub_catagories = serializers.PrimaryKeyRelatedField(queryset=PromptSubCategories.objects.all(),many=False,required=False)
    class Meta:
        model = AiPrompt
        fields = ('id','user','prompt_string','description','document','model_gpt_name','catagories','sub_catagories',
            'source_prompt_lang','Tone' ,'response_copies','product_name','keywords',
            'response_charecter_limit','targets')
  
    def prompt_generation(self,ins,obj,ai_langs,targets):
        instance = AiPrompt.objects.get(id=ins)
        lang = instance.source_prompt_lang_id 
        start_phrase = None
        prompt=''
        if instance.catagories.category == 'Free Style':
            prompt+= instance.description if lang in ai_langs else instance.description_mt
        else:
            print("not Free Style")
            start_phrase = instance.sub_catagories.prompt_sub_category.first()
            prompt+=start_phrase.start_phrase+' '
            if instance.product_name:
                prompt+=' '+instance.product_name if lang in ai_langs else instance.product_name_mt
            if instance.description:
                prompt+=' '+instance.description if lang in ai_langs else instance.description_mt
            
            prompt+=', in {} tone'.format(instance.Tone.tone)
            print("prompt-->",prompt)
            if instance.keywords:
                prompt+=' including words '+ instance.keywords if lang in ai_langs else ' including words '+ instance.keywords_mt
            if start_phrase.punctuation:
                prompt+=start_phrase.punctuation
        initial_credit = instance.user.credit_balance.get("total_left")
        consumable_credit = get_consumable_credits_for_text(prompt,target_lang=None,source_lang=instance.source_prompt_lang_code)
        if initial_credit < consumable_credit:
            return  Response({'msg':'Insufficient Credits'},status=400)

        token = instance.sub_catagories.prompt_sub_category.first().max_token if instance.sub_catagories else 256
        openai_response =get_prompt(prompt,instance.model_gpt_name.model_code , 
                                token ,instance.response_copies )

        generated_text = openai_response.get('choices' ,None)
        response_id =openai_response.get('id' , None)
        token_usage = openai_response.get('usage' ,None) 
        prompt_token = token_usage['prompt_tokens']
        total_tokens=token_usage['total_tokens']
        completion_tokens=token_usage['completion_tokens']
        print("CompletionTokens------->",completion_tokens)
        no_of_outcome = instance.response_copies
        token_usage=TokenUsage.objects.create(user_input_token=instance.response_charecter_limit,prompt_tokens=prompt_token,
                                    total_tokens=total_tokens , completion_tokens=completion_tokens,  
                                    no_of_outcome=no_of_outcome)
        total_tokens = get_consumable_credits_for_openai_text_generator(total_tokens)
        self.customize_token_deduction(instance , total_tokens)            
        
        if generated_text:
            print("generated_text" , generated_text)
            rr = [AiPromptResult.objects.update_or_create(prompt=instance,result_lang=obj.result_lang,copy=j,\
                    defaults = {'prompt_generated':prompt,'start_phrase':start_phrase,\
                    'response_id':response_id,'token_usage':token_usage,'api_result':i['text'].strip()}) for j,i in enumerate(generated_text)]
        return None

    def customize_token_deduction(self,instance ,total_tokens):
        initial_credit = instance.user.credit_balance.get("total_left")
        if initial_credit >=total_tokens:
            debit_status, status_code = UpdateTaskCreditStatus.update_credits(instance.user, total_tokens)
        else:
            token_deduction = total_tokens - initial_credit 
            debit_status, status_code = UpdateTaskCreditStatus.update_credits(instance.user, initial_credit)
            deduction_update = TextgeneratedCreditDeduction.objects.filter(user=instance.user)
            if deduction_update.exists():
                total_deduction = deduction_update.first().credit_to_deduce
                total_deduction = total_deduction+token_deduction
                deduction_update.update(credit_to_deduce = total_deduction)
                # deduction_update.save()
            else:
                TextgeneratedCreditDeduction.objects.create(user=instance.user,credit_to_deduce = token_deduction)
        
    def prompt_result_update(self,ins,obj,ai_langs,targets):
        instance = AiPrompt.objects.get(id=ins)
        prompt = self.prompt_generation(ins,obj,ai_langs,targets) 
        if prompt:
            return prompt
        queryset = instance.ai_prompt.filter(response_id=None).filter(api_result=None).exclude(result_lang__in=ai_langs) 
        queryset_2 = instance.ai_prompt.filter(result_lang__in=ai_langs)
        for j in queryset_2:
            for i in queryset:
                if i.copy==j.copy:
                    content = j.api_result
                    trans = get_translation(1, content , j.result_lang_code, i.result_lang_code,user_id = instance.user.id) if content else None
                    i.translated_prompt_result = trans
                    i.save()
                    word_count = get_consumable_credits_for_text(content,source_lang=j.result_lang_code,target_lang=i.result_lang_code)
                    self.customize_token_deduction(instance , word_count)

    def get_total_consumable_credits(self,source_lang,prompt_string_list):
        credit = 0
        for i in prompt_string_list:
            if i != None:
                consumable_credit = get_consumable_credits_for_text(i,None,source_lang)
                credit+=consumable_credit
        return credit

    def create(self, validated_data):
        openai_available_langs = [17]
        targets = validated_data.pop('targets',None)
        instance = AiPrompt.objects.create(**validated_data)
        initial_credit = instance.user.credit_balance.get("total_left")
        user = instance.user 
        if instance.source_prompt_lang_id not in openai_available_langs:
            string_list = [instance.description,instance.keywords,instance.prompt_string,instance.product_name]
            prmt_res = AiPromptResult.objects.create(prompt=instance,result_lang_id=17,copy=0)
            description_mt = get_translation(1, instance.description , instance.source_prompt_lang_code, prmt_res.result_lang_code,user_id=user.id) if instance.description else None
            keywords_mt = get_translation(1, instance.keywords , instance.source_prompt_lang_code, prmt_res.result_lang_code,user_id=user.id) if instance.keywords else None
            prompt_string_mt = get_translation(1, instance.prompt_string , instance.source_prompt_lang_code, prmt_res.result_lang_code,user_id=user.id) if instance.prompt_string else None
            product_name_mt = get_translation(1, instance.product_name , instance.source_prompt_lang_code, prmt_res.result_lang_code,user_id=user.id) if instance.product_name else None
            AiPrompt.objects.filter(id=instance.id).update(description_mt = description_mt,keywords_mt=keywords_mt,prompt_string_mt=prompt_string_mt,product_name_mt=product_name_mt)
            consumed_credits = self.get_total_consumable_credits(instance.source_prompt_lang_code,string_list)
            print("cons---------->",consumed_credits)
            if initial_credit < consumed_credits:
                raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
            self.customize_token_deduction(instance , consumed_credits)
        else:
            prmt_res = AiPromptResult.objects.create(prompt=instance,result_lang_id=instance.source_prompt_lang_id,copy=0)
        if instance.response_copies >1:
            tt = [AiPromptResult.objects.get_or_create(prompt=instance,result_lang_id=i,copy=j) for i in targets for j in range(instance.response_copies)]
        else:
            tt= [AiPromptResult.objects.get_or_create(prompt=instance,result_lang_id=i,copy=0) for i in targets]       
        pr_result = self.prompt_result_update(instance.id,prmt_res,openai_available_langs,targets) 
        if pr_result:
            raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)        
        return instance



class AiPromptResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiPromptResult
        fields = ('id', 'copy','prompt_generated','api_result','translated_prompt_result','result_lang','prompt',)#'__all__'
        
        extra_kwargs = {
            "prompt_generated": {"write_only": True},
        }

class AiPromptGetSerializer(serializers.ModelSerializer):
    prompt_results = serializers.SerializerMethodField()
    target_langs = serializers.SerializerMethodField()
    doc_name = serializers.ReadOnlyField(source='document.doc_name')
    #ai_prompt = AiPromptResultSerializer(many=True)

    class Meta:
        model = AiPrompt
        fields = ('id','user','prompt_string','doc_name','document','source_prompt_lang','target_langs','description','catagories','sub_catagories','Tone',
                    'product_name','keywords','created_at','prompt_results',)#,'ai_prompt'
        
        extra_kwargs = {
            "prompt_string": {"write_only": True},
            "document": {"write_only": True},
        }
        
    def get_target_langs(self,obj):
        return [i.result_lang.language for i in obj.ai_prompt.all().distinct('result_lang')]

    def get_prompt_results(self,obj):
        result_dict ={}
        results = AiPromptResult.objects.filter(prompt_id = obj.id).distinct('copy')
        for i in results:
            rr = AiPromptResult.objects.filter(prompt_id = obj.id).filter(copy=i.copy)
            result_dict[i.copy] = AiPromptResultSerializer(rr,many=True).data
        return result_dict

    # def create(self, validated_data):
    #     print("validated_data--->" , validated_data)
    #     return super().create(validated_data)


class AiCustomizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiCustomize
        fields = ('id' , 'customize')


class AiPromptCustomizeSerializer(serializers.ModelSerializer):
    customize_name = serializers.ReadOnlyField(source='customize.customize')
    doc_name =  serializers.ReadOnlyField(source='document.doc_name')
    class Meta:
        model = AiPromptCustomize
        fields = ('id','document','doc_name','customize','customize_name','user_text',\
                    'tone','api_result','prompt_result','user_text_lang','user',\
                    'credits_used','prompt_generated','user_text_mt','created_at')

        extra_kwargs = {
            "user":{"write_only": True},
            "prompt_generated": {"write_only": True},
            "credits_used": {"write_only": True},
            "user_text_mt": {"write_only": True},
        }
        
        
from django import core

class ImageGenerationPromptResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageGenerationPromptResponse
        fields = ('id' , 'generated_image')

class ImageGeneratorPromptSerializer(serializers.ModelSerializer):  
    gen_img = ImageGenerationPromptResponseSerializer(many=True,required=False)
    class Meta:
        model = ImageGeneratorPrompt
        fields = ('id','prompt','prompt_mt','image_resolution','no_of_image','gen_img' )
        
        
    def create(self, validated_data):
        user=self.context['request'].user
        inst = ImageGeneratorPrompt.objects.create(**validated_data)
        image_reso = ImageGeneratorResolution.objects.get(image_resolution =inst.image_resolution )
        image_res = get_prompt_image_generations(inst.prompt,
                                          image_reso.image_resolution,
                                          inst.no_of_image)
        data = image_res['data']     
        created_id = image_res["created"]  
        for i in range(inst.no_of_image):
            img_content = get_img_content_from_openai_url(data[i]['url'])
            image_file = core.files.File(core.files.base.ContentFile(img_content),"file.png")
            img_gen_Pmpt_res=ImageGenerationPromptResponse.objects.create(user =user,created_id = created_id ,
                                                        generated_image = image_file,
                                                        image_generator_prompt = inst)                                                                                    
        return inst
    
    
# class InstantTranslationSerializer(serializers.ModelSerializer):
#     instant_result = serializers.CharField(required = False)
#     class Meta:
#         model = InstantTranslation
#         fields = '__all__'
        
 
def openai_token_usage(openai_response ):
    token_usage = openai_response.get("usage",None)
    prompt_token = token_usage['prompt_tokens']
    total_tokens=token_usage['total_tokens']
    completion_tokens=token_usage['completion_tokens']
    return TokenUsage.objects.create(user_input_token=150,prompt_tokens=prompt_token,
                                total_tokens=total_tokens , completion_tokens=completion_tokens,  
                                no_of_outcome=1)


class BlogtitleSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Blogtitle
        fields = ('id' , 'blog_keyword_gen' , 'blog_title' , 'blog_title_mt'
                  , 'token_usage' ,  'selected_field' )


class BlogKeywordGenerateSerializer(serializers.ModelSerializer):
    # blogtitle_keygen = BlogtitleSerializer(required=False,many=True)
    class Meta:
        model = BlogKeywordGenerate
        fields = ('id','blog_creation','token_usage','selected_field','blog_keyword_mt',
                  'blog_keyword' , 'blogtitle_keygen')
 


class BlogCreationSerializer(serializers.ModelSerializer):
    blogcreate = BlogKeywordGenerateSerializer(required=False,many=True)
    sub_categories = serializers.PrimaryKeyRelatedField(queryset=PromptSubCategories.objects.all(),many=False,required=False)
    categories = serializers.PrimaryKeyRelatedField(queryset=PromptCategories.objects.all(),many=False,required=False)
    blog_key_gen = serializers.PrimaryKeyRelatedField(queryset=BlogKeywordGenerate.objects.all(),many=False,required=False)
    
    blogtitle_keygen = BlogtitleSerializer(required=False,many=True)
    blog_title_gen = serializers.PrimaryKeyRelatedField(queryset=Blogtitle.objects.all(),many=False,required=False)
    blog_title_create_boolean = serializers.BooleanField(required=False)
    
    class Meta:
        model = BlogCreation
        fields = ('id','user_title' , 'categories' , 'sub_categories', 'user_language' , 'user_title_mt' , 
                  'keywords_mt' , 'blogcreate','blog_key_gen' , 'blogtitle_keygen' ,'blog_title_gen'
                  ,'blog_title_create_boolean'  )  
    
    def validate(self, data ,request=None):
        validated_data = super().validate(data)
        user=self.context.get('request' , None)
        if user:
            validated_data['user'] = user.user
        return validated_data
      
    def create(self, validated_data):
        blog_available_langs = [17]
        user=self.context['request'].user
        instance = BlogCreation.objects.create(**validated_data)
        blog_sub_phrase = PromptStartPhrases.objects.get(sub_category = instance.sub_categories)
        # BlogKeywordGenerate
        if (instance.user_language_id not in blog_available_langs):
            instance.user_title_mt = get_translation(1, instance.user_title , instance.user_language_code,"en"  ,user_id=instance.user.id) if instance.user_title else None
            openai_response = get_prompt(blog_sub_phrase.start_phrase+ " " +instance.user_title_mt , OPENAI_MODEL,
                                         blog_sub_phrase.max_token, n=3)
            token_usage = openai_token_usage(openai_response)
            for i in range(len(openai_response["choices"])):
                blog_keyword = openai_response["choices"][i]['text']
                blog_keyword_mt = get_translation(1, blog_keyword ,"en",instance.user_language_code,user_id=instance.user.id) if instance.user_title else None
                BlogKeywordGenerate.objects.create(blog_creation = instance
                                                , blog_keyword =blog_keyword, selected_field= False , 
                                                blog_keyword_mt=blog_keyword_mt,token_usage=token_usage)
        else:
            openai_response = get_prompt(blog_sub_phrase.start_phrase+ " " +instance.user_title , OPENAI_MODEL,
                                         blog_sub_phrase.max_token, n=3)
            token_usage = openai_token_usage(openai_response)
            for i in range(len(openai_response["choices"])):
                blog_keyword = openai_response["choices"][i]['text']
                BlogKeywordGenerate.objects.create(blog_creation = instance
                                                , blog_keyword =blog_keyword, selected_field= False , 
                                                blog_keyword_mt=None,token_usage=token_usage)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        blog_available_langs = [17]
        if validated_data.get('blog_key_gen'):
            blog_key_id = validated_data.pop('blog_key_gen')
            blog_key_id.selected_field = True
            blog_key_id.save()
            #other fields blog_key_select_update selected_field
            BlogKeywordGenerate.objects.filter(blog_creation = instance).exclude(id = blog_key_id.id).update(selected_field = False)
             
        if validated_data.get('blogcreate'):
            blog_update_keyword = validated_data.get('blogcreate')
            
            for i in blog_update_keyword:
                if i.get('blog_keyword'):
                    print("blog_key_------------>>>")
                    blog_keyword = i.get('blog_keyword')
                    blog_key_gen_inst =  BlogKeywordGenerate.objects.filter(blog_creation = instance 
                                            ,selected_field = True )
                    blog_key_gen_inst.update(blog_keyword =blog_keyword)
                    #if it contains mt content ,should call get_translate
                    if blog_key_gen_inst.first().blog_keyword_mt:
                        trans_text = blog_key_gen_inst.first().blog_keyword_mt
                        trans_data = get_translation(1, blog_keyword ,"en",instance.user_language_code,user_id=instance.user.id)           
                        blog_key_gen_inst.update(blog_keyword_mt = trans_data )                                          
             

    ##blog_title_or_topic_create
        if validated_data.get('blog_title_create_boolean'):
            sub_categories = validated_data.get('sub_categories')
            blog_sub_phrase = PromptStartPhrases.objects.get(sub_category = sub_categories)
            blog_title_gen_inst = BlogKeywordGenerate.objects.filter(blog_creation = instance ,selected_field = True ).first()
            if blog_title_gen_inst.blog_keyword:
                openai_response = get_prompt(blog_sub_phrase.start_phrase+ " " +blog_title_gen_inst.blog_keyword , OPENAI_MODEL,
                                         blog_sub_phrase.max_token, n=3)
                token_usage = openai_token_usage(openai_response)
                
                for i in range(len(openai_response["choices"])):
                    blog_title = openai_response["choices"][i]['text']
                    blog_title_mt = None
                    if (instance.user_language_id not in blog_available_langs):
                        blog_title_mt =  get_translation(1, blog_title , instance.user_language_code,"en" 
                                                                                   ,user_id=instance.user.id)
                    Blogtitle.objects.create(blog_keyword_gen = blog_title_gen_inst
                                                , blog_title =blog_title, selected_field= False , 
                                                blog_title_mt=blog_title_mt,token_usage=token_usage)
        
        
        if validated_data.get('blog_title_gen'):
            blog_title_gen = validated_data.get('blog_title_gen')
            blog_title_gen.selected_field = True
            blog_title_gen.save()
            blog_key_gen_inst = blog_title_gen.blog_keyword_gen
            Blogtitle.objects.filter(blog_keyword_gen = blog_key_gen_inst).exclude(id = blog_title_gen.id).update(selected_field = False)
        
        if validated_data.get('blogcreate'):
            blog_update_title = validated_data.get('blog_title')
            print("blog_update_title" , blog_update_title)
            for i in blog_update_title:
                if i.get('blog_keyword'):
                    for j in i.get('blog_title'):
                        print("---------->" ,i.get('blog_title') )
        return instance



# class BlogKeywordGenerateSerializer(serializers.ModelSerializer):
#     user_title = serializers.CharField(max_length = 100)
#     categories = serializers.PrimaryKeyRelatedField(queryset=PromptCategories.objects.all(),many=False,required=True)
#     sub_catagories = serializers.PrimaryKeyRelatedField(queryset=PromptSubCategories.objects.all(),many=False,required=True)
#     user_language = serializers.PrimaryKeyRelatedField(queryset=Languages.objects.all(),many=False,required=True)
#     selected_field = serializers.BooleanField(required=False )
#     blog_creation = BlogCreationSerializer(required=False )
#     class Meta:
#         model = BlogKeywordGenerate
#         fields = ('id' ,'user_title' , 'categories' ,'sub_catagories' , 'user_language','selected_field' 
#                   , 'blog_creation' ,)

    
#     def create(self, validated_data):
#         print("validated_data", validated_data)
#         return validated_data
        
      
      
      
      
      
        #if not in english
        # if (instance.user_language_id not in blog_available_langs) and (instance.keywords is None):
        #     instance.user_title_mt = get_translation(1, instance.user_title , instance.user_language_code,"en"  ,user_id=instance.user.id) if instance.user_title else None
        #     openai_response = get_prompt(blog_sub_phrase.start_phrase+ " " +instance.user_title_mt , OPENAI_MODEL, blog_sub_phrase.max_token, n=1)
        #     token_usage = openai_token_usage(openai_response = openai_response )
        #     instance.token_usage = token_usage
        #     instance.keywords_mt = openai_response['choices'][0]['text'] 
        #     # instance.keywords_mt = "keywords from translated user_title_mt"
        #     instance.keywords = get_translation(1, instance.keywords_mt ,"en",instance.user_language_code,user_id=instance.user.id) if instance.user_title else None     
        # # in eng
        # if (instance.user_language_id in blog_available_langs) and (instance.keywords is None):
        #     openai_response = get_prompt(blog_sub_phrase.start_phrase+ " " +instance.user_title , OPENAI_MODEL, blog_sub_phrase.max_token, n=1) 
        #     print(openai_response)
        #     token_usage = openai_token_usage(openai_response = openai_response)
        #     instance.token_usage = token_usage
            
        #     instance.keywords = openai_response['choices'][0]['text']
        #     # instance.keywords = "keywords user_title"

        # if (instance.user_language_id not in blog_available_langs):
        #     instance.user_title_mt = get_translation(1, instance.user_title , instance.user_language_code,"en",user_id=instance.user.id) if instance.user_title else None
        #     instance.keywords_mt = get_translation(1, instance.keywords , instance.user_language_code,"en" ,user_id=instance.user.id) if instance.keywords else None
        


        
 
        