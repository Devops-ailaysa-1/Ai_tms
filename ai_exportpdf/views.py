from ai_exportpdf.models import (Ai_PdfUpload ,AiPrompt ,AiPromptResult)
from django.http import   JsonResponse
import logging ,os
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from ai_exportpdf.serializer import (PdfFileSerializer ,PdfFileStatusSerializer ,
                                     AiPromptSerializer ,AiPromptResultSerializer,
                                     AiPromptGetSerializer)
from rest_framework.views import  Response
from rest_framework.decorators import permission_classes ,api_view
from rest_framework.permissions  import IsAuthenticated
from ai_exportpdf.utils import pdf_conversion
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from ai_workspace_okapi.utils import download_file
from ai_exportpdf.utils import (get_consumable_credits_for_pdf_to_docx ,file_pdf_check,\
                                get_consumable_credits_for_openai_text_generator)
from ai_auth.models import UserCredits
from ai_workspace.api_views import UpdateTaskCreditStatus
from django.core.files.base import ContentFile
from .utils import ai_export_pdf,convertiopdf2docx
from ai_workspace.models import Task
from ai_staff.models import AiCustomize ,Languages
from langdetect import detect
from ai_exportpdf.utils import get_prompt 
from ai_workspace_okapi.utils import get_translation
openai_model = os.getenv('OPENAI_MODEL')

logger = logging.getLogger('django')
google_ocr_indian_language = ['bengali','hindi','kannada','malayalam','marathi','punjabi','tamil','telugu']

class Pdf2Docx(viewsets.ViewSet, PageNumberPagination):
    permission_classes = [IsAuthenticated]
    page_size = 20
    serializer_class = PdfFileSerializer
    serializer = PdfFileSerializer
    search_fields = ['pdf_file_name' , 'status']
    filterset_fields = ['status','pdf_language']
    #filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]

    def list(self, request):
        task = request.GET.get('task',None)
        ids = request.query_params.getlist('id',None)
        user = request.user
        if ids:
            queryset = Ai_PdfUpload.objects.filter(id__in = ids)
            serializer = PdfFileSerializer(queryset,many=True)
            return Response(serializer.data)
        if task:
            task_obj = Task.objects.get(id=task)
            queryset = task_obj.pdf_task.last()
            serializer = PdfFileSerializer(queryset)
            return Response(serializer.data)
        else:
            query_filter = Ai_PdfUpload.objects.filter(user = user).filter(task_id=None).order_by('-id') 
            queryset = self.filter_queryset(query_filter)
            pagin_tc = self.paginate_queryset(queryset, request , view=self)
            serializer = PdfFileSerializer(pagin_tc,many=True ,context={'request':request})
            response = self.get_paginated_response(serializer.data)
            return response

    def filter_queryset(self, queryset):
        filter_backends = (DjangoFilterBackend,SearchFilter,OrderingFilter)
        for backend in list(filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        return queryset

    def create(self,request):
        pdf_request_file = request.FILES.getlist('pdf_request_file')
        file_language = request.POST.get('file_language')
        user = request.user.id
        data = [{'pdf_file':pdf_file_list ,'pdf_language':file_language,'user':user ,'pdf_file_name' : pdf_file_list._get_name() ,
                 'file_name':pdf_file_list._get_name() ,'status':'YET TO START' } for pdf_file_list in pdf_request_file]
        serializer = PdfFileSerializer(data = data,many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def retrieve(self, request, pk):
        queryset = Ai_PdfUpload.objects.get(id = pk)
        serializer = PdfFileSerializer(queryset)
        return Response(serializer.data)
    
    def update(self,request,pk):
        tt = request.POST.get('by')
        if tt == 'task':
            task_obj = Task.objects.get(id = pk)
            ins = task_obj.pdf_task.last()
        else:
           ins = Ai_PdfUpload.objects.get(id = pk)
        docx_file = request.FILES.get('docx_file')
        if docx_file:
            serializer = PdfFileSerializer(ins,data={**request.POST.dict(),"docx_file_from_writer":docx_file},partial=True)
        else:
            serializer = PdfFileSerializer(ins,data={**request.POST.dict()},partial=True) 
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def destroy(self,request,pk):
        try:
            obj = Ai_PdfUpload.objects.get(id=pk)
            obj.delete()
            return Response({'msg':'deleted successfully'},status=200)
        except:
            return Response({'msg':'deletion unsuccessfull'},status=400)

from rest_framework.views import APIView
class ConversionPortableDoc(APIView):
    permission_classes = [IsAuthenticated]
    serializer = PdfFileSerializer
    def get(self,request):
        celery_task = {}
        user = request.user
        ids = request.query_params.getlist('id', None)
        initial_credit = user.credit_balance.get("total_left")
        for id in ids:
            pdf_path = Ai_PdfUpload.objects.get(id = int(id)).pdf_file.path
            file_format,page_length = file_pdf_check(pdf_path)
            #pdf consuming credits
            consumable_credits = get_consumable_credits_for_pdf_to_docx(page_length,file_format)
            if initial_credit > consumable_credits:
                task_id = pdf_conversion(int(id))
                celery_task[int(id)] = task_id
                debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)
            else:
                return Response({'msg':'Insufficient Credits'},status=400)
        return Response(celery_task)


@api_view(['GET',])
@permission_classes([IsAuthenticated])
def docx_file_download(request):
    task_id = request.GET.get('task_id')
    obj_id = request.GET.get('id')
    if obj_id:pdf_doc_file = Ai_PdfUpload.objects.get(id=obj_id).pdf_file.path
    else:pdf_doc_file = Ai_PdfUpload.objects.get(task_id=task_id).pdf_file.path
    if pdf_doc_file:
        docx_file_path = str(pdf_doc_file).split(".pdf")[0] +".docx"
        return download_file(docx_file_path)
    else:
        return JsonResponse({"msg":"no file associated with it"})


def get_docx_file_path(pdf_id):
    pdf_path = Ai_PdfUpload.objects.get(id=pdf_id).pdf_file.path
    docx_file_path = pdf_path.split(".pdf")[0] +".docx"
    return docx_file_path


@api_view(['POST',])
@permission_classes([IsAuthenticated])
def project_pdf_conversion(request,task_id):
    from ai_workspace.models import Task
    from ai_staff.models import Languages
    task_obj = Task.objects.get(id = task_id)
    user = task_obj.job.project.ai_user
    file_obj = ContentFile(task_obj.file.file.read(),task_obj.file.filename)
    initial_credit = user.credit_balance.get("total_left")
    file_format,page_length = file_pdf_check(task_obj.file.file.path)

    consumable_credits = get_consumable_credits_for_pdf_to_docx(page_length,file_format)
    if initial_credit > consumable_credits:
        pdf_obj = Ai_PdfUpload.objects.filter(task = task_obj).last()
        if pdf_obj == None:
            pdf_obj = Ai_PdfUpload.objects.create(user= user , file_name = task_obj.file.filename, status='YET TO START',
                                   pdf_file_name =task_obj.file.filename  ,task = task_obj ,pdf_file =file_obj , pdf_language = task_obj.job.source_language_id)
        #file_details = Ai_PdfUpload.objects.filter(task = task_obj).last()
        lang = Languages.objects.get(id=int(pdf_obj.pdf_language)).language.lower()
        debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)
        if (file_format == 'ocr') or (lang in google_ocr_indian_language):

            response_result = ai_export_pdf.apply_async((pdf_obj.id, ),)
            pdf_obj.pdf_task_id = response_result.id
            pdf_obj.save()
            return Response({'celery_id':response_result.id ,"pdf":pdf_obj.id})
        elif file_format == 'text':
            response_result = convertiopdf2docx.apply_async((pdf_obj.id,lang ,file_format),0)
            pdf_obj.pdf_task_id = response_result.id
            pdf_obj.save()
            return Response({'celery_id':response_result.id ,"pdf":pdf_obj.id})
        else:
            return Response({"msg":"error"})
    else:
        return Response({'msg':'Insufficient Credits'},status=400)


