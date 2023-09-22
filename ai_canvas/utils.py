import requests 
from ai_canvas.models import SourceImageAssetsCanvasTranslate,TextboxUpdate
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

# HOST_NAME="http://localhost:8091"


 

# def calculate_font_size(box_width, box_height,text,font_size):
#     while True:
#         font = ImageFont.truetype("arial.ttf", font_size)
#         text_width, text_height = font.getbbox(text)[2:]
#         if text_width <= box_width and text_height <= box_height:
#             break
#         font_size -= 1
#     return font_size

# from google.cloud import translate_v2 as translate

# def get_translation_canvas(source_string,target_lang_code):
#     client = translate.Client(credentials=credentials)
#     if isinstance(source_string ,str):
#         return client.translate(source_string,target_language=target_lang_code,format_="text").get("translatedText")
#     elif isinstance(source_string,list):
#         source_string_list= client.translate(source_string,target_language=target_lang_code,format_="text")
#         return [translated_text['translatedText'] for translated_text in source_string_list]


def json_src_change(json_src ,req_host,instance,text_box_save):
    req_host_url = str(req_host)
    for i in json_src['objects']:
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
        if i['type']== 'textbox': ####to check the type of object from canvas_json
            i['isTranslate']=True
            # if text_box_save:
            #     TextboxUpdate.objects.create(canvas=instance,text=i['text'],text_id=i['name'])

        if 'objects' in i.keys():
            json_src_change(i,req_host,instance,text_box_save=True)
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
    return font_size+15

def canva_group(_dict,src_lang ,lang):
    for count , grp_data in enumerate(_dict):
        if grp_data['type']== 'textbox':
            grp_data['text'] = get_translation(1,source_string = grp_data['text'],source_lang_code=src_lang ,target_lang_code = lang.strip())
        if grp_data['type'] == 'group':
            canva_group(grp_data['objects'])


def dict_rec(canvas_json_copy,languages,src_lang):
 
    if 'template_json' in  canvas_json_copy.keys():
        for count, i in enumerate(canvas_json_copy['template_json']['objects']):
            if 'objects' in i.keys():
                dict_rec(i,languages,src_lang)
            if i['type']== 'textbox':
                fontSize=canvas_json_copy['objects'][count]['fontSize']
                tar_word=get_translation(1,source_string=text,source_lang_code=src_lang,target_lang_code = languages.strip())
                canvas_json_copy['objects'][count]['text']=tar_word
                canvas_json_copy['objects'][count]['rawMT']=tar_word
                if languages == 'ar':
                    # canvas_json_copy['objects'][count]['direction']='rtl'
                    canvas_json_copy['objects'][count]['textAlign']="right"
                text_width, text_height=calculate_textbox_dimensions(text,fontSize,bold=False,italic=False)
                font_size=calculate_font_size(text_width, text_height,tar_word,fontSize)
                canvas_json_copy['objects'][count]['fontSize']=font_size
 
    else:
        for count, i in enumerate(canvas_json_copy['objects']):
            if 'objects' in i.keys():
                dict_rec(i,languages,src_lang)
            if i['type']== 'textbox':
                text = i['text']
                fontSize=canvas_json_copy['objects'][count]['fontSize']
                tar_word=get_translation(1,source_string = text,source_lang_code=src_lang,target_lang_code = languages.strip())
                canvas_json_copy['objects'][count]['text']=tar_word
                canvas_json_copy['objects'][count]['rawMT']=tar_word
                if languages == 'ar':
                    # canvas_json_copy['objects'][count]['direction']='rtl'
                    canvas_json_copy['objects'][count]['textAlign']="right"
                text_width, text_height=calculate_textbox_dimensions(text,fontSize,bold=False,italic=False)
                font_size=calculate_font_size(text_width, text_height,tar_word,fontSize)
                canvas_json_copy['objects'][count]['fontSize']=font_size
    return canvas_json_copy


def canvas_translate_json_fn(canvas_json,src_lang,languages):
    languages = languages.split(",")
    canvas_result = {}
    for lang in languages:
        canvas_json_copy =copy.deepcopy(canvas_json)
        canvas_json_copy = dict_rec(canvas_json_copy,lang,src_lang)
        canvas_result[lang] = canvas_json_copy
    return canvas_result
    
         

