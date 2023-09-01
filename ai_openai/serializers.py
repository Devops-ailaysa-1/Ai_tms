from rest_framework.response import Response
from rest_framework import serializers
from .models import (AiPrompt ,AiPromptResult,TokenUsage,TextgeneratedCreditDeduction,
                    AiPromptCustomize ,ImageGeneratorPrompt ,ImageGenerationPromptResponse ,
                    ImageGeneratorResolution,TranslateCustomizeDetails, CustomizationSettings,
                    BlogArticle,BlogCreation,BlogKeywordGenerate,BlogOutline,Blogtitle,BlogOutlineSession)
import re 
from ai_staff.models import (PromptCategories,PromptSubCategories ,AiCustomize, LanguagesLocale ,
                            PromptStartPhrases ,PromptTones ,Languages)
from .utils import get_prompt ,get_consumable_credits_for_openai_text_generator,\
                    get_prompt_freestyle ,get_prompt_image_generations ,get_prompt_gpt_4,\
                    get_img_content_from_openai_url,get_consumable_credits_for_image_gen,get_prompt_chatgpt_turbo
from ai_workspace_okapi.utils import get_translation
from ai_tms.settings import  OPENAI_MODEL
from django.db.models import Q
from ai_openai.utils import outline_gen
from googletrans import Translator
from ai_auth.api_views import get_lang_code
from ai_workspace.api_views import UpdateTaskCreditStatus ,get_consumable_credits_for_text
from ai_workspace_okapi.utils import special_character_check
from rest_framework.exceptions import ValidationError
from rest_framework import status
import string
from ai_openai.utils import blog_generator
from django.db.models import Case, IntegerField, When, Value
from django.db.models.functions import Coalesce
from django.db.models import Case, ExpressionWrapper, F
from django.db import IntegrityError
from django.db import models, transaction

def replace_punctuation(text):
    for punctuation_mark in string.punctuation:
        text = text.replace(punctuation_mark, "")
    return text

detector = Translator()
def lang_detector(user_text):
    lang = detector.detect(user_text).lang
    if isinstance(lang,list):
        lang = lang[0]
    # lang = get_lang_code(lang)
    return lang


def openai_token_usage(openai_response ):
    print("Response------------------->",openai_response)
    token_usage = openai_response.get("usage",None)
    prompt_token = token_usage['prompt_tokens']
    total_tokens=token_usage['total_tokens']
    completion_tokens=token_usage.get('completion_tokens',None)
    if completion_tokens:
        return TokenUsage.objects.create(user_input_token=150,prompt_tokens=prompt_token,total_tokens=total_tokens,
                                    completion_tokens=completion_tokens, no_of_outcome=1)
    else:
        raise ValidationError({'msg':'empty_token from ailaysa generator retry again'},code=status.HTTP_204_NO_CONTENT)


class AiPromptSerializer(serializers.ModelSerializer):
    targets = serializers.ListField(allow_null=True,required=False)
    sub_catagories = serializers.PrimaryKeyRelatedField(queryset=PromptSubCategories.objects.all(),many=False,required=False)
    class Meta:
        model = AiPrompt
        fields = ('id','user','prompt_string','description','document','task','pdf','model_gpt_name','catagories','sub_catagories',
            'source_prompt_lang','Tone' ,'response_copies','product_name','keywords',
            'response_charecter_limit','targets','created_by',)

    
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

  
    def prompt_generation(self,ins,obj,ai_langs,targets,user):
        instance = AiPrompt.objects.get(id=ins)
        lang = instance.source_prompt_lang_id 
        start_phrase = None
        prompt=''
        if not user: user = instance.user
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
        initial_credit = user.credit_balance.get("total_left")
        consumable_credit = get_consumable_credits_for_text(prompt,target_lang=None,source_lang=instance.source_prompt_lang_code)
        if initial_credit < consumable_credit:
            return  Response({'msg':'Insufficient Credits'},status=400)
        token = instance.sub_catagories.prompt_sub_category.first().max_token if instance.sub_catagories else 256
        # openai_response =get_prompt(prompt,instance.model_gpt_name.model_code , token,instance.response_copies )
        # generated_text = openai_response.get('choices' ,None)
        openai_response =get_prompt_chatgpt_turbo(prompt,instance.response_copies,token)
        generated_text =openai_response.get('choices',None)#["choices"][0]["message"]["content"]
        response_id =openai_response.get('id' , None)
        token_usage = openai_response.get('usage' ,None) 
        prompt_token = token_usage['prompt_tokens']
        total_tokens=token_usage['total_tokens']
        completion_tokens=token_usage.get('completion_tokens',None)
        #print("CompletionTokens------->",completion_tokens)
        no_of_outcome = instance.response_copies
        token_usage=TokenUsage.objects.create(user_input_token=instance.response_charecter_limit,prompt_tokens=prompt_token,
                                    total_tokens=total_tokens , completion_tokens=completion_tokens,  
                                    no_of_outcome=no_of_outcome)
        total_tokens = get_consumable_credits_for_openai_text_generator(total_tokens)
        self.customize_token_deduction(instance , total_tokens,user)            
        
        if generated_text:
            print("generated_text" , generated_text)
            rr = [AiPromptResult.objects.update_or_create(prompt=instance,result_lang=obj.result_lang,copy=j,\
                    defaults = {'prompt_generated':prompt,'start_phrase':start_phrase,\
                    'response_id':response_id,'token_usage':token_usage,'api_result':i["message"]["content"].strip()}) for j,i in enumerate(generated_text)]#'api_result':i['text'].strip().strip('\"')#'api_result':i["message"]["content"].strip().strip('\"')
        return None

    def customize_token_deduction(self,instance ,total_tokens,user=None):
        print("Ins----------->",instance)
        print("user-------------->",user)
        if not user:
            user = instance.user
        # if instance: user = instance.user
        # else : user = user
        initial_credit = user.credit_balance.get("total_left")
        if initial_credit >=total_tokens:
            debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, total_tokens)
            print("Debited User------------>",user)
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
        
    def prompt_result_update(self,ins,obj,ai_langs,targets,user):
        instance = AiPrompt.objects.get(id=ins)
        prompt = self.prompt_generation(ins,obj,ai_langs,targets,user) 
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
                    self.customize_token_deduction(instance , word_count,user)

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
        if instance.task != None:
            user = instance.task.job.project.ai_user
        elif instance.pdf != None:
            user = instance.pdf.user
        else:    
            user = instance.user.team.owner if instance.user.team else instance.user
        initial_credit = user.credit_balance.get("total_left")
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
            self.customize_token_deduction(instance ,consumed_credits,user)
        else:
            prmt_res = AiPromptResult.objects.create(prompt=instance,result_lang_id=instance.source_prompt_lang_id,copy=0)
        if instance.response_copies >1:
            tt = [AiPromptResult.objects.get_or_create(prompt=instance,result_lang_id=i,copy=j) for i in targets for j in range(instance.response_copies)]
        else:
            tt= [AiPromptResult.objects.get_or_create(prompt=instance,result_lang_id=i,copy=0) for i in targets]       
        pr_result = self.prompt_result_update(instance.id,prmt_res,openai_available_langs,targets,user) 
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
                    'product_name','keywords','created_at','prompt_results','created_by',)#,'ai_prompt'
        
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
        fields = ('id','document','task','pdf','doc_name','customize','customize_name','user_text',\
                    'tone','api_result','prompt_result','user_text_lang','user',\
                    'credits_used','prompt_generated','user_text_mt','created_at',\
                    'customization','created_by')

        extra_kwargs = {
            "user":{"write_only": True},
            'created_by':{'write_only':True},
            "prompt_generated": {"write_only": True},
            "credits_used": {"write_only": True},
            "user_text_mt": {"write_only": True},
        }
        


