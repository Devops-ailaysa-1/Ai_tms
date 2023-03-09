from rest_framework.response import Response
from rest_framework import serializers
from .models import (AiPrompt ,AiPromptResult,TokenUsage,TextgeneratedCreditDeduction,
                    AiPromptCustomize ,ImageGeneratorPrompt ,ImageGenerationPromptResponse ,
                    ImageGeneratorResolution,TranslateCustomizeDetails, 
                    BlogArticle,BlogCreation,BlogKeywordGenerate,BlogOutline,Blogtitle)
import re 
from ai_staff.models import (PromptCategories,PromptSubCategories ,AiCustomize, LanguagesLocale ,
                            PromptStartPhrases ,PromptTones ,Languages)
from .utils import get_prompt ,get_consumable_credits_for_openai_text_generator,\
                    get_prompt_freestyle ,get_prompt_image_generations ,\
                    get_img_content_from_openai_url,get_consumable_credits_for_image_gen
from ai_workspace_okapi.utils import get_translation
import math
from ai_tms.settings import  OPENAI_MODEL
from django.db.models import Q
from googletrans import Translator
from ai_auth.api_views import get_lang_code
from ai_workspace.api_views import UpdateTaskCreditStatus ,get_consumable_credits_for_text

class AiPromptSerializer(serializers.ModelSerializer):
    targets = serializers.ListField(allow_null=True,required=False)
    sub_catagories = serializers.PrimaryKeyRelatedField(queryset=PromptSubCategories.objects.all(),many=False,required=False)
    class Meta:
        model = AiPrompt
        fields = ('id','user','prompt_string','description','document','model_gpt_name','catagories','sub_catagories',
            'source_prompt_lang','Tone' ,'response_copies','product_name','keywords',
            'response_charecter_limit','targets')

    
    # def to_internal_value(self, data):
    #     print("to_internal_value")
    #     print("before",type(data['catagories']))
    #     data = super().to_internal_value(data)
    # #     data['model_gpt_name'] = int(data['model_gpt_name'])
    #     data['catagories'] = int(data['catagories'])
    #     print("after",data)
    # #     data['sub_catagories'] = int(data['sub_catagories'])
    # #     data['source_prompt_lang'] = int(data['source_prompt_lang'])
    # #     data['Tone'] = int(data['Tone'])
    # #     data['response_copies'] = int(data['response_copies'])
    #     return data

  
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

    def customize_token_deduction(self,instance ,total_tokens,user=None):
        print("Ins----------->",instance)
        print("user-------------->",user)
        if instance: user = instance.user
        else : user = user
        initial_credit = user.credit_balance.get("total_left")
        if initial_credit >=total_tokens:
            debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, total_tokens)
            print("Debited inside customize detection-------->",total_tokens)
        else:
            token_deduction = total_tokens - initial_credit 
            debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, initial_credit)
            deduction_update = TextgeneratedCreditDeduction.objects.filter(user=user)
            if deduction_update.exists():
                total_deduction = deduction_update.first().credit_to_deduce
                total_deduction = total_deduction+token_deduction
                deduction_update.update(credit_to_deduce = total_deduction)
                # deduction_update.save()
            else:
                TextgeneratedCreditDeduction.objects.create(user=user,credit_to_deduce = token_deduction)
        
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
                    trans = get_translation(1, content , j.result_lang_code, i.result_lang_code,user_id = instance.user.id,from_open_ai=True) if content else None
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
            description_mt = get_translation(1, instance.description , instance.source_prompt_lang_code, prmt_res.result_lang_code,user_id=user.id,from_open_ai=True) if instance.description else None
            keywords_mt = get_translation(1, instance.keywords , instance.source_prompt_lang_code, prmt_res.result_lang_code,user_id=user.id,from_open_ai=True) if instance.keywords else None
            prompt_string_mt = get_translation(1, instance.prompt_string , instance.source_prompt_lang_code, prmt_res.result_lang_code,user_id=user.id,from_open_ai=True) if instance.prompt_string else None
            product_name_mt = get_translation(1, instance.product_name , instance.source_prompt_lang_code, prmt_res.result_lang_code,user_id=user.id,from_open_ai=True) if instance.product_name else None
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


