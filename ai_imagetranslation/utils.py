from .models import *
import cv2 ,io #,torch
import numpy as np
from PIL import Image
from google.cloud import vision_v1 , vision
from google.oauth2 import service_account
import extcolors 
from django import core
# from torch.utils.data._utils.collate import default_collate
from django.conf import settings
credentials = service_account.Credentials.from_service_account_file(settings.GOOGLE_APPLICATION_CREDENTIALS_OCR)
client = vision.ImageAnnotatorClient(credentials=credentials)
from django.core.exceptions import ValidationError
import os 
import requests
IMAGE_TRANSLATE_URL = os.getenv('IMAGE_TRANSLATE_URL')
 

def image_ocr_google_cloud_vision(image_path , inpaint):
    if inpaint:
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()
        image = vision_v1.types.Image(content=content)
        response = client.text_detection(image = image)
        texts = response.full_text_annotation
        return texts

def color_extract_from_text( x,y,w,h ,pillow_image_to_extract_color):
    if w<x:x,w = w,x
    if h<y:h,y = y,h
    t= 15
    x = x-t
    y = y-t
    w = w+t
    h = h+t
    cropped_img = pillow_image_to_extract_color.crop([x,y,w,h])
    extracted_color = extcolors.extract_from_image(cropped_img ,limit=2)
    # final_color = extracted_color[0][1][0] if len(extracted_color[0]) >=2  else (extracted_color[0][0][0] if len(extracted_color[0]) <=1 else 0)
    return [i[0] for i in extracted_color[0]][::-1]

def creating_image_bounding_box(image_path):
    poly_line = []
    pillow_image_to_extract_color =  Image.open(image_path) 
    texts = image_ocr_google_cloud_vision(image_path,inpaint = True)  
    text_and_bounding_results = {}
    no_of_segments = 0
    text_list = []
    for i in  texts.pages:
        for j in i.blocks:
            x,y,w,h = j.bounding_box.vertices[0].x ,j.bounding_box.vertices[1].y ,j.bounding_box.vertices[2].x,j.bounding_box.vertices[3].y 
            vertex = j.bounding_box.vertices
            poly_line.append([[vertex[0].x ,vertex[0].y] , [vertex[1].x,vertex[1].y] ,[vertex[2].x ,vertex[2].y] ,[vertex[3].x,vertex[3].y]])
            final_color = color_extract_from_text(x,y,w,h,pillow_image_to_extract_color)
            for k in j.paragraphs:
                # text_list = [] 
                for a in  k.words:
                    text_list.append(" ") 
                    font_size = []
                    font_size2 = []  
                    for b in a.symbols:
                        text_list.append(b.text)
                        fx,fy,fw,fh  = b.bounding_box.vertices[0].x,b.bounding_box.vertices[1].y ,b.bounding_box.vertices[2].x,b.bounding_box.vertices[3].y
                        font_size.append(fh-fy)  
                        font_size2.append(fw-fx)
            text_and_bounding_results[no_of_segments] = {"text":"".join(text_list),
            "bbox":[x,y,w,h],"fontsize":sum(font_size)//len(font_size),"fontsize2":sum(font_size2)//len(font_size2),"color1":final_color ,"poly_line":poly_line}
            no_of_segments+=1
            text_list = []
    return text_and_bounding_results 
 

def image_content(image_numpy):
    _, encoded_image = cv2.imencode('.png', image_numpy)
    content = encoded_image.tobytes()
    return content

def inpaint_image(im,msk):
    headers = {}
    # 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
    # 'Content-Type': 'application/json','Accept': 'application/json'}
    data={}
    files=[
    ('image',('',open(im,'rb'),'image/jpeg')),
    ('mask',('',open(msk,'rb'),'image/png'))]
    response = requests.request("POST",IMAGE_TRANSLATE_URL, headers=headers, data=data, files=files)
    print(response.content)
    if response.status_code==200:
        arr = np.frombuffer(response.content, dtype=np.uint8)
        return {'result':arr,'code':response.status_code }
    else:
        return {'result':'error in inpaint prediction','code':response.status_code }


def inpaint_image_creation(image_details):
    img_path=image_details.image.path
    mask_path=image_details.mask.path
    mask = cv2.imread(mask_path)
    img_mode = Image.open(img_path)
    if img_mode.mode == 'RGBA':
        img_mode = img_mode.convert('RGB')
        img_mode = np.array(img_mode)
        name = image_details.image.name.split('/')[-1]
        image_byte_content= core.files.File(core.files.base.ContentFile(image_content(img_mode)),name)
        image_details.image = image_byte_content
        image_details.save()
    img = cv2.imread(img_path)
    print(mask.shape)
    print(img.shape)
    if image_details.mask:
        # image_to_extract_text = np.bitwise_and(mask ,img)
        # content = image_content(image_to_extract_text)
        # inpaint_image_file= core.files.File(core.files.base.ContentFile(content),"file.png")
        # image_details.create_inpaint_pixel_location=inpaint_image_file
        # image_details.save()
        image_text_details = creating_image_bounding_box(image_details.create_inpaint_pixel_location.path)

        output=inpaint_image(img_path, mask_path)
        if output['code']==200:
            print(output)
            res=np.reshape(output['result'],img.shape)   
            return res,image_text_details
        else:
            return ValidationError(output)
    # else:
    #     image_text_details = creating_image_bounding_box(image_details.image.path)
    #     mask_out_to_inpaint  = np.zeros((img.shape[0] , img.shape[1] ,3) , np.uint8)
    #     for i in image_text_details.values():
    #         bbox =  i['bbox']
    #         cv2.rectangle(mask_out_to_inpaint, bbox[:2], bbox[2:] , (255,255,255), thickness=cv2.FILLED)
    #     img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
    #     mask = cv2.cvtColor(mask_out_to_inpaint , cv2.COLOR_BGR2GRAY)
    #     output = inpaint_image(img_path, mask_path)
    #     output = np.reshape(output, img.shape) 
    #     return output,image_text_details


 


# def load_image(fname , mode):
#     if mode == "L":
#         # img = cv2.resize(fname, (200,200)) 
#         img = fname
#     else:
#         # fname = cv2.resize(fname, (200,200))
#         img = np.transpose(fname, (2, 0, 1))
#     out_img = img.astype('float32') / 255
#     return out_img   


# def move_to_device(obj, device):
#     if isinstance(obj, torch.nn.Module):
#         return obj.to(device)
#     if torch.is_tensor(obj):
#         return obj.to(device)
#     if isinstance(obj, (tuple, list)):
#         return [move_to_device(el, device) for el in obj]
#     if isinstance(obj, dict):
#         return {name: move_to_device(val, device) for name, val in obj.items()}
#     raise ValueError(f'Unexpected type {type(obj)}')