from django import core

class ImageGenerationPromptResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageGenerationPromptResponse
        fields = ('id','generated_image')#,'created_by','created_id',)
        # extra_kwargs = {
        #     "created_id":{"write_only": True},
        #     'created_by':{'write_only':True},
        # }

class ImageGeneratorPromptSerializer(serializers.ModelSerializer):  
    gen_img = ImageGenerationPromptResponseSerializer(many=True,required=False)
    class Meta:
        model = ImageGeneratorPrompt
        fields = ('id','prompt','prompt_mt','image_resolution','no_of_image','gen_img','created_at', )
        
        
    def create(self, validated_data):
        request_user=self.context['request'].user
        user = request_user.team.owner if request_user.team else request_user
        print("User-------------->",user)
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
                image_res = get_prompt_image_generations(eng_prompt,image_reso.image_resolution,inst.no_of_image)
            else:
                image_res = get_prompt_image_generations(inst.prompt,image_reso.image_resolution,inst.no_of_image)
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
                                                                image_generator_prompt = inst,created_by = request_user)  
                return inst
            else:
                raise serializers.ValidationError({'msg':image_res}, code=400) 
        else:
            raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400) 




class BlogArticleSerializer(serializers.ModelSerializer):

    class Meta:
        model=BlogArticle
        fields='__all__'
    


class CustomizationSettingsSerializer(serializers.ModelSerializer):
    src = serializers.SerializerMethodField()
    tar = serializers.SerializerMethodField()
    class Meta:
        model=CustomizationSettings
        fields=('id','user','append','new_line','src','tar','mt_engine',)

    def get_src(self,obj):
        if self.context.get('request'):
            user = self.context.get('request').user.id
        else:
            user = self.context.get('user')
        queryset = TranslateCustomizeDetails.objects.filter(customization__user_id = user)
        print("Qr------------>",queryset.last())
        if queryset:
            try:
                source = queryset.last().customization.user_text_lang_id
                return source
            except: return None
        return None

    def get_tar(self,obj):
        if self.context.get('request'):
            user = self.context.get('request').user.id
        else:
            user = self.context.get('user')
        queryset = TranslateCustomizeDetails.objects.filter(customization__user_id = user)
        if queryset:
            target = queryset.last().target_language_id
            return target
        return None