class TranslateCustomizeDetailSerializer(serializers.ModelSerializer):
	class Meta:
		model = TranslateCustomizeDetails
		fields = "__all__"



class AiPromptCustomizeSerializer(serializers.ModelSerializer):
    customize_name = serializers.ReadOnlyField(source='customize.customize')
    doc_name =  serializers.ReadOnlyField(source='document.doc_name')
    customization = TranslateCustomizeDetailSerializer(required=False,many=True)
    class Meta:
        model = AiPromptCustomize
        fields = ('id','document','doc_name','customize','customize_name','user_text',\
                    'tone','api_result','prompt_result','user_text_lang','user',\
                    'credits_used','prompt_generated','user_text_mt','created_at',\
                    'customization',)

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
        fields = ('id','prompt','prompt_mt','image_resolution','no_of_image','gen_img','created_at', )
        
        
    def create(self, validated_data):
        user=self.context['request'].user
        inst = ImageGeneratorPrompt.objects.create(**validated_data)
        print("Inst--------->",inst)
        detector = Translator()
        lang = detector.detect(inst.prompt).lang
        if isinstance(lang,list):
            lang = lang[0]
        lang = get_lang_code(lang)
        initial_credit = user.credit_balance.get("total_left")
        print("Initial--------->",initial_credit)
        image_reso = ImageGeneratorResolution.objects.get(image_resolution =inst.image_resolution )
        consumable_credits = get_consumable_credits_for_image_gen(image_reso.id,inst.no_of_image)
        if initial_credit > consumable_credits:
            if lang!= 'en':
                consumable_credits_user_text =  get_consumable_credits_for_text(inst.prompt,lang,'en')
                print("Consumable----->",consumable_credits_user_text)
                if initial_credit < consumable_credits_user_text:
                    raise serializers.ValidationError({'msg':'Insufficient Credits'})
                eng_prompt = get_translation(mt_engine_id=1 , source_string = inst.prompt,
                                            source_lang_code=lang , target_lang_code='en',user_id=user.id)
                ImageGeneratorPrompt.objects.filter(id=inst.id).update(prompt_mt=eng_prompt)
                #debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits_user_text)    
                print("Translated Prompt--------->",eng_prompt)
                image_res = get_prompt_image_generations(eng_prompt,
                                                image_reso.image_resolution,
                                                inst.no_of_image)
            else:
                image_res = get_prompt_image_generations(inst.prompt,
                                                image_reso.image_resolution,
                                                inst.no_of_image)
            if 'data' in image_res:
                consumable_credits = get_consumable_credits_for_image_gen(image_reso.id,inst.no_of_image) 
                print("CC---------->",consumable_credits)
                debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)                                                                                    
                data = image_res['data']
                print("Data------------>",image_res)     
                created_id = image_res["created"]  
                for i in range(inst.no_of_image):
                    img_content = get_img_content_from_openai_url(data[i]['url'])
                    image_file = core.files.File(core.files.base.ContentFile(img_content),"file.png")
                    img_gen_Pmpt_res=ImageGenerationPromptResponse.objects.create(user =user,created_id = created_id ,
                                                                generated_image = image_file,
                                                                image_generator_prompt = inst)  
                return inst
            else:
                raise serializers.ValidationError({'msg':image_res}, code=400) 
        else:
            raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400) 

 
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
        fields = '__all__'
        extra_kwargs = {'blog_keyword': {'required': True},'selected_field':{'required': False}} 

    def create(self, validated_data):
        blog_available_langs = [17]
        blog_create_instance = validated_data.get('blog_creation_gen')
        instance = Blogtitle.objects.create(**validated_data)
        blog_keyword_instance = BlogKeywordGenerate.objects.filter(blog_creation=instance.blog_creation_gen)
        title_start_phrase = PromptStartPhrases.objects.get(sub_category=instance.sub_categories)
        #prompt creation
        if (blog_create_instance.user_language_id not in blog_available_langs):
            print("user_language is not in en")
            prompt = title_start_phrase.start_phrase.format(blog_create_instance.user_title_mt)
            prompt+=' with keywords '+blog_create_instance.keywords_mt
 
        else:
            prompt = title_start_phrase.start_phrase.format(blog_create_instance.user_title)
            prompt+=' with keywords '+blog_create_instance.keywords
        openai_response = get_prompt(prompt,OPENAI_MODEL,title_start_phrase.max_token, instance.response_copies_keyword)
        token_usage = openai_token_usage(openai_response)
        title_generation = openai_response['choices'][0]['text']
        print("title_gen-->",title_generation)
        return super().create(validated_data)
    
