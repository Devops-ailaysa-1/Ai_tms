from .models import *
from PIL import Image
from google.cloud import vision_v1,vision
from google.oauth2 import service_account
import extcolors 
from django import core
# from torch.utils.data._utils.collate import default_collate
from django.conf import settings
credentials=service_account.Credentials.from_service_account_file(settings.GOOGLE_APPLICATION_CREDENTIALS_OCR)
client = vision.ImageAnnotatorClient(credentials=credentials)
from django.core.exceptions import ValidationError
import os 
import requests
import cv2,requests,base64,io 
from PIL import Image
import numpy as np
from io import BytesIO
from rest_framework import serializers
from ai_canvas.template_json import textbox_json
import copy
import uuid,math
# from ai_canvas.serializers import TemplateGlobalDesignSerializer


IMAGE_TRANSLATE_URL = os.getenv('IMAGE_TRANSLATE_URL')
BACKGROUND_REMOVAL_URL= os.getenv('BACKGROUND_REMOVAL_URL')

def image_ocr_google_cloud_vision(image_path , inpaint):
    if inpaint:
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()
        image = vision_v1.types.Image(content=content)
        response = client.text_detection(image = image)
        texts = response.full_text_annotation   #full_text_annotation
        return texts

def color_extract_from_text( x,y,w,h ,pillow_image_to_extract_color):
    if w<x:x,w=w,x
    if h<y:h,y=y,h
    t= 15
    x = x-t
    y = y-t
    w = w+t
    h = h+t
    cropped_img=pillow_image_to_extract_color.crop([x,y,w,h])
    extracted_color=extcolors.extract_from_image(cropped_img ,limit=2)
    # final_color = extracted_color[0][1][0] if len(extracted_color[0]) >=2  else (extracted_color[0][0][0] if len(extracted_color[0]) <=1 else 0)
    return [i[0] for i in extracted_color[0]][::-1] #if i[0]!=(0,0,0)