class BlogOutlineSessionSerializer(serializers.ModelSerializer):
    blog_title = serializers.PrimaryKeyRelatedField(queryset=Blogtitle.objects.all(),many=False) 
    blog_outline_gen = serializers.PrimaryKeyRelatedField(queryset=BlogOutline.objects.all(),many=False) 
    selected = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=BlogOutlineSession.objects.all(),
                                                                    many=False,required=False),required=False)
    unselected = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=BlogOutlineSession.objects.all(),
                                                             many=False,required=False),required=False)
    group = serializers.IntegerField()
    selected_group = serializers.IntegerField(required=False)
    order_list = serializers.CharField(required=False)
    class Meta:
        model = BlogOutlineSession
        fields = ('id','blog_title','blog_outline_gen','unselected','selected','blog_outline','custom_order','temp_order','blog_outline_mt','selected_field','group','selected_group','order_list',)
        extra_kwargs = {'blog_outline_gen': {'required': True},'selected':{'required':False},
                        'group':{'required':True},'unselected':{'required':False},'order_list':{'required':False}}

    def validate(self, data):
        if data.get('group',None) and data.get('blog_outline_gen',None):
            blog_outline_gen_ins = data['blog_outline_gen']
            group_ins = BlogOutlineSession.objects.filter(blog_outline_gen=blog_outline_gen_ins).values_list('group',flat=True)
            group_ins = list(set(group_ins))
            if data['group'] not in group_ins:
                raise serializers.ValidationError("group should be in {}".format(group_ins))
        return data
    
    def create(self, validated_data):
        blog_available_langs =[17]
        count = BlogOutlineSession.objects.filter(group=validated_data.get('group'),blog_title=validated_data.get('blog_title')).count()
        print("Count------->",count)
        instance = BlogOutlineSession.objects.create(**validated_data)
        instance.custom_order = count+1
        instance.temp_order = count+1
        initial_credit = instance.blog_title.blog_creation_gen.user.credit_balance.get("total_left")
        user_lang = instance.blog_title.blog_creation_gen.user_language_id
        lang_code =instance.blog_title.blog_creation_gen.user_language_code
        user_id = instance.blog_title.blog_creation_gen.user.id
        consumable_credit = get_consumable_credits_for_text(instance.blog_outline,'en',lang_code)
        if (user_lang not in blog_available_langs):
            instance.selected_field =True
            
            if initial_credit > consumable_credit:
                instance.blog_outline_mt = get_translation(1,instance.blog_outline,
                                                    lang_code,"en",user_id=user_id) if instance.blog_outline else None
                instance.selected_field =True
            else:
                raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
        else:
            lang_detect_outline_create =  lang_detector(instance.blog_outline) 
            if lang_detect_outline_create!='en':
                instance.blog_outline_mt = get_translation(1,instance.blog_outline,lang_detect_outline_create,"en",user_id=user_id)  
                debit_status, status_code = UpdateTaskCreditStatus.update_credits(user_id,consumable_credit)
            instance.selected_field =True
        instance.save()
        return instance
    
    def update(self, instance, validated_data):
        print("ValiData----------->",validated_data)
        lang_code =instance.blog_title.blog_creation_gen.user_language_code
        user_id = instance.blog_title.blog_creation_gen.user.id
        if validated_data.get('blog_outline',None):
            instance.blog_outline = validated_data.get('blog_outline',instance.blog_outline)
            initial_credit = instance.blog_title.blog_creation_gen.user.credit_balance.get("total_left")
            consumable_credit_section = get_consumable_credits_for_text(instance.blog_outline ,'en',lang_code)
            if initial_credit < consumable_credit_section:
                raise serializers.ValidationError({'msg':'Insufficient Credits'},code=400)

            if instance.blog_outline_mt:
                instance.blog_outline_mt = get_translation(1,instance.blog_outline,lang_code,"en",
                                           user_id=user_id) if instance.blog_outline else None
                debit_status, status_code = UpdateTaskCreditStatus.update_credits(instance.blog_title.blog_creation_gen.user,consumable_credit_section)
             
            lang_detect_user_outline =  lang_detector(instance.blog_outline) 

            if lang_detect_user_outline !='en':
                instance.blog_outline_mt =get_translation(1,instance.blog_outline,lang_detect_user_outline,"en",user_id=instance.blog_title.blog_creation_gen.user.id,from_open_ai=True)  
                debit_status, status_code = UpdateTaskCreditStatus.update_credits(instance.blog_title.blog_creation_gen.user, consumable_credit_section)
        instance.save() 

        if 'selected_group' in validated_data:
            print("selected_gr------->",validated_data.get('selected_group'))
            instance.blog_outline_gen.selected_group_num = validated_data.get('selected_group')
            instance.blog_outline_gen.save()
            print("gg-------->",instance.blog_outline_gen)
            BlogOutlineSession.objects.filter(group=validated_data.get('selected_group'),blog_outline_gen=instance.blog_outline_gen).update(selected_field=True)
            BlogOutlineSession.objects.filter(blog_title=instance.blog_title).exclude(group=validated_data.get('selected_group')).update(selected_field=False)

        if validated_data.get('group',None):
            instance.group = validated_data.get('group',instance.group)
  
        if validated_data.get('selected',None):
            session_ids = validated_data.get('selected')
            print("ss--------->",session_ids)
            for session_id in session_ids:
                session_id.selected_field = True
                session_id.save()

        if validated_data.get('unselected',None):
            session_ids = validated_data.get('unselected')
            for session_id in session_ids:
                session_id.selected_field = False
                session_id.save()

        if validated_data.get('order_list',None):
            order_list = validated_data.get('order_list')
            group = validated_data.get('group')
            order_list = list(map(int, order_list.split(',')))
            for index, order in enumerate(order_list, 1):
                BlogOutlineSession.objects.filter(temp_order=order).filter(blog_title=instance.blog_title).filter(group=group).update(custom_order=index)

        return instance

