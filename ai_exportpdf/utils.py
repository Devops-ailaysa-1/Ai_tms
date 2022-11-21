import base64
import docx ,json,logging,mimetypes,os ,pdftotext
import re,requests,time,urllib.request
from io import BytesIO
from PyPDF2 import PdfFileReader
from celery import shared_task
from django.contrib.auth import settings
from django.http import HttpResponse
from google.cloud import vision_v1, vision
from google.oauth2 import service_account
from pdf2image import convert_from_path
from tqdm import tqdm
from ai_auth.models import UserCredits
from ai_exportpdf.models import Ai_PdfUpload
from ai_tms.settings import GOOGLE_APPLICATION_CREDENTIALS_OCR, CONVERTIO_API
from ai_exportpdf.convertio_ocr_lang import lang_code ,lang_codes
from ai_staff.models import Languages
logger = logging.getLogger('django')
credentials = service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS_OCR)
client = vision.ImageAnnotatorClient(credentials=credentials)
google_ocr_indian_language = ['bengali','hindi','kannada','malayalam','marathi','punjabi','tamil','telugu']

def download_file(file_path):
    filename = os.path.basename(file_path)
    fl = open(file_path, 'rb')
    mime_type, _ = mimetypes.guess_type(file_path)
    response = HttpResponse(fl, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response

def direct_download_urlib_docx(url,filename):
    x = urllib.request.urlretrieve(url=url , filename=filename)

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
def convertiopdf2docx(id ,language,ocr = None ):
    txt_field_obj = Ai_PdfUpload.objects.get(id = id)
    fp  = txt_field_obj.pdf_file.path
    pdf_file_name = fp.split("/")[-1].split(".pdf")[0]+'.docx'    ## file_name for pdf to sent to convertio
    txt_field_obj = Ai_PdfUpload.objects.get(id = id)
    total_credits = UserCredits.objects.get(user_id =txt_field_obj.user)    
    with open(fp, "rb") as pdf_path:
        encoded_string = base64.b64encode(pdf_path.read())
    data = {'apikey': CONVERTIO_API ,'input': 'base64', 'file': encoded_string.decode('utf-8'),'filename':   pdf_file_name,'outputformat': 'docx' }
    # if ocr == "ocr":
        # language = language.split(",")                    #if ocr is True and selecting multiple language 
        # language_convertio = [lang_code(i) for i in language]
        # ocr_option =  { "options": { "ocr_enabled": True, "ocr_settings": { "langs": [language_convertio]}}}
        # data = {**data , **ocr_option}     #merge dict 
        # txt_field_obj.pdf_api_use = "convertio_ocr"
    #     print("[convertio ocr]")
    # else:
    #     txt_field_obj.pdf_api_use = "convertio"
    #     print("[convertio text]")
    txt_field_obj.pdf_api_use = "convertio"
    response_status = requests.post(url='https://api.convertio.co/convert' , data=json.dumps(data)).json()
    if response_status['status'] == 'error': 
        txt_field_obj.status = "ERROR"
        txt_field_obj.save()
        ###retain cred if error
        consum_cred = get_consumable_credits_for_pdf_to_docx(file_pdf_check(fp)[1])
        total_credits.credits_left = total_credits.credits_left + consum_cred
        total_credits.save()
        return  {"result":"Error during input file fetching: couldn't connect to host"} 
    else:
        get_url = 'https://api.convertio.co/convert/{}/status'.format(str(response_status['data']['id']))
        while requests.get(url = get_url).json()['data']['step'] != 'finish':
            txt_field_obj.status = "PENDING"
            txt_field_obj.save()
            time.sleep(2)
        convertio_response_link =  requests.get(url = get_url).json()  
        file_link = convertio_response_link['data']['output']['url']  ##after finished get converted file from convertio 
        direct_download_urlib_docx(url= file_link , filename= str(settings.MEDIA_ROOT+"/"+ str(txt_field_obj.pdf_file)).split(".pdf")[0] +".docx" )  
        txt_field_obj.status = "DONE"
        txt_field_obj.pdf_conversion_sec = int(convertio_response_link['data']['minutes'])*60
        txt_field_obj.docx_url_field = str(settings.MEDIA_URL+str(txt_field_obj.pdf_file)).split(".pdf")[0] +".docx" ##save path to database
        txt_field_obj.docx_file_name = str(txt_field_obj.pdf_file_name).split('.pdf')[0]+ '.docx'
        txt_field_obj.save()
        return {"result":"finished_task" }
import tempfile
#########ocr ######
@shared_task(serializer='json')  
def ai_export_pdf(id): # , file_language , file_name , file_path
    txt_field_obj = Ai_PdfUpload.objects.get(id = id)
    total_credits = UserCredits.objects.get(user_id =txt_field_obj.user) 
    fp = txt_field_obj.pdf_file.path
    start = time.time()
    pdf = PdfFileReader(open(fp,'rb') ,strict=False)
    pdf_len = pdf.getNumPages()
    try:
        no_of_page_processed_counting = 0    
        txt_field_obj.pdf_no_of_page = int(pdf_len)
        doc = docx.Document()
        for i in tqdm(range(1,pdf_len+1)):
            with tempfile.TemporaryDirectory() as image:
                image = convert_from_path(fp ,thread_count=8,fmt='png',grayscale=True ,first_page=i,last_page=i ,size=(500, 500) )[0]
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
        docx_file_path = str(fp).split(".pdf")[0] +".docx"
        doc.save(docx_file_path)
        txt_field_obj.docx_url_field = docx_file_path
        txt_field_obj.pdf_conversion_sec = int(round(end-start,2))
        txt_field_obj.pdf_api_use = "google-ocr"
        txt_field_obj.docx_file_name = str(txt_field_obj.pdf_file_name).split('.pdf')[0]+ '.docx'
        txt_field_obj.save()
        return {"result":"finished_task"}
    except BaseException as e:
        end = time.time()
        logger.error(str(e))
        txt_field_obj.status = "ERROR"
        txt_field_obj.save()
        ###retain cred if error
        consum_cred = get_consumable_credits_for_pdf_to_docx(file_pdf_check(fp)[1])
        total_credits.credits_left = total_credits.credits_left + consum_cred
        print(file_pdf_check(fp)[1])
        total_credits.save()
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
 

def file_pdf_check(file_path):
    text = ""
    with open(file_path ,"rb") as f:
        pdf = pdftotext.PDF(f)
    for page in range(len(pdf)):
        text+=pdf[page]
    return ["text" if len(text)>=700 else "ocr" , len(pdf)]
    
def pdf_conversion(id):
    file_details = Ai_PdfUpload.objects.get(id = id)
    lang = Languages.objects.get(id=int(file_details.pdf_language)).language.lower()
    pdf_text_ocr_check = file_pdf_check(file_details.pdf_file.path)[0]
    # if lang in google_ocr_indian_language:
    if (pdf_text_ocr_check == 'ocr') or \
                (lang in google_ocr_indian_language):
        print("google ocr text",lang)
        response_result = ai_export_pdf.delay(id)
        file_details.pdf_task_id = response_result.id
        file_details.save()
        logger.info('assigned ocr ,file_name: google indian language'+str(file_details.pdf_file_name))
        return response_result.id
    # elif lang in list(lang_codes.keys()):
    elif pdf_text_ocr_check == 'text':
        response_result = convertiopdf2docx.delay(id,language = lang ,ocr = pdf_text_ocr_check)
        file_details.pdf_task_id = response_result.id
        file_details.save()
        logger.info('assigned pdf text ,file_name: convertio'+str(file_details.pdf_file_name))
        return response_result.id
    else:
        return "error"


def get_consumable_credits_for_pdf_to_docx(total_pages , formats):
    if formats == 'text':
        return int(total_pages)
    else:
        return int(total_pages)*5


# def convertio_check_credit(total_pages):
#     if total_pages <=50:
#         credit = 75
#     elif total_pages <=100:
#         credit = 150
#     else:
        
