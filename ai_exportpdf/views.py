from asyncore import file_dispatcher
from tabnanny import check
from ai_exportpdf.models import Ai_PdfUpload
from django.http import   JsonResponse 
import  os  ,logging , pdftotext
from ai_auth.models import AiUser
from rest_framework import viewsets
from django.shortcuts import get_object_or_404
from ai_exportpdf.serializer import PdfFileSerializer 
from rest_framework.views import  Response
from rest_framework.decorators import permission_classes
from django.http import Http404
from django.contrib.auth import settings
from rest_framework.permissions  import IsAuthenticated
from ai_exportpdf.utils import  convertiopdf2docx ,ai_export_pdf 
from ai_exportpdf.convertio_ocr_lang import lang_code ,lang_codes
from ai_staff.models import Languages

logger = logging.getLogger('django')
google_ocr_indian_language = ['bengali','hindi','kannada','malayalam','marathi','punjabi','tamil','telugu']


def file_pdf_check(file_path):
    text = ""
    with open(file_path ,"rb") as f:
        pdf = pdftotext.PDF(f)
    count = 5 if len(pdf)>=5 else len(pdf)
    for page in range(count):
        text+=pdf[page]
    return "text" if len(text)>=700 else "ocr"

class Pdf2Docx(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def create(self, request):
        pdf_request_file = request.FILES.get('pdf_request_file')
        file_language = request.POST.get('file_language')
        # format = request.POST.get('format')  

        file_language = Languages.objects.get(id=int(file_language)).language.lower()
        print("lang ---> ", file_language)
        user = request.user.id
        response_result = {}
        if pdf_request_file.name.endswith('.pdf') and file_language: 
            Ai_PdfUpload.objects.create(user_id = user , pdf_file = pdf_request_file , 
                                        pdf_file_name = str(pdf_request_file) , 
                                        pdf_language =file_language.lower()).save()  
            serve_path = str(Ai_PdfUpload.objects.all().filter(user_id = user).last().pdf_file)
            pdf_file_name = settings.MEDIA_ROOT+"/"+serve_path
            pdf_text_ocr_check = file_pdf_check(pdf_file_name)

            if file_language in google_ocr_indian_language:  ###this may throw false if multiple language
                print("[OCR]")
                response_result = ai_export_pdf.delay(serve_path)        #, file_language , pdf_file_name_only , instance_path
                Ai_PdfUpload.objects.filter(pdf_file = serve_path).update(pdf_task_id = response_result.id)                      
                logger.info('assigned ocr ,file_name: google colud indian language'+str(pdf_file_name))
                return JsonResponse({'result':response_result.id} , safe=False)
    
            elif file_language in list(lang_codes.keys()):  ###this may throw false if multiple language
                print("[convertio]")
                response_result = convertiopdf2docx.delay(serve_path = serve_path ,language = file_language , ocr = pdf_text_ocr_check )
                Ai_PdfUpload.objects.filter(pdf_file = serve_path).update(pdf_task_id = response_result.id)
                logger.info('assigned pdf text ,file_name: convertio'+str(pdf_file_name))      
                return JsonResponse({'result':response_result.id} , safe=False)
            else :return JsonResponse({'result':'error'} , safe=False)
        else:
            return JsonResponse({'result':"need pdf file to process"})    


    def list(self, request):
        queryset = Ai_PdfUpload.objects.all()
        id = request.query_params.get('id', None)
        pdf_status_id = request.query_params.get('pdf_status_id', None)
        user = request.user.id
        print(user)
        if pdf_status_id:
            pdf_status = queryset.filter(pdf_task_id = pdf_status_id,user_id = user).first()
            serializer = PdfFileSerializer(pdf_status)
            return Response(serializer.data)

        if not id:
            files = Ai_PdfUpload.objects.filter(user_id = user)
            serializer = PdfFileSerializer(files,many=True)
            return Response(serializer.data)
        else:
            # files = Ai_PdfUpload.objects.get(id = id)
            # print("check",files , type(files))
            serializer = PdfFileSerializer(queryset,many=True)
            print("serializer data--->",serializer.data) 
            return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Ai_PdfUpload.objects.filter(id = pk)
        user = get_object_or_404(queryset, pk=pk)
        serializer = PdfFileSerializer(user)
        return Response(serializer.data)
            
    def destroy(self,request,pk):
        try:
            obj = Ai_PdfUpload.objects.get(id=pk)
            obj.delete()
            return Response({'msg':'deleted successfully'},status=200)
        except:
            return Response({'msg':'deletion unsuccessfull'},status=400)
        