class BlogKeywordGenerateSerializer(serializers.ModelSerializer):

    class Meta:
        model = BlogKeywordGenerate
        fields = ('id','blog_creation','blog_keyword','blog_keyword_mt','selected_field')
        extra_kwargs = {'blog_keyword': {'required': True},'selected_field':{'required': True}} 
    
    def create(self, validated_data):
        blog_available_langs = [17]
        
        keyword_instance = BlogKeywordGenerate.objects.create(**validated_data)
        if (keyword_instance.blog_creation.user_language_id not in blog_available_langs):
            print("other lang should convert to eng")
            user_lang = keyword_instance.blog_creation.user_language_code
            keyword_instance.blog_keyword_mt = get_translation(1,keyword_instance.blog_keyword,
                                                           user_lang,"en",user_id=keyword_instance.blog_creation.user.id) if keyword_instance.blog_keyword else None
            keyword_instance.save()
        return keyword_instance

    def update(self, instance, validated_data):
        instance.blog_keyword = validated_data.get('blog_keyword' , instance.blog_keyword)
        instance.selected_field = validated_data.get('selected_field' ,instance.selected_field)
        user_lang = instance.blog_creation.user_language_code
        if instance.blog_keyword_mt:
            instance.blog_keyword_mt = get_translation(1,instance.blog_keyword,
                                                           user_lang,"en",user_id=instance.blog_creation.user.id) if instance.blog_keyword else None
        instance.save()
        return instance
    
