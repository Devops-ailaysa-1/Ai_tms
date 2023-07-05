import requests 
from ai_canvas.models import SourceImageAssetsCanvasTranslate
from django import core
from ai_workspace_okapi.utils import get_translation
import os
import pygame
from django.core.exceptions import ValidationError
IMAGE_THUMBNAIL_CREATE_URL =  os.getenv("IMAGE_THUMBNAIL_CREATE_URL")
HOST_NAME=os.getenv("HOST_NAME")
import json ,base64
from fontTools.ttLib import TTFont
import os
import shutil
import io,re
from PIL import Image ,ImageFont


 

def calculate_font_size(box_width, box_height,text,font_size):
    while True:
        font = ImageFont.truetype("arial.ttf", font_size)
        text_width, text_height = font.getbbox(text)[2:]
        if text_width <= box_width and text_height <= box_height:
            break
        font_size -= 1
    return font_size

# from google.cloud import translate_v2 as translate

# def get_translation_canvas(source_string,target_lang_code):
#     client = translate.Client(credentials=credentials)
#     if isinstance(source_string ,str):
#         return client.translate(source_string,target_language=target_lang_code,format_="text").get("translatedText")
#     elif isinstance(source_string,list):
#         source_string_list= client.translate(source_string,target_language=target_lang_code,format_="text")
#         return [translated_text['translatedText'] for translated_text in source_string_list]


def json_src_change(json_src ,req_host,instance):
    req_host_url = str(req_host)
    src_obj = json_src['objects']
    for i in src_obj:
        if 'src' in i.keys():
            image_url = i['src']
            image_extention ="."+image_url.split('.')[-1]
            if req_host_url not in image_url:
                req=requests.get(image_url).content
                src_img_assets_can = SourceImageAssetsCanvasTranslate.objects.create(canvas_design_img=instance)
                src_file=core.files.File(core.files.base.ContentFile(req),"file"+image_extention)
                src_img_assets_can.img =src_file
                src_img_assets_can.save()
                i['src'] = 'https://'+req_host_url+src_img_assets_can.img.url #
                # print("src_url",i['src'])
        if 'objects' in i.keys():
            json_src_change(i,req_host,instance)
        else:
            break
    return json_src



def calculate_textbox_dimensions(text,font_size,bold,italic): #
    font_size=int(font_size)
    pygame.init()
    # font=0
    font = pygame.font.SysFont("Arial.ttf", font_size) #,bold=bold,italic=italic
    text_surface = font.render(text, True, (0, 0, 0))  # Render the text on a surface
    textbox_width = text_surface.get_width()
    textbox_height = text_surface.get_height()
    pygame.quit()
    return textbox_width, textbox_height


def calculate_font_size(box_width, box_height, text,font_size):
    font_size=int(font_size)
    while True:
        font = ImageFont.truetype("NotoSans-Regular.ttf",font_size)
        text_width, text_height = font.getbbox(text)[2:]
        if text_width <= box_width and text_height <= box_height:
            break
        font_size -= 1
    return font_size



def canva_group(_dict,src_lang ,lang):
    for count , grp_data in enumerate(_dict):
        if grp_data['type']== 'textbox':
            grp_data['text'] = get_translation(1,source_string = grp_data['text'],source_lang_code=src_lang ,target_lang_code = lang.strip())
        if grp_data['type'] == 'group':
            canva_group(grp_data['objects'])


def canvas_translate_json_fn(canvas_json,src_lang,languages):
    # print("canvas_json")
    # print(canvas_json)
    false = False
    null = 'null'
    true = True
    languages = languages.split(",")
    canvas_json_copy =canvas_json
    # fontSize=canvas_json_copy['fontSize']
    # height=canvas_json_copy['height']
    # width=canvas_json_copy['width']
    canvas_result = {}
    
    for lang in languages:
        if 'template_json' in  canvas_json_copy.keys():
            for count , i in enumerate(canvas_json_copy['template_json']['objects']):
                if i['type']== 'textbox':
                    text = i['text'] 
                    fontSize=canvas_json_copy['objects'][count]['fontSize']
                    tar_word=get_translation(1,source_string=text,source_lang_code=src_lang,target_lang_code = lang.strip())
                    canvas_json_copy['objects'][count]['text']=tar_word

                    # text_width, text_height=calculate_textbox_dimensions(text,fontSize,bold=False,italic=False)
                    # font_size=calculate_font_size(text_width, text_height,tar_word,fontSize)
                    font_size=32
                    canvas_json_copy['objects'][count]['fontSize']=font_size
 
                if i['type'] == 'group':
                    canva_group(i['objects'])
        else:
            for count , i in enumerate(canvas_json_copy['objects']):
                if i['type']== 'textbox':
                    text = i['text'] 
                    fontSize=canvas_json_copy['objects'][count]['fontSize']
                    tar_word=get_translation(1,source_string = text,source_lang_code=src_lang,target_lang_code = lang.strip())
                    canvas_json_copy['objects'][count]['text'] =  tar_word
                    
                    # text_width, text_height=calculate_textbox_dimensions(text,fontSize,bold=False,italic=False)
                    # font_size=calculate_font_size(text_width, text_height,tar_word,fontSize)
                    font_size=34
                    canvas_json_copy['objects'][count]['fontSize']=font_size
 
                    # fontSize=calculate_font_size(box_width=width, box_height=height,text=tar_word,font_size=fontSize)
                    # canvas_json_copy['fontSize']=fontSize
                    if i['type'] == 'group':
                        canva_group(i['objects'])
        canvas_result[lang] = canvas_json_copy
    return canvas_result



