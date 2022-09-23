from asyncore import file_dispatcher
from ai_exportpdf.models import Ai_PdfUpload
from django.http import   JsonResponse 
import  os  ,logging ,requests  
from celery.result import AsyncResult
from ai_auth.models import AiUser
from pathlib import Path
from rest_framework import viewsets
from django.shortcuts import get_object_or_404
from ai_exportpdf.serializer import PdfFileSerializer 
from rest_framework.views import  Response
from rest_framework.decorators import permission_classes
from django.http import Http404
from ai_tms.settings import CONVERTIO_IP
from rest_framework.permissions  import IsAuthenticated
from ai_exportpdf.utils import direct_download_urlib_docx , convertiopdf2docx ,ai_export_pdf , convertio_ocr_lang_pair  
logger = logging.getLogger('django')

google_ocr_indian_language = ['bengali','hindi','kannada','malayalam','marathi','punjabi','tamil','telugu']

class PDFTODOCX(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        pdf_request_file = request.FILES.get('pdf_request_file')
        file_language = request.POST.get('file_language')
        format = request.POST.get('format') ##########text pdf(searchable ,non searchable) , image pdf 
        user = request.user.id
        file_path = AiUser.objects.get(id =user).uid
        print("1. file_path -->" , file_path)
        print("2. user" , user)
        print("3. file_name" ,pdf_request_file )
        response_result = {}
        if pdf_request_file.name.endswith('.pdf') and file_language and format:
            Ai_PdfUpload.objects.create(user_id = user , pdf_file = pdf_request_file , pdf_format_option = format ,pdf_file_name = str(pdf_request_file) , pdf_language =file_language.lower()).save()  
            # file_name = Ai_PdfUpload.objects.last(user_id = user).pdf_file.split("/")[-1]
            # print("file_name ----> " , file_name)
            pdf_file_name =str(sorted(Path(os.getcwd()+"/media/"+str(file_path)+"/pdf_file/").iterdir() , key=os.path.getctime)[-1])
        
             
            pdf_file_name_with_extension = os.path.basename(pdf_file_name)
            print("pdf_file_name_with_extension" , pdf_file_name_with_extension)
            serve_path = str(file_path)+"/pdf_file/"+pdf_file_name_with_extension
            pdf_file_name_path = pdf_file_name_with_extension.split('.')[0]
            
            if file_language in google_ocr_indian_language:
                print("[OCR]")
                response_result = ai_export_pdf.delay(pdf_file_name , file_language , serve_path , file_path)       
                Ai_PdfUpload.objects.filter(pdf_file = serve_path).update(pdf_task_id = response_result.id)                      
                
                logger.info('assigned ocr ,file_name: google colud indian language '+str(pdf_file_name))
                return JsonResponse({'result':response_result.id} , safe=False)
            if format == 'text' :
                response_result = convertiopdf2docx(pdf_file_name = pdf_file_name_path , pdf_file_name_with_extension = pdf_file_name_with_extension , ocr = False , language=file_language.lower())
                logger.info('assigned pdf text ,file_name: convertio  '+str(pdf_file_name))      
                return JsonResponse({'result':response_result} , safe=False)

            if format == 'ocr':
                 
                if file_language in list(convertio_ocr_lang_pair.keys()):
                    response_result = convertiopdf2docx(pdf_file_name = pdf_file_name_path ,pdf_file_name_with_extension = pdf_file_name_with_extension , ocr = True ,language=file_language)
                    logger.info('assigned pdf text ,file_name: convertio '+str(pdf_file_name))      
                    return JsonResponse({'result':response_result} , safe=False)
                else:
                    response_result = ai_export_pdf.delay(pdf_file_name , file_language , pdf_file_name_with_extension ,file_path)    
                    print("----->>" , response_result.id)   
                    Ai_PdfUpload.objects.filter(pdf_file = serve_path).update(pdf_task_id = response_result.id)                       ########pdf_database_creation
                    logger.info('assigned ocr ,file_name: google cloud'+str(pdf_file_name))
                    return JsonResponse({'result':response_result.id} , safe=False)
        else:
            return JsonResponse({'result':"need pdf file to process"})    

    def list(self, request):
        pk = request.query_params.get('pk', None)
        if not pk:
 
            user = request.user.id
            files = Ai_PdfUpload.objects.filter(user_id = user)
            serializer = PdfFileSerializer(files,many=True)
            return Response(serializer.data)
        else:
            files = Ai_PdfUpload.objects.get(id = pk)
            serializer = PdfFileSerializer(files,many=True)
            print(serializer.data)
            return Response({'data':'data'})


    def retrieve(self, request, pk=None):
        queryset = Ai_PdfUpload.objects.all()
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
        



 

    #     if view_all:
    #         file_details = Ai_PdfUpload.objects.all()
    #         serializer = PdfFileSerializer(file_details,many=True)
    #         return Response(serializer.data)
    #     if pk:
    #         try:
    #             link = Ai_PdfUpload.objects.filter(id =pk) 
    #             serializer = PdfFileDownloadLinkSerializer(link,many=True)
    #             print(serializer)
    #             return Response(serializer.data)
    #         except Ai_PdfUpload.DoesNotExist:
    #             return Http404
    #     pdf_download_url = {}
    #     if "-" not in pdf_status_id:
    #         get_url = 'https://api.convertio.co/convert/{}/status'.format(pdf_status_id)
    #         r_get = requests.get(url = get_url )
    #         output_response = r_get.json() 
    #         if output_response['code'] == 422:
    #             return JsonResponse({'context': "update_cred"} , safe=False)
    #         if output_response['code'] == 200:
    #             if isinstance(output_response['data']['output'] , dict):   
    #                 file_name = output_response['data']['output']['url'].split("/")[-1]
    #                 pdf_url_from_convertio = output_response['data']['output']['url']
    #                 direct_download_urlib_docx(url= pdf_url_from_convertio , filename=str('/code/output_docx/'+file_name))
    #                 url = "{}/exportpdf/output_docx/{}".format(CONVERTIO_IP , str(file_name))
    #                 pdf_download_url['url'] = "SUCCESS"
    #                 pdf_download_url['download'] = url    
    #                 return JsonResponse({'context': pdf_download_url} , safe=False)
    #             else:
    #                 pdf_download_url['url'] = 'PENDING'
    #                 return JsonResponse({'context':pdf_download_url} , safe=False)
    #         else:
    #             return JsonResponse({'context':"FAILURE"} , safe=False)
    #     else:
    #         task_result = AsyncResult(pdf_status_id)
    #         pdf_download_url['url'] = task_result.status
    #         print("====>" , task_result.status)
    #         if task_result.status == 'SUCCESS':
    #             download= Ai_PdfUpload.objects.filter(pdf_task_id = pdf_status_id).last()
    #             print(download)
    #             file_name = str(download.pdf_file).split(".pdf")[0]+".docx"
    #             url = "{}/exportpdf/output_docx/{}".format(CONVERTIO_IP , str(file_name))
    #             pdf_download_url['download'] = url  
    #             Ai_PdfUpload.objects.filter(pdf_task_id = pdf_status_id).update(docx_file_urls = url)                                                                                #   docx_file_url
    #             return JsonResponse({'context': pdf_download_url} , safe=False)
    #         elif task_result.status == 'PENDING':
    #             download= Ai_PdfUpload.objects.filter(pdf_task_id = pdf_status_id).last()
               
    #             remain = '{} of {}'.format(download.counter , download.pdf_no_of_page)
    #             return JsonResponse({'context':'PENDING' , 'no_of_page_finished' :remain} , safe=False)
    #         else:
    #             return JsonResponse({'context': 'FAILURE'} , safe=False)

    # def delete(self,request):
    #     pk = request.query_params.get('id')
    #     # pdf_status_id = request.query_params.get('pdf_status_id')
    #     try:
    #         obj = Ai_PdfUpload.objects.get(id=pk)
    #         obj.delete()
    #         # task_result = AsyncResult(pdf_status_id)
    #         # print("-------->" ,task_result.status)
    #         # print("-------->" , task_result)
    #         # if task_result.status == 'PENDING':
    #         #     AsyncResult.revoke(pdf_status_id , terminate=True)
                 
    #         #     print("deleted successfully " , pdf_status_id)
    #         # else:print("task not presented")

    #         return Response({'msg':'deleted successfully'},status=200)
    #     except:
    #         return Response({'msg':'deletion unsuccessfull'},status=400)


    # # def delete(self,request):
    # #     delete_files()
    # #     return JsonResponse({'context': 'deleted successfully'} , safe=False)
 