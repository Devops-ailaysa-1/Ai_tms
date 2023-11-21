from .models import (AiPrompt ,AiPromptResult, AiPromptCustomize  ,ImageGeneratorPrompt, BlogArticle,BlogCreation ,BlogKeywordGenerate,Blogtitle,
                     BlogOutline,BookCreation,BookTitle,BookBody,BlogOutlineSession ,TranslateCustomizeDetails,CustomizationSettings,
                     ImageGenerationPromptResponse, BookBackMatter,BookFrontMatter,BookBodyDetails,)
import logging ,os         
from django.core import serializers
import logging ,os ,json
from rest_framework import status
 
from rest_framework import viewsets,generics
from rest_framework.pagination import PageNumberPagination
from .serializers import (AiPromptSerializer ,AiPromptResultSerializer, AiPromptGetSerializer,AiPromptCustomizeSerializer,ImageGeneratorPromptSerializer,
                          TranslateCustomizeDetailSerializer ,BlogCreationSerializer,BlogKeywordGenerateSerializer,BlogtitleSerializer,
                        BlogOutlineSerializer,BlogOutlineSessionSerializer,BlogArticleSerializer,CustomizationSettingsSerializer,BookCreationSerializer,BookTitleSerializer,
                        BookBodySerializer,BookBodyDetailSerializer,)
from rest_framework.views import  Response
from django.http import JsonResponse, Http404, HttpResponse
from rest_framework.decorators import permission_classes ,api_view
from rest_framework.permissions  import IsAuthenticated
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from ai_workspace_okapi.utils import download_file
from .utils import get_consumable_credits_for_openai_text_generator
from ai_auth.models import UserCredits
from ai_workspace.api_views import UpdateTaskCreditStatus ,get_consumable_credits_for_text
from ai_workspace.models import Task
from ai_staff.models import AiCustomize ,Languages, PromptTones, LanguagesLocale, AilaysaSupportedMtpeEngines
#from langdetect import detect
#import langid
from googletrans import Translator
from .utils import get_prompt ,get_prompt_edit,get_prompt_image_generations, get_prompt_chatgpt_turbo
from ai_workspace_okapi.utils import get_translation
openai_model = os.getenv('OPENAI_MODEL')
logger = logging.getLogger('django')
from string import punctuation
from django.db.models import Q
from ai_openai.models import BookBody
from ai_openai.serializers import BookBackMatterSerializer,BookFrontMatterSerializer


class AiPromptViewset(viewsets.ViewSet):
    model = AiPrompt

    def get(self, request):
        query_set = self.model.objects.all()
        serializer = AiPromptSerializer(query_set ,many =True)
        return Response(serializer.data)

    def create(self,request):
        # keywords = request.POST.getlist('keywords')
        targets = request.POST.getlist('get_result_in')
        description = request.POST.get('description').rstrip(punctuation)
        char_limit = request.POST.get('response_charecter_limit',256)
        user = request.user.team.owner if request.user.team else request.user
        serializer = AiPromptSerializer(data={**request.POST.dict(),'user':user.id,'description':description,'created_by':self.request.user.id,'targets':targets,'response_charecter_limit':char_limit})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