# def canvas_translate_json_fn(canvas_json,src_lang,languages):
#     false = False
#     null = 'null'
#     true = True
#     languages = languages.split(",")
#     canvas_json_copy =copy.deepcopy(canvas_json)
#     # height=canvas_json_copy['height']
#     # width=canvas_json_copy['width']
#     canvas_result = {}
#     for lang in languages:
#         if 'template_json' in  canvas_json_copy.keys():
#             for count , i in enumerate(canvas_json_copy['template_json']['objects']):
#                 if i['type']== 'textbox':
#                     text = i['text'] 
#                     fontSize=canvas_json_copy['objects'][count]['fontSize']
#                     tar_word=get_translation(1,source_string=text,source_lang_code=src_lang,target_lang_code = lang.strip())
#                     canvas_json_copy['objects'][count]['text']=tar_word
#                     canvas_json_copy['objects'][count]['rawMT']=tar_word
#                     if lang == 'ar':
#                         # canvas_json_copy['objects'][count]['direction']='rtl'
#                         canvas_json_copy['objects'][count]['textAlign']="right"

#                     text_width, text_height=calculate_textbox_dimensions(text,fontSize,bold=False,italic=False)
#                     font_size=calculate_font_size(text_width, text_height,tar_word,fontSize)
#                     canvas_json_copy['objects'][count]['fontSize']=font_size
#                 if i['type'] == 'group':
#                     canva_group(i['objects'])
#         else:
#             for count , i in enumerate(canvas_json_copy['objects']):
#                 if i['type']== 'textbox':
#                     text = i['text'] 
#                     fontSize=canvas_json_copy['objects'][count]['fontSize']
#                     tar_word=get_translation(1,source_string = text,source_lang_code=src_lang,target_lang_code = lang.strip())
#                     canvas_json_copy['objects'][count]['text']=tar_word
#                     canvas_json_copy['objects'][count]['rawMT']=tar_word
#                     if lang == 'ar':
#                         # canvas_json_copy['objects'][count]['direction']='rtl'
#                         canvas_json_copy['objects'][count]['textAlign']="right"
#                     text_width, text_height=calculate_textbox_dimensions(text,fontSize,bold=False,italic=False)
#                     font_size=calculate_font_size(text_width, text_height,tar_word,fontSize)
#                     canvas_json_copy['objects'][count]['fontSize']=font_size
#                     if i['type'] == 'group':
#                         canva_group(i['objects'])
#         canvas_result[lang] = canvas_json_copy
#     return canvas_result


def thumbnail_create(json_str,formats):
    all_format=['png','jpeg','jpg','svg']
    width=json_str['backgroundImage']['width']
    height=json_str['backgroundImage']['height']

    if formats=='mask' or formats=='backgroundMask':
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
    
    
import copy
from ai_canvas.cmyk_conversion import convertImage
def export_download(json_str,format,multipliervalue,base_image=False):
    dpi = (96,96)
    json_ = json.dumps(json_str)
    print("format__form_export_download",format)
    format = 'pdf' if format=='pdf-standard' else format

    if format in ["png","jpeg","pdf",'jpeg-print']:
        multipliervalue=3 if format=='jpeg-print' else multipliervalue
        data = {'json':json_ , 'format':'png','multiplierValue':multipliervalue}
    
    elif format =='svg':
        data = {'json':json_ ,'format':'svg'}

    elif format=='png-transparent':
        json_trans = copy.deepcopy(json_str)
        json_trans['background']='transparent'
        json_trans['backgroundImage']['fill']='transparent'
        # json_trans['backgroundImage']['globalCompositeOperation'] ='source-over' #
        for i in json_trans['objects']:
            if 'globalCompositeOperation' in i.keys():
                i['globalCompositeOperation']='source-over'
        json_ = json.dumps(json_trans)
        format='png'
        data = {'json':json_ , 'format':format,'multiplierValue':multipliervalue}

    elif format == 'pdf-print':
        dpi=(300,300)
        data = {'json':json_ , 'format':'png','multiplierValue':3,'dpi':dpi[0]}
        
    thumb_image = requests.request('POST',url=IMAGE_THUMBNAIL_CREATE_URL,data=data ,headers={},files=[])
    if not base_image:
        if thumb_image.status_code ==200:
            if format=='svg':
                compressed_data=svg_convert_base64(thumb_image.text)
            else:
                im_file = io.BytesIO(base64.b64decode(thumb_image.text.split(",")[-1]))
                img = Image.open(im_file)
                output_buffer=io.BytesIO()
                if format=='jpeg':
                    img = img.convert('RGB')
                if format == 'jpeg-print':
                    img=convertImage(im_file).image
                    format='jpeg'
                    dpi=(300,300)
                if format == 'pdf' and img.mode == 'RGBA':
                    img = img.convert('RGB')
                if format == 'pdf-print':
                    img=convertImage(im_file).image
                    format='pdf'
                img.save(output_buffer, format=format.upper(),dpi=dpi)
                compressed_data=output_buffer.getvalue()
            return compressed_data 
        else:
            return ValidationError("error in node server")
    return thumb_image.text

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

