from rest_framework.response import Response
from rest_framework import serializers
from .models import (AiPrompt ,AiPromptResult,TokenUsage,TextgeneratedCreditDeduction,
                    AiPromptCustomize ,ImageGeneratorPrompt ,ImageGenerationPromptResponse ,
                    ImageGeneratorResolution,TranslateCustomizeDetails, CustomizationSettings,
                    BlogArticle,BlogCreation,BlogKeywordGenerate,BlogOutline,Blogtitle,BlogOutlineSession,
                    BookCreation,BookBackMatter,BookBodyDetails,BookBody,BookFrontMatter,BookTitle)
import re 
from ai_staff.models import (PromptCategories,PromptSubCategories ,AiCustomize, LanguagesLocale ,
                            PromptStartPhrases ,PromptTones ,Languages,Levels,Genre,BackMatter,FrontMatter)
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
from ai_workspace.models import Project,ProjectType,ProjectSteps,Steps

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
    source_prompt_lang = serializers.PrimaryKeyRelatedField(queryset=Languages.objects.all(),many=False,required=False)
    sub_catagories = serializers.PrimaryKeyRelatedField(queryset=PromptSubCategories.objects.all(),many=False,required=False)
    class Meta:
        model = AiPrompt
        fields = ('id','user','prompt_string','description','book','document','task','pdf','model_gpt_name','catagories','sub_catagories',
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
            
            if instance.keywords:
                prompt+=' including words '+ instance.keywords if lang in ai_langs else ' including words '+ instance.keywords_mt
            prompt+=' in {} tone'.format(instance.Tone.tone)
            
            if start_phrase.punctuation:
                prompt+=start_phrase.punctuation
        print("prompt-->",prompt)
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
        source_prompt_lang = validated_data.get('source_prompt_lang',None)
        if source_prompt_lang == None and targets == []:
            lng = lang_detector(validated_data.get('description'))
            try:
                lang_ins = LanguagesLocale.objects.filter(locale_code = lng).first().language 
            except:
                lang_ins = LanguagesLocale.objects.filter(locale_code = 'en').first().language
            validated_data['source_prompt_lang'] = lang_ins
            targets = [lang_ins.id]
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
    book_name = serializers.ReadOnlyField(source='book.project.project_name')
    #ai_prompt = AiPromptResultSerializer(many=True)

    class Meta:
        model = AiPrompt
        fields = ('id','user','prompt_string','doc_name','book','book_name','document','source_prompt_lang','target_langs','description','catagories','sub_catagories','Tone',
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
    book_name = serializers.ReadOnlyField(source='book.project.project_name')
    customization = TranslateCustomizeDetailSerializer(required=False,many=True)
    class Meta:
        model = AiPromptCustomize
        fields = ('id','document','task','pdf','doc_name','customize','customize_name','user_text',\
                    'tone','api_result','prompt_result','user_text_lang','user',\
                    'credits_used','prompt_generated','user_text_mt','created_at',\
                    'customization','created_by','book_name','book',)

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
        qr = BlogOutlineSession.objects.filter(group=validated_data.get('group'),blog_title=validated_data.get('blog_title')).order_by('custom_order')
        if qr: count = qr.last().custom_order
        else: count = 1
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
        prompt_response_gpt = outline_gen(prompt=prompt,n=2)

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
        debit_status, status_code = UpdateTaskCreditStatus.update_credits(instance.user, consumable_credits)      ################# 2 times update          
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



class BookTitleSerializer(serializers.ModelSerializer):
      
    class Meta:
        model = BookTitle
        fields = '__all__'

    def create(self,validated_data):
        blog_available_langs = [17]
        book_creation = validated_data.get('book_creation')
        sub_categories = validated_data.get('sub_categories')
        title_start_phrase = PromptStartPhrases.objects.get(sub_category=sub_categories)
        initial_credit = book_creation.user.credit_balance.get("total_left")
        description = book_creation.description_mt if book_creation.description_mt else book_creation.description
        genre = book_creation.genre.genre
        level = book_creation.level.level
        author_info = book_creation.author_info_mt if book_creation.author_info_mt else book_creation.author_info
        prompt = title_start_phrase.start_phrase.format(author_info,description,level,genre)
        print("prompt----->>>>>>>>>>>>>>>>>>>>>>>>>>>",prompt)
        consumable_credits = get_consumable_credits_for_text(prompt,None,'en')

        if initial_credit < consumable_credits:
            raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
        
        openai_response = get_prompt_chatgpt_turbo(prompt,1,title_start_phrase.max_token)
        token_usage = openai_token_usage(openai_response)
        token_usage_to_reduce = get_consumable_credits_for_openai_text_generator(token_usage.total_tokens)
        AiPromptSerializer().customize_token_deduction(book_creation,token_usage_to_reduce)
        
        book_titles = openai_response["choices"][0]["message"]["content"]
        #title creation
        for book_title in book_titles.split('\n'):
            if book_title.strip().strip('.'):
                book_title = re.sub(r'\d+.','',book_title)
                book_title = book_title.strip().strip('"')
                if (book_creation.book_language_id not in blog_available_langs):
                    print("book title create not in en")
                    initial_credit = book_creation.user.credit_balance.get("total_left")
                    consumable_credits_to_translate_title = get_consumable_credits_for_text(book_title,book_creation.book_language_code,'en')
                    if initial_credit > consumable_credits_to_translate_title:
                        book_title_in_other_lang=get_translation(1,book_title,"en",book_creation.book_language_code,
                                                             user_id=book_creation.user.id,from_open_ai=True) 
                        debit_status, status_code = UpdateTaskCreditStatus.update_credits(book_creation.user,consumable_credits_to_translate_title)
                    else:
                        raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
                    BookTitle.objects.create(book_creation=book_creation,sub_categories=sub_categories,
                                         book_title=book_title_in_other_lang,book_title_mt=book_title,
                                         token_usage=token_usage,selected_field=False)
                else:
                    BookTitle.objects.create(book_creation=book_creation,sub_categories=sub_categories,
                                                book_title=book_title,token_usage=token_usage,selected_field=False)

        return validated_data

    def update(self, instance, validated_data):
        user_lang = instance.book_creation.book_language_code
        if validated_data.get('book_title' , None):
            instance.book_title = validated_data.get('book_title' ,instance.book_title)
            lang_detect_book_title = lang_detector(instance.book_title) 
            initial_credit = instance.book_creation.user.credit_balance.get("total_left")
            if lang_detect_book_title !='en':
                consumable_credits_to_translate_update_title = get_consumable_credits_for_text(instance.book_title,instance.book_creation.blog_language_code,'en')
                if initial_credit < consumable_credits_to_translate_update_title:
                    raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
                instance.book_title_mt = get_translation(1,instance.book_title,user_lang,"en",
                                                    user_id=instance.book_creation.user.id) if instance.book_title else None
            else:
                instance.book_title_mt = None 
            instance.save()    

    # def to_representation(self, instance):
    #     representation = super().to_representation(instance)
    #     bdy = instance.book_title_bdy.order_by('custom_order')
    #     representation['book_body_matter'] = BookBodySerializer(bdy, many=True).data
    #     return representation


 
class BookCreationSerializer(serializers.ModelSerializer):
    book_title_create=BookTitleSerializer(many=True,required=False)
    sub_categories = serializers.PrimaryKeyRelatedField(queryset=PromptSubCategories.objects.all(),many=False,required=False)
    categories = serializers.PrimaryKeyRelatedField(queryset=PromptCategories.objects.all(),many=False,required=False)
    project_name = serializers.CharField(required=False,write_only=True)
    name = serializers.ReadOnlyField(source='project.project_name'  )
    class Meta:
        model = BookCreation
        fields = ('id','user', 'description','description_mt','author_info','author_info_mt',
                'author_name','genre','level','title','title_mt','categories','sub_categories',
                'book_language','book_title_create','project','name','project_name','created_by','created_at',)
        

    def create(self,validated_data):  
        blog_available_langs = [17]
        instance = BookCreation.objects.create(**validated_data)
        initial_credit = instance.user.credit_balance.get("total_left")

        total_usage = 0

        lang_detect_description = lang_detector(instance.description) 
        if lang_detect_description !='en':
            consumable_credits = get_consumable_credits_for_text(instance.description,instance.book_language_code,'en')
            if initial_credit < consumable_credits:
                raise serializers.ValidationError({'msg':'Insufficient Credits','book_id':instance.id}, code=400)
            
            instance.description_mt=get_translation(1,instance.description,lang_detect_description,"en",user_id=instance.user.id) if instance.description else None
            instance.save()

        lang_detect_author_info = lang_detector(instance.author_info) 
        if lang_detect_author_info !='en':
            consumable_credits = get_consumable_credits_for_text(instance.author_info,instance.book_language_code,'en')
            if initial_credit < consumable_credits:
                raise serializers.ValidationError({'msg':'Insufficient Credits','book_id':instance.id}, code=400)
            
            instance.author_info_mt=get_translation(1,instance.author_info,lang_detect_author_info,"en",user_id=instance.user.id) if instance.author_info else None
            instance.save()

        lang_detect_title = lang_detector(instance.title) 
        if lang_detect_author_info !='en':
            consumable_credits = get_consumable_credits_for_text(instance.title,instance.book_language_code,'en')

            if initial_credit < consumable_credits:
                raise serializers.ValidationError({'msg':'Insufficient Credits','book_id':instance.id}, code=400)
            
            instance.author_info_mt=get_translation(1,instance.title,lang_detect_author_info,"en",user_id=instance.user.id) if instance.title else None
            instance.save()

        project_type = ProjectType.objects.get(id=7) #Writer Project creation
        default_step = Steps.objects.get(id=1)
        team = instance.user.team if instance.user.team else None
        project_instance =  Project.objects.create(project_type =project_type, ai_user=instance.user,created_by=instance.user,team=team)
        project_steps = ProjectSteps.objects.create(project=project_instance,steps=default_step)
        print("prIns--------------->",project_instance)
        instance.project = project_instance
        instance.save()
        default_bm = BackMatter.objects.get(name='Afterword')
        default_fm = FrontMatter.objects.get(name='Preface')
        bm = BookBackMatter.objects.create(book_creation=instance,back_matter=default_bm,sub_categories_id=69,temp_order=1,custom_order=1,name=default_bm.name)
        fm = BookFrontMatter.objects.create(book_creation=instance,front_matter=default_fm,sub_categories_id=68,temp_order=1,custom_order=1,name=default_fm.name)
        print("RRRRRRR-------------------->",bm,fm)
        return instance
    
    def update(self, instance, validated_data):
        #print("VD------------->",validated_data)
        blog_available_langs = [17]
        lang = instance.book_language_code
        initial_credit = instance.user.credit_balance.get("total_left")

        if validated_data.get('description',None):
            instance.description = validated_data.get('description',instance.description)
            lang_detect_description = lang_detector(instance.description) 
            if lang_detect_description !='en':
                consumable_credits = get_consumable_credits_for_text(instance.description,instance.book_language_code,'en')
                if initial_credit < consumable_credits:
                    raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
                instance.description_mt = get_translation(1,instance.description,lang,"en",user_id=instance.user.id)  
            else:
                instance.description_mt = None
            instance.save()
        
        if validated_data.get('project_name'):
            instance.project.project_name = validated_data.get('project_name')
            instance.project.save()

        if validated_data.get('author_info',None):
            instance.author_info = validated_data.get('author_info',instance.author_info)
            lang_detect_author_info = lang_detector(instance.author_info) 
            if lang_detect_author_info !='en':
                consumable_credits = get_consumable_credits_for_text(instance.author_info,instance.book_language_code,'en')
                if initial_credit < consumable_credits:
                    raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
                instance.author_info_mt = get_translation(1,instance.author_info,lang,"en",user_id=instance.user.id)  
            else:
                instance.author_info_mt = None
            instance.save()
        
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        titles = instance.book_title_create.order_by('-id')
        representation['book_title_create'] = BookTitleSerializer(titles, many=True).data
        front_matter = instance.book_fm_create.order_by('custom_order')
        representation['front_matter'] = BookFrontMatterSerializer(front_matter, many=True).data
        body_matter = instance.book_bdy_create.order_by('custom_order')
        representation['body_matter'] = BookBodySerializer(body_matter, many=True).data
        back_matter = instance.book_bm_create.order_by('custom_order')
        representation['back_matter'] = BookBackMatterSerializer(back_matter, many=True).data
        return representation

class BookBodySerializer(serializers.ModelSerializer):
    select_group = serializers.BooleanField(required=False)
    order_list = serializers.CharField(required=False)
    selected = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=BookBody.objects.all(),
                                                                    many=False,required=False),required=False)
    unselected = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=BookBody.objects.all(),
                                                             many=False,required=False),required=False)

    class Meta:
        model = BookBody
        fields = '__all__'
        extra_kwargs = {'select_group':{'required' : False},'order_list':{'required':False}}
         
    def create(self, validated_data):
        print("ValiData----------->",validated_data)
        blog_available_langs =[17]
        book_title_inst = validated_data.get('book_title')
        book_creation = validated_data.get('book_creation')
        generated_content = validated_data.get('generated_content',None)
        body_matter = validated_data.get('body_matter',1)
        group = validated_data.get('group',0)
        sub_categories = validated_data.get('sub_categories')
        book_obj = book_title_inst.book_creation if book_title_inst else book_creation
        if book_title_inst or book_creation and generated_content==None:
            print("Inside If")
            if book_title_inst:
                book_tit = BookTitle.objects.filter(id=book_title_inst.id).update(selected_field = True)
                BookTitle.objects.filter(book_creation=book_title_inst.book_creation).exclude(id = book_title_inst.id).update(selected_field=False)
            initial_credit = book_obj.user.credit_balance.get("total_left")
            print("InitialCredit----------------->",initial_credit)
            if initial_credit < 150:
                raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
            book_body_start_phrase = PromptStartPhrases.objects.get(sub_category=sub_categories)
            print("sSR-------->",book_body_start_phrase)
            if book_title_inst:
                print("BookObj------------>",book_obj)
                book_obj.title = book_title_inst.book_title
                book_obj.title_mt = book_title_inst.book_title_mt
                book_obj.save()
            title = book_obj.title_mt if book_obj.title_mt else book_obj.title
            description = book_obj.description_mt if book_obj.description_mt else book_obj.description


            if body_matter.id == 1:
                print("-------------------------------------------")
                print(book_body_start_phrase.start_phrase)
                prompt = book_body_start_phrase.start_phrase.format(title,description,book_obj.level.level,book_obj.genre.genre)
                print("PR------------->",prompt)
                prompt_response_gpt = outline_gen(prompt=prompt,n=1)

                prompt_response = prompt_response_gpt.choices
                print('PRS--------------->',prompt_response)
                total_token = prompt_response_gpt['usage']['total_tokens']
                token_usage = openai_token_usage(prompt_response_gpt)
                total_token = get_consumable_credits_for_openai_text_generator(total_token)
                AiPromptSerializer().customize_token_deduction(book_obj,total_token)
                print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
                queryset = BookBody.objects.filter(book_creation=book_obj,body_matter_id=body_matter.id).distinct('group')
                print("QR----------------->",queryset)
                if queryset: start = queryset.count()
                else: start = 0
                print("Start---------------------->",start)
                qr = BookBody.objects.filter(book_creation=book_obj,body_matter_id=body_matter.id,group=group).order_by('custom_order')
                print("qr-------------------------->",qr)
                if qr: start_ = qr.last().custom_order
                else:start_ = 0
                print("Start________",start_)
                for group,chapter_res in enumerate(prompt_response,start=start):
                    chapters = chapter_res.message['content'].split('\n')
                    for order,chapter in enumerate(chapters,start=start_+1):
                        print("Order----------->",order)
                        if chapter:
                            chapter = re.sub(r'\d+.','',chapter).strip()
                            print("chap========>",chapter)
                            if (book_obj.book_language_id not in blog_available_langs):
                                initial_credit = book_obj.user.credit_balance.get("total_left")
                                consumable_credits_to_translate_section = get_consumable_credits_for_text(chapter,book_obj.book_language_code,'en')
                                if initial_credit > consumable_credits_to_translate_section:
                                    book_chapter=get_translation(1,chapter,'en',book_obj.book_language_code,
                                                                user_id=book_obj.user.id) 
                                    BookBody.objects.create(body_matter=body_matter,sub_categories=sub_categories,generated_content=book_chapter,custom_order=order,temp_order=order,book_creation=book_obj,
                                                            generated_content_mt=chapter,group=group,book_title =book_title_inst,name=body_matter.name,token_usage=token_usage)
                                    # debit_status, status_code = UpdateTaskCreditStatus.update_credits(instance.blog_title_gen.blog_creation_gen.user,consumable_credits_to_translate_section)
                                else:
                                    raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
                            else:
                                rr = BookBody.objects.create(body_matter =body_matter,sub_categories=sub_categories, 
                                generated_content=chapter,group=group,temp_order=order,custom_order=order,
                                book_title =book_title_inst,book_creation=book_obj,
                                name=body_matter.name,token_usage=token_usage) 
                                print(rr)
            else:
                prompt = book_body_start_phrase.start_phrase.format(body_matter.name,title,description,book_obj.genre.genre,book_obj.level.level)
                print("PR------------->",prompt)
                openai_response = get_prompt_chatgpt_turbo(prompt,1)
                token_usage = openai_token_usage(openai_response)
                token_usage_to_reduce = get_consumable_credits_for_openai_text_generator(token_usage.total_tokens)
                AiPromptSerializer().customize_token_deduction(book_obj,token_usage_to_reduce)
                qr = BookBody.objects.filter(book_creation=book_obj,body_matter=body_matter).order_by('custom_order')
                print("QR-------------------->",qr)
                if qr:
                    count = qr.last().custom_order
                else: count = 1
                print("Count--------->",count)
                generated_content = openai_response["choices"][0]["message"]["content"]
                if (book_obj.book_language_id not in blog_available_langs):
                    initial_credit = book_obj.user.credit_balance.get("total_left")
                    consumable_credits_to_translate_section = get_consumable_credits_for_text(chapter,book_obj.book_language_code,'en')
                    if initial_credit > consumable_credits_to_translate_section:
                        content=get_translation(1,generated_content,'en',book_obj.blog_language_code,
                                                    user_id=book_obj.user.id) 
                        BookBody.objects.create(body_matter=body_matter,sub_categories=sub_categories,generated_content=content,custom_order=count+1,temp_order=count+1,book_creation=book_obj,
                                                generated_content_mt=generated_content,group=group,book_title =book_title_inst,name=body_matter.name,token_usage=token_usage)
                        # debit_status, status_code = UpdateTaskCreditStatus.update_credits(instance.blog_title_gen.blog_creation_gen.user,consumable_credits_to_translate_section)
                    else:
                        raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
                else:
                    BookBody.objects.create(body_matter=body_matter,sub_categories=sub_categories,generated_content=generated_content,
                                            book_title =book_title_inst,book_creation=book_obj,name=body_matter.name,custom_order=count+1,
                                            temp_order=count+1,token_usage=token_usage) 
            instance = BookBody.objects.filter(book_creation=book_obj,body_matter=body_matter).first()
            return instance
        
        else:
            print("Inside Else")
            blog_available_langs =[17]
            qr = BookBody.objects.filter(book_creation=book_creation,body_matter=body_matter).order_by('custom_order')
            print("QR------------------>",qr)
            if qr: count = qr.last().custom_order
            else: count = 0
            #count = BookBody.objects.filter(group=group,book_creation=book_creation,body_matter=body_matter).count()
            print("Count------->",count)
            instance = BookBody.objects.create(**validated_data)
            if instance.book_title:
                instance.book_creation = instance.book_title.book_creation
                instance.save()
            instance.custom_order = count+1
            instance.temp_order = count+1
            initial_credit = instance.book_creation.user.credit_balance.get("total_left")
            user_lang = instance.book_creation.book_language_id
            lang_code =instance.book_creation.book_language_code
            user_id = instance.book_creation.user.id
            consumable_credit = get_consumable_credits_for_text(instance.generated_content,'en',lang_code)
            if (user_lang not in blog_available_langs):
                instance.selected_field =True
                
                if initial_credit > consumable_credit:
                    instance.generated_content_mt = get_translation(1,instance.generated_content,
                                                        lang_code,"en",user_id=user_id) if instance.generated_content else None
                    instance.selected_field =True
                else:
                    raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
            else:
                lang_detect_chapter_create =  lang_detector(instance.generated_content) 
                if lang_detect_chapter_create!='en':
                    instance.generated_content_mt = get_translation(1,instance.generated_content,lang_detect_chapter_create,"en",user_id=user_id)  
                    debit_status, status_code = UpdateTaskCreditStatus.update_credits(user_id,consumable_credit)
                instance.selected_field =True
            instance.group = group
            instance.save()
        return instance

    def update(self, instance, validated_data):
        print("ValiData----------->",validated_data)
        lang_code =instance.book_creation.book_language_code
        user_id = instance.book_creation.user.id

        if validated_data.get('select_group',None):
            BookBody.objects.filter(group=validated_data.get('select_group'),book_title_id=instance.book_title_id).update(selected_field=True)
            BookBody.objects.filter(book_title_id=instance.book_title_id).exclude(group=validated_data.get('select_group')).update(selected_field=False)

        if validated_data.get('generated_content',None):
            instance.generated_content = validated_data.get('generated_content',instance.generated_content)
            instance.save()
            # initial_credit = instance.book_creation.user.credit_balance.get("total_left")
            # consumable_credit_section = get_consumable_credits_for_text(instance.generated_content ,'en',lang_code)
            # if initial_credit < consumable_credit_section:
            #     raise serializers.ValidationError({'msg':'Insufficient Credits'},code=400)

            # if instance.generated_content_mt:
            #     instance.generated_content_mt = get_translation(1,instance.generated_content,lang_code,"en",
            #                                user_id=user_id) if instance.generated_content else None
            #     debit_status, status_code = UpdateTaskCreditStatus.update_credits(instance.book_creation.user,consumable_credit_section)
             
            # lang_detect_user_gc =  lang_detector(instance.generated_content) 

            # if lang_detect_user_gc !='en':
            #     instance.generated_content_mt =get_translation(1,instance.generated_content,lang_detect_user_gc,"en",user_id=instance.book_creation.user.id,from_open_ai=True)  
            #     debit_status, status_code = UpdateTaskCreditStatus.update_credits(instance.book_creation.user, consumable_credit_section)
        #instance.save() 


        if validated_data.get('group',None):
            instance.group = validated_data.get('group',instance.group)
  
        if validated_data.get('selected',None):
            bd_ids = validated_data.get('selected')
            for bd in bd_ids:
                bd.selected_field = True
                bd.save()

        if validated_data.get('unselected',None):
            bd_ids = validated_data.get('unselected')
            for bd in bd_ids:
                bd.selected_field = False
                bd.save()

        
        if validated_data.get('html_data',None):
            instance.html_data = validated_data.get('html_data')
            instance.save()

        if validated_data.get('order_list',None):
            order_list = validated_data.get('order_list')
            group = validated_data.get('group',0)
            order_list = list(map(int, order_list.split(',')))
            for index, order in enumerate(order_list, 1):
                BookBody.objects.filter(temp_order=order).filter(book_title=instance.book_title).filter(group=group).update(custom_order=index)

        return instance

        # if validated_data.get('blog_outline_selected_list'):
            
    # def to_representation(self, instance):
    #     #representation = super().to_representation(instance)
    #     sessions = instance.order_by('custom_order')
    #     representation['book_chapters'] = BookBodyMatter(sessions, many=True).data
    #     return representation


