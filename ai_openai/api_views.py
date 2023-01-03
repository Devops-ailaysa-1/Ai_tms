from .models import AiPrompt ,AiPromptResult
from django.http import   JsonResponse
import logging ,os
from rest_framework import viewsets,generics
from rest_framework.pagination import PageNumberPagination
from .serializers import (AiPromptSerializer ,AiPromptResultSerializer,
                                     AiPromptGetSerializer)
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
from ai_staff.models import AiCustomize ,Languages
from langdetect import detect
from .utils import get_prompt ,get_prompt_edit
from ai_workspace_okapi.utils import get_translation
openai_model = os.getenv('OPENAI_MODEL')
logger = logging.getLogger('django')



class AiPromptViewset(viewsets.ViewSet):
    model = AiPrompt

    def get(self, request):
        query_set = self.model.objects.all()
        serializer = AiPromptSerializer(query_set ,many =True)
        return Response(serializer.data)

    def create(self,request):
        # keywords = request.POST.getlist('keywords')
        targets = request.POST.getlist('get_result_in')
        char_limit = request.POST.get('response_charecter_limit',256)
        serializer = AiPromptSerializer(data={**request.POST.dict(),'user':self.request.user.id,'targets':targets,'response_charecter_limit':char_limit})
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



def customize_response(customize ,user_text,request):
    if customize.prompt:
        initial_credit = request.user.credit_balance.get("total_left")
        response = get_prompt(prompt=customize.prompt+" "+user_text,model_name=openai_model,max_token =256,n=1)
        total_tokens = response['usage']['total_tokens']
        total_tokens = get_consumable_credits_for_openai_text_generator(total_tokens)
        AiPromptSerializer().customize_token_deduction(instance = request,total_tokens=total_tokens)
    else:
        response = get_prompt_edit(input_text=user_text ,instruction=customize.customize)
    return response 
    

@api_view(['POST',])
@permission_classes([IsAuthenticated])
def customize_text_openai(request):
    user = request.user
    customize_id = request.POST.get('customize_id')
    user_text = request.POST.get('user_text')
    customize = AiCustomize.objects.get(id =customize_id)
    lang = detect(user_text)
    
    if lang!= 'en':
        initial_credit = user.credit_balance.get("total_left")
        consumable_credits_user_text =  get_consumable_credits_for_text(user_text,source_lang=lang,target_lang='en')
        #print("credits for input text----------->",consumable_credits_user_text)
        if initial_credit > consumable_credits_user_text:
            user_text_mt_en = get_translation(mt_engine_id=1 , source_string = user_text,
                                        source_lang_code=lang , target_lang_code='en')
            consumable_credits_txt_generated = get_consumable_credits_for_text(user_text_mt_en,source_lang=lang,target_lang='en')
            #print("credits for mt------------>",consumable_credits_txt_generated)
            response = customize_response(customize,user_text_mt_en,request)
            result_txt = response['choices'][0]['text']
            #print("openai_result--------->",result_txt)
            txt_generated = get_translation(mt_engine_id=1 , source_string = result_txt,
                                        source_lang_code='en' , target_lang_code=lang)
            #print("credits for result mt---------> ",get_consumable_credits_for_text(txt_generated,source_lang='en',target_lang=lang))
            consumable_credits_txt_generated += get_consumable_credits_for_text(txt_generated,source_lang='en',target_lang=lang)
            #print("Tot----------->",consumable_credits_txt_generated)
            AiPromptSerializer().customize_token_deduction(instance = request,total_tokens= consumable_credits_txt_generated)
            
        else:
            return  Response({'msg':'Insufficient Credits'},status=400)
        
    else:##english
        response = customize_response(customize,user_text,request)
        txt_generated = response['choices'][0]['text']
    #total_tokens = response['usage']['total_tokens']
    return Response({'customize_text': txt_generated ,'lang':lang ,'customize_cat':customize.customize},status=200)

 

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

