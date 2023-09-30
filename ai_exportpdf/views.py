from ai_exportpdf.models import Ai_PdfUpload #,AiPrompt ,AiPromptResult)
from django.http import   JsonResponse
import logging ,os
from rest_framework import viewsets,generics
from rest_framework.pagination import PageNumberPagination
from ai_exportpdf.serializer import (PdfFileSerializer ,PdfFileStatusSerializer )
                                    #  AiPromptSerializer ,AiPromptResultSerializer,
                                    #  AiPromptGetSerializer)
from rest_framework.views import  Response
from rest_framework.decorators import permission_classes ,api_view
from rest_framework.permissions  import IsAuthenticated
from ai_exportpdf.utils import pdf_conversion
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from ai_workspace_okapi.utils import download_file
from ai_exportpdf.utils import get_consumable_credits_for_pdf_to_docx ,file_pdf_check
from ai_auth.models import UserCredits
from ai_workspace.api_views import UpdateTaskCreditStatus ,get_consumable_credits_for_text, update_task_assign
from django.core.files.base import ContentFile
from .utils import ai_export_pdf,convertiopdf2docx
from ai_workspace.models import Task
from ai_staff.models import AiCustomize ,Languages
from langdetect import detect
from django.db.models import Q
from ai_workspace_okapi.utils import get_translation
from celery.result import AsyncResult
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
            project_managers = user.team.get_project_manager if user.team else []
            owner = user.team.owner if user.team  else user
            query_filter = Ai_PdfUpload.objects.filter(Q(user = user) |Q(created_by=user)|Q(created_by__in=project_managers)|Q(user=owner))\
                            .filter(task_id=None).order_by('-id') 
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
        user = request.user.team.owner if request.user.team else request.user
        created_by = request.user
        data = [{'pdf_file':pdf_file_list ,'pdf_language':file_language,'user':user.id,'created_by':created_by.id ,'pdf_file_name' : pdf_file_list._get_name() ,
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
            update_task_assign(task_obj,request.user) if tt == 'task' else None
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
        user = request.user.team.owner if request.user.team else request.user
        ids = request.query_params.getlist('id', None)
        initial_credit = user.credit_balance.get("total_left")
        for id in ids:
            pdf_path = Ai_PdfUpload.objects.get(id = int(id)).pdf_file.path
            file_format,page_length = file_pdf_check(pdf_path,id)
            if page_length:
            #pdf consuming credits
                consumable_credits = get_consumable_credits_for_pdf_to_docx(page_length,file_format)
                if initial_credit > consumable_credits:
                    task_id = pdf_conversion(int(id))
                    print("TaskId---------->",task_id)
                    celery_task[int(id)] = task_id  
                    debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)
                else:
                    return Response({'msg':'Insufficient Credits'},status=400)
            else:
                celery_task[int(id)] = 'pdf corrupted'
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
    file_format,page_length = file_pdf_check(task_obj.file.file.path,None)
    if page_length:
        consumable_credits = get_consumable_credits_for_pdf_to_docx(page_length,file_format)
        if initial_credit > consumable_credits:
            pdf_obj = Ai_PdfUpload.objects.filter(task = task_obj).last()
            if pdf_obj == None:
                pdf_obj = Ai_PdfUpload.objects.create(user= user , file_name = task_obj.file.filename, status='YET TO START',
                                    pdf_file_name =task_obj.file.filename ,task = task_obj ,pdf_file =file_obj , pdf_language = task_obj.job.source_language_id)
            lang = Languages.objects.get(id=int(pdf_obj.pdf_language)).language.lower()
            debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)
            if file_format:
                response_result = ai_export_pdf.apply_async((pdf_obj.id, ),)
                pdf_obj.pdf_task_id = response_result.id
                pdf_obj.save()
                return Response({'celery_id':response_result.id ,"pdf":pdf_obj.id})
            else:
               return Response({"msg":"error"})
        else:
            return Response({'msg':'Insufficient Credits'},status=400)
    else:
        pdf_obj = Ai_PdfUpload.objects.filter(task = task_obj).last()
        if pdf_obj:
            pdf_obj.pdf_api_use = "FileCorrupted"
            pdf_obj.save()
        else:
            pdf_obj = Ai_PdfUpload.objects.create(user= user,task=task_obj,pdf_api_use="FileCorrupted")
        return Response({'msg':'File Cannot be Processed'},status=400)