class BookFrontMatterSerializer(serializers.ModelSerializer):
    order_list = serializers.CharField(required=False)
    obj=serializers.PrimaryKeyRelatedField(queryset=BookFrontMatter.objects.all(),
                                        many=False,required=False)
    class Meta:
        model = BookFrontMatter
        fields = "__all__"
        extra_kwargs = {'order_list':{'required':False}}

    def create(self,validated_data):
        blog_available_langs =[17]
        front_matter = validated_data.get('front_matter',1)
        sub_categories = validated_data.get('sub_categories',68)
        obj = validated_data.get('obj')
        name = validated_data.get('name',None)
        qr = BookFrontMatter.objects.filter(book_creation=validated_data.get('book_creation')).order_by('custom_order')
        if qr:count = qr.last().custom_order
        else: count = 0
        print("Count------->",count)
        if not obj:
            instance = BookFrontMatter.objects.create(**validated_data)
            instance.custom_order = count+1
            instance.temp_order = count+1
            instance.name = name if name else front_matter.name
            instance.save()
        else: instance=obj
        if obj:
            initial_credit = instance.book_creation.user.credit_balance.get("total_left")
            if initial_credit <150:
                raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
            book_fm_phrase = PromptStartPhrases.objects.get(sub_category=sub_categories)
            book_obj = instance.book_creation
            print("BookObj------------>",book_obj)
            title = book_obj.title_mt if book_obj.title_mt else book_obj.title
            description = book_obj.description_mt if book_obj.description_mt else book_obj.description
            prompt = book_fm_phrase.start_phrase.format(instance.name,title,description,book_obj.genre.genre,book_obj.level.level)
            openai_response = get_prompt_chatgpt_turbo(prompt,1,book_fm_phrase.max_token)
            token_usage = openai_token_usage(openai_response)
            token_usage_to_reduce = get_consumable_credits_for_openai_text_generator(token_usage.total_tokens)
            AiPromptSerializer().customize_token_deduction(book_obj,token_usage_to_reduce)
            
            front_matter = openai_response["choices"][0]["message"]["content"]
            if (book_obj.book_language_id not in blog_available_langs):
                    print("book title create not in en")
                    initial_credit = book_obj.user.credit_balance.get("total_left")
                    consumable_credits_to_translate_title = get_consumable_credits_for_text(front_matter,book_obj.book_language_code,'en')
                    if initial_credit > consumable_credits_to_translate_title:
                        fm_in_other_lang=get_translation(1,front_matter,"en",book_obj.book_language_code,
                                                                user_id=book_obj.user.id,from_open_ai=True) 
                        debit_status, status_code = UpdateTaskCreditStatus.update_credits(book_obj.user,consumable_credits_to_translate_title)
                    else:
                        raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
                    BookFrontMatter.objects.filter(id=instance.id).update(book_creation=book_obj,sub_categories=sub_categories,
                                            generated_content=fm_in_other_lang,generated_content_mt=front_matter,
                                            token_usage=token_usage,selected_field=True)
            else:
                BookFrontMatter.objects.filter(id=instance.id).update(book_creation=book_obj,sub_categories=sub_categories,
                                            generated_content=front_matter,token_usage=token_usage,selected_field=True)
        ins = BookFrontMatter.objects.get(id=instance.id)
        return ins
    
    def update(self, instance, validated_data):
        lang_code =instance.book_creation.book_language_code
        user_id = instance.book_creation.user.id

        if validated_data.get('generated_content',None):
            instance.generated_content = validated_data.get('generated_content',instance.generated_content)
            instance.save() 
        # if validated_data.get('generated_content',None):
        #     instance.generated_content = validated_data.get('generated_content',instance.generated_content)
            
        #     initial_credit = instance.book_creation.user.credit_balance.get("total_left")
        #     consumable_credit_section = get_consumable_credits_for_text(instance.generated_content ,'en',lang_code)
        #     if initial_credit < consumable_credit_section:
        #         raise serializers.ValidationError({'msg':'Insufficient Credits'},code=400)

        #     if instance.generated_content_mt:
        #         instance.generated_content_mt = get_translation(1,instance.generated_content,lang_code,"en",
        #                                    user_id=user_id) if instance.generated_content else None
        #         debit_status, status_code = UpdateTaskCreditStatus.update_credits(instance.book_creation.user,consumable_credit_section)
             
        #     lang_detect_user_gc =  lang_detector(instance.generated_content) 

        #     if lang_detect_user_gc !='en':
        #         instance.generated_content_mt =get_translation(1,instance.generated_content,lang_detect_user_gc,"en",user_id=instance.book_creation.user.id,from_open_ai=True)  
        #         debit_status, status_code = UpdateTaskCreditStatus.update_credits(instance.book_creation.user, consumable_credit_section)
       

        if validated_data.get('name',None):
            instance.name = validated_data.get('name')
            instance.save()

        # if validated_data.get('selected_field',None):
        #     instance.selected_field = selected_field
        #     instance.save()

        if validated_data.get('html_data',None):
            instance.html_data = validated_data.get('html_data')
            instance.save()

        if validated_data.get('order_list',None):
            order_list = validated_data.get('order_list')
            order_list = list(map(int, order_list.split(',')))
            for index, order in enumerate(order_list, 1):
                BookFrontMatter.objects.filter(temp_order=order).filter(book_creation=instance.book_creation).update(custom_order=index)

        return instance#super().update(instance, validated_data)