def creating_image_bounding_box(image_path,color_find_image_diff):
    poly_line = []
    # pillow_image_to_extract_color=Image.open(image_path)  #color_find_image_diff
    pillow_image_to_extract_color=Image.fromarray(color_find_image_diff)
    texts=image_ocr_google_cloud_vision(image_path,inpaint=True)  
    text_and_bounding_results={}
    no_of_segments=0
    text_list=[]
    text_box_list=[]
    for i in  texts.pages:
        # x,y,w,h=i.bounding_box.vertices[0].x ,i.bounding_box.vertices[1].y,i.bounding_box.vertices[2].x,i.bounding_box.vertices[3].y 
        for j in i.blocks:
            count=0
            text_uuid=uuid.uuid4()
            textbox_=copy.deepcopy(textbox_json)
            name="Textbox_"+(str(text_uuid))
            textbox_['id']="text_"+(str(text_uuid))
            count+=1
            textbox_['name']=name
            x,y,w,h=j.bounding_box.vertices[0].x ,j.bounding_box.vertices[1].y,j.bounding_box.vertices[2].x,j.bounding_box.vertices[3].y 
            textbox_['left']=x
            textbox_['top']=y
            textbox_['width']=w-x
            textbox_['height']=h
            final_color=color_extract_from_text(x,y,w,h,pillow_image_to_extract_color)
            for k in j.paragraphs:
                for a in k.words:
                    text_list.append(" ") 
                    font_size=[]
                    font_size2=[]  
                    for b in a.symbols:
                        text_list.append(b.text)
                        fx,fy,fw,fh=b.bounding_box.vertices[0].x,b.bounding_box.vertices[1].y,b.bounding_box.vertices[2].x,b.bounding_box.vertices[3].y
                        font_size.append(fh-fy)  
                        font_size2.append(fw-fx)
                    text_and_bounding_results[no_of_segments]={"text":"".join(text_list),"bbox":[x,y,w,h],"fontsize":sum(font_size)//len(font_size),
                                                            "fontsize2":sum(font_size2)//len(font_size2),"color1":final_color}
                                                            # "poly_line":poly_line}
                    textbox_['text']="".join(text_list).strip()
                    print("text-------------->>","".join(text_list))
                    textbox_['fill']="rgb{}".format(tuple(final_color[0]))
                    # textbox_['angle']=arrival_angle
                    font=max([sum(font_size)//len(font_size),sum(font_size2)//len(font_size2)])+5
                    textbox_['fontSize']=font
                    no_of_segments+=1
                    text_list=[]
                    text_box_list.append(textbox_)
    return text_and_bounding_results,text_box_list
 

            # dx = j.bounding_box.vertices[1].x - j.bounding_box.vertices[0].x
            # dy = j.bounding_box.vertices[1].y- j.bounding_box.vertices[0].y
            # arrival_angle=math.degrees(math.atan2(dy, dx))
            # arrival_angle=(arrival_angle + 360) % 360
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
    if response.status_code==200:
        arr = np.frombuffer(response.content, dtype=np.uint8)
        return {'result':arr,'code':response.status_code }
    else:
        return {'result':'error in inpaint prediction','code':response.status_code }


def convert_transparent(img,value):
    img = img.convert("RGBA")
    data = img.getdata()
    new_data = []
    for pixel in data:
        if pixel[0] == value and pixel[1] == value and pixel[2] == value:
            new_data.append((value, value, value, 0))
        else:
            new_data.append(pixel)
    img.putdata(new_data)
    return img

def layer_blend(lama_result,img_transparent):
    lama_result=lama_result.convert('RGBA')
    img_transparent=img_transparent.convert('RGBA')
    lama_result.alpha_composite(img_transparent)
    # lama_result.paste(img_transparent, (0, 0), img_transparent) 
    return lama_result

def lama_diff(mask,diff):
    mask[mask!= 0] = 255
    msk_pil=convert_transparent(Image.fromarray(mask),value=255)
    img_blend=layer_blend(Image.fromarray(diff),msk_pil)
    return  np.asarray(img_blend)

def lama_inpaint_optimize(image_diff,lama_result,original):
    buffered = BytesIO()
    img_gen='https://apinodestaging.ailaysa.com/ai_canvas_mask_generate'
    resized_image = image_diff.resize((256,256))
    resized_image.save(buffered, format="PNG")
    img_str=base64.b64encode(buffered.getvalue())
    resized_width,resized_heigth= resized_image.size
    output=img_str.decode()
    ima_str='data:image/png;base64,'+str(output)
    data = {'maskimage':ima_str , 'width':resized_width,'height':resized_heigth}
    thumb_image = requests.request('POST',url=img_gen,data=data ,headers={},files=[])
    ###convert thumb to black and white
    black_and_white=Image.open(BytesIO(base64.b64decode(thumb_image.content.decode().split(',')[-1])))
    black_and_white=black_and_white.resize(image_diff.size)
    img_arr=np.asarray(black_and_white)
    img_arr_copy=np.copy(img_arr)
    img_arr_copy[img_arr_copy!= 0]=255

    ###morphing
    SE=cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9,9))
    res=cv2.morphologyEx(img_arr_copy, cv2.MORPH_DILATE, SE)
    img_transparent=Image.fromarray(res)
    img_transparent=convert_transparent(img_transparent,255)
    lama_transparent=layer_blend(lama_result=lama_result,img_transparent=img_transparent)
    lama_convert_transparent=convert_transparent(lama_transparent,0)
    result=layer_blend(original,lama_convert_transparent)
    return result,black_and_white


# from celery import shared_task
# @shared_task(serializer='json')

def inpaint_image_creation(image_details,inpaintparallel=False):
    # if hasattr(image_details,'image'):
    #     img_path=image_details.image.path
    # else:
    #     img_path=image_details.inpaint_image.path
    
    if inpaintparallel:
        img_path=image_details.inpaint_image.path
    else:
        img_path=image_details.image.path

    mask_path=image_details.mask.path
    mask=cv2.imread(mask_path)
    img=cv2.imread(img_path)
    if image_details.mask:
        image_to_extract_text=np.bitwise_and(mask ,img)
        content=image_content(image_to_extract_text)
        inpaint_image_file=core.files.File(core.files.base.ContentFile(content),"file.png")
        image_details.create_inpaint_pixel_location=inpaint_image_file
        image_details.save()
        # image_text_details=creating_image_bounding_box(image_details.create_inpaint_pixel_location.path)
        output=inpaint_image(img_path, mask_path)
        if output['code']==200:
            if output['result'].shape[0]==np.prod(img.shape):
                res=np.reshape(output['result'],img.shape)  
                diff=cv2.absdiff(img,res)
                diff=lama_diff(mask,diff)
                diff=cv2.cvtColor(diff,cv2.COLOR_BGR2RGB)
                res=cv2.cvtColor(res,cv2.COLOR_BGR2RGB)
                diff=Image.fromarray(diff)
                lama_result=Image.fromarray(res)
                original=Image.open(img_path)
                dst,black_and_white=lama_inpaint_optimize(image_diff=diff,lama_result=lama_result,original=original)
                dst=np.asarray(dst)
                dst_final=np.copy(dst)
                dst_final=cv2.cvtColor(dst_final,cv2.COLOR_BGR2RGB)
                image_color_change=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
                black_and_white=np.asarray(black_and_white)
                black_and_white=black_and_white[:, :, :3]
                image_color_change=image_color_change[:, :, :3]
 
                image_to_ext_color=np.bitwise_and(black_and_white ,image_color_change)
                image_text_details,text_box_list=creating_image_bounding_box(image_details.create_inpaint_pixel_location.path,image_to_ext_color)
                
                return dst_final,image_text_details,text_box_list
            else:return serializers.ValidationError({'shape_error':'pred_output_shape is dissimilar to user_image'})
                
        else:
            return ValidationError(output)

def background_merge(u2net_result,original_img):
    newdata=[]
    original_img=cv2.cvtColor(original_img,cv2.COLOR_BGR2RGB)
    u2net_result=cv2.subtract(u2net_result,original_img)
    # cv2.imwrite("u2net_result.png",u2net_result)
    u2net_result=Image.fromarray(u2net_result).convert('RGBA')
    original_img=Image.fromarray(original_img).convert("RGBA")
    u2net_data=u2net_result.getdata()
    original_img=original_img.getdata()
    for i in range(u2net_data.size[0]*u2net_data.size[1]):
        if u2net_data[i][0]==0 and u2net_data[i][1]==0 and u2net_data[i][2]==0:
            newdata.append((255,255,255,0))
        else:
            newdata.append(original_img[i])
    u2net_result.putdata(newdata)
    img_io = io.BytesIO()
    u2net_result.save(img_io, format='PNG')
    img_byte_arr = img_io.getvalue()
    # print(type(img_byte_arr))
    return core.files.File(core.files.base.ContentFile(img_byte_arr),"background_remove.png")
 


def background_remove(image_path):
    headers={}
    data={}
    files=[('image',('',open(image_path,'rb'),'image/jpeg'))]
    response = requests.request("POST",BACKGROUND_REMOVAL_URL, headers=headers, data=data, files=files)
    arr = np.frombuffer(response.content, dtype=np.uint8)
    res=np.reshape(arr,(320,320,3))
    user_image=cv2.imread(image_path)
    # im = Image.fromarray(res * 255).convert('RGB')
    # im.save("afternath.png")
    # im=np.asarray(im)
    image_h, image_w, _ = user_image.shape
    y0=cv2.resize(res, (image_w, image_h))
    bck_gur_res=background_merge(y0,user_image)
    return bck_gur_res

 


    # else:
    #     image_text_details=creating_image_bounding_box(image_details.image.path)
    #     mask_out_to_inpaint=np.zeros((img.shape[0],img.shape[1] ,3) , np.uint8)
    #     for i in image_text_details.values():
    #         bbox =  i['bbox']
    #         cv2.rectangle(mask_out_to_inpaint, bbox[:2], bbox[2:] , (255,255,255), thickness=cv2.FILLED)
    #     img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
    #     mask = cv2.cvtColor(mask_out_to_inpaint , cv2.COLOR_BGR2GRAY)
    #     output = inpaint_image(img_path, mask_path)
    #     output = np.reshape(output, img.shape) 
    #     return output,image_text_details



# def image_inpaint_revert(instance,mask_json):
#     main_image=cv2.imread(instance.image.path)
#     mask_image=TemplateGlobalDesignSerializer().thumb_create(json_str=mask_json,formats='mask',multiplierValue=None)
#     bit_wise_ = cv2.bitwise_and(mask_image,main_image)
#     tmp = cv2.cvtColor(bit_wise_, cv2.COLOR_BGR2GRAY)
#     _,alpha = cv2.threshold(tmp,0,255,cv2.THRESH_BINARY)
#     b, g, r = cv2.split(bit_wise_)
#     rgba = [b,g,r, alpha]
#     masked_tr = cv2.merge(rgba,4)
#     masked_tr=Image.fromarray(masked_tr)
#     main_image=Image.fromarray(main_image)
#     masked_tr.paste(main_image, (0, 0), main_image)
#     instance.inpaint_image=masked_tr
#     instance.save()
    





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
