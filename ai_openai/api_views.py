from .models import AiPrompt ,AiPromptResult
from django.http import   JsonResponse
import logging ,os
from rest_framework import viewsets,generics
from rest_framework.pagination import PageNumberPagination
from .serializers import (AiPromptSerializer ,AiPromptResultSerializer,
                                     AiPromptGetSerializer,AiPromptCustomizeSerializer)
from rest_framework.views import  Response
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
from ai_staff.models import AiCustomize ,Languages, PromptTones, LanguagesLocale
#from langdetect import detect
#import langid
from googletrans import Translator
from .utils import get_prompt ,get_prompt_edit,get_prompt_image_generations
from ai_workspace_okapi.utils import get_translation
openai_model = os.getenv('OPENAI_MODEL')
logger = logging.getLogger('django')


from string import punctuation
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
        serializer = AiPromptSerializer(data={**request.POST.dict(),'description':description,'user':self.request.user.id,'targets':targets,'response_charecter_limit':char_limit})
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
    page_size = None

    def get_queryset(self):
        prmp_id = self.request.query_params.get('prompt_id')
        #prmp_id = self.request.GET.get('prompt_id')
        if prmp_id:
            queryset = AiPrompt.objects.filter(id=prmp_id)
        else:
            queryset = AiPrompt.objects.filter(user=self.request.user)
        return queryset



def customize_response(customize ,user_text,tone,used_tokens):
    if customize.prompt or customize.customize == "Text completion":
        if customize.customize == "Text completion":
            tone_ = PromptTones.objects.get(id=tone).tone
            prompt = customize.prompt+' {} tone : '.format(tone_)+user_text#+', in {} tone.'.format(tone_)
            response = get_prompt(prompt=prompt,model_name=openai_model,max_token =150,n=1)
        else:
            if customize.grouping == "Ask":
                prompt = customize.prompt+" "+user_text+"?"
            else:
                prompt = customize.prompt+" "+user_text+"."
            response = get_prompt(prompt=prompt,model_name=openai_model,max_token =256,n=1)
        tokens = response['usage']['total_tokens']
        total_tokens = get_consumable_credits_for_openai_text_generator(tokens)
        total_tokens += used_tokens
    else:
        total_tokens = 0
        prompt = None
        response = get_prompt_edit(input_text=user_text ,instruction=customize.instruct)
    return response,total_tokens,prompt
    

@api_view(['POST',])
@permission_classes([IsAuthenticated])
def customize_text_openai(request):
    user = request.user
    document = request.POST.get('document_id')
    customize_id = request.POST.get('customize_id')
    user_text = request.POST.get('user_text')
    tone = request.POST.get('tone',1)
    customize = AiCustomize.objects.get(id =customize_id)
    detector = Translator()
    total_tokens = 0
    user_text_mt_en,txt_generated = None,None
    lang = detector.detect(user_text).lang
    user_text_lang = LanguagesLocale.objects.filter(locale_code=lang).first().language.id
    if lang!= 'en':
        initial_credit = user.credit_balance.get("total_left")
        consumable_credits_user_text =  get_consumable_credits_for_text(user_text,source_lang=lang,target_lang='en')
        if initial_credit > consumable_credits_user_text:
            user_text_mt_en = get_translation(mt_engine_id=1 , source_string = user_text,
                                        source_lang_code=lang , target_lang_code='en')
            total_tokens += get_consumable_credits_for_text(user_text_mt_en,source_lang=lang,target_lang='en')
            response,total_tokens,prompt = customize_response(customize,user_text_mt_en,tone,total_tokens)
            result_txt = response['choices'][0]['text']
            txt_generated = get_translation(mt_engine_id=1 , source_string = result_txt.strip(),
                                        source_lang_code='en' , target_lang_code=lang)
            total_tokens += get_consumable_credits_for_text(txt_generated,source_lang='en',target_lang=lang)
            AiPromptSerializer().customize_token_deduction(instance = request,total_tokens= total_tokens)
        else:
            return  Response({'msg':'Insufficient Credits'},status=400)
        
    else:##english
        response,total_tokens,prompt = customize_response(customize,user_text,tone,total_tokens)
        result_txt = response['choices'][0]['text']
    data = {'document':document,'customize':customize_id,'user':request.user.id,\
            'user_text':user_text,'user_text_mt':user_text_mt_en if user_text_mt_en else None,\
            'tone':tone,'credits_used':total_tokens,'prompt_generated':prompt,'user_text_lang':user_text_lang,\
            'api_result':result_txt.strip() if result_txt else None,'prompt_result':txt_generated}
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
    if obj:
        result = AiPromptResult.objects.get(id=obj)
        count = result.prompt.ai_prompt.all().count()
        if count>1:
            result.delete()
        else:
            result.prompt.delete()
    if prmp:
        prmb_obj = AiPrompt.objects.get(id=prmp).delete()
    return Response(status=204)