class BlogOutlineSerializer(serializers.ModelSerializer):
    blog_outline_session = BlogOutlineSessionSerializer(many=True,required=False)
    blog_title_gen = serializers.PrimaryKeyRelatedField(queryset=Blogtitle.objects.all(),many=False) 
    select_group = serializers.IntegerField(required=False)

    class Meta:
        model = BlogOutline
        fields = ('id','user_selected_title','selected_group_num','user_selected_title_mt','blog_title_gen','sub_categories',
                  'token_usage','response_copies','select_group','blog_outline_session')
        extra_kwargs = {'blog_title_gen': {'required': True},'selected_field':{'required': False},
                        'select_group':{'required': False}}
         
    def create(self, validated_data):
        blog_available_langs =[17]
        blog_title_gen_inst = validated_data.get('blog_title_gen')
        print("BB----------->",blog_title_gen_inst.id)
        blg_tit = Blogtitle.objects.filter(id=blog_title_gen_inst.id).update(selected_field = True)
        Blogtitle.objects.filter(blog_creation_gen=blog_title_gen_inst.blog_creation_gen).exclude(id = blog_title_gen_inst.id).update(selected_field=False)
        queryset = BlogOutlineSession.objects.filter(blog_title=blog_title_gen_inst)
        if queryset:instance = BlogOutline.objects.get(blog_title_gen=blog_title_gen_inst)
        else:instance,created = BlogOutline.objects.get_or_create(**validated_data)
        print("Ins---------->",instance)
        initial_credit = instance.blog_title_gen.blog_creation_gen.user.credit_balance.get("total_left")
        if initial_credit <150:
            raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
        blog_outline_start_phrase = PromptStartPhrases.objects.get(sub_category=instance.sub_categories)
        print("sSR-------->",blog_outline_start_phrase)
        if (blog_title_gen_inst.blog_creation_gen.user_language_id not in blog_available_langs):
            instance.user_selected_title = instance.blog_title_gen.blog_title
            instance.user_selected_title_mt = instance.blog_title_gen.blog_title_mt
        else:
            instance.user_selected_title = instance.blog_title_gen.blog_title
        instance.save()


        # if instance.blog_title_gen.blog_creation_gen.prompt_user_title_mt:
        title = instance.blog_title_gen.blog_title
        detected_lang = lang_detector(title)
        if detected_lang != 'en':
            title = instance.blog_title_gen.blog_title_mt
        #title = instance.blog_title_gen.blog_title if instance.blog_title_gen.blog_title else instance.blog_title_gen.blog_title_mt
        keywords = instance.blog_title_gen.blog_creation_gen.keywords 
        detected_lang = lang_detector(keywords)
        if detected_lang!='en':
            keywords = instance.blog_title_gen.blog_creation_gen.keywords_mt
        #if instance.blog_title_gen.blog_creation_gen.keywords else instance.blog_title_gen.blog_creation_gen.keywords_mt
        print("TT------>",title)
        print("KK------->",keywords)
        prompt = blog_outline_start_phrase.start_phrase.format(title,keywords)
        prompt+='use a {} tone.'.format(instance.blog_title_gen.blog_creation_gen.tone.tone)
        print("PR------------->",prompt)
        # prompt_response_gpt = get_prompt_chatgpt_turbo(prompt=prompt,n=1)
        prompt_response_gpt = outline_gen(prompt=prompt)

        prompt_response = prompt_response_gpt.choices
        total_token = prompt_response_gpt['usage']['total_tokens']
        total_token = get_consumable_credits_for_openai_text_generator(total_token)
        AiPromptSerializer().customize_token_deduction(instance.blog_title_gen.blog_creation_gen,total_token)
        queryset = BlogOutlineSession.objects.filter(blog_title=instance.blog_title_gen).distinct('group')
        if queryset: start = queryset.count()
        else: start = 0
        for group,outline_res in enumerate(prompt_response,start=start):
            outline = outline_res.message['content'].split('\n')
            for order,session in enumerate(outline,start=1):
                if session:
                    session = re.sub(r'\d+.','',session).strip()
                    if (blog_title_gen_inst.blog_creation_gen.user_language_id not in blog_available_langs):
                        initial_credit = instance.blog_title_gen.blog_creation_gen.user.credit_balance.get("total_left")
                        consumable_credits_to_translate_section = get_consumable_credits_for_text(session,instance.blog_title_gen.blog_creation_gen.user_language_code,'en')
                        if initial_credit > consumable_credits_to_translate_section:
                            blog_outline=get_translation(1,session,'en',blog_title_gen_inst.blog_creation_gen.user_language_code,
                                                        user_id=blog_title_gen_inst.blog_creation_gen.user.id) 
                            BlogOutlineSession.objects.create(blog_outline_gen=instance,blog_outline=blog_outline,custom_order=order,temp_order=order,
                                                          blog_outline_mt=session,group=group,blog_title =instance.blog_title_gen )
                            # debit_status, status_code = UpdateTaskCreditStatus.update_credits(instance.blog_title_gen.blog_creation_gen.user,consumable_credits_to_translate_section)
                        else:
                            raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
                    else:
                        BlogOutlineSession.objects.create(blog_outline_gen=instance,blog_outline=session,group=group,temp_order=order,custom_order=order,blog_title =instance.blog_title_gen ) 
        token_usage = openai_token_usage(prompt_response_gpt)
        instance.token_usage = token_usage
        instance.save()
        return instance

    def update(self, instance, validated_data):
        if validated_data.get('select_group',None):
            instance.selected_group_num = validated_data.get('select_group')
            BlogOutlineSession.objects.filter(group=validated_data.get('select_group')).update(selected_field=True)
        instance.save()

        # if validated_data.get('blog_outline_selected_list'):
            
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        sessions = instance.blog_outline_session.order_by('custom_order')
        representation['blog_outline_session'] = BlogOutlineSessionSerializer(sessions, many=True).data
        return representation