def thumbnail_create(json_str,formats):
    all_format=['png','jpeg','jpg','svg']
    width=json_str['backgroundImage']['width']
    height=json_str['backgroundImage']['height']

    if formats=='mask':
        multiplierValue=1
    elif formats in all_format:
        multiplierValue=min([300 /width, 300 / height])

    json_=json.dumps(json_str)
    data={'json':json_ , 'format':formats,'multiplierValue':multiplierValue}
    thumb_image=requests.request('POST',url=IMAGE_THUMBNAIL_CREATE_URL,data=data ,headers={},files=[])

    if thumb_image.status_code ==200:
        split_text_base64 = thumb_image.text.split(",")[-1]
        b64_bytes = base64.b64decode(split_text_base64)
        return b64_bytes
    else:
        return ValidationError("error in node server")

url_pattern = r'xlink:href="([^"]+)"'
def svg_convert_base64(response_text):
    matches = re.findall(url_pattern, response_text)
    for match in matches:
        response = requests.get(match)
        format=match.split(".")[-1]
        image_data = response.content
        base64_data = base64.b64encode(image_data).decode('utf-8')
        response_text = response_text.replace(match, f'data:image/{format};base64,{base64_data}')
    return response_text
    
    

def export_download(json_str,format,multipliervalue):
    json_ = json.dumps(json_str)
    if format in ["png","jpeg"]:
        data = {'json':json_ , 'format':'png','multiplierValue':multipliervalue}
     
    elif format =='svg':
        data = {'json':json_ ,'format':'svg'}


        
    thumb_image = requests.request('POST',url=IMAGE_THUMBNAIL_CREATE_URL,data=data ,headers={},files=[])
 
    if thumb_image.status_code ==200:
        if format=='svg':
            compressed_data=svg_convert_base64(thumb_image.text)
        else:
            im_file = io.BytesIO(base64.b64decode(thumb_image.text.split(",")[-1]))
            img = Image.open(im_file)
            output_buffer=io.BytesIO()
            if format=='jpeg':
                img = img.convert('RGB')
            img.save(output_buffer, format=format.upper(), optimize=True, quality=85)
            compressed_data=output_buffer.getvalue()
        return compressed_data
    else:
        return ValidationError("error in node server")

####font_creation

def install_font(font_path):
    install_dir="/usr/share/fonts/truetype"
    font=TTFont(font_path)
    family_name=font["name"].getName(1, 3, 1, 1033).toUnicode()
    destination_path=os.path.join(install_dir, family_name)
    os.makedirs(destination_path,exist_ok=True)
    font_filename=os.path.basename(font_path)
    destination_file_path=os.path.join(destination_path, font_filename)
    shutil.copy(font_path,destination_file_path)
    os.system("fc-cache -f -v")
    # print(f"Font '{family_name}' installed successfully!")
    return family_name

def convert_image_url_to_file(image_url,no_pil_object=True):
    img_io = io.BytesIO()
    if no_pil_object:
        im=Image.open(requests.get(image_url, stream=True).raw)
        im.save(img_io, format='PNG')
        img_byte_arr = img_io.getvalue()
        return core.files.File(core.files.base.ContentFile(img_byte_arr),image_url.split('/')[-1])
    else:
        im=image_url
        im.save(img_io, format='PNG')
        img_byte_arr = img_io.getvalue()
        return core.files.File(core.files.base.ContentFile(img_byte_arr),"thumbnail.png")


def json_sr_url_change(json,instance):
    for i in json['objects']:
        if ('type' in i.keys()) and (i['type'] =='image') and ('src' in i.keys()) and ("ailaysa" not in  i['src']):
                third_party_url=i['src']
                image=convert_image_url_to_file(third_party_url)
                src_img_assets_can = SourceImageAssetsCanvasTranslate.objects.create(canvas_design_img=instance,img=image)
                i['src']=HOST_NAME+src_img_assets_can.img.url
        if 'objects' in i.keys():
            json_sr_url_change(i,instance)
    return json



def paginate_items(items, page_number, items_per_page):
    total_items = len(items)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    if page_number < 1 or page_number > total_pages:
        raise ValueError("Invalid page number")
    start_index = (page_number - 1) * items_per_page
    end_index = start_index + items_per_page
    paginated_items = items[start_index:end_index]
    return paginated_items, total_pages