from celery import Celery
from ai_exportpdf.utils import ai_export_pdf
@api_view(['POST',])
@permission_classes([IsAuthenticated])
def celery_revoke(request):
    app = Celery()
    task_id=request.POST.get('task_id')
    # result = AsyncResult(task_id)
    # print(result.result)
    # if result:
    # ai_export_pdf.AsyncResult(task_id).revoke()
    app.control.revoke(task_id, terminate=True)
    response_data = {"status": "task_revoked"}
    return JsonResponse(response_data, status=200)
 




# app = Celery('ai_tms')
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def stop_task(request):
#     task_id = request.GET.get('task_id')
#     task = AsyncResult(task_id)
#     print("TT---------->",task.state)
#     if task.state == 'STARTED':
#         app.control.revoke(task_id, terminated=True, signal='SIGKILL')
#         return JsonResponse({'status':'Task has been stopped.'}) 
#     elif task.state == 'PENDING':
#         app.control.revoke(task_id)
#         return JsonResponse({'status':'Task has been revoked.'})
#     else:
#         return JsonResponse({'status':'Task is already running or has completed.'})



# @api_view(['POST',])
# @permission_classes([IsAuthenticated])
# def project_pdf_conversion(request,task_id):
#     from ai_workspace.models import Task
#     from ai_staff.models import Languages
#     task_obj = Task.objects.get(id = task_id)
#     user = task_obj.job.project.ai_user
#     file_obj = ContentFile(task_obj.file.file.read(),task_obj.file.filename)
#     initial_credit = user.credit_balance.get("total_left")
#     file_format,page_length = file_pdf_check(task_obj.file.file.path,None)
#     if page_length:
#         consumable_credits = get_consumable_credits_for_pdf_to_docx(page_length,file_format)
#         if initial_credit > consumable_credits:
#             pdf_obj = Ai_PdfUpload.objects.filter(task = task_obj).last()
#             if pdf_obj == None:
#                 pdf_obj = Ai_PdfUpload.objects.create(user= user , file_name = task_obj.file.filename, status='YET TO START',
#                                     pdf_file_name =task_obj.file.filename ,task = task_obj ,pdf_file =file_obj , pdf_language = task_obj.job.source_language_id)
#             #file_details = Ai_PdfUpload.objects.filter(task = task_obj).last()
#             lang = Languages.objects.get(id=int(pdf_obj.pdf_language)).language.lower()
#             debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)
#             #if (file_format == 'ocr'): #or (lang in google_ocr_indian_language):

#             response_result = ai_export_pdf.apply_async((pdf_obj.id, ),)
#             pdf_obj.pdf_task_id = response_result.id
#             pdf_obj.save()
#             return Response({'celery_id':response_result.id ,"pdf":pdf_obj.id})
#             # elif file_format == 'text':
#             #     response_result = convertiopdf2docx.apply_async((pdf_obj.id,lang ,file_format),0)
#             #     pdf_obj.pdf_task_id = response_result.id
#             #     pdf_obj.save()
#             #     return Response({'celery_id':response_result.id ,"pdf":pdf_obj.id})
#             #else:
#             #    return Response({"msg":"error"})
#         else:
#             return Response({'msg':'Insufficient Credits'},status=400)
#     else:
#         pdf_obj = Ai_PdfUpload.objects.filter(task = task_obj).last()
#         if pdf_obj:
#             pdf_obj.pdf_api_use = "FileCorrupted"
#             pdf_obj.save()
#         else:
#             pdf_obj = Ai_PdfUpload.objects.create(user= user,task=task_obj,pdf_api_use="FileCorrupted")
#         return Response({'msg':'File Cannot be Processed'},status=400)