class BlogCreationSerializer(serializers.ModelSerializer):
    blog_key_create = BlogKeywordGenerateSerializer(many=True,required=False)
    sub_categories = serializers.PrimaryKeyRelatedField(queryset=PromptSubCategories.objects.all(),many=False,required=False)
    categories = serializers.PrimaryKeyRelatedField(queryset=PromptCategories.objects.all(),many=False,required=False)
    selected_keywords_list = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=BlogKeywordGenerate.objects.all(),
                                                                                             many=False,required=False),required=False)
    unselected_keywords_list= serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=BlogKeywordGenerate.objects.all(),
                                                                                             many=False,required=False),required=False)
    class Meta:
        model =BlogCreation
        fields = ('id','user_title','user_title_mt','keywords','keywords_mt','categories','sub_categories',
                  'user_language','tone','response_copies_keyword','selected_keywords_list',
                  'unselected_keywords_list','blog_key_create','user')
        
    def create(self, validated_data):
        blog_available_langs = [17]
        instance = BlogCreation.objects.create(**validated_data)
        blog_sub_phrase = PromptStartPhrases.objects.get(sub_category = instance.sub_categories)
        keyword_start_phrase = blog_sub_phrase.start_phrase.format(instance.response_copies_keyword)
        if (instance.user_language_id not in blog_available_langs):
            instance.user_title_mt = get_translation(1, instance.user_title , instance.user_language_code,"en",user_id=instance.user.id) if instance.user_title else None
            instance.keywords_mt = get_translation(1, instance.keywords , instance.user_language_code,"en",user_id=instance.user.id) if instance.keywords else None
            if instance.keywords_mt:
                prompt = keyword_start_phrase+ " " +instance.user_title_mt+ " with keywords"+ instance.keywords_mt
            else:
                prompt = keyword_start_phrase+ " " +instance.user_title_mt 
            openai_response = get_prompt(prompt,OPENAI_MODEL,blog_sub_phrase.max_token, instance.response_copies_keyword)
            token_usage = openai_token_usage(openai_response)
            keywords = openai_response['choices'][0]['text']
            for blog_keyword in keywords.split('\n'):
                if blog_keyword.strip():
                    blog_keyword = re.sub(r'\d+.','',blog_keyword)
                    blog_keyword = blog_keyword.strip()
                    blog_keyword_mt = get_translation(1, blog_keyword ,"en",instance.user_language_code,user_id=instance.user.id) if instance.user_title else None
                    BlogKeywordGenerate.objects.create(blog_creation = instance,blog_keyword =blog_keyword, selected_field= False , 
                                                blog_keyword_mt=blog_keyword_mt,token_usage=token_usage)
        else:
            if instance.keywords:
                prompt = keyword_start_phrase+ " " +instance.user_title+ " with keywords"+ instance.keywords
            else:
                prompt = keyword_start_phrase+ " " +instance.user_title
            openai_response = get_prompt(prompt,OPENAI_MODEL,blog_sub_phrase.max_token, instance.response_copies_keyword)
            token_usage = openai_token_usage(openai_response)
            keywords = openai_response['choices'][0]['text']
            for blog_keyword in keywords.split('\n'):
                if blog_keyword.strip():
                    blog_keyword = re.sub(r'\d+.','',blog_keyword)
                    blog_keyword = blog_keyword.strip()
                    BlogKeywordGenerate.objects.create(blog_creation=instance,blog_keyword=blog_keyword,selected_field= False, 
                                                blog_keyword_mt=None,token_usage=token_usage)
        instance.save()
        return instance
        
    def update(self, instance, validated_data):
        blog_available_langs = [17]
        user_lang = instance.user_language_code
        if validated_data.get('selected_keywords_list',None):
            select_keyword_ids = validated_data.get('selected_keywords_list')
            for select_keyword_id in select_keyword_ids:
                select_keyword_id.selected_field=True
                select_keyword_id.save()

        if validated_data.get('unselected_keywords_list',None):
            unselect_keyword_ids = validated_data.get('unselected_keywords_list')
            for unselect_keyword_id in unselect_keyword_ids:
                unselect_keyword_id.selected_field=False
                unselect_keyword_id.save()


        if validated_data.get('user_title',None):
            instance.user_title = validated_data.get('user_title',instance.user_title)
            if (instance.user_title_mt and (instance.user_language_id not in blog_available_langs)):
                instance.user_title_mt = get_translation(1,instance.user_title,user_lang,"en",user_id=instance.user.id)  
                instance.save()

        if validated_data.get('keywords',None):
            instance.keywords = validated_data.get('keywords',instance.keywords)
            if (instance.user_language_id not in blog_available_langs):
                instance.keywords_mt = get_translation(1,instance.keywords,user_lang,"en",user_id=instance.user.id) 
                instance.save()
        return super().update(instance, validated_data)
 
            # for blog_keyword in keywords.split('\n'):
            #     blog_keyword = blog_keyword.strip()
            #     blog_keyword = re.sub(r'\d+.','',blog_keyword)



# class BlogArticleSerializer(serializers.ModelSerializer):
#     class Meta:
#         model=BlogArticle
#         fields = '__all__'        

# class BlogOutlineSerializer(serializers.ModelSerializer):
#     blogarticle_outline = BlogArticleSerializer(required=False,many=True)
#     class Meta:
#         model=BlogOutline
#         fields = ('id' ,'blog_title_gen','blog_outline','blog_outline_mt' ,'tone','selected_field','token_usage','blogarticle_outline' )

# class BlogtitleSerializer(serializers.ModelSerializer):
#     blogoutline_title = BlogOutlineSerializer(required=False,many=True)
#     class Meta:
#         model = Blogtitle
#         fields = ('id','blog_title','blog_title_mt','token_usage',
#                   'selected_field','blog_keyword_gen' ,'blogoutline_title','blog_intro' , 'blog_intro_mt')


# class BlogKeywordGenerateSerializer(serializers.ModelSerializer):
#     blogtitle_keygen = BlogtitleSerializer(required=False,many=True)
#     class Meta:
#         model = BlogKeywordGenerate
#         fields = ('id','blog_creation','token_usage','selected_field','blog_keyword_mt',
#                   'blog_keyword' , 'blogtitle_keygen' )
 

