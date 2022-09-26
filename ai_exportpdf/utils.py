from cgitb import text
import os ,mimetypes
from django.http import HttpResponse  
from ai_exportpdf.models import Ai_PdfUpload
import urllib.request ,docx ,re ,io
import os ,logging ,requests ,json,time 
from io import BytesIO 
from google.cloud import vision_v1 , vision
from google.oauth2 import service_account
from ai_tms.settings import GOOGLE_APPLICATION_CREDENTIALS_OCR ,CONVERTIO_API ,CONVERTIO_IP
from PyPDF2 import PdfFileReader
from tqdm import tqdm
from pdf2image import convert_from_path
from celery import shared_task
from django.core.files.base import ContentFile
logger = logging.getLogger('django')

output_docx_path = os.getcwd()+"/output_docx/"
print(output_docx_path)
if not os.path.exists(output_docx_path):
    os.makedirs(output_docx_path)


with open('tesseract_language.json') as fp:
    tesseract_language_pair = json.load(fp)

with open('convertio.json') as fp:
    convertio_ocr_lang_pair = json.load(fp)

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
            # return texts[0].description  
            return texts
        else:
            #####empty page
            return ""


def convertiopdf2docx(pdf_file_name ,pdf_file_name_with_extension ,ocr , language):
    pdf_file_url = "{}/exportpdf/media/{}".format(CONVERTIO_IP, pdf_file_name_with_extension)
    # callback_url = "{}/exportpdf/checkstatuspdf".format(CONVERTIO_IP)
    data = {
                'apikey': CONVERTIO_API,
                'input': 'url',
                'file': pdf_file_url,
                'filename':  pdf_file_name +'.docx',
                'outputformat': 'docx' ,
                   }
    if ocr:
        language_convertio = convertio_ocr_lang_pair[language]
        ocr_option =  {"options": {"ocr_enabled": True, "ocr_settings": {"langs": [language_convertio]}}}
        data = {**data , **ocr_option}
    response_status = requests.post(url='https://api.convertio.co/convert' , data = json.dumps(data) ).json()
    logger.info("convertiopdf2docx"+str(pdf_file_name) )
    if response_status['status'] == 'error': 
        return  "Error during input file fetching: couldn't connect to host"  
    else:
        return  str(response_status['data']['id'])


from django.contrib.auth import settings

#########ocr ######
@shared_task(serializer='json')
def ai_export_pdf(serve_path , file_language , file_name , file_path):
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
        return {"result":"finished_task" , "time":end}
        
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