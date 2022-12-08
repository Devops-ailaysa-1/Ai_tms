from ai_exportpdf.models import Ai_PdfUpload
from django.http import   JsonResponse 
import logging  
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from ai_exportpdf.serializer import PdfFileSerializer ,PdfFileStatusSerializer
from rest_framework.views import  Response
from rest_framework.decorators import permission_classes ,api_view
from rest_framework.permissions  import IsAuthenticated
from ai_exportpdf.utils import pdf_conversion
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from ai_workspace_okapi.utils import download_file
from ai_exportpdf.utils import get_consumable_credits_for_pdf_to_docx ,file_pdf_check
from ai_auth.models import UserCredits
from ai_workspace.api_views import UpdateTaskCreditStatus



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
        ids = request.query_params.getlist('id',None)
        user = request.user
        if ids:
            queryset = Ai_PdfUpload.objects.filter(id__in = ids)
            serializer = PdfFileStatusSerializer(queryset,many=True)
            return Response(serializer.data)
        else:
            query_filter = Ai_PdfUpload.objects.filter(user = user).order_by('id')
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
def docx_file_download(request,id):
    pdf_doc_file = Ai_PdfUpload.objects.get(id=id).pdf_file.path
    if pdf_doc_file:
        docx_file_path = str(pdf_doc_file).split(".pdf")[0] +".docx"
        return download_file(docx_file_path)
    else:
        return JsonResponse({"msg":"no file associated with it"})























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