class BookBackMatterSerializer(serializers.ModelSerializer):
    order_list = serializers.CharField(required=False)
    obj=serializers.PrimaryKeyRelatedField(queryset=BookBackMatter.objects.all(),
                                        many=False,required=False)
    class Meta:
        model = BookBackMatter
        fields = "__all__"
        extra_kwargs = {'order_list':{'required':False}}

    def create(self,validated_data):
        blog_available_langs =[17]
        back_matter = validated_data.get('back_matter',1)
        sub_categories = validated_data.get('sub_categories',68)
        obj = validated_data.get('obj')
        name = validated_data.get('name',None)
        obj = validated_data.get('obj')
        qr = BookBackMatter.objects.filter(book_creation=validated_data.get('book_creation')).order_by('custom_order')
        if qr:count = qr.last().custom_order
        else: count = 0
        print("Count------->",count)
        if not obj:
            instance = BookBackMatter.objects.create(**validated_data)
            instance.custom_order = count+1
            instance.temp_order = count+1
            instance.save()
            instance.name = name if name else front_matter.name
            instance.save()
        else: instance = obj
        # instance.name = name if name else back_matter.name
        # instance.save()
        if obj:
            initial_credit = instance.book_creation.user.credit_balance.get("total_left")
            if initial_credit <150:
                    raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
            book_bm_phrase = PromptStartPhrases.objects.get(sub_category=sub_categories)
            book_obj = instance.book_creation
            print("BookObj------------>",book_obj)
            title = book_obj.title_mt if book_obj.title_mt else book_obj.title
            description = book_obj.description_mt if book_obj.description_mt else book_obj.description
            prompt = book_bm_phrase.start_phrase.format(instance.name,title,description,book_obj.genre.genre,book_obj.level.level)
            openai_response = get_prompt_chatgpt_turbo(prompt,1,book_bm_phrase.max_token)
            token_usage = openai_token_usage(openai_response)
            token_usage_to_reduce = get_consumable_credits_for_openai_text_generator(token_usage.total_tokens)
            AiPromptSerializer().customize_token_deduction(book_obj,token_usage_to_reduce)
            
            back_matter = openai_response["choices"][0]["message"]["content"]
            if (book_obj.book_language_id not in blog_available_langs):
                    print("book title create not in en")
                    initial_credit = book_obj.user.credit_balance.get("total_left")
                    consumable_credits_to_translate_title = get_consumable_credits_for_text(back_matter,book_obj.book_language_code,'en')
                    if initial_credit > consumable_credits_to_translate_title:
                        bm_in_other_lang=get_translation(1,back_matter,"en",book_obj.book_language_code,
                                                                user_id=book_obj.user.id,from_open_ai=True) 
                        debit_status, status_code = UpdateTaskCreditStatus.update_credits(book_obj.user,consumable_credits_to_translate_title)
                    else:
                        raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
                    BookBackMatter.objects.filter(id=instance.id).update(book_creation=book_obj,sub_categories=sub_categories,
                                            generated_content=bm_in_other_lang,generated_content_mt=back_matter,
                                            token_usage=token_usage,selected_field=True)
            else:
                BookBackMatter.objects.filter(id=instance.id).update(book_creation=book_obj,sub_categories=sub_categories,
                                            generated_content=back_matter,token_usage=token_usage,selected_field=True)
        ins = BookBackMatter.objects.get(id=instance.id)
        return ins
    
    def update(self, instance, validated_data):
        print("ValiData----------->",validated_data)
        lang_code =instance.book_creation.book_language_code
        user_id = instance.book_creation.user.id

        if validated_data.get('generated_content',None):
            instance.generated_content = validated_data.get('generated_content',instance.generated_content)
            instance.save() 

        # if validated_data.get('generated_content',None):
        #     instance.generated_content = validated_data.get('generated_content',instance.generated_content)
        #     initial_credit = instance.book_creation.user.credit_balance.get("total_left")
        #     consumable_credit_section = get_consumable_credits_for_text(instance.generated_content ,'en',lang_code)
        #     if initial_credit < consumable_credit_section:
        #         raise serializers.ValidationError({'msg':'Insufficient Credits'},code=400)

        #     if instance.generated_content_mt:
        #         instance.generated_content_mt = get_translation(1,instance.generated_content,lang_code,"en",
        #                                    user_id=user_id) if instance.generated_content else None
        #         debit_status, status_code = UpdateTaskCreditStatus.update_credits(instance.book_creation.user,consumable_credit_section)
             
        #     lang_detect_user_gc =  lang_detector(instance.generated_content) 

        #     if lang_detect_user_gc !='en':
        #         instance.generated_content_mt =get_translation(1,instance.generated_content,lang_detect_user_gc,"en",user_id=instance.book_creation.user.id,from_open_ai=True)  
        #         debit_status, status_code = UpdateTaskCreditStatus.update_credits(instance.book_creation.user, consumable_credit_section)
        # instance.save() 

        if validated_data.get('name',None):
            instance.name = validated_data.get('name')
            instance.save()

        # if validated_data.get('selected_field',None):
        #     instance.selected_field = selected_field
        #     instance.save()

        if validated_data.get('html_data',None):
            instance.html_data = validated_data.get('html_data')
            instance.save()

        if validated_data.get('order_list',None):
            order_list = validated_data.get('order_list')
            order_list = list(map(int, order_list.split(',')))
            for index, order in enumerate(order_list, 1):
                BookBackMatter.objects.filter(temp_order=order).filter(book_creation=instance.book_creation).update(custom_order=index)

        return instance#super().update(instance, validated_data)
    

from ai_openai.models import BookBodyDetails
class BookBodyDetailSerializer(serializers.ModelSerializer):
 
    class Meta:
        model = BookBodyDetails
        fields = "__all__"
