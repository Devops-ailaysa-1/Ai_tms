import base64
import docx
import json
import logging
import mimetypes
import os
import re
import requests
import time
import urllib.request
from io import BytesIO

from PyPDF2 import PdfFileReader
from celery import shared_task
from django.contrib.auth import settings
from django.http import HttpResponse
from google.cloud import vision_v1, vision
from google.oauth2 import service_account
from pdf2image import convert_from_path
from tqdm import tqdm

from ai_exportpdf.convertio_ocr_lang import lang_code
from ai_exportpdf.models import Ai_PdfUpload
from ai_tms.settings import GOOGLE_APPLICATION_CREDENTIALS_OCR, CONVERTIO_API

logger = logging.getLogger('django')
# with open('tesseract_language.json') as fp:
#     tesseract_language_pair = json.load(fp)

credentials = service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS_OCR)
client = vision.ImageAnnotatorClient(credentials=credentials)

def download_file(file_path):
    filename = os.path.basename(file_path)
    fl = open(file_path, 'rb')
    mime_type, _ = mimetypes.guess_type(file_path)
    response = HttpResponse(fl, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response

def direct_download_urlib_docx(url,filename):
    x = urllib.request.urlretrieve(url=url , filename=filename)

# def delete_files():
#     try:
#         Ai_PdfUpload.objects.all().delete()
#         # shutil.rmtree(os.getcwd()+"/media/")
#         for i in os.listdir(os.getcwd()+"/media/"):
#             os.remove(os.getcwd()+"/media/"+i)
#     except:
#         print("not deleted")
def remove_carraige_return(txt):
    with open(f'1.txt', 'w' , encoding="utf-8",newline= '\r\n') as the_file:
            the_file.write(txt)
    final_data = [line.replace('\r\n','\n') if '\r\n' in  line[:2] else line.replace('\r\n','') for line in [x.decode() for x in  open(f'1.txt','rb').readlines()]]
    final_data = "".join(final_data)
    y = final_data.split(".")
    y = "\n".join(y)
    return y

def image_ocr_google_cloud_vision(image , inpaint):
    if inpaint:
        image = vision_v1.types.Image(content=image)
        response = client.text_detection(image = image)
        texts = response.full_text_annotation
        return texts
    else:
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        image = vision_v1.types.Image(content=buffer.getvalue() )
        response = client.text_detection(image = image)
        texts = response.full_text_annotation
        if texts:
            texts = para_creation_from_ocr(texts)
            return texts
        else:
            return ""

@shared_task(serializer='json')
def convertiopdf2docx(serve_path ,language,ocr = None ):
    '''
    Args
    serve_path : pdf path
    language : pdf language
    ocr : bool
    '''
    fp  =str(settings.MEDIA_ROOT+"/"+ serve_path)
    txt_field_obj = Ai_PdfUpload.objects.get(pdf_file = serve_path)
    pdf_file_name = serve_path.split("/")[-1].split(".pdf")[0]+'.docx'    ## file_name for pdf to sent to convertio
    with open(fp, "rb") as pdf_path:
        encoded_string = base64.b64encode(pdf_path.read())           ##pdf file convert to base64 
    data = {'apikey': CONVERTIO_API ,                          # CONVERTIO_API,           #convertio crediential
                'input': 'base64',  #['url ,raw,base64]
                'file': encoded_string.decode('utf-8'),
                'filename':   pdf_file_name,
                'outputformat': 'docx' }
    if ocr == "ocr":
        language = language.split(",")                    #if ocr is True and selecting multiple language 
        language_convertio = [lang_code(i) for i in language]
        ocr_option =  { "options": { "ocr_enabled": True, "ocr_settings": { "langs": [language_convertio]}}}
        data = {**data , **ocr_option}     #merge dict 
        txt_field_obj.pdf_api_use = "convertio-ocr"
    else:
        txt_field_obj.pdf_api_use = "convertio"
    response_status = requests.post(url='https://api.convertio.co/convert' , data=json.dumps(data)).json() ###   posting for conversion to convert io 
    if response_status['status'] == 'error': 
        txt_field_obj.status = "ERROR"
        txt_field_obj.save()
        return  {"result":"Error during input file fetching: couldn't connect to host"} 
    else:
        print("no error found")
        get_url = 'https://api.convertio.co/convert/{}/status'.format(str(response_status['data']['id']))
        while requests.get(url = get_url).json()['data']['step'] != 'finish':  #####checking status of posted pdf file
            txt_field_obj.status = "PENDING"
            txt_field_obj.save()
            print("converting")
            time.sleep(2)
        print("finished-conversion")
        file_link = requests.get(url = get_url).json()['data']['output']['url']  ##after finished get converted file from convertio 
        direct_download_urlib_docx(url= file_link , filename= str(settings.MEDIA_ROOT+"/"+ serve_path).split(".pdf")[0] +".docx" )  #download it from convertio to out server
        txt_field_obj.status = "DONE"
        txt_field_obj.docx_url_field = str(settings.MEDIA_URL+ serve_path).split(".pdf")[0] +".docx" ##save path to database
        txt_field_obj.save()
        return {"result":"finished_task" }

##   pdf file url (pdf_path ) ---> get it from serve_path
### create data[dict] to send to convertio api 
#########ocr ######
@shared_task(serializer='json')
def ai_export_pdf(serve_path): # , file_language , file_name , file_path
    pdf_path  = settings.MEDIA_ROOT+"/"+ serve_path
    txt_field_obj = Ai_PdfUpload.objects.get(pdf_file = serve_path)
    start = time.time()
    try:
        pdf = PdfFileReader(open(pdf_path,'rb') ,strict=False)
        pdf_len = pdf.getNumPages()
        no_of_page_processed_counting = 0    
        txt_field_obj.pdf_no_of_page = int(pdf_len)
        doc = docx.Document()
        for i in tqdm(range(1,pdf_len+1)):
            image = convert_from_path(pdf_path ,thread_count=1,fmt='png',grayscale=True ,first_page=i,last_page=i ,size=(700, 700) )[0]
            # ocr_pages[i] = pytesseract.image_to_string(image ,lang=language_pair)  tessearct function
            text = image_ocr_google_cloud_vision(image , inpaint=False)
            text = re.sub(u'[^\u0020-\uD7FF\u0009\u000A\u000D\uE000-\uFFFD\U00010000-\U0010FFFF]+', '', text)
            doc.add_paragraph(text) 
            end = time.time()
            no_of_page_processed_counting+=1
            txt_field_obj.counter = int(no_of_page_processed_counting)
            txt_field_obj.status = "PENDING"
            txt_field_obj.save()
        logger.info('finished ocr and saved as docx ,file_name: ' )
        txt_field_obj.status = "DONE"
        docx_file_path = str(settings.MEDIA_ROOT+"/"+ serve_path).split(".pdf")[0] +".docx"
        doc.save(docx_file_path)
        txt_field_obj.docx_url_field = str(settings.MEDIA_URL+ serve_path).split(".pdf")[0] +".docx"
        txt_field_obj.pdf_conversion_sec = int(round(end-start,2)) 
        txt_field_obj.pdf_api_use = "google-ocr"
        txt_field_obj.save()
        return {"result":"finished_task"}
    except BaseException as e:
        end = time.time()
        logger.error(str(e))
        txt_field_obj.status = "ERROR"
        txt_field_obj.save()
        return {'result':"something went wrong"}  

def para_creation_from_ocr(texts):
    para_text = []
    for i in  texts.pages:
        for j in i.blocks: 
            for k in j.paragraphs:
                text_list = []
                for a in  k.words:
                    text_list.append(" ")
                    for b in a.symbols:
                        text_list.append(b.text)
            para_text.append("".join(text_list)) 
    return "\n".join(para_text)