# class BlogCreationSerializer(serializers.ModelSerializer):
#     blogcreate = BlogKeywordGenerateSerializer(required=False,many=True)
#     sub_categories = serializers.PrimaryKeyRelatedField(queryset=PromptSubCategories.objects.all(),many=False,required=False)
#     categories = serializers.PrimaryKeyRelatedField(queryset=PromptCategories.objects.all(),many=False,required=False)
#     blog_key_gen = serializers.PrimaryKeyRelatedField(queryset=BlogKeywordGenerate.objects.all(),many=False,required=False)
#     blog_title_gen = serializers.PrimaryKeyRelatedField(queryset=Blogtitle.objects.all(),many=False,required=False)
#     blog_title_create_boolean = serializers.BooleanField(required=False)
#     blog_outline_gen = serializers.PrimaryKeyRelatedField(queryset=BlogOutline.objects.all(),many=False,required=False)
#     blog_outline_create_boolean = serializers.BooleanField(required=False)
#     blog_article_create_boolean = serializers.BooleanField(required=False)
 
#     class Meta:
#         model = BlogCreation
#         fields = ('id','user_title' , 'categories' , 'sub_categories', 'user_language' , 'user_title_mt' , 
#                   'keywords_mt' , 'blogcreate','blog_key_gen' ,'blog_title_gen',
#                   'blog_title_create_boolean' , 'blog_outline_create_boolean' , 
#                   'blog_article_create_boolean','blog_outline_gen')  
    
#     def validate(self, data ,request=None):
#         validated_data = super().validate(data)
#         user=self.context.get('request' , None)
#         if user:
#             validated_data['user'] = user.user
#         return validated_data
      
#     def create(self, validated_data):
#         blog_available_langs = [17]
#         user=self.context['request'].user
#         instance = BlogCreation.objects.create(**validated_data)
#         blog_sub_phrase = PromptStartPhrases.objects.get(sub_category = instance.sub_categories)
#         # BlogKeywordGenerate
#         if (instance.user_language_id not in blog_available_langs):
#             instance.user_title_mt = get_translation(1, instance.user_title , instance.user_language_code,"en"  ,user_id=instance.user.id) if instance.user_title else None
#             openai_response = get_prompt(blog_sub_phrase.start_phrase+ " " +instance.user_title_mt , OPENAI_MODEL,
#                                          blog_sub_phrase.max_token, n=3)
#             token_usage = openai_token_usage(openai_response)
#             for i in range(len(openai_response["choices"])):
#                 blog_keyword = openai_response["choices"][i]['text']
#                 blog_keyword_mt = get_translation(1, blog_keyword ,"en",instance.user_language_code,user_id=instance.user.id) if instance.user_title else None
#                 BlogKeywordGenerate.objects.create(blog_creation = instance
#                                                 , blog_keyword =blog_keyword, selected_field= False , 
#                                                 blog_keyword_mt=blog_keyword_mt,token_usage=token_usage)
#         else:
#             openai_response = get_prompt(blog_sub_phrase.start_phrase+ " " +instance.user_title , OPENAI_MODEL,
#                                          blog_sub_phrase.max_token, n=3)
#             token_usage = openai_token_usage(openai_response)
#             for i in range(len(openai_response["choices"])):
#                 blog_keyword = openai_response["choices"][i]['text']
#                 BlogKeywordGenerate.objects.create(blog_creation = instance, blog_keyword =blog_keyword, selected_field= False , 
#                                                 blog_keyword_mt=None,token_usage=token_usage)
#         instance.save()
#         return instance