@api_view(['POST',])
@permission_classes([IsAuthenticated])
def image_gen(request):
    prompt = request.POST.get('prompt')
    res = get_prompt_image_generations(prompt=prompt.strip(),size='256x256',n=2)
    if 'data' in res:
        res_url = res["data"]
        return Response({'gen_image_url': res_url},status=200) 
    else:
        return Response({'gen_image_url':res}, status=400 )


    

























# def customize_response(customize ,user_text,tone,request):
#     if customize.prompt or customize.customize == "Text completion":
#         initial_credit = request.user.credit_balance.get("total_left")
#         if customize.customize == "Text completion":
#             tone_ = PromptTones.objects.get(id=tone).tone
#             prompt = customize.prompt+' {} tone : '.format(tone_)+user_text#+', in {} tone.'.format(tone_)
#             print("Prompt Created-------->",prompt)
#             response = get_prompt(prompt=prompt,model_name=openai_model,max_token =150,n=1)
#         else:
#             if customize.grouping == "Ask":
#                 prompt = customize.prompt+" "+user_text+"?"
#             else:
#                 prompt = customize.prompt+" "+user_text+"."
#             print("Prompt Created-------->",prompt)
#             response = get_prompt(prompt=prompt,model_name=openai_model,max_token =256,n=1)
#         total_tokens = response['usage']['total_tokens']
#         total_tokens = get_consumable_credits_for_openai_text_generator(total_tokens)
#         AiPromptSerializer().customize_token_deduction(instance = request,total_tokens=total_tokens)
#     else:
#         try:response = get_prompt_edit(input_text=user_text ,instruction=customize.instruct)
#         except:return None
#     return response 
    

# @api_view(['POST',])###########rework
# @permission_classes([IsAuthenticated])
# def customize_text_openai(request):
#     user = request.user
#     customize_id = request.POST.get('customize_id')
#     user_text = request.POST.get('user_text')
#     tone = request.POST.get('tone',1)
#     customize = AiCustomize.objects.get(id =customize_id)
#     detector = Translator()
#     lang = detector.detect(user_text).lang
#     if lang!= 'en':
#         initial_credit = user.credit_balance.get("total_left")
#         consumable_credits_user_text =  get_consumable_credits_for_text(user_text,source_lang=lang,target_lang='en')
#         #print("credits for input text----------->",consumable_credits_user_text)
#         if initial_credit > consumable_credits_user_text:
#             user_text_mt_en = get_translation(mt_engine_id=1 , source_string = user_text,
#                                         source_lang_code=lang , target_lang_code='en')
#             consumable_credits_txt_generated = get_consumable_credits_for_text(user_text_mt_en,source_lang=lang,target_lang='en')
#             #print("credits for mt------------>",consumable_credits_txt_generated)
#             response = customize_response(customize,user_text_mt_en,tone,request)
#             result_txt = response['choices'][0]['text']
#             #print("openai_result--------->",result_txt)
#             txt_generated = get_translation(mt_engine_id=1 , source_string = result_txt.strip(),
#                                         source_lang_code='en' , target_lang_code=lang)
#             #print("credits for result mt---------> ",get_consumable_credits_for_text(txt_generated,source_lang='en',target_lang=lang))
#             consumable_credits_txt_generated += get_consumable_credits_for_text(txt_generated,source_lang='en',target_lang=lang)
#             #print("Tot----------->",consumable_credits_txt_generated)
#             AiPromptSerializer().customize_token_deduction(instance = request,total_tokens= consumable_credits_txt_generated)
            
#         else:
#             return  Response({'msg':'Insufficient Credits'},status=400)
        
#     else:##english
#         response = customize_response(customize,user_text,tone,request)
#         if response:txt_generated = response['choices'][0]['text']
#         else:txt_generated = 'Something Went Wrong.Try Again'
#         #print("Txt------>",txt_generated.strip())
#     #total_tokens = response['usage']['total_tokens']
#     return Response({'customize_text': txt_generated.strip() ,'lang':lang ,'customize_cat':customize.customize},status=200)