class BlogtitleSerializer(serializers.ModelSerializer):
    blogoutline_title = BlogOutlineSerializer(many=True,required=False)
    selected_title = serializers.PrimaryKeyRelatedField(queryset=Blogtitle.objects.all(),many=False,required=False) 
    unselected_title = serializers.PrimaryKeyRelatedField(queryset=Blogtitle.objects.all(),many=False,required=False) 
    class Meta:
        model = Blogtitle
        fields = '__all__'
        extra_kwargs = {'blog_keyword': {'required': True},'selected_field':{'required': False}} 

    def create(self, validated_data):
        blog_available_langs = [17]
        blog_create_instance = validated_data.get('blog_creation_gen')
        sub_categories = validated_data.get('sub_categories')
        title_start_phrase = PromptStartPhrases.objects.get(sub_category=sub_categories)
        #prompt creation
        initial_credit = blog_create_instance.user.credit_balance.get("total_left")
        title = blog_create_instance.user_title
        detected_lang = lang_detector(title)
        if detected_lang != 'en':
            title = blog_create_instance.user_title_mt
        prompt = title_start_phrase.start_phrase.format(title)
        keywords = blog_create_instance.keywords
        detected_lang = lang_detector(keywords)
        print("DL--------->>",detected_lang)
        if detected_lang!='en':
            keywords = blog_create_instance.keywords_mt
        if keywords:
            prompt+=' with keywords '+ keywords 
        prompt+=', in {} tone'.format(blog_create_instance.tone.tone)
        consumable_credits = get_consumable_credits_for_text(prompt,None,'en')

        if initial_credit < consumable_credits:
            raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
        print("prompt----->>>>>>>>>>>>>>>>>>>>>>>>>>>",prompt)
        #openai_response = get_prompt(prompt,OPENAI_MODEL,title_start_phrase.max_token,1)
        openai_response = get_prompt_chatgpt_turbo(prompt,1,title_start_phrase.max_token)
        token_usage = openai_token_usage(openai_response)
        token_usage_to_reduce = get_consumable_credits_for_openai_text_generator(token_usage.total_tokens)
        AiPromptSerializer().customize_token_deduction(blog_create_instance,token_usage_to_reduce)
        
        #blog_titles = openai_response['choices'][0]['text']
        blog_titles = openai_response["choices"][0]["message"]["content"]
        #title creation
        for blog_title in blog_titles.split('\n'):
            if blog_title.strip().strip('.'):
                blog_title = re.sub(r'\d+.','',blog_title)
                blog_title = blog_title.strip().strip('"')
                if (blog_create_instance.user_language_id not in blog_available_langs):
                    print("blog title create not in en")
                    initial_credit = blog_create_instance.user.credit_balance.get("total_left")
                    consumable_credits_to_translate_title = get_consumable_credits_for_text(blog_title,blog_create_instance.user_language_code,'en')
                    if initial_credit > consumable_credits_to_translate_title:
                        blog_title_in_other_lang=get_translation(1,blog_title,"en",blog_create_instance.user_language_code,
                                                             user_id=blog_create_instance.user.id,from_open_ai=True) 
                        debit_status, status_code = UpdateTaskCreditStatus.update_credits(blog_create_instance.user,consumable_credits_to_translate_title)
                    else:
                        raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
                    Blogtitle.objects.create(blog_creation_gen=blog_create_instance,sub_categories=sub_categories,
                                         blog_title=blog_title_in_other_lang,blog_title_mt=blog_title,
                                         token_usage=token_usage,selected_field=False)
                else:
                    Blogtitle.objects.create(blog_creation_gen=blog_create_instance,sub_categories=sub_categories,
                                                blog_title=blog_title,token_usage=token_usage,selected_field=False)

        return validated_data
    
    def update(self, instance, validated_data):
        user_lang = instance.blog_creation_gen.user_language_code
        if validated_data.get('blog_title' , None):
            instance.blog_title = validated_data.get('blog_title' ,instance.blog_title)
            lang_detect_user_title = lang_detector(instance.blog_title) 
            initial_credit = instance.blog_creation_gen.user.credit_balance.get("total_left")
            if lang_detect_user_title !='en':
                consumable_credits_to_translate_update_title = get_consumable_credits_for_text(instance.blog_title,instance.blog_creation_gen.user_language_code,'en')
                if initial_credit < consumable_credits_to_translate_update_title:
                    raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
                instance.blog_title_mt = get_translation(1,instance.blog_title,user_lang,"en",
                                                    user_id=instance.blog_creation_gen.user.id) if instance.blog_title else None
            else:
                instance.blog_title_mt = None 
            instance.save()

###########################################
        if validated_data.get('selected_title',None):
            Blogtitle.objects.filter(blog_creation_gen=instance.blog_creation_gen).update(selected_field=False)
            select_title_id = validated_data.get('selected_title')
            select_title_id.selected_field=True
            select_title_id.save()

        if validated_data.get('unselected_title',None):
            unselect_title_id = validated_data.get('unselected_title')
            unselect_title_id.selected_field=False
            unselect_title_id.save()

        new_inst = Blogtitle.objects.get(id=instance.id)
        return new_inst

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        titles = instance.blogoutline_title.order_by('-id')
        representation['blogoutline_title'] = BlogOutlineSerializer(titles, many=True).data
        return representation



def keyword_process(keyword_start_phrase,user_title,instance,trans):
    blog_sub_phrase = PromptStartPhrases.objects.get(sub_category = instance.sub_categories)
    prompt = keyword_start_phrase+ " " +user_title
    prompt+=', in {} tone'.format(instance.tone.tone)
    print("Prompt------------>",prompt)
    print("Trans----------->",trans)
    #openai_response = get_prompt(prompt,OPENAI_MODEL,blog_sub_phrase.max_token,1)
    openai_response = get_prompt_chatgpt_turbo(prompt,1,blog_sub_phrase.max_token)
    token_usage = openai_token_usage(openai_response)
    #keywords = openai_response['choices'][0]['text']
    keywords = openai_response["choices"][0]["message"]["content"]
    print("From openai-------->",keywords)
    print("RR---------->",instance.user_language_code)
    for blog_keyword in keywords.split('\n'):
        if blog_keyword.strip():
            blog_keyword = re.sub(r'\d+.','',blog_keyword)
            blog_keyword = blog_keyword.strip()
            if special_character_check(blog_keyword):
                print("punc")
            else:
                blog_keyword = replace_punctuation(blog_keyword)
                if trans == True:
                    print("Inside True")
                    blog_keyword_trans = get_translation(1, blog_keyword ,"en",instance.user_language_code,user_id=instance.user.id) if instance.user_title else None
                    print("BKT---------->",blog_keyword_trans)
                    BlogKeywordGenerate.objects.create(blog_creation = instance,blog_keyword =blog_keyword_trans, selected_field= False , 
                                    blog_keyword_mt=blog_keyword,token_usage=token_usage)
                else:
                    print("Inside False")
                    blog_keyword_trans = None
                    BlogKeywordGenerate.objects.create(blog_creation = instance,blog_keyword =blog_keyword, selected_field= False , 
                                    blog_keyword_mt=blog_keyword_trans,token_usage=token_usage)

    print("Keyword processed and stored")
    return token_usage

class BlogKeywordGenerateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogKeywordGenerate
        fields = ('id','blog_creation','blog_keyword','blog_keyword_mt','selected_field')
        #extra_kwargs = {'blog_keyword': {'required': True},'selected_field':{'required': True}} 
    
    def create(self, validated_data):
        blog_available_langs = [17]
        blog = validated_data.get('blog_creation')
        print("Blog------------>",blog)
        instance = blog
        consumable_credits = 0
        credits_needed_to_generate = 2 
        blog_sub_phrase = PromptStartPhrases.objects.get(sub_category = instance.sub_categories)
        keyword_start_phrase = blog_sub_phrase.start_phrase.format(instance.response_copies_keyword)
        initial_credit = instance.user.credit_balance.get("total_left")
        lang_detect_user_title_key = lang_detector(instance.user_title) 
        print('detected--------->',lang_detect_user_title_key)
        #if lang_detect_user_title_key !='en':
        if (instance.user_language_id not in blog_available_langs):
            consumable_credits = get_consumable_credits_for_text(instance.user_title,instance.user_language_code,'en')

            if initial_credit < consumable_credits:
                raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
            title = instance.user_title_mt if lang_detect_user_title_key !='en' else instance.user_title
            token_usage = keyword_process(keyword_start_phrase,title,instance,trans=True)
        else:
            if initial_credit < credits_needed_to_generate:#credits needed for keyword generation
                raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
            title = instance.user_title_mt if lang_detect_user_title_key !='en' else instance.user_title
            token_usage = keyword_process(keyword_start_phrase,instance.user_title,instance,trans=False)
        debit_status, status_code = UpdateTaskCreditStatus.update_credits(instance.user, consumable_credits)                 
        total_usage = get_consumable_credits_for_openai_text_generator(token_usage.total_tokens)
        print("total_usage_openai----->>>>>>>>>>>>>>>>",total_usage)
        print("trans---->>>>>>>>>>>>>>>>>>>",consumable_credits)
        AiPromptSerializer().customize_token_deduction(instance,total_usage)
        instance.save() 
        keyword_instance = BlogKeywordGenerate.objects.filter(blog_creation = instance).last()
        return keyword_instance

    def update(self, instance, validated_data):
        instance.blog_keyword = validated_data.get('blog_keyword' , instance.blog_keyword)
        instance.selected_field = validated_data.get('selected_field' ,instance.selected_field)
        user_lang = instance.blog_creation.user_language_code
        if instance.blog_keyword_mt:

            initial_credit = instance.blog_creation.user.credit_balance.get("total_left")
            consumable_credits = get_consumable_credits_for_text(instance.blog_keyword,user_lang,'en')
            if initial_credit< consumable_credits:
                raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
            instance.blog_keyword_mt = get_translation(1,instance.blog_keyword,"en",user_lang,
                                                       user_id=instance.blog_creation.user.id) if instance.blog_keyword else None
        debit_status, status_code = UpdateTaskCreditStatus.update_credits(instance.blog_creation.user, consumable_credits)
        instance.save()
        return instance
    
    # def to_representation(self, instance):
    #     representation = super().to_representation(instance)
    #     titles = instance.blogoutline_title.order_by('-id')
    #     representation['blogoutline_title'] = BlogOutlineSerializer(titles, many=True).data
    #     return representation
    