#     def update(self, instance, validated_data):
#         blog_available_langs = [17]
#         if validated_data.get('blog_key_gen'):
#             blog_key_id = validated_data.pop('blog_key_gen')
#             blog_key_id.selected_field = True
#             blog_key_id.save()
#             #other fields blog_key_select_update selected_field
#             BlogKeywordGenerate.objects.filter(blog_creation = instance).exclude(id = blog_key_id.id).update(selected_field = False)
#         ####updation
#         if validated_data.get('blogcreate'):
#             blog_update_keyword = validated_data.get('blogcreate')
#             for i in blog_update_keyword:
#                 updt_blog_keyword = i.get('blog_keyword')
#                 blog_key_gen_inst =  BlogKeywordGenerate.objects.filter(blog_creation=instance,selected_field=True)
#                 blog_for_key = blog_key_gen_inst.first()
#                 if i.get('blog_keyword'):
#                     if (instance.user_language_id in blog_available_langs):
#                         keywords = blog_for_key.blog_keyword
#                         keywords = keywords+' \n '+updt_blog_keyword 
#                         blog_key_gen_inst.update(blog_keyword =keywords)
#                         # blog_key_gen_inst.save()
#                     else:
#                         keywords = blog_for_key.blog_keyword_mt
#                         keywords = keywords+' \n '+updt_blog_keyword
#                         blog_key_gen_inst.update(blog_keyword_mt =keywords)
#                         trans_data=get_translation(1, updt_blog_keyword ,instance.user_language_code,"en",user_id=instance.user.id)
#                         blog_for_key.blog_keyword = blog_for_key.blog_keyword +"\n "+trans_data
#                         blog_for_key.save()
 
#     ##blog_title_or_topic_create
#         if validated_data.get('blog_title_create_boolean'):
#             print("validated_data" ,validated_data)
#             sub_categories = validated_data.get('sub_categories')
#             blog_sub_phrase = PromptStartPhrases.objects.get(sub_category = sub_categories)
#             blog_title_gen_inst = BlogKeywordGenerate.objects.filter(blog_creation = instance ,selected_field = True ).first()
#             if blog_title_gen_inst.blog_keyword:
#                 prompt = blog_sub_phrase.start_phrase+ " " +blog_title_gen_inst.blog_keyword+" "+ blog_title_gen_inst.blog_creation.user_title
#                 if blog_title_gen_inst.blog_creation.keywords:
#                     prompt =blog_sub_phrase.start_phrase+ " " +blog_title_gen_inst.blog_keyword+" "+ blog_title_gen_inst.blog_creation.keywords +" "+ blog_title_gen_inst.blog_creation.user_title 
#                 openai_response = get_prompt(prompt,OPENAI_MODEL,blog_sub_phrase.max_token, n=3)
#                 token_usage = openai_token_usage(openai_response)
#                 for i in range(len(openai_response["choices"])):
#                     blog_title = openai_response["choices"][i]['text']
#                     blog_title_mt = None
#                     if (instance.user_language_id not in blog_available_langs):
#                         blog_title_mt =  get_translation(1, blog_title ,"en",instance.user_language_code 
#                                                                                    ,user_id=instance.user.id)
#                     Blogtitle.objects.create(blog_keyword_gen = blog_title_gen_inst,
#                                             blog_title =blog_title, selected_field= False , 
#                                             blog_title_mt=blog_title_mt,token_usage=token_usage)
        
#         if validated_data.get('blog_title_gen'):
#             blog_title_gen = validated_data.get('blog_title_gen')
#             blog_title_gen.selected_field = True
#             blog_title_gen.save()
#             blog_key_gen_inst = blog_title_gen.blog_keyword_gen
#             blog_inst = Blogtitle.objects.filter(blog_keyword_gen=blog_key_gen_inst).exclude(id=blog_title_gen.id).update(selected_field = False)
#             blog_sel_field_inst = Blogtitle.objects.filter(blog_keyword_gen=blog_key_gen_inst ,selected_field = True).first()
#             if not blog_sel_field_inst.blog_intro:
#                 blog_intro_gen = get_prompt("create introduction for a title "+ blog_sel_field_inst.blog_title +"with the following keywords "+blog_sel_field_inst.blog_keyword_gen.blog_keyword,OPENAI_MODEL , 200, n=1)
#                 blog_intro_gen = blog_intro_gen["choices"][0]['text']
#                 blog_sel_field_inst.blog_intro = blog_intro_gen
#                 blog_sel_field_inst.save()
#             if (instance.user_language_id not in blog_available_langs):
#                 if blog_sel_field_inst.blog_intro:
#                     blog_sel_field_inst.blog_intro_mt = get_translation(1, blog_sel_field_inst.blog_intro ,"en",instance.user_language_code 
#                                             ,user_id=instance.user.id)
#                     blog_sel_field_inst.save()
                    