from ai_exportpdf.utils import openai_endpoint
@api_view(['POST',])
@permission_classes([IsAuthenticated])
def text_generator_openai(request):
    user = request.user
    prompt = request.POST.get('prompt')
    initial_credit = user.credit_balance.get("total_left")
    tot_tokn =256*4
    consumable_credits = get_consumable_credits_for_openai_text_generator(total_token =tot_tokn )
    if initial_credit > consumable_credits:
        response = openai_endpoint(prompt)
        consume_credit = response.pop('usage')
        consume_credit = get_consumable_credits_for_openai_text_generator(total_token =consume_credit )
        debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consume_credit)
        return JsonResponse(response)
    else:
        return Response({'msg':'Insufficient Credits'},status=400)



class AiPromptViewset(viewsets.ViewSet):
    model = AiPrompt

    def get(self, request):
        query_set = self.model.objects.all()
        serializer = AiPromptSerializer(query_set ,many =True)
        return Response(serializer.data)


    def create(self,request):
        # keywords = request.POST.getlist('keywords')
        targets = request.POST.getlist('get_result_in')
        serializer = AiPromptSerializer(data={**request.POST.dict(),'user':self.request.user.id,'targets':targets})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)


class AiPromptResultViewset(viewsets.ViewSet):
    model = AiPromptResult

    def list(self, request):
        prmp_id = request.GET.get('prompt_id')
        print("prmp_id----------------->",prmp_id)
        prmp_obj = AiPrompt.objects.get(id=prmp_id)
        serializer = AiPromptGetSerializer(prmp_obj)
        return Response(serializer.data)

        # query_set = prmp_obj.ai_prompt.all()
        # serializer = AiPromptResultSerializer(query_set ,many =True)
        # return Response(serializer.data)

    # def create(self,request):
    #     serializer = AiPromptResultSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors)

    