def convert_image_url_to_file(image_url,no_pil_object=True,name="thumbnail.png",transparent=True):
    
    if no_pil_object:
        im=Image.open(requests.get(image_url, stream=True).raw)
        print(im)
        im=im.convert("RGB")
        name=image_url.split('/')[-1]
        print("name",name)
        # im.save(img_io, format='PNG')
        # img_byte_arr = img_io.getvalue()
        # return core.files.File(core.files.base.ContentFile(img_byte_arr),)
    else:
        im=image_url
        if transparent:
            im=im.convert("RGB")
    img_io = io.BytesIO()
    im.save(img_io, format='PNG')
    img_byte_arr = img_io.getvalue()
    print("im_by_crted")
    return core.files.File(core.files.base.ContentFile(img_byte_arr),name)


def json_sr_url_change(json,instance):
    for i in json['objects']:
        if ('type' in i.keys()) and (i['type'] =='image') and ('src' in i.keys()) and ("ailaysa" not in  i['src']):
            third_party_url=i['src']
            print(third_party_url)
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



def download_font(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        print(f"Failed to download font from {url}")
        return None

def convert_to_base64(font_url):
    font_data = download_font(font_url)
    if font_data:
        return base64.b64encode(font_data).decode("utf-8")
    return None



def replace_url_with_base64(input_string):
    font_url_pattern = r"url\('([^']+)'\)"
    font_urls = re.findall(font_url_pattern, input_string)
    for url in font_urls:
        base64_data = convert_to_base64(url)
        if base64_data:
            input_string = input_string.replace(url, f"data:application/font-ttf;base64,{base64_data}")
    return input_string

# import random

# def generate_random_rgba():
#     r = random.randint(0, 255)
#     g = random.randint(0, 255)
#     b = random.randint(0, 255)
#     a=1
#     return f"rgba({r}, {g}, {b}, {a})"

# def create_thumbnail(json_str,formats):
#     all_format=['png','jpeg','jpg','svg']
#     width=json_str['backgroundImage']['width']
#     height=json_str['backgroundImage']['height']

#     if formats=='mask' or formats=='backgroundMask':
#         multiplierValue=1
#     elif formats in all_format:
#         multiplierValue=min([300 /width, 300 / height])

#     json_=json.dumps(json_str)
#     data={'json':json_ , 'format':formats,'multiplierValue':multiplierValue}
#     thumb_image=requests.request('POST',url=IMAGE_THUMBNAIL_CREATE_URL,data=data ,headers={},files=[])

#     if thumb_image.status_code ==200:
#         return thumb_image.text
#     else:
#         return ValidationError("error in node server")
    

# def grid_position(width, height):
#     rows=5
#     cols=5
#     cell_width = width // rows
#     cell_height = height // cols
#     text= []
#     image=[]
#     for row in range(rows):
#         for col in range(cols):
#             if (row !=0 and row != rows-1) and (col !=0 and col != cols-1):
#                 grid=[]
#                 grid.append(row * cell_height)
#                 grid.append(col * cell_width)
#                 image.append(grid)
#             elif (row ==0 or row == rows-1)  and (col !=0 and col != cols-1):
#                 grid1 = []
#                 if row ==0:
#                     grid1.append(row * cell_height+(height/10))
#                 else:
#                     grid1.append(row * cell_height-(height/10))
#                 grid1.append(col * cell_width)
#                 text.append(grid1)
#     return text,image

# def clip_position(width, height,rows,cols):
#     cell_width = width // rows
#     cell_height = height // cols
#     co_oridination = []
#     for row in range(rows):
#         for col in range(cols):
#             grid = []
#             grid.append(row * cell_height)
#             grid.append(col * cell_width)
#             co_oridination.append(grid)
#     return co_oridination

# from .template import image,textbox,backgroundImage,path,clipPath,backgroundHardboard
# import random
# from .meta import *
# from ai_staff.models import FontFamily,FontData

# def genarate_image(instance,image_grid,template):
#     print(instance)
#     temp_height =int(template.height)
#     temp_width = int(template.width)
#     x=temp_width*3/4
#     y=temp_height*3/4
   
#     # image=copy.deepcopy(image)
#     # text_grid,image_grid=grid_position(temp_width,temp_height)
#     pos= image_grid.pop(random.randint(0,(len(image_grid)-1)))
#     img=copy.deepcopy(image)
#     img["src"]=HOST_NAME+instance.image.url
#     print("img---->", img["src"])
#     # img["src"]="https://aicanvas.ailaysa.com/media/stable-diffusion-image/0-e084f77d-fb66-4f66-b874-fa5786c70b0d.png"
#     # bg_remove=backgroundremo
#     img["name"]="Image"+str(pos[0])+str(pos[1])
#     if instance.width<instance.height:
#         scale=(x/int(instance.width))
#     else:
#         scale=(y/int(instance.height))
#     img["scaleX"]=img["scaleY"]=scale
#     img["oldScaleX"]=img["oldScaleY"]=scale

#     img["width"]=img["oldWidth"]=instance.height*scale
#     img["height"]=img["oldHeight"]=instance.width*scale
#     img["top"]=image_grid[0][0]
#     img["left"]=image_grid[0][1]
#     return img

# def genarate_text(font_family,prompt,text_grid,template):
#         temp_height =int(template.height)
#         temp_width = int(template.width)
#         text=copy.deepcopy(textbox)
#         # text_grid,image_grid=grid_position(temp_width,temp_height)
#         text["fill"] =generate_random_rgba()
#         # text["fontStyle"] =
#         text["fontFamily"] =font_family[random.randint(0,(len(font_family)-1))]
#         text["fontWeight"] =font["fontWeight"][random.randint(0,2)]
#         # textline=prompt.capitalize().split(" ")
#         # text=prompt.split(" ")
#         text["textLines"]=prompt
#         text["text"]=prompt.capitalize()
#         text["width"]=500
#         text["height"]=90
#         text["fontSize"]=random.randint(100,300)

#         pos= text_grid.pop(random.randint(0,(len(text_grid)-1)))
#         text["top"]= pos[0]
#         text["left"]= pos[1]
#         return text

# def random_background_image(template,instance):
#     bg_image=copy.deepcopy(backgroundImage)
#     temp_height =int(template.height)
#     temp_width = int(template.width)
#     bg_image["src"]=HOST_NAME+instance.bg_image.url
#     print(bg_image["src"])
#     scaleX, scaleY, left, top = background_scaling(temp_width, temp_height, instance.width, instance.height)


#     if instance.width<instance.height:
#         scale=(temp_width/int(instance.width))
#     else:
#         scale=(temp_height/int(instance.height))

#     img_width=instance.width*scale
#     img_height=instance.height*scale
#     # bg_image["src"]=instance.image.url
#     bg_image["width"]=img_width
#     bg_image["height"]=img_height

#     # bg_image["scaleX"]=bg_image=scaleX
#     # bg_image["oldScaleX"]=bg_image["oldScaleY"]=scaleY

#     bg_image["scaleX"]=bg_image["oldScaleX"]=scaleX
#     bg_image["scaleY"]=bg_image["oldScaleY"]=scaleY

#     bg_image["top"]=top
#     bg_image["left"]=left

#     """backgroud as colr"""
#     # bg=copy.deepcopy(backgroundHardboard)
#     # random_color= random.randint(0, 19)
#     # bg["fill"]=generate_random_rgba()
#     # bg["width"]=int(temp_width)
#     # bg["height"]=int(temp_height)

#     return bg_image

# def genarate_text(font_family,instance,text_grid,template,attr,color_attr):
#         temp_height =int(template.height)
#         temp_width = int(template.width)
#         text=copy.deepcopy(textbox)
#         custom_style=attr["textbox"]
#         text=custom_attr(text,custom_style)
#         text["textLines"]=instance.prompt
#         text["text"]=instance.prompt.capitalize()
#         text["fill"]=color_attr["textbox"]
#         return text

# def background_scaling(canvas_width, canvas_height, image_width, image_height):
#     scaleX, scaleY, left, top = 0, 0, 0, 0
    
#     if canvas_width > canvas_height:  # Landscape image
#         scaleX = canvas_width / image_width
#         scaleY = canvas_width / image_width
#         left = 0
#         top = (canvas_height - (image_height * scaleY)) / 2
#     elif canvas_width == canvas_height:
#         if image_width >= image_height:  # Landscape image
#             scaleX = canvas_height / image_height
#             scaleY = canvas_height / image_height
#             left = (canvas_width - (image_width * scaleX)) / 2
#             top = 0
#         else:  # Portrait image
#             scaleX = canvas_width / image_width
#             scaleY = canvas_width / image_width
#             left = 0
#             top = (canvas_height - (image_height * scaleY)) / 2
#     else:  # Portrait image
#         scaleX = canvas_height / image_height
#         scaleY = canvas_height / image_height
#         left = (canvas_width - (image_width * scaleX)) / 2
#         top = 0
        
#     return scaleX, scaleY, left, top

"""-------------------------------------------------------------------------------"""

# def random_background_image(bg_image,template,instance,style_attr):
    # temp_height =int(template.height)
    # temp_width = int(template.width)
    # background_image=[]
    # custom_style=style_attr["backgroundImage"]
    # # bg_image=custom_attr(bg_image,custom_style)
    # print(len(instance),len(style_attr["backgroundImage"]))
    # for instance in instance:
    #     # bg_image["src"]=HOST_NAME+instance.bg_image.url
    #     # for testing
    #     bg_image["src"]="https://aicanvas.ailaysa.com/media/backround-template/green-background-with-marbled-vintage-grunge.png"
    #     scaleX, scaleY, left, top = background_scaling(temp_width, temp_height, instance.width, instance.height)

    #     img_width=instance.width
    #     img_height=instance.height
    #     rand=random.randint(0,len(style_attr["backgroundImage"])-1)
    #     obj=style_attr["backgroundImage"].pop(rand)
    #     for key, value in obj.items():
    #         bg_image[key]=obj[key]

    #     bg_image["width"]=img_width
    #     bg_image["height"]=img_height
        
    #     bg_image["oldWidth"]=bg_image["originalWidth"]=img_width
    #     bg_image["oldHeight"]=bg_image["originalheight"]=img_height
    #     bg_image["scaleX"]=bg_image["oldScaleX"]=scaleX
    #     bg_image["scaleY"]=bg_image["oldScaleY"]=scaleY

    #     bg_image["top"]=top
    #     bg_image["left"]=left

    #     background_image.append(bg_image)

    # return background_image

# def genarate_image(instance,image_grid,template,style_attr):
#     from ai_imagetranslation.utils import background_remove
#     # print(instance)
#     temp_height =int(template.height)
#     temp_width = int(template.width)
#     x=temp_width/2
#     y=temp_height/2
#     # instance=PromptEngine.objects.filter(id=19).first()
#     pos= image_grid.pop(random.randint(0,(len(image_grid)-1)))
#     picture=[]
#     for instance in instance:
#         img=copy.deepcopy(image)
#         """mask"""
#         if instance.mask==None or instance.backround_removal_image ==None:
#             print("masking...........................")
#             rem_img=background_remove(instance)
#             instance.backround_removal_image=rem_img
#             instance.save()   

#         img["name"]="Image"+str(pos[0])+str(pos[1])
#         if instance.width <= instance.height:
#             scale=(x/int(instance.width))
#         else:
#             scale=(y/int(instance.height))


#         rand=random.randint(0,len(style_attr["image"])-1)
#         obj=style_attr["image"].pop(rand)
#         for key, value in obj.items():
#            img[key]=obj[key]

#         img["scaleX"]=img["scaleY"]=scale
#         img["oldScaleX"]=img["oldScaleY"]=scale
#         img["width"]=img["oldWidth"]=instance.width
#         img["height"]=img["oldHeight"]=instance.height

#         # imge=custom_attr(img,attr["image"])
#         if img["clipPath"]:
#             print("clip_path...............")
            
#             path_string=img["clipPath"]
#             img["clipPath"]=get_clip_path(path_string)
#             img["id"]="background"
#             img["src"]=HOST_NAME+instance.image.url
            
#             # img["src"]="https://aicanvas.ailaysa.com/media/prompt-image/0-20cd0623-a4d3-41f1-8cfc-b7547d40371a.png"
#         else:
#             # img["src"] ="https://aicanvas.ailaysa.com/media/u124698/background_removel/background_remove_SEpEE1y.png"
#             img["sourceImage"]=HOST_NAME+instance.image.url
#             img["bgMask"]=HOST_NAME+instance.mask.url
#             img["src"]=HOST_NAME+instance.backround_removal_image.url
#             img["brs"]=2

#         picture.append(img)

#     return picture


# def genarate_text(font_family,instance,text_grid,template,attr,color_attr):
#         temp_height =int(template.height)
#         temp_width = int(template.width)
#         text_box=[]
#         for instance in instance:
#             text=copy.deepcopy(textbox)
#             custom_style=attr["textbox"]
#             text=custom_attr(text,custom_style)
#             text["textLines"]=instance.prompt
#             text["text"]=instance.prompt.capitalize()
#             text["fill"]=color_attr["textbox"]
#             text_box.append(text)
#         return text_box

"""--------------------------------------------------------------------------------------------"""


# def scaletemplate(data,temp_height,temp_json_height,temp_json_width,temp_width):
#     template_json=data
    # if (temp_height!=temp_json_height):
    #     scale_y=temp_height/temp_json_height
    #     for element in template_json["objects"]:
    #         element["scaleY"] *= scale_y
    #         if "height" in element:
    #             element["height"] *= scale_y
    # if (temp_width!=temp_json_width):
    #     scale_x=temp_width/temp_json_width
    #     for element in template_json["objects"]:
    #         element["scaleX"] *= scale_x
    #         if "width" in element:
    #             element["width"] *= scale_x

    # if (temp_width!=temp_json_width) or (temp_width!=temp_json_width):
    #     scale_y=temp_height/temp_json_height
    #     scale_x=temp_width/temp_json_width
    #     scale=min(scale_y,scale_x)
    #     for element in template_json["objects"]:
    #         element["scaleX"] *= scale
    #         element["scaleY"] *= scale
    #         if temp_height>temp_width:
    #             if "height" in element:
    #                 element["height"] *= scale
    #             else:
    #                 element["width"] *= scale

    # scale_multiplier_x=temp_width/temp_json_width
    # scale_multiplier_y=temp_height/temp_json_height
    # for i in template_json['objects']:
    #     i['scaleX']=i['scaleX']*scale_multiplier_x
    #     i['scaleY']=i['scaleY']*scale_multiplier_x
    #     i['left']=i['left']*scale_multiplier_x
    #     i['top']=i['top']*scale_multiplier_y
#     return template_json

# from ai_canvas.color import Color_Palettes

# def get_color_combinations(colors):

#     min_contrast_ratio = 7
#     color_combinations= []
#     for i in range(0,len(colors)):
#         for text_color in colors[i]:
#             for background_color in colors[i]:
#                 if text_color != background_color:
#                     contrast_ratio = calculate_contrast_ratio(text_color, background_color)
#                     contrast_ratio2 = calculate_contrast_ratio(background_color,text_color,)

#                     if contrast_ratio >= min_contrast_ratio:
#                         color_combinations.append({i:[text_color, background_color]})
#                     if contrast_ratio2 >= min_contrast_ratio:
#                         color_combinations.append({i:[background_color,text_color]})
#     return color_combinations

# def calculate_contrast_ratio(color1, color2):
#     def relative_luminance(rgba_color):
#         color=rgba_string_to_tuple(rgba_color)
#         r, g, b,a = color
#         r = r / 255.0 if r <= 255 else 1.0
#         g = g / 255.0 if g <= 255 else 1.0
#         b = b / 255.0 if b <= 255 else 1.0
#         r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
#         g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
#         b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
#         return 0.2126 * r + 0.7152 * g + 0.0722 * b
#     L1 = relative_luminance(color1)
#     L2 = relative_luminance(color2)

#     contrast_ratio = (L1 + 0.05) / (L2 + 0.05)
#     return contrast_ratio

# import re
# def rgba_string_to_tuple(rgba_str):
#   match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)', rgba_str)
#   if match:
#     red = int(match.group(1))
#     green = int(match.group(2))
#     blue = int(match.group(3))
#     alpha = float(match.group(4))
#     alpha = int(alpha * 255)
#     return (red, green, blue, alpha)
#   else:
#     raise ValueError("Invalid color format")