class ImageGeneratorPromptViewset(viewsets.ViewSet):
    model = ImageGeneratorPrompt
    
    def get(self, request):
        query_set = self.model.objects.all()
        serializer = ImageGeneratorPromptSerializer(query_set ,many =True)
        return Response(serializer.data)
    
    def create(self,request):
        serializer = ImageGeneratorPromptSerializer(data=request.POST.dict() ,context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
        
class PromptFilter(django_filters.FilterSet):
    prompt = django_filters.CharFilter(field_name='description',lookup_expr='icontains')
    source = django_filters.CharFilter(field_name='source_prompt_lang__language',lookup_expr='icontains')
    target = django_filters.CharFilter(field_name='ai_prompt__result_lang__language',lookup_expr='icontains')
    category = django_filters.CharFilter(field_name='catagories__category',lookup_expr='icontains')
    sub_category = django_filters.CharFilter(field_name='sub_catagories__sub_category',lookup_expr='icontains')
    tone = django_filters.CharFilter(field_name='Tone__tone',lookup_expr='icontains')
    class Meta:
        model = AiPrompt
        fields = ('prompt', 'source','target','category','sub_category','tone',)



class NoPagination(PageNumberPagination):
      page_size = None

class AiPromptResultViewset(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AiPromptGetSerializer
    filter_backends = [DjangoFilterBackend ,SearchFilter,OrderingFilter]
    ordering_fields = ['id']
    ordering = ('-id')
    filterset_class = PromptFilter
    search_fields = ['description','catagories__category','sub_catagories__sub_category',]
    pagination_class = NoPagination
     

    def get_queryset(self):
        prmp_id = self.request.query_params.get('prompt_id')
        #prmp_id = self.request.GET.get('prompt_id')
        if prmp_id:
            queryset = AiPrompt.objects.filter(id=prmp_id)
        else:
            project_managers = self.request.user.team.get_project_manager if self.request.user.team else []
            owner = self.request.user.team.owner if self.request.user.team  else self.request.user
            queryset = AiPrompt.objects.prefetch_related('ai_prompt').filter(Q(user=self.request.user)|Q(created_by=self.request.user)|Q(created_by__in=project_managers)|Q(user=owner))\
                        .exclude(ai_prompt__id__in=AiPromptResult.objects.filter(Q(api_result__isnull = True)\
                         & Q(translated_prompt_result__isnull = True)).values('id'))
            
        
        return queryset
 

def instant_customize_response(customize ,user_text,used_tokens):
    print("Initial----------->",used_tokens)
    if customize.customize == 'Simplify':
        import re
        NEWLINES_RE = re.compile(r"\n{1,}")
        no_newlines = user_text.strip("\n")  # remove leading and trailing "\n"
        split_text = NEWLINES_RE.split(no_newlines)
    else:
        split_text = [user_text.replace('\n','')]
    final = ''
    cust_tokens = 0
    for text_ in split_text:
        text_ = text_ + '.'
        prompt = customize.prompt +' "{}"'.format(text_)
        #prompt = customize.prompt+" "+text+"."
        print("Prompt------------------->",prompt)
        response = get_prompt_chatgpt_turbo(prompt=prompt,max_token =256,n=1)
        #text = response['choices'][0]['text']
        text = response["choices"][0]["message"]["content"]
        text = text.strip('\n').strip('\"')
        final = final + "\n\n" + text
        tokens = response['usage']['total_tokens']
        print("Tokens from openai------------------>", tokens)
        total_tokens = get_consumable_credits_for_openai_text_generator(tokens)
        print("Calculated_token--------------->",total_tokens)
        cust_tokens = cust_tokens + total_tokens
    print("Cust tokens---------->",cust_tokens)
    cust_tokens += used_tokens
    print("Final----------->",cust_tokens)
    final = final.strip('\n')
    return final,cust_tokens


def customize_response(customize ,user_text,tone,used_tokens):
    #print("Initial------->",used_tokens)
    user_text = user_text.strip()
    if customize.prompt or customize.customize == "Text completion":
        if customize.customize == "Text completion":
            tone_ = PromptTones.objects.get(id=tone).tone
            prompt = customize.prompt+' {} tone : '.format(tone_)+user_text#+', in {} tone.'.format(tone_)
            response = get_prompt_chatgpt_turbo(prompt=prompt,max_token =150,n=1)
        else:
            if customize.grouping == "Explore":
                prompt = customize.prompt+" "+user_text+"?"
            else:
                user_text = user_text + '.'
                prompt = customize.prompt +' "{}"'.format(user_text)
                #prompt = customize.prompt+" "+user_text+"."
            print("Pr-------->",prompt)
            response = get_prompt_chatgpt_turbo(prompt=prompt,max_token =256,n=1)
        tokens = response['usage']['total_tokens']
        total_tokens = get_consumable_credits_for_openai_text_generator(tokens)
        total_tokens += used_tokens
    else:
        total_tokens = 0
        prompt = None
        response = get_prompt_edit(input_text=user_text ,instruction=customize.instruct)
    #print("Final----------->",total_tokens)
    return response,total_tokens,prompt

def translate_text(customized_id,user,user_text,source_lang,target_langs,mt_engine):
    res = []
    source_lang_code = Languages.objects.get(id=source_lang).locale.first().locale_code
    for i in target_langs:
        target_lang_code = Languages.objects.get(id=i).locale.first().locale_code
        mt_engine_id = AilaysaSupportedMtpeEngines.objects.get(id=mt_engine).id
        initial_credit = user.credit_balance.get("total_left")
        consumable_credits_user_text =  get_consumable_credits_for_text(user_text,source_lang_code,target_lang_code)
        if initial_credit >= consumable_credits_user_text:
            translation = get_translation(mt_engine_id, user_text, source_lang_code,target_lang_code,user_id=user.id)
            #debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits_user_text)
            data = {'customization':customized_id,'target_language':i,
                'mt_engine':mt_engine,'credits_used':consumable_credits_user_text,'result':translation}
            ser = TranslateCustomizeDetailSerializer(data=data)
            if ser.is_valid():
                ser.save()
                out = {'target_lang':i,'translation':ser.data}
                res.append(out)
            else:
                print(ser.errors)
        else:
            out = {'target_lang':i,'translation':"insufficient credits"}
            res.append(out)
    return res


from ai_auth.api_views import get_lang_code
@api_view(['POST',])
@permission_classes([IsAuthenticated])
def customize_text_openai(request):
    from ai_exportpdf.models import Ai_PdfUpload
    document = request.POST.get('document_id')
    task = request.POST.get('task',None)
    pdf = request.POST.get('pdf',None)
    book = request.POST.get('book',None)
    customize_id = request.POST.get('customize_id')
    user_text = request.POST.get('user_text')
    tone = request.POST.get('tone',1)
    language =  request.POST.get('language',None)
    customize = AiCustomize.objects.get(id =customize_id)
    target_langs = request.POST.getlist('target_lang')
    mt_engine = request.POST.get('mt_engine',None)
    detector = Translator()

    if task != None:
        obj = Task.objects.get(id=task)
        user = obj.job.project.ai_user
    elif pdf != None:
        obj = Ai_PdfUpload.objects.get(id=pdf)
        user = obj.user
    elif book != None:
        obj = BookCreation.objects.get(id=book)
        user = obj.user
    else:    
        user = request.user.team.owner if request.user.team else request.user
    print("User---------->",user)
        #project.team.owner if project.team else project.ai_user

    if language:lang = Languages.objects.get(id=language).locale.first().locale_code
    else:
        lang = detector.detect(user_text).lang
        if isinstance(lang,list):
            lang = lang[0]
        lang = get_lang_code(lang)

    initial_credit = user.credit_balance.get("total_left")
    if initial_credit == 0:
        return  Response({'msg':'Insufficient Credits'},status=400)

    if customize.customize == "Translate":
        consumable_credits_user_text =  get_consumable_credits_for_text(user_text,lang,'en')
        if initial_credit < consumable_credits_user_text:
           return  Response({'msg':'Insufficient Credits'},status=400) 
        data = {'document':document,'book':book,'task':task,'pdf':pdf,'customize':customize_id,'created_by':request.user.id,\
            'user':user.id,'user_text':user_text,'user_text_lang':language}
        try:mt_engine = user.custom_setting.mt_engine_id 
        except:mt_engine = 1
        ser = AiPromptCustomizeSerializer(data=data)
        if ser.is_valid():
            ser.save()
        print(ser.errors)
        created_obj_id = ser.data.get('id') 
        res = translate_text(created_obj_id,user,user_text,language,target_langs,mt_engine)
        return Response(res)

    
    total_tokens = 0
    user_text_mt_en,txt_generated = None,None
    try:user_text_lang = LanguagesLocale.objects.filter(locale_code=lang).first().language.id
    except:user_text_lang = 17

    if lang!= 'en':
        initial_credit = user.credit_balance.get("total_left")
        consumable_credits_user_text =  get_consumable_credits_for_text(user_text,source_lang=lang,target_lang='en')
        if initial_credit >= consumable_credits_user_text:
            user_text_mt_en = get_translation(mt_engine_id=1 , source_string = user_text,
                                        source_lang_code=lang , target_lang_code='en',user_id=user.id,from_open_ai=True)
            total_tokens += get_consumable_credits_for_text(user_text_mt_en,source_lang=lang,target_lang='en')
            response,total_tokens,prompt = customize_response(customize,user_text_mt_en,tone,total_tokens)
            #result_txt = response['choices'][0]['text']
            result_txt = response["choices"][0]["message"]["content"]
            txt_generated = get_translation(mt_engine_id=1 , source_string = result_txt.strip(),
                                        source_lang_code='en' , target_lang_code=lang,user_id=user.id,from_open_ai=True)
            total_tokens += get_consumable_credits_for_text(txt_generated,source_lang='en',target_lang=lang)
            #AiPromptSerializer().customize_token_deduction(instance = request,total_tokens= total_tokens)
        else:
            return  Response({'msg':'Insufficient Credits'},status=400)
        
    else:##english      
        response,total_tokens,prompt = customize_response(customize,user_text,tone,total_tokens)
        #result_txt = response['choices'][0]['text']
        result_txt = response["choices"][0]["message"]["content"]
    AiPromptSerializer().customize_token_deduction(instance = request,total_tokens= total_tokens,user = user)
    print("TT---------->",prompt)
    data = {'document':document,'task':task,'pdf':pdf,'book':book,'customize':customize_id,'created_by':request.user.id,\
            'user':user.id,'user_text':user_text,'user_text_mt':user_text_mt_en if user_text_mt_en else None,\
            'tone':tone,'credits_used':total_tokens,'prompt_generated':prompt,'user_text_lang':user_text_lang,\
            'api_result':result_txt.strip().strip('\"') if result_txt else None,'prompt_result':txt_generated}
    ser = AiPromptCustomizeSerializer(data=data)
    if ser.is_valid():
        ser.save()
        return Response(ser.data)
    return Response(ser.errors)


@api_view(['DELETE',])
@permission_classes([IsAuthenticated])
def history_delete(request):
    prmp = request.GET.get('prompt_id',None)
    obj = request.GET.get('obj_id',None)
    customize_obj = request.GET.get('customize_obj_id',None)
    if obj:
        result = AiPromptResult.objects.get(id=obj)
        count = result.prompt.ai_prompt.all().count()
        if count>1:
            result.delete()
        else:
            result.prompt.delete()
    if prmp:
        prmb_obj = AiPrompt.objects.get(id=prmp).delete()
    if customize_obj:
        AiPromptCustomize.objects.get(id=customize_obj).delete()
    return Response(status=204)


@api_view(['POST',])
@permission_classes([IsAuthenticated])
def image_gen(request):
    prompt = request.POST.get('prompt')
    img_resolution = request.POST.get('img_resolution',1)
    res = get_prompt_image_generations(prompt=prompt.strip(),size=img_resolution,no_of_image=1)
    if 'data' in res:
        res_url = res["data"]
        return Response({'gen_image_url': res_url},status=200) 
    else:
        return Response({'gen_image_url':res}, status=400 )





class AiCustomizeSettingViewset(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user.team.owner if request.user.team else request.user
        query_1 = CustomizationSettings.objects.filter(user = user)
        if query_1:
            ser = CustomizationSettingsSerializer(query_1.last(),context={'request':request})
            data = ser.data
        else: 
            queryset = TranslateCustomizeDetails.objects.filter(customization__user = request.user)   
            if queryset:
                target = queryset.last().target_language_id
                source = queryset.last().customization.user_text_lang_id
                mt_engine = queryset.last().mt_engine_id
                data = {'src':source,'tar':target,'mt_engine':mt_engine}
            else:
                return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(data)
                #data = {'user':user.id,'mt_engine':1,'append':True,'new_line':True}  
            #return Response({'user':None,'mt_engine':None,'append':None,'new_line':None,'src':None,'tar':None,'mt_engine':None})

    def create(self,request):
        user = request.user.team.owner if request.user.team else request.user
        serializer = CustomizationSettingsSerializer(data={**request.POST.dict(),'user':user.id})
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self,request,pk):
        user = request.user.team.owner if request.user.team else request.user
        obj = CustomizationSettings.objects.get(id = pk, user=user)
        if not obj:
            return Response({"msg":"No detail"})
        serializer = CustomizationSettingsSerializer(obj,data={**request.POST.dict(),'user':user.id},partial=True)
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        obj = CustomizationSettings.objects.filter(id = pk, user=request.user)
        if not obj:
            return Response({"msg":"No detail"})
        obj.delete()
        return Response(status=204)





@api_view(['GET',])
@permission_classes([IsAuthenticated])
def user_preffered_langs(request):
    queryset = TranslateCustomizeDetails.objects.filter(customization__user = request.user)
    if queryset:
        target = queryset.last().target_language_id
        source = queryset.last().customization.user_text_lang_id
        mt_engine = queryset.last().mt_engine_id
        return Response({'src':source,'tar':target,'mt_engine':mt_engine})
    else:
        return Response({'src':None,'tar':None,'mt_engine':None})




class AiPromptCustomizeViewset(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AiPromptCustomizeSerializer
    filter_backends = [DjangoFilterBackend ,SearchFilter,OrderingFilter]
    ordering_fields = ['id']
    ordering = ('-id')
    #filterset_class = PromptFilter
    search_fields = ['user_text','customize__customize',]
    pagination_class = NoPagination
    page_size = None

    def get_queryset(self):
        project_managers = self.request.user.team.get_project_manager if self.request.user.team else []
        owner = self.request.user.team.owner if self.request.user.team  else self.request.user
        queryset = AiPromptCustomize.objects.filter(Q(user=self.request.user)|Q(created_by=self.request.user)|Q(created_by__in=project_managers)|Q(user=owner))
        return queryset


class AiImageHistoryViewset(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ImageGeneratorPromptSerializer
    filter_backends = [DjangoFilterBackend ,SearchFilter,OrderingFilter]
    ordering_fields = ['id']
    ordering = ('-id')
    # pagination_class = AiImageHistoryPagination
    #filterset_class = PromptFilter
    search_fields = ['prompt',]
    pagination_class = NoPagination
    page_size = None
    #paginate_by=20

    def get_queryset(self):
        project_managers = self.request.user.team.get_project_manager if self.request.user.team else []
        owner = self.request.user.team.owner if self.request.user.team  else self.request.user
        queryset = ImageGeneratorPrompt.objects.filter(Q(gen_img__user=self.request.user)|Q(gen_img__created_by=self.request.user)|Q(gen_img__created_by__in=project_managers)|Q(gen_img__user=owner))
        return queryset


class ImageGeneratorPromptDelete(generics.DestroyAPIView):
    queryset = ImageGeneratorPrompt.objects.all()
    serializer_class = ImageGeneratorPromptSerializer
    lookup_field = 'pk'


@api_view(['GET',])
@permission_classes([IsAuthenticated])
def download_ai_image_generated_file(request,id):
    try:
        file = ImageGenerationPromptResponse.objects.get(id=id).generated_image 
        return download_file(file.path)
    except:
        return Response({'msg':'Requested file not exists'},status=401)



class BlogCreationViewset(viewsets.ViewSet):

    def retrieve(self, request,pk=None):
        query_set = BlogCreation.objects.get(id=pk)
        serializer = BlogCreationSerializer(query_set )
        return Response(serializer.data)

    def list(self,request):
        query_set = BlogCreation.objects.all()
        serializer = BlogCreationSerializer(query_set,many=True)
        return Response(serializer.data)
    
    def create(self,request):
        categories = 10
        sub_categories = 61
        user = request.user.team.owner if request.user.team else request.user
        serializer = BlogCreationSerializer(data={**request.POST.dict(),'categories':categories,'sub_categories':sub_categories,'created_by':request.user.id,'user':user.id} ) 
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def update(self,request,pk):
        selected_keywords_list=request.POST.getlist('selected_keywords_list',None)
        unselected_keywords_list=request.POST.getlist('unselected_keywords_list',None)
        query_set = BlogCreation.objects.get(id = pk)
        serializer = BlogCreationSerializer(query_set,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    def delete(self,request,pk):
        obj = BlogCreation.objects.get(id=pk)
        obj.delete()
        return Response(status=204)

class BlogKeywordGenerateViewset(viewsets.ViewSet):
 
    def retrieve(self, request,pk=None):
        query_set = BlogKeywordGenerate.objects.get(id=pk)
        serializer = BlogKeywordGenerateSerializer(query_set )
        return Response(serializer.data)
    
    def list(self, request):
        blog_creation = request.GET.get('blog')
        query_set=BlogKeywordGenerate.objects.filter(blog_creation=blog_creation).order_by('-id')
        serializer=BlogKeywordGenerateSerializer(query_set,many=True)
        return Response(serializer.data)

    def create(self,request):
        serializer = BlogKeywordGenerateSerializer(data=request.POST.dict()) 
        if serializer.is_valid():
            serializer.save()
            ins = serializer.data.get('blog_creation')
            queryset = BlogKeywordGenerate.objects.filter(blog_creation = ins).order_by('-id')
            ser2=BlogKeywordGenerateSerializer(queryset,many=True)
            return Response(ser2.data)
        return Response(serializer.errors)

    def update(self,request,pk):
        query_set = BlogKeywordGenerate.objects.get(id = pk)
        serializer = BlogKeywordGenerateSerializer(query_set,data=request.data,partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

class BlogtitleViewset(viewsets.ViewSet):
    def create(self,request):
        blog_inst = request.POST.get('blog_creation_gen',None)
        sub_categories = 62
        serializer = BlogtitleSerializer(data={**request.POST.dict(),'sub_categories':sub_categories})  
        if serializer.is_valid():
            serializer.save()
            blog_creation=BlogCreation.objects.filter(id=blog_inst).last()
            blog_title_ins=Blogtitle.objects.filter(blog_creation_gen=blog_creation).order_by('-id')
            ser = BlogtitleSerializer(blog_title_ins,many=True)
            return Response(ser.data)
        return Response(serializer.errors)

    def list(self, request):
        query_set=Blogtitle.objects.all()
        serializer=BlogtitleSerializer(query_set,many=True)
        return Response(serializer.data)

    def retrieve(self, request,pk=None):
        query_set = Blogtitle.objects.get(id=pk)
        serializer=BlogtitleSerializer(query_set )
        return Response(serializer.data)
    
    def update(self,request,pk):
        selected_title= request.POST.get('selected_title',None)
        unselected_title=request.POST.get('unselected_title',None)
        query_set = Blogtitle.objects.get(id = pk)
        serializer = BlogtitleSerializer(query_set,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    def delete(self,request,pk):
        obj = Blogtitle.objects.get(id=pk)
        obj.delete()
        return Response(status=204)

class BlogOutlineViewset(viewsets.ViewSet):

    def create(self,request):
        sub_categories = 63
        serializer = BlogOutlineSerializer(data={**request.POST.dict(),'sub_categories':sub_categories}) 
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
    
    def list(self, request):
        query_set=BlogOutline.objects.all()
        serializer=BlogOutlineSerializer(query_set,many=True)
        return Response(serializer.data)

    def retrieve(self, request,pk=None):
        query_set = BlogOutline.objects.get(id=pk)
        serializer=BlogOutlineSerializer(query_set )
        return Response(serializer.data)

    def update(self,request,pk):
        select_group=request.POST.get('select_group',None)
        query_set = BlogOutline.objects.get(id = pk)
        serializer = BlogOutlineSerializer(query_set,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)


class BlogOutlineSessionViewset(viewsets.ViewSet):

    def list(self, request):
        #blog_outline_gen_id = request.POST.get('blog_outline_gen_id',None)
        group = request.GET.get('group',None)
        title = request.GET.get('blog_title',None)
        
        if title and group:
            #blog_out_ins = BlogOutline.objects.get(id =blog_outline_gen_id)
            blog_out_sec = BlogOutlineSession.objects.filter(blog_title_id = title,group=group).order_by('custom_order')
            serializer=BlogOutlineSessionSerializer(blog_out_sec,many=True)

        elif title:
            #blog_out_ins = BlogOutline.objects.get(id =blog_outline_gen_id)
            blog_out_sec = BlogOutlineSession.objects.filter(blog_title_id = title).order_by('id')
            serializer=BlogOutlineSessionSerializer(blog_out_sec,many=True)
            
        else:
            query_set=BlogOutlineSession.objects.all().order_by('id')
            serializer=BlogOutlineSessionSerializer(query_set,many=True)
        return Response(serializer.data)

    def retrieve(self, request,pk=None):
        query_set = BlogOutlineSession.objects.get(id=pk)
        serializer=BlogOutlineSessionSerializer(query_set )
        return Response(serializer.data)

    def create(self,request):
        serializer = BlogOutlineSessionSerializer(data=request.POST.dict()) 
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def update(self,request,pk):
        selected = request.POST.getlist('selected')
        unselected = request.POST.getlist('unselected')
        order_list = request.POST.get('order_list')
        query_set = BlogOutlineSession.objects.get(id = pk)
        print('qs------->',query_set)
        serializer = BlogOutlineSessionSerializer(query_set,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)
        
    def delete(self,request,pk=None):
        group = request.GET.get('group')
        title = request.GET.get('blog_title')
        if pk:
            obj = BlogOutlineSession.objects.get(id=pk)
            obj.delete()
        else:
            queryset = BlogOutlineSession.objects.filter(blog_title = title).filter(group=group).delete()
        return Response(status=204)
        
class BlogArticleViewset(viewsets.ViewSet):

    def list(self,request):
        blog_creation = request.GET.get('blog_creation')
        query_set=BlogArticle.objects.filter(blog_creation_id = blog_creation).last()
        serializer=BlogArticleSerializer(query_set)
        return Response(serializer.data)

    def create(self,request):
        pass
        # sub_categories = 64
        # outline_list = request.POST.get('outline_section_list')
        # blog_creation = request.POST.get('blog_creation')
        # outline_section_list = list(map(int, outline_list.split(',')))
        # print("outline_section_list------------>",outline_section_list)
        # serializer = BlogArticleSerializer(data={'blog_creation':blog_creation,'sub_categories':sub_categories,'outline_section_list':outline_section_list}) 
        # if serializer.is_valid():
        #     serializer.save()
        #     return Response(serializer.data)
        # return Response(serializer.errors)
    
    def update(self,request, pk):
        doc = request.POST.get('document')
        sub_categories = 64
        print("Doc------>",doc)
        bc_obj = BlogCreation.objects.get(id = pk)
        bc_obj.document_id = doc
        bc_obj.save()
        query_set=BlogArticle.objects.filter(blog_creation_id = pk).last()
        print("Qr--------->",query_set)
        serializer=BlogArticleSerializer(query_set,data = {'blog_creation':pk,'document':doc,'sub_categories':sub_categories},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)


class BookTitleViewset(viewsets.ViewSet):

    def list(self, request):
        query_set=BookTitle.objects.all()
        serializer=BookTitleSerializer(query_set,many=True)
        return Response(serializer.data)

    def retrieve(self, request,pk=None):
        query_set = BookTitle.objects.get(id=pk)
        serializer=BookTitleSerializer(query_set )
        return Response(serializer.data)

    def create(self,request):
        book_inst = request.POST.get('book_creation',None)
        sub_categories = 66
        serializer = BookTitleSerializer(data={**request.POST.dict(),'sub_categories':sub_categories})  
        if serializer.is_valid():
            serializer.save()
            book_creation=BookCreation.objects.filter(id=book_inst).last()
            book_title_ins=BookTitle.objects.filter(book_creation=book_creation)
            ser = BookTitleSerializer(book_title_ins,many=True)
            return Response(ser.data)
        return Response(serializer.errors)
    
    def update(self,request,pk):
        query_set = BookTitle.objects.get(id = pk)
        serializer = BookTitleSerializer(query_set,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    def delete(self,request,pk):
        obj = BookTitle.objects.get(id=pk)
        obj.delete()
        return Response(status=204)

class BookCreationViewset(viewsets.ViewSet):

    def list(self, request):
        user = request.user.team.owner if request.user.team else request.user 
        query_set=BookCreation.objects.filter(user=user).order_by('-id')
        serializer=BookCreationSerializer(query_set,many=True)
        return Response(serializer.data)

    def retrieve(self, request,pk=None):
        query_set = BookCreation.objects.get(id=pk)
        serializer=BookCreationSerializer(query_set )
        return Response(serializer.data)

    def create(self,request):
        categories = 11
        #sub_categories = 61
        user = request.user.team.owner if request.user.team else request.user
        serializer = BookCreationSerializer(data={**request.POST.dict(),'categories':categories,'created_by':request.user.id,'user':user.id} ) 
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
    
    def update(self,request,pk):
        query_set = BookCreation.objects.get(id = pk)
        serializer = BookCreationSerializer(query_set,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    def delete(self,request,pk):
        obj = BookCreation.objects.get(id=pk)
        obj.project.delete()
        obj.delete()
        return Response(status=204)


class BookBodyViewset(viewsets.ViewSet):

    def list(self, request):
        group = request.GET.get('group',0)
        title = request.GET.get('book_title',None)
        if title and group:
            query_set = BookBody.objects.filter(book_title_id = title,group=group).order_by('custom_order')
        else:
            query_set=BookBody.objects.all()
        serializer=BookBodySerializer(query_set,many=True)
        return Response(serializer.data)

    def retrieve(self, request,pk=None):
        query_set = BookBody.objects.get(id=pk)
        serializer=BookBodySerializer(query_set)
        return Response(serializer.data)

    def create(self,request):
        categories = 11   
        body_matter = request.POST.get('body_matter',1)
        book_title = request.POST.get('book_title',None)
        sub_categories = 67 if int(body_matter) == 1 else 68
        user = request.user.team.owner if request.user.team else request.user
        serializer = BookBodySerializer(data={**request.POST.dict(),'body_matter':body_matter,'sub_categories':sub_categories,'created_by':request.user.id,'user':user.id} ) 
        if serializer.is_valid():
            serializer.save()
            # qr = BookBody.objects.filter(book_title_id=book_title,body_matter_id=body_matter).order_by('custom_order')
            # ser = BookBodySerializer(qr,many=True)
            return Response(serializer.data)
        return Response(serializer.errors)
    
    def update(self,request,pk):
        query_set = BookBody.objects.get(id = pk)
        serializer = BookBodySerializer(query_set,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    def delete(self,request,pk):
        obj = BookBody.objects.get(id=pk)
        obj.delete()
        return Response(status=204)



class BookFMViewset(viewsets.ViewSet):

    def list(self, request):
        user = request.user.team.owner if request.user.team else request.user
        query_set=BookFrontMatter.objects.filter(book_creation__user=request.user).order_by('custom_order')
        serializer=BookFrontMatterSerializer(query_set,many=True)
        return Response(serializer.data)

    def retrieve(self, request,pk=None):
        query_set = BookFrontMatter.objects.get(id=pk)
        serializer=BookFrontMatterSerializer(query_set)
        return Response(serializer.data)

    def create(self,request):
        categories = 11
        sub_categories = 68
        front_matter = request.POST.get('front_matter',1)
        user = request.user.team.owner if request.user.team else request.user
        serializer = BookFrontMatterSerializer(data={**request.POST.dict(),'front_matter':front_matter,'sub_categories':sub_categories,'created_by':request.user.id,'user':user.id} ) 
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
    
    def update(self,request,pk):
        query_set = BookFrontMatter.objects.get(id = pk)
        serializer = BookFrontMatterSerializer(query_set,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    def delete(self,request,pk):
        obj = BookFrontMatter.objects.get(id=pk)
        obj.delete()
        return Response(status=204)


class BookBMViewset(viewsets.ViewSet):

    def list(self, request):
        query_set=BookBackMatter.objects.all()
        serializer=BookBackMatterSerializer(query_set,many=True)
        return Response(serializer.data)

    def retrieve(self, request,pk=None):
        query_set = BookBackMatter.objects.get(id=pk)
        serializer=BookBackMatterSerializer(query_set)
        return Response(serializer.data)

    def create(self,request):
        categories = 11
        sub_categories = 69
        back_matter = request.POST.get('back_matter',1)
        user = request.user.team.owner if request.user.team else request.user
        serializer = BookBackMatterSerializer(data={**request.POST.dict(),'back_matter':back_matter,'sub_categories':sub_categories,'created_by':request.user.id,'user':user.id} ) 
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
    
    def update(self,request,pk):
        query_set = BookBackMatter.objects.get(id = pk)
        serializer = BookBackMatterSerializer(query_set,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    def delete(self,request,pk):
        obj = BookBackMatter.objects.get(id=pk)
        obj.delete()
        return Response(status=204)



from django.http import StreamingHttpResponse,JsonResponse
import openai,tiktoken,time,os  #blog_cre_id list
from ai_staff.models import PromptSubCategories
from rest_framework import serializers
from ai_openai.serializers import lang_detector
 
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
encoding = tiktoken.encoding_for_model('gpt-3.5-turbo')

from ai_openai.models import MyDocuments
from ai_openai.utils import get_prompt_gpt_turbo_1106
from ai_openai.models import NewsPrompt



import json

@api_view(['GET'])
def newscontentbuilder(request):
    sentence =  request.query_params.get('sentence')
    news_prompt = request.query_params.get('news_prompt')
    news_prompt_instance = NewsPrompt.objects.get(id = news_prompt)
    prompt_template = """Context: {context}

    
    {prompt}
    """
    
    if news_prompt_instance.name:
 
        prompt_template = prompt_template.format(context=sentence,prompt=news_prompt_instance.prompt)
        messages = [{"role":"system","content":news_prompt_instance.assistant},
                    {"role": "user", "content":prompt_template}]
        completion = get_prompt_gpt_turbo_1106(messages=messages)
        result = completion['choices'][0]['message']['content']
        res = json.loads(result)
    return Response({'id':news_prompt_instance.id ,'sentence':sentence , 'result':res})
    


def num_tokens_from_string(string) -> int:
    print("openai____",string)
    num_tokens = len(encoding.encode(string))
    token_usage=get_consumable_credits_for_openai_text_generator(num_tokens)
    return token_usage

@api_view(['GET'])
def blog_crt(request):
    instance=request.query_params.get('blog_creation_instance')
    title = instance.blog_creation.user_title
    detected_lang = lang_detector(title)
    if detected_lang!='en':
        title = instance.blog_creation.user_title_mt
    article = instance.blog_article_mt if instance.blog_creation.user_language_code != 'en' else instance.blog_article
    tt = MyDocuments.objects.create(doc_name=title,blog_data = article,document_type_id=2,ai_user=instance.blog_creation.user)
    instance.document = tt
    return Response({'id':tt.id})



@api_view(["GET"])
def credit_check_blog(request):
    if request.method=='GET':
        blog_id=request.query_params.get('blog_id')
        blog_creation=BlogCreation.objects.get(id=blog_id)
        initial_credit = request.user.credit_balance.get("total_left")
        if blog_creation.user_language_code != 'en':
            credits_required = 2500
        else:
            credits_required = 200
        if initial_credit < credits_required:
            raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
        else:
            return Response({'msg':'sufficient Credits'},status=200)

            

@api_view(["GET"])
def generate_article(request):
    if request.method=='GET':
        blog_available_langs=[17]
        sub_categories=64
        blog_article_start_phrase=PromptSubCategories.objects.get(id=sub_categories).prompt_sub_category.first().start_phrase
        outline_list=request.query_params.get('outline_section_list')
        blog_creation=request.query_params.get('blog_creation')
 
        blog_creation=BlogCreation.objects.get(id=blog_creation)
        outline_section_list=list(map(int,outline_list.split(',')))
        outline_section_list=BlogOutlineSession.objects.filter(id__in=outline_section_list)

        instance = BlogArticle.objects.create(blog_creation=blog_creation,sub_categories_id=sub_categories)

        initial_credit = instance.blog_creation.user.credit_balance.get("total_left")
        if instance.blog_creation.user_language_code != 'en':
            credits_required = 2500
        else:
            credits_required = 200
        if initial_credit < credits_required:
            raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)

        title = instance.blog_creation.user_title
        detected_lang = lang_detector(title)
        if detected_lang!='en':
            title = instance.blog_creation.user_title_mt
        
        keyword = instance.blog_creation.keywords 
        detected_lang = lang_detector(keyword)
        if detected_lang!='en':
            keyword = instance.blog_creation.keywords_mt


        print("OutlineSelection---------------->",outline_section_list)
        if outline_section_list:
            detected_lang = lang_detector(outline_section_list[0].blog_outline)
        else: raise serializers.ValidationError({'msg':'No Outlines Selected'}, code=400)


        if detected_lang!='en':
            outlines = [i.blog_outline_mt for i in outline_section_list if i.blog_outline_mt ]
        else:
            outlines = [i.blog_outline for i in outline_section_list]


        joined_list = "', '".join(outlines)

        selected_outline_section_list = f"'{joined_list}'"

        print("Selected------------>",selected_outline_section_list)
        print("title----->>",title)
        prompt = blog_article_start_phrase.format(title,selected_outline_section_list,keyword,instance.blog_creation.tone.tone)

        print("prompt____article--->>>>",prompt)
        
        #title='# '+title
        if blog_creation.user_language_code== 'en':
            completion=openai.ChatCompletion.create(model="gpt-3.5-turbo",messages=[{"role":"user","content":prompt}],stream=True)
            def stream_article_response_en(title):
                str_con=""
                for chunk in completion:
                    ins=chunk['choices'][0]
                    if ins["finish_reason"]!='stop':
                        delta=ins['delta']
                        if 'content' in delta.keys():
                            content=delta['content']
                            word=content+' '
                            str_con+=content
                            yield '\ndata: {}\n\n'.format({"t":content})
                    else:
                        token_usage=num_tokens_from_string(str_con+" "+prompt)
                        print("Token Usage----------->",token_usage)
                        AiPromptSerializer().customize_token_deduction(instance.blog_creation,token_usage)
                        print("token_usage---------->>",token_usage)
                        # article = instance.blog_article_mt if instance.blog_creation.user_language_code != 'en' else instance.blog_article
                        # tt = MyDocuments.objects.create(doc_name=title,blog_data = article,document_type_id=2,ai_user=instance.blog_creation.user)
                        # instance.document = tt
                        # instance.save()
            return StreamingHttpResponse(stream_article_response_en(title),content_type='text/event-stream')
        else:
            completion=openai.ChatCompletion.create(model="gpt-3.5-turbo",messages=[{"role":"user","content":prompt}],stream=True)
            def stream_article_response_other_lang(title):
                arr=[]
                str_cont=''
                for chunk in completion:
                    ins=chunk['choices'][0]
                    if ins["finish_reason"]!='stop':
                        delta=ins['delta']
                        if 'content' in delta.keys():
                            content=delta['content']
                            word=content
                            str_cont+=content########
                            print(str_cont)
                            if "." in word or "\n" in word:
                                if "\n" in word:
                                    new_line_split=word.split("\n")
                                    arr.append(new_line_split[0]+'\n')
                                    str_cont+='\n' #####
                                    text=" ".join(arr)
                                    consumable_credits_for_article_gen = get_consumable_credits_for_text(str_cont,instance.blog_creation.user_language_code,'en')
                                    consumable = max(round(consumable_credits_for_article_gen/3),1) 
                                    print("Consumable--------->",consumable)
                                    print("consumable_credits_for_article_gen--------->",consumable_credits_for_article_gen)
                                    token_usage=num_tokens_from_string(str_cont)
                                    AiPromptSerializer().customize_token_deduction(instance.blog_creation,token_usage)
                                    #print("StrContent------------->",str_cont) 
                                    if initial_credit >= consumable:
                                        print("Str----------->",str_cont)
                                        blog_article_trans=get_translation(1,str_cont,"en",blog_creation.user_language_code,user_id=blog_creation.user.id,cc=consumable)
                                        #AiPromptSerializer().customize_token_deduction(instance.blog_creation,consumable_credits_for_article_gen)
                                    yield '\ndata: {}\n\n'.format({"t":blog_article_trans})                                    
                                    arr=[]
                                    str_cont='' #####
                                    arr.append(new_line_split[-1])
                                elif "." in word:
                                    sente=" ".join(arr)
                                    if sente[-1]!='.':
                                        sente=sente+'.'
                                        consumable_credits_for_article_gen = get_consumable_credits_for_text(str_cont,instance.blog_creation.user_language_code,'en')
                                        consumable = max(round(consumable_credits_for_article_gen/3),1) 
                                        print("Consumable--------->",consumable)
                                        print("consumable_credits_for_article_gen--------->",consumable_credits_for_article_gen)
                                        token_usage=num_tokens_from_string(str_cont)
                                        AiPromptSerializer().customize_token_deduction(instance.blog_creation,token_usage)
                                        #print("StrContent------------->",str_cont) 
                                        if initial_credit >= consumable:
                                            #print("StrContent------------->",str_cont)
                                            blog_article_trans=get_translation(1,str_cont,"en",blog_creation.user_language_code,user_id=blog_creation.user.id,cc=consumable)
                                            #AiPromptSerializer().customize_token_deduction(instance.blog_creation,consumable_credits_for_article_gen)
                                        yield '\ndata: {}\n\n'.format({"t":blog_article_trans})
                                    else:
                                    # blog_article_trans=markdowner.convert(blog_article_trans)
                                        yield '\ndata: {}\n\n'.format({"t":blog_article_trans})
                                    arr=[]
                                    str_cont='' ######
                            else:
                                arr.append(word)
                    else:
                        token_usage=num_tokens_from_string(prompt)
                        print("prompt",prompt)
                        print("tot_us",token_usage)
                        AiPromptSerializer().customize_token_deduction(instance.blog_creation,token_usage)
                        print("finished")
                        # article = instance.blog_article_mt if instance.blog_creation.user_language_code != 'en' else instance.blog_article
                        # tt = MyDocuments.objects.create(doc_name=title,blog_data = article,document_type_id=2,ai_user=instance.blog_creation.user)
                        # instance.document = tt
                        # instance.save()
            return StreamingHttpResponse(stream_article_response_other_lang(title),content_type='text/event-stream')
    return JsonResponse({'error':'Method not allowed.'},status=405)


from ai_openai.models import BookBody
from ai_staff.models import PromptStartPhrases
@api_view(["GET"])
def generate_chapter(request):
    if request.method=='GET':
        bookbody_id=request.query_params.get('bookbody_id')
        book_body_instance = BookBody.objects.get(id=bookbody_id)
        # book_phrase = PromptStartPhrases.objects.get(sub_category=book_body_instance.sub_categories)
        book_title =book_body_instance.book_creation.title_mt if book_body_instance.book_creation.title_mt else book_body_instance.book_creation.title
        generated_content =book_body_instance.generated_content_mt if book_body_instance.generated_content_mt else book_body_instance.generated_content
        book_level = book_body_instance.book_creation.level.level
        book_description = book_body_instance.book_creation.description_mt if book_body_instance.book_creation.description_mt else book_body_instance.book_creation.description
        author_info =book_body_instance.book_creation.author_info_mt if book_body_instance.book_creation.author_info_mt else book_body_instance.book_creation.author_info
        print("-------",book_title)
        print(generated_content)
        print(book_level)
        print(book_description)
        print(author_info)
        sub_cat = 71
        prompt =  PromptStartPhrases.objects.get(id=sub_cat).start_phrase
        prompt = prompt.format(generated_content,book_title,book_description,book_level,author_info)
        print(prompt)

        initial_credit = book_body_instance.book_creation.user.credit_balance.get("total_left")
        if book_body_instance.book_creation.book_language_code != 'en':
            credits_required = 2500
        else:
            credits_required = 200
        if initial_credit < credits_required:
            raise serializers.ValidationError({'msg':'Insufficient Credits'}, code=400)
        language_code = book_body_instance.book_creation.book_language_code
        if language_code == 'en':
            completion=openai.ChatCompletion.create(model="gpt-3.5-turbo",messages=[{"role":"user","content":prompt}],stream=True)
            def stream_article_response_en(title):
                str_con=""
                for chunk in completion:
                    ins=chunk['choices'][0]
                    if ins["finish_reason"]!='stop':
                        delta=ins['delta']
                        if 'content' in delta.keys():
                            content=delta['content']
                            word=content+' '
                            str_con+=content
                            yield '\ndata: {}\n\n'.format({"t":content})
                    else:
                        token_usage=num_tokens_from_string(str_con+" "+prompt)
                        print("Token Usage----------->",token_usage)
                        AiPromptSerializer().customize_token_deduction(book_body_instance.book_creation,token_usage)
                        print("token_usage---------->>",token_usage)
            return StreamingHttpResponse(stream_article_response_en(book_title),content_type='text/event-stream')
        else:
            completion=openai.ChatCompletion.create(model="gpt-3.5-turbo",messages=[{"role":"user","content":prompt}],stream=True)
            def stream_article_response_other_lang(title):
                arr=[]
                str_cont=''
                for chunk in completion:
                    ins=chunk['choices'][0]
                    if ins["finish_reason"]!='stop':
                        delta=ins['delta']
                        if 'content' in delta.keys():
                            content=delta['content']
                            word=content
                            str_cont+=content########
                            #print(str_cont)
                            if "." in word or "\n" in word:
                                if "\n" in word:
                                    new_line_split=word.split("\n")
                                    arr.append(new_line_split[0]+'\n')
                                    str_cont+='\n' #####
                                    text=" ".join(arr)
                                    consumable_credits_for_article_gen = get_consumable_credits_for_text(str_cont,language_code,'en')
                                    consumable = max(round(consumable_credits_for_article_gen/3),1) 
                                    print("Consumable--------->",consumable)
                                    print("consumable_credits_for_article_gen--------->",consumable_credits_for_article_gen)
                                    token_usage=num_tokens_from_string(str_cont)
                                    AiPromptSerializer().customize_token_deduction(book_body_instance.book_creation,token_usage)
                                    #print("StrContent------------->",str_cont) 
                                    if initial_credit >= consumable:
                                        print("Str----------->",str_cont)
                                        blog_article_trans=get_translation(1,str_cont,"en",language_code,user_id=book_body_instance.book_creation.user.id,cc=consumable)
                                        #AiPromptSerializer().customize_token_deduction(instance.blog_creation,consumable_credits_for_article_gen)
                                    yield '\ndata: {}\n\n'.format({"t":blog_article_trans})                                    
                                    arr=[]
                                    str_cont='' #####
                                    arr.append(new_line_split[-1])
                                elif "." in word:
                                    sente=" ".join(arr)
                                    if sente[-1]!='.':
                                        sente=sente+'.'
                                        consumable_credits_for_article_gen = get_consumable_credits_for_text(str_cont,language_code,'en')
                                        consumable = max(round(consumable_credits_for_article_gen/3),1) 
                                        token_usage=num_tokens_from_string(str_cont)
                                        AiPromptSerializer().customize_token_deduction(book_body_instance.book_creation,token_usage)
                                        #print("StrContent------------->",str_cont) 
                                        if initial_credit >= consumable:
                                            #print("StrContent------------->",str_cont)
                                            blog_article_trans=get_translation(1,str_cont,"en",language_code,user_id=book_body_instance.book_creation.user.id,cc=consumable)
                                            #AiPromptSerializer().customize_token_deduction(instance.blog_creation,consumable_credits_for_article_gen)
                                        yield '\ndata: {}\n\n'.format({"t":blog_article_trans})
                                    else:
                                    # blog_article_trans=markdowner.convert(blog_article_trans)
                                        yield '\ndata: {}\n\n'.format({"t":blog_article_trans})
                                    arr=[]
                                    str_cont='' ######
                            else:
                                arr.append(word)
                    else:
                        token_usage=num_tokens_from_string(prompt)
                        AiPromptSerializer().customize_token_deduction(book_body_instance.book_creation,token_usage)
            return StreamingHttpResponse(stream_article_response_other_lang(book_title),content_type='text/event-stream')
    return JsonResponse({'error':'Method not allowed.'},status=405)




class BookBodyDetailsViewset(viewsets.ViewSet,PageNumberPagination):
    permission_classes = [IsAuthenticated,]
    page_size=20

    def get_object(self, pk):
        try:
            user = self.request.user.team.owner if self.request.user.team else self.request.user
            return BookBodyDetails.objects.get(book_bm__book_creation__user=user,id=pk)
        except BookBodyDetails.DoesNotExist:
            raise Http404
    
    def list(self, request):
        user = request.user.team.owner if request.user.team else request.user
        queryset = BookBodyDetails.objects.filter(book_bm__book_creation__user=user).order_by('-id')
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = BookBodyDetailSerializer(pagin_tc,many=True)
        response = self.get_paginated_response(serializer.data)
        return response
    
    def retrieve(self,request,pk):
        obj =self.get_object(pk)
        serializer = BookBodyDetailSerializer(obj)
        return Response(serializer.data)
    
    def create(self,request):
        serializer = BookBodyDetailSerializer(data=request.POST.dict()) 
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)


    def update(self,request,pk):
        obj =self.get_object(pk)
        serializer = BookBodyDetailSerializer(obj,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors,status=400)
        
    def destroy(self,request,pk):
        try:
            user = request.user.team.owner if request.user.team else request.user
            obj = BookBodyDetails.objects.get(book_bm__book_creation__user=user,id=pk)
            obj.delete()
            return Response({'msg':'deleted successfully'},status=200)
        except:
            return Response({'msg':'deletion unsuccessfull'},status=400)





#####for testing streaming #############
import time
@api_view(["GET"])
def generate(request):
    title="""Quantum computing is a type of computing that uses the principles of quantum mechanics to perform calculations. In traditional computers, data is represented in bits, which can be either 0 or 1. But in quantum computing, data is represented using quantum bits, or qubits.

The fascinating thing about qubits is that they can exist in multiple states at the same time due to a phenomenon called superposition. It's like a coin that can be both heads and tails simultaneously. This allows quantum computers to explore many possibilities at once, making them potentially much faster for certain types of problems.

Another important concept in quantum computing is entanglement. When qubits are entangled, the state of one qubit instantly affects the state of another, no matter the distance between them. This allows quantum computers to process information in a highly interconnected way.

Quantum computing has the potential to solve certain complex problems that are practically impossible for classical computers to tackle. For example, it could help with simulations of large molecules, optimizing complex systems, and breaking some cryptographic codes.

However, building and maintaining quantum computers is very challenging because qubits are fragile and can be easily affected by their environment, leading to errors in calculations. Scientists and researchers are actively working on overcoming these challenges to unlock the full potential of quantum computing and revolutionize various fields of science and technology.

            """ 
    if request.method=='GET':
        title=title.split(" ")
        def stream():
            for chunk in title:
                time.sleep(0.05)
                if chunk:
                    yield '\ndata: {}\n\n'.format(chunk)
                else:
                    print("stream is finished")
        return StreamingHttpResponse(stream(),content_type='text/event-stream')
    
    return JsonResponse({'error':'Method not allowed.'},status=405)

# @api_view(["GET"])
# def generate_article(request):
#     if request.method=='GET':
#         blog_available_langs=[17]
#         sub_categories=64
#         blog_article_start_phrase=PromptSubCategories.objects.get(id=sub_categories).prompt_sub_category.first().start_phrase
#         outline_list=request.query_params.get('outline_section_list')
#         blog_creation=request.query_params.get('blog_creation')
#         blog_creation=BlogCreation.objects.get(id=blog_creation)
#         outline_section_list=list(map(int,outline_list.split(',')))
#         outline_section_list=BlogOutlineSession.objects.filter(id__in=outline_section_list)
#         if blog_creation.user_language_id not in blog_available_langs:
#             title=blog_creation.user_title_mt
#             keyword=blog_creation.keywords_mt
#             outlines=list(outline_section_list.values_list('blog_outline_mt',flat=True))
#         else:
#             title=blog_creation.user_title
#             keyword=blog_creation.keywords
#             outlines=list(outline_section_list.values_list('blog_outline',flat=True))
#         joined_list = "', '".join(outlines)
#         tone=blog_creation.tone.tone
#         prompt=blog_article_start_phrase.format(title,joined_list,keyword,tone)
#         print("pmpt---->",prompt)
#         completion=openai.ChatCompletion.create(model="gpt-3.5-turbo",
#                                                 messages=[{"role":"user","content":prompt}],
#                                                 stream=True)
#         def stream_article_response():
#             for chunk in completion:
#                 ins=chunk['choices'][0]
#                 if ins["finish_reason"]!='stop':
#                     delta=ins['delta']
#                     if 'content' in delta.keys():
#                         content=delta['content']
#                         t=content+' '
#                         yield '\ndata: {}\n\n'.format(t.encode('utf-8'))
#         return StreamingHttpResponse(stream_article_response(),content_type='text/event-stream')
#     return JsonResponse({'error':'Method not allowed.'},status=405)

# from django.http import StreamingHttpResponse
# import time,json
# from django.http import JsonResponse
# text="Please generate a 700-word blog post titled '{}' with sections: {} Use keywords such as {} and a {} tone. Keep the language simple and concise. Pre-written content for the section headlines is allowed. Please format everything in Markdown and blog post sections should be in ## tag. Please generate the content as quickly as possible.".format('Cost-Saving Strategies',
#                                                                                                                                                                                                                                                                                                                                                           'Introduction and overview of vanishing gradient and backpropagation ,The problem of vanishing gradients and how it affects neural network training,Explaining backpropagation and its role in solving the vanishing gradient problem,Analyzing the mathematical concepts behind backpropagation and gradient descent',
#                                                                                                                                                                                                                                                                                                                                                           'machine learning,cost machine gpu',
#                                                                                                                                                                                                                                                                                                                                                           'professional')


# @api_view(["GET"])
# def generate(request):
#     if request.method=='GET':
#         completion=openai.ChatCompletion.create(model="gpt-3.5-turbo",messages=[{"role":"user","content":text}],stream=True)
#         def stream_article_response_en():
#             for chunk in completion:
#                 ins=chunk['choices'][0]
#                 if ins["finish_reason"]!='stop':
#                     delta=ins['delta']
#                     if 'content' in delta.keys():
#                         content=delta['content']
#                         yield '\ndata: {}\n\n'.format({"t":content})
#         return StreamingHttpResponse(stream_article_response_en(),content_type='text/event-stream')  #text/event-stream
#     return JsonResponse({'error':'Method not allowed.'},status=405)




    # response = StreamingHttpResponse(stream(), status=200, content_type='text/event-stream')
    # response['Cache-Control'] = 'no-cache'
    # return response
    # response.status_code = 200
    # return response(stream())
    #return StreamingHttpResponse(stream(), content_type='text/event-stream')
    #return JsonResponse({'error': 'Error'}, status=405)


from google.cloud import translate_v2 as translate
from html import unescape
from lxml import html


@api_view(["GET"])
def translate_html_file(request, input_file, target_language):
    # Initialize the translation client
    client = translate.Client()

    with open(input_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Parse the HTML content using lxml
    root = html.fromstring(html_content)

    # Find all text nodes and translate them
    for element in root.iter():
        if element.text:
            translated_text = client.translate(unescape(element.text), target_language=target_language)
            element.text = translated_text['translatedText']

    # Serialize the modified HTML tree back to a string
    translated_html = html.tostring(root, encoding='unicode')

    return Response({"translated_html":translated_html})


from docx import Document
from docxcompose.composer import Composer
@api_view(["POST"])
def docx_merger(request):
    punctuation='''!"#$%&'``()*+,-./:;<=>?@[\]^`{|}~_'''
    name = request.POST.get('book_name')
    files = request.FILES.getlist('docx_files')
    print("Files------------>",files)
    #composed = name + ".docx"
    composed =  name + ".docx" if len(name.split())<=5 else ' '.join(name.split()[:3]).strip(punctuation)+ ".docx"
    #files = ["big_file_test.docx", "Data.docx", "nupedia_small.docx"]
    result = Document()
    composer = Composer(result)

    for i in range(0, len(files)):
        print("File---------------->",files[i])
        doc = Document(files[i])

        if i != 0:
            doc.add_page_break()

        composer.append(doc)

    composer.save(composed)
    res = download_file(composed)
    os.remove(composed)
    return res

    