@api_view(['POST',])
@permission_classes([IsAuthenticated])
def customize_text_openai(request):
    user = request.user
    customize_id = request.POST.get('customize_id')
    user_text = request.POST.get('user_text')
    customize = AiCustomize.objects.get(id =customize_id).customize
    lang = detect(user_text)
     
    if lang!= 'en':
        user_text_mt_en = get_translation(mt_engine_id=1 , source_string = user_text,
                                       source_lang_code=lang , target_lang_code='en')
        user_text = customize +"this:"+ user_text_mt_en
        response = get_prompt(user_text ,model_name=openai_model , max_token =256 ,n=1 )
        txt_generated = response['choices'][0]['text']
        user_text = get_translation(mt_engine_id=1 , source_string = txt_generated,
                                       source_lang_code='en' , target_lang_code=lang)
        
    else:##english
        user_text = customize +"this:"+ user_text
        response = get_prompt(user_text ,model_name=openai_model , max_token =256 ,n=1 )
        user_text = response['choices'][0]['text']
    total_tokens = response['usage']['total_tokens']
    
    return Response({'customize_text': user_text ,'lang':lang ,'customize_cat':customize},status=200)

    # consumable_credits = get_consumable_credits_for_openai_text_generator(total_token =tot_tokn )
    # if initial_credit > consumable_credits:
    #     response = openai_endpoint(prompt)
    #     consume_credit = response.pop('usage')
    #     consume_credit = get_consumable_credits_for_openai_text_generator(total_token =consume_credit )
    #     debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consume_credit)
    #     return JsonResponse(response)
    # else:
    #     return Response({'msg':'Insufficient Credits'},status=400)
        
     

# from ai_exportpdf.utils import openai_endpoint
# import os,json ,requests

# @api_view(['POST',])
# @permission_classes([IsAuthenticated])
# def word_count_check(request):
#     spring_host = os.environ.get("SPRING_HOST")
#     prompt = request.POST.get('prompt')
#     seg = {'segment_source': prompt,
#             'source_language': 17,
#             'target_language': 77,
#             'processor_name': 'plain-text-processor',
#             'extension': '.txt'}
#     res = requests.post(url=f"http://{spring_host}:8080/segment/word_count",
#                         data={"segmentWordCountdata": json.dumps(seg)})
#     return Response({'msg':res.json()},status=200)







    # def create(self, request):
    #     pdf_request_file = request.FILES.getlist('pdf_request_file')
    #     file_language = request.POST.get('file_language')
    #     # format = request.POST.get('format')
    #     user = request.user.id
    #     response_result = {}
    #     celery_status_id = {}
    #     for pdf_file_lis in  pdf_request_file :

    #         lang = Languages.objects.get(id=int(file_language)).language.lower()
    #         if pdf_file_lis.name.endswith('.pdf') and lang:
    #             Ai_PdfUpload.objects.create(user_id = user , pdf_file = pdf_file_lis ,
    #                                         pdf_file_name = str(pdf_file_lis) ,
    #                                         pdf_language =lang.lower()).save()
    #             serve_path = str(Ai_PdfUpload.objects.all().filter(user_id = user).last().pdf_file)
    #             pdf_file_name = settings.MEDIA_ROOT+"/"+serve_path
    #             pdf_text_ocr_check = file_pdf_check(pdf_file_name)
    #             if lang in google_ocr_indian_language:  ###this may throw false if multiple language
    #                 response_result = ai_export_pdf.delay(serve_path)        #, file_language , pdf_file_name_only , instance_path
    #                 file_upload = Ai_PdfUpload.objects.get(pdf_file = serve_path)
    #                 file_upload.pdf_task_id = response_result.id
    #                 file_upload.save()
    #                 # file_uploadpdf_task_id = response_result.id)
    #                 logger.info('assigned ocr ,file_name: google indian language'+str(pdf_file_name))
    #                 celery_status_id[file_upload.id] = response_result.id
    #                 # return JsonResponse({'result':response_result.id} , safe=False)
    #             elif lang in list(lang_codes.keys()):  ###this may throw false if multiple language
    #                 response_result = convertiopdf2docx.delay(serve_path = serve_path ,
    #                                                           language = lang ,
    #                                                           ocr = pdf_text_ocr_check)
    #                 file_upload = Ai_PdfUpload.objects.get(pdf_file = serve_path)
    #                 file_upload.pdf_task_id = response_result.id
    #                 file_upload.save()
    #                 file_upload.pdf_task_id = response_result.id
    #                 logger.info('assigned pdf text ,file_name: convertio'+str(pdf_file_name))
    #                 celery_status_id[file_upload.id] = response_result.id
    #                 # return JsonResponse({'result':response_result.id} , safe=False)
    #             else:
    #                 celery_status_id["err"] = "error"
    #         else:
    #             celery_status_id[serve_path] = "need_pdf_file"
    #     return JsonResponse({'result':celery_status_id} , safe=False)