class BlogCreationSerializer(serializers.ModelSerializer):
    blog_title_create=BlogtitleSerializer(many=True,required=False)
    blog_key_create = BlogKeywordGenerateSerializer(many=True,required=False)
    sub_categories = serializers.PrimaryKeyRelatedField(queryset=PromptSubCategories.objects.all(),many=False,required=False)
    categories = serializers.PrimaryKeyRelatedField(queryset=PromptCategories.objects.all(),many=False,required=False)
    selected_keywords_list = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=BlogKeywordGenerate.objects.all(),
                                                                                             many=False,required=False),required=False)
    unselected_keywords_list= serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=BlogKeywordGenerate.objects.all(),
                                                                                             many=False,required=False),required=False)
    class Meta:
        model = BlogCreation
        fields = ('id','user_title','steps','user_title_mt','keywords','keywords_mt','prompt_user_title_mt','prompt_keyword_mt',
                  'categories','sub_categories','user_language','tone','response_copies_keyword','selected_keywords_list',
                  'unselected_keywords_list','blog_key_create','user','blog_title_create','created_by')
        
    def create(self, validated_data):
        blog_available_langs = [17]
        instance = BlogCreation.objects.create(**validated_data)
        initial_credit = instance.user.credit_balance.get("total_left")
        total_usage = 0
        # if initial_credit < 1400:
        #     raise serializers.ValidationError({'msg':'Insufficient Credits','blog_id':instance.id}, code=400)

        lang_detect_user_title_key = lang_detector(instance.user_title) 
        if lang_detect_user_title_key !='en':
            consumable_credits = get_consumable_credits_for_text(instance.user_title,instance.user_language_code,'en')

            if initial_credit < consumable_credits:
                raise serializers.ValidationError({'msg':'Insufficient Credits','blog_id':instance.id}, code=400)
            
            instance.user_title_mt=get_translation(1,instance.user_title,lang_detect_user_title_key,"en",user_id=instance.user.id) if instance.user_title else None
            instance.save()

        detected_lang = lang_detector(instance.keywords)
        if detected_lang !='en':
            consumable_credits = get_consumable_credits_for_text(instance.keywords,instance.user_language_code,'en')

            if initial_credit < consumable_credits:
                raise serializers.ValidationError({'msg':'Insufficient Credits','blog_id':instance.id}, code=400)
            
            instance.keywords_mt=get_translation(1,instance.keywords,detected_lang,"en",user_id=instance.user.id) if instance.user_title else None
            instance.save() 
        #debit_status, status_code = UpdateTaskCreditStatus.update_credits(instance.user, consumable_credits)                
        instance.save()
        return instance
        
    def update(self, instance, validated_data):
        blog_available_langs = [17]
        user_lang = instance.user_language_code
        initial_credit = instance.user.credit_balance.get("total_left")

        if validated_data.get('user_title',None):
            instance.user_title = validated_data.get('user_title',instance.user_title)
            #if (instance.user_title_mt and (instance.user_language_id not in blog_available_langs)):
            lang_detect_user_blog_title = lang_detector(instance.user_title) 
            if lang_detect_user_blog_title !='en':
                consumable_credits = get_consumable_credits_for_text(instance.user_title,instance.user_language_code,'en')
                if initial_credit < consumable_credits:
                    raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
                instance.user_title_mt = get_translation(1,instance.user_title,user_lang,"en",user_id=instance.user.id)  
            else:
                instance.user_title_mt = None
            instance.save()
                #debit_status, status_code = UpdateTaskCreditStatus.update_credits(instance.user, consumable_credits)

        if validated_data.get('keywords',None):
            instance.keywords = validated_data.get('keywords',instance.keywords)
            detected_lang = lang_detector(instance.keywords)
            if detected_lang != 'en':
                consumable_credits = get_consumable_credits_for_text(instance.keywords,instance.user_language_code,'en')
                if initial_credit < consumable_credits:
                    raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
                instance.keywords_mt = get_translation(1,instance.keywords,user_lang,"en",user_id=instance.user.id) 
            else:
                instance.keywords_mt = None
                #debit_status, status_code = UpdateTaskCreditStatus.update_credits(instance.user, consumable_credits)
            instance.save()

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        keywords = instance.blog_key_create.order_by('-id')
        representation['blog_key_create'] = BlogKeywordGenerateSerializer(keywords, many=True).data
        titles = instance.blog_title_create.order_by('-id')
        representation['blog_title_create'] = BlogtitleSerializer(titles, many=True).data
        return representation






















 
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
 



 #instance.keywords_mt = get_translation(1, instance.keywords , instance.user_language_code,"en",user_id=instance.user.id) if instance.keywords else None
            # also concat keywords with prompt
            # if instance.keywords_mt:
            #     prompt = keyword_start_phrase+ " " +instance.user_title_mt+ " with based on this keywords"+ instance.keywords_mt
            # else:
             
            # prompt = keyword_start_phrase+ " " +instance.user_title_mt 
            # openai_response = get_prompt(prompt,OPENAI_MODEL,blog_sub_phrase.max_token, instance.response_copies_keyword)
            # token_usage = openai_token_usage(openai_response)
            # keywords = openai_response['choices'][0]['text']
            # print("From openai-------->",keywords)
            # for blog_keyword in keywords.split('\n'):
            #     if blog_keyword.strip():
            #         blog_keyword = re.sub(r'\d+.','',blog_keyword)
            #         blog_keyword = blog_keyword.strip()
            #         if special_character_check(blog_keyword):
            #             print("punc")
            #         else:
            #             blog_keyword = replace_punctuation(blog_keyword)
            #             blog_keyword_trans = get_translation(1, blog_keyword ,"en",instance.user_language_code,user_id=instance.user.id) if instance.user_title else None
            #             BlogKeywordGenerate.objects.create(blog_creation = instance,blog_keyword =blog_keyword_trans, selected_field= False , 
            #                                 blog_keyword_mt=blog_keyword,token_usage=token_usage)
   
  # print("prompt--------------------->",prompt)
            # openai_response = get_prompt(prompt,OPENAI_MODEL,blog_sub_phrase.max_token, instance.response_copies_keyword)
            # token_usage = openai_token_usage(openai_response)
            # keywords = openai_response['choices'][0]['text']
            # for blog_keyword in keywords.split('\n'):
            #     if blog_keyword.strip():
            #         blog_keyword = re.sub(r'\d+.','',blog_keyword)
            #         blog_keyword = blog_keyword.strip()
            #         if special_character_check(blog_keyword):
            #             print("punc")
            #         else: 
            #             blog_keyword =replace_punctuation(blog_keyword)
            #             BlogKeywordGenerate.objects.create(blog_creation=instance,blog_keyword=blog_keyword,selected_field= False, 
            #                                     blog_keyword_mt=None,token_usage=token_usage)                   


                    # queryset_new = queryset.annotate(
        #                 order_new=Coalesce('custom_order', models.Value(9999, output_field=IntegerField()))
        #                 ).order_by(ExpressionWrapper(Case(
        #                 When(custom_order__isnull=True, then=F('id')),  # Use 'id' field as default value when 'order' is null
        #                 default=F('order_new'),  # Use 'custom_order' field for ordering
        #                 output_field=IntegerField()),
        #             output_field=IntegerField()
        #             ))
        # queryset = instance.blog_creation.blog_title_create.filter(selected_field = True).first().blogoutlinesession_title.filter(selected_field=True)