#         if validated_data.get('blog_outline_create_boolean'):
#             sub_categories = validated_data.get('sub_categories')
#             blog_sub_phrase = PromptStartPhrases.objects.get(sub_category = sub_categories)
#             blog_key_gen_inst = BlogKeywordGenerate.objects.filter(blog_creation = instance ,selected_field = True ).first()
#             blog_title_gen_inst = Blogtitle.objects.filter(blog_keyword_gen=blog_key_gen_inst ,selected_field = True ).first() 
#             if blog_title_gen_inst.blog_title:
#                 openai_response = get_prompt(blog_sub_phrase.start_phrase+ " " +blog_title_gen_inst.blog_title +" "+"with keyword "+ blog_title_gen_inst.blog_keyword_gen.blog_keyword , OPENAI_MODEL,
#                                             blog_sub_phrase.max_token, n=3)
#                 token_usage = openai_token_usage(openai_response)
#                 for i in range(len(openai_response["choices"])):
#                     blog_outline = openai_response["choices"][i]['text']
#                     blog_outline_mt = None        
#                     if (instance.user_language_id not in blog_available_langs):
#                         blog_outline_mt = get_translation(1, blog_outline ,"en",instance.user_language_code 
#                                             ,user_id=instance.user.id)
#                     tone = PromptTones.objects.get(id = 1)
#                     BlogOutline.objects.create(blog_title_gen=blog_title_gen_inst,blog_outline=blog_outline,
#                                               blog_outline_mt =blog_outline_mt,tone=tone, token_usage=token_usage ,selected_field= False)   
                    
#         if validated_data.get('blog_outline_gen'):
#             blog_outline_gen = validated_data.get('blog_outline_gen')
#             blog_outline_gen.selected_field = True
#             blog_outline_gen.save()
#             blog_title_gen_inst = blog_outline_gen.blog_title_gen
#             BlogOutline.objects.filter(blog_title_gen=blog_title_gen_inst).exclude(id=blog_outline_gen.id).update(selected_field = False)
             
#         if  validated_data.get('blog_article_create_boolean'):
#             blog_article_create_boolean = validated_data.get('blog_article_create_boolean')
#             sub_categories = validated_data.get('sub_categories')
#             blog_sub_phrase = PromptStartPhrases.objects.get(sub_category = sub_categories)
#             blog_key_gen_inst = BlogKeywordGenerate.objects.filter(blog_creation = instance ,selected_field = True ).first()
#             blog_title_gen_inst = Blogtitle.objects.filter(blog_keyword_gen=blog_key_gen_inst ,selected_field = True ).first() 
#             blog_outline_gen_inst = BlogOutline.objects.filter(blog_title_gen = blog_title_gen_inst ,selected_field = True).first()  
#             if blog_outline_gen_inst.blog_outline:
#                 openai_response = get_prompt(blog_sub_phrase.start_phrase+ " " +blog_outline_gen_inst.blog_outline  +" "+"with keyword "+ blog_title_gen_inst.blog_keyword_gen.blog_keyword,OPENAI_MODEL,blog_sub_phrase.max_token, n=1)
#                 token_usage = openai_token_usage(openai_response)
#                 for i in range(len(openai_response["choices"])):
#                     blog_article = openai_response["choices"][i]['text']
#                     blog_article_mt = None
#                     if (instance.user_language_id not in blog_available_langs):
#                         blog_article_mt = get_translation(1, blog_article ,"en",instance.user_language_code 
#                                             ,user_id=instance.user.id)
#                     BlogArticle.objects.create(blog_outline_gen = blog_outline_gen_inst
#                                                     , blog_article =blog_article, selected_field= False , 
#                                                     blog_article_mt=blog_article_mt,token_usage=token_usage)                        
#         return instance
 



 
   
