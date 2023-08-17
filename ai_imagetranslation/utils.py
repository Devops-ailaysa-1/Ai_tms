from .models import *
from PIL import Image
from google.cloud import vision_v1,vision
from google.oauth2 import service_account
import extcolors 
from django import core
import random
# from torch.utils.data._utils.collate import default_collate
from django.conf import settings
credentials=service_account.Credentials.from_service_account_file(settings.GOOGLE_APPLICATION_CREDENTIALS_OCR)
client = vision.ImageAnnotatorClient(credentials=credentials)
from django.core.exceptions import ValidationError
import os 
import requests
import cv2,requests,base64,io 
from PIL import Image,ImageFilter
import numpy as np
from io import BytesIO
from rest_framework import serializers
from ai_canvas.template_json import textbox_json
import copy
import uuid,math,json
# from ai_canvas.serializers import TemplateGlobalDesignSerializer
from ai_canvas.utils import convert_image_url_to_file 

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
    poly_line=[]
    pillow_image_to_extract_color=Image.fromarray(color_find_image_diff)
    texts=image_ocr_google_cloud_vision(image_path,inpaint=True)  
    text_and_bounding_results={}
    no_of_segments=0
    text_list=[]
    text_box_list=[]
    for i in  texts.pages:
        for j in i.blocks:
            # x,y,w,h=j.bounding_box.vertices[0].x ,j.bounding_box.vertices[1].y,j.bounding_box.vertices[2].x,j.bounding_box.vertices[3].y 
            for k in j.paragraphs:
                count=0
                text_uuid=uuid.uuid4()
                textbox_=copy.deepcopy(textbox_json)
                name="Textbox_"+(str(text_uuid))
                textbox_['id']="text_"+(str(text_uuid))
                count+=1
                textbox_['name']=name
                x,y,w,h=k.bounding_box.vertices[0].x ,k.bounding_box.vertices[1].y,k.bounding_box.vertices[2].x,k.bounding_box.vertices[3].y 
                textbox_['left']=x
                textbox_['top']=y
                textbox_['width']=w-x
                textbox_['height']=h-y
                final_color=color_extract_from_text(x,y,w,h,pillow_image_to_extract_color)
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
                textbox_['fill']="rgb{}".format(tuple(final_color[0]))
                font=max([sum(font_size)//len(font_size),sum(font_size2)//len(font_size2)])+5
                textbox_['fontSize']=font-5
                no_of_segments+=1
                text_list=[]
                text_box_list.append(textbox_)
    return text_and_bounding_results,text_box_list
 

 
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
    data = {'maskimage':ima_str,'width':resized_width,'height':resized_heigth}
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


def resize_data_remove(resize_instance):
    img_path=resize_instance.resize_image.path
    mask_path=resize_instance.resize_mask.path
    resize_instance.delete()
    os.remove(img_path)
    os.remove(mask_path)

# from celery import shared_task
# @shared_task(serializer='json')

def inpaint_image_creation(image_details,inpaintparallel=False,magic_erase=False):
    IMG_RESIZE_SHAPE=(256,256)
    if inpaintparallel:
        img_path=image_details.inpaint_image.path
    else:
        img_path=image_details.image.path
    mask_path=image_details.mask.path
    mask=cv2.imread(mask_path)
    img=cv2.imread(img_path)
    if image_details.mask:
        image_to_extract_text=np.bitwise_and(mask,img)
        content=image_content(image_to_extract_text)
        inpaint_image_file=core.files.File(core.files.base.ContentFile(content),"file.png")
        image_details.create_inpaint_pixel_location=inpaint_image_file
        image_details.save()
        resize_img=cv2.resize(img,IMG_RESIZE_SHAPE)
        resize_mask=cv2.resize(mask,IMG_RESIZE_SHAPE)
        resize_image=core.files.File(core.files.base.ContentFile(image_content(resize_img)),"resize_image.png")
        resize_mask=core.files.File(core.files.base.ContentFile(image_content(resize_mask)),"resize_mask.png")
        img_trans_resize=ImageTranslateResizeImage.objects.create(image_translate=image_details,resize_image=resize_image,resize_mask=resize_mask)
        output=inpaint_image(img_trans_resize.resize_image.path,img_trans_resize.resize_mask.path)
        resize_data_remove(img_trans_resize)
        if output['code']==200:
            if output['result'].shape[0]==np.prod(resize_img.shape):
                res=np.reshape(output['result'],resize_img.shape)
                res=cv2.resize(res,img.shape[1::-1])
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
            else:
                raise serializers.ValidationError({'shape_error':'pred_output_shape is dissimilar to user_image'})
        else:
            return ValidationError(output)


def convert_transparent_for_image(image,value):
    img=image.convert('RGBA')
    data = img.getdata()
    new_data = []
    for pixel in data:
        if pixel[0] == value and pixel[1] == value and pixel[2] == value:
            new_data.append((231, 232, 234, 0))
        else:
            new_data.append(pixel)
    img.putdata(new_data)
    img=convert_image_url_to_file(img,no_pil_object=False,name="erase_mask.png")
    return img

def background_merge(u2net_result,original_img):
    newdata=[]
    original_img=cv2.cvtColor(original_img,cv2.COLOR_BGR2RGB)
    u2net_result=cv2.subtract(u2net_result,original_img)
    # cv2.imwrite("u2net_result.png",u2net_result)
    u2net_result=Image.fromarray(u2net_result).convert('RGBA')
    u2net_result= u2net_result.filter(ImageFilter.GaussianBlur(radius=1))
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
    return core.files.File(core.files.base.ContentFile(img_byte_arr),"background_remove.png")


import numpy as np

from cv2 import (
    BORDER_DEFAULT,
    MORPH_OPEN,
    GaussianBlur,
    morphologyEx,
    getStructuringElement,
    MORPH_ELLIPSE
)
kernel = getStructuringElement(MORPH_ELLIPSE, (3, 3))
def post_process(mask: np.ndarray) -> np.ndarray:
    mask = morphologyEx(mask, MORPH_OPEN, kernel)
    mask = GaussianBlur(mask, (5, 5), sigmaX=2, sigmaY=2, borderType=BORDER_DEFAULT)
    mask = np.where(mask < 127, 0, 255).astype(np.uint8)  # convert again to binary
    return mask


def background_remove(instance):
    image_path=instance.image.path
    headers={}
    data={}
    files=[('image',('',open(image_path,'rb'),'image/jpeg'))]
    response = requests.request("POST",BACKGROUND_REMOVAL_URL, headers=headers, data=data, files=files)
    arr = np.frombuffer(response.content, dtype=np.uint8)
    res=np.reshape(arr,(320,320,3))
    res = post_process(res)
    user_image=cv2.imread(image_path)
    image_h, image_w, _ = user_image.shape
    y0=cv2.resize(res, (image_w, image_h))

    im_mask=Image.fromarray(y0).convert('RGBA')
    mask_store = convert_image_url_to_file(im_mask,no_pil_object=False,name="mask.png")
    
    eraser_transparent_mask=convert_transparent_for_image(im_mask,255)

    instance.eraser_transparent_mask=eraser_transparent_mask
    instance.mask=mask_store
    instance.save()
    bck_gur_res=background_merge(y0,user_image)
    return bck_gur_res

#########stabilityai
 
STABLE_DIFFUSION_API= os.getenv('STABLE_DIFFUSION_API') 
STABILITY=os.getenv('STABILITY')   
STABLE_DIFFUSION_API_URL =os.getenv('STABLE_DIFFUSION_API_URL')
MODEL_VERSION =os.getenv('MODEL_VERSION')
STABLE_DIFFUSION_PUBLIC_API=os.getenv('STABLE_DIFFUSION_PUBLIC_API')

def stable_diffusion_api(prompt,weight,steps,height,width,style_preset,sampler,negative_prompt):
    # token = "Bearer {}".format(STABILITY)
    # header={
    #     "Content-Type": "application/json",
    #     "Accept": "application/json",
    #     "Authorization":token ,
    # }
    # json = {"samples":1,"height": height,"width": width,
    # "steps": steps,"cfg_scale": 7 ,"sampler":sampler,
    # "style_preset": style_preset,
    # "text_prompts": [
    #     {"text": prompt,"weight": weight},
    #     {"text":negative_prompt,"weight":-1}
    #     ]
    # }
    # url="https://api.stability.ai/v1/generation/{}/text-to-image".format(MODEL_VERSION)
    # response = requests.post(url=url,headers=header,json=json)
    # if response.status_code != 200:
    #     raise Exception("Non-200 response: " + str(response.text))
    # data =base64.b64decode(response.json()['artifacts'][0]['base64'])
    # image = core.files.File(core.files.base.ContentFile(data),"stable_diffusion_stibility_image.png")
    pass
def sd_status_check(id):
    url = "https://stablediffusionapi.com/api/v4/dreambooth/fetch"
    payload = json.dumps({"key":STABLE_DIFFUSION_PUBLIC_API,"request_id": id})
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()




def stable_diffusion_public(prompt,weight,steps,height,width,style_preset,sampler,negative_prompt):
    url = "https://stablediffusionapi.com/api/v4/dreambooth"
    # url="https://stablediffusionapi.com/api/v3/text2img"
    #midjourney  sdxl realistic-vision-v13
    data = {
    "key":STABLE_DIFFUSION_PUBLIC_API ,
    "model_id": "sdxl",
    "prompt": prompt,
    "width": "1024",
    "height": "1024",
    "samples": "1",
    "num_inference_steps": 41,   
    "seed": random.randint(0,99999999999),
    "guidance_scale": 5,
    "safety_checker": "yes",
    "multi_lingual": "no",
    "panorama": "no",
    "self_attention": "yes",
    "upscale": "no",
    "embeddings_model": None,
    "webhook": None,"track_id": None,
    "enhance_prompt":'yes',
    'scheduler':'PNDMScheduler', 
    "self_attention":'yes',
    'use_karras_sigmas':"yes"
    } # DDIMScheduler EulerAncestralDiscreteScheduler
    if negative_prompt:
        data['negative_prompt']=negative_prompt
    payload = json.dumps(data) 
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    x=response.json()
    process=False
    while True:
        x=sd_status_check(response.json()['id'])
        if not x['status']=='processing' or x['status']=='success':
            print("processing")
            process=True
            break
    if process:
        return convert_image_url_to_file(image_url=x['output'][0],no_pil_object=True)
    else:
        raise serializers.ValidationError({'msg':"error on processing SD"})
 

    # headers = {'Content-Type': 'application/json'}
    # response = requests.request("POST", url, headers=headers, data=payload)
    # print(response.json())
    # if response.status_code==200:
    #     response=response.json()
    #     reference_id=response['id']
    #     print("reference_id",reference_id)
    #     print(response['output'])
    #     if len(response['output'])==0 and response['status']=='processing':
    #         while True:
    #             response=sd_status_check(reference_id)
    #             if response['status']=='processing':
    #                 print("processing sd")
    #                 print(response)
    #             elif response['status']=='success':
    #                 break
    #     return  convert_image_url_to_file(image_url=response['output'][0],no_pil_object=True)
    # else:
    #     raise serializers.ValidationError({'msg':response.text})



# json.dumps({
# "key":STABLE_DIFFUSION_PUBLIC_API ,
# "model_id": "realistic-vision-v13",
# "prompt": prompt,"negative_prompt":negative_prompt,"width": width,"height": height,
# "samples": "1","num_inference_steps": "41","safety_checker": "yes",
# "enhance_prompt": "yes","seed": None,
# "guidance_scale":7.5,"multi_lingual": "no",
# "panorama": "no","self_attention": "yes",
# "upscale": "no","embeddings_model": None,
# "lora_model": None,"tomesd": "yes",
# "use_karras_sigmas": "yes","vae": None,"lora_strength": None,
# "scheduler": "UniPCMultistepScheduler","webhook": None, "track_id": None})



 


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