##########################Blog Article creation before streaming###############################################################



#from ai_workspace.models import MyDocuments
    # blog_creation = serializers.PrimaryKeyRelatedField(queryset=BlogCreation.objects.all(),required=True)
    # sub_categories = serializers.PrimaryKeyRelatedField(queryset=PromptSubCategories.objects.all(),
    #                                                     many=False,required=False)
    # outline_section_list = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=BlogOutlineSession.objects.all(),
    #                                                                                  many=False),write_only=True,required=True)
        #('id','blog_article','blog_article_mt','blog_creation','document',
        #        'token_usage','sub_categories','created_at','updated_at','outline_section_list')
        # extra_kwargs = {'outline_section_list':{'required':True}}'blog_outline_article_gen','outline_section_list',

    # def create(self, validated_data): #prompt, Blog Title, keywords, outline 
    #     blog_available_langs =[17]
    #     if 'outline_section_list' in validated_data:
    #         outline_section_list = validated_data.pop('outline_section_list')
    #     else:outline_section_list = None
    #     instance = BlogArticle.objects.create(**validated_data)
    #     initial_credit = instance.blog_creation.user.credit_balance.get("total_left")
    #     if instance.blog_creation.user_language_code != 'en':
    #         credits_required = 2000
    #     else:
    #         credits_required = 200
    #     if initial_credit < credits_required:
    #         raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
    #     blog_article_start_phrase = instance.sub_categories.prompt_sub_category.first().start_phrase
    #     title = instance.blog_creation.user_title
    #     detected_lang = lang_detector(title)
    #     if detected_lang!='en':
    #         title = instance.blog_creation.user_title_mt
    #     keyword = instance.blog_creation.keywords 
    #     detected_lang = lang_detector(keyword)
    #     if detected_lang!='en':
    #         keyword = instance.blog_creation.keywords_mt
    #     print("OutlineSelection---------------->",outline_section_list)
    #     if outline_section_list:
    #         detected_lang = lang_detector(outline_section_list[0].blog_outline)
    #     else: raise serializers.ValidationError({'msg':'No Outlines Selected'}, code=400)
    #     if detected_lang!='en':
    #         outlines = [i.blog_outline_mt for i in outline_section_list if i.blog_outline_mt ]
    #     else:
    #         outlines = [i.blog_outline for i in outline_section_list]
    #     joined_list = "', '".join(outlines)
    #     selected_outline_section_list = f"'{joined_list}'"
    #     print("Selected------------>",selected_outline_section_list)
    #     prompt = blog_article_start_phrase.format(title,selected_outline_section_list,keyword,instance.blog_creation.tone.tone)
    #     #prompt+=', in {} tone'.format(instance.blog_creation.tone.tone)
    #     print("prompt____article--->>>>",prompt)
    #     # if isinstance(prompt,list):
    #     prompt_response = get_prompt_chatgpt_turbo(prompt=prompt,n=1)
    #     print("prot_resp--->>>>>>>>>>>",prompt_response)
    #     prompt_response_article_resp = prompt_response['choices'][0].message['content']
    #     total_token = openai_token_usage(prompt_response)
    #     token_usage = get_consumable_credits_for_openai_text_generator(total_token.total_tokens)
    #     #prompt_responses = blog_generator(outline_section_prompt_list= outlines,title=title,tone=instance.blog_creation.tone.tone,
    #     #                                      keyword=keyword)
    #     # prompt_response_article_resp=[]
    #     # token_usage=0
    #     # for count,prompt_response in enumerate(prompt_responses):
    #     #     generated_text=prompt_response.choices[0].text
    #     #     prompt_response_article_resp.append('\n'+'<h2>'+outlines[count]+'</h2>'+generated_text)
    #     #     total_token=openai_token_usage(prompt_response)
    #     #     token_usage+=total_token.total_tokens
    #     # token_usage = get_consumable_credits_for_openai_text_generator(token_usage)

    #     # prompt_response_article_resp= '<h1>'+title+'</h1>'+'\n\n'+"'\n".join(prompt_response_article_resp)
    #     # print("prot_resp--->>>>>>>>>>>",prompt_response_article_resp)
    #     # print("token_usage---->>",token_usage)

    #     if instance.blog_creation.user_language_id not in blog_available_langs:
    #         consumable_credits_for_article_gen = get_consumable_credits_for_text(prompt_response_article_resp,
    #                                                                              instance.blog_creation.user_language_code,'en')
    #         if initial_credit >= consumable_credits_for_article_gen:
    #             blog_article_trans = get_translation(1,prompt_response_article_resp,"en",instance.blog_creation.user_language_code,
    #                                                 user_id=instance.blog_creation.user.id)  
    #             instance.blog_article_mt = blog_article_trans
    #         else:
    #             instance.blog_article_mt = prompt_response_article_resp
    #         tot_tok =  token_usage#+consumable_credits_for_article_gen
    #         print("tot_tok",tot_tok)
    #         AiPromptSerializer().customize_token_deduction(instance.blog_creation,tot_tok)
    #         #instance.blog_article_mt=prompt_response_article_resp
    #     else:
    #         instance.blog_article = prompt_response_article_resp 
    #         AiPromptSerializer().customize_token_deduction(instance.blog_creation,token_usage)
    #     instance.save()
    #     article = instance.blog_article_mt if instance.blog_creation.user_language_code != 'en' else instance.blog_article
    #     tt = MyDocuments.objects.create(doc_name=title,blog_data = article,document_type_id=2,ai_user=instance.blog_creation.user)
    #     print("Doc--------->",tt)
    #     instance.document = tt
    #     instance.save()
    #     return instance
