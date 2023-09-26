from .models import *
from google.cloud import vision_v1,vision
from google.oauth2 import service_account
from django import core
# from torch.utils.data._utils.collate import default_collate
from django.conf import settings
from django.core.exceptions import ValidationError
import os , requests ,copy,uuid,json,random,extcolors
import cv2,requests,base64,io 
from PIL import Image,ImageFilter
import numpy as np
from io import BytesIO
from rest_framework import serializers
from ai_canvas.template_json import textbox_json

from cv2 import (
    BORDER_DEFAULT,
    MORPH_OPEN,
    GaussianBlur,
    morphologyEx,
    getStructuringElement,
    MORPH_ELLIPSE
)
# from ai_canvas.serializers import TemplateGlobalDesignSerializer

from ai_canvas.utils import convert_image_url_to_file 
import numpy as np
import onnxruntime as ort
from ai_tms.settings import BASE_DIR

path = '/bgr_onnx_model/u2.pt'
_providers = ort.get_available_providers()
providers=[]
providers.extend(_providers)
sess_opts = ort.SessionOptions()
inner_session = ort.InferenceSession(BASE_DIR+path,providers=providers,sess_options=sess_opts)


IMAGE_TRANSLATE_URL = os.getenv('IMAGE_TRANSLATE_URL')
BACKGROUND_REMOVAL_URL= os.getenv('BACKGROUND_REMOVAL_URL')
STABLE_DIFFUSION_API= os.getenv('STABLE_DIFFUSION_API') 
STABILITY=os.getenv('STABILITY')   
STABLE_DIFFUSION_API_URL =os.getenv('STABLE_DIFFUSION_API_URL')
MODEL_VERSION =os.getenv('MODEL_VERSION')
STABLE_DIFFUSION_PUBLIC_API=os.getenv('STABLE_DIFFUSION_PUBLIC_API')


credentials=service_account.Credentials.from_service_account_file(settings.GOOGLE_APPLICATION_CREDENTIALS_OCR)
client = vision.ImageAnnotatorClient(credentials=credentials)

def image_ocr_google_cloud_vision(image_path , inpaint):
    if inpaint:
        with io.open(image_path, 'rb') as image_file:
            content = image_file.read()
        image = vision_v1.types.Image(content=content)
        response = client.text_detection(image = image)
        texts = response.full_text_annotation   #full_text_annotation
        return texts

def create_thumbnail_img_load(base_dimension,image):
    wpercent = (base_dimension/float(image.size[0]))
    hsize = int((float(image.size[1])*float(wpercent)))
    img = image.resize((base_dimension,hsize), Image.ANTIALIAS)
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_byte_arr = img_io.getvalue()
    im=core.files.File(core.files.base.ContentFile(img_byte_arr),"thumbnail.png")
    return im



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
            new_data.append(pixel[:-1]+(0,))# (231, 232, 234, 0)
        else:
            new_data.append((231, 232, 234, 255))
    img.putdata(new_data)
    img=convert_image_url_to_file(img,no_pil_object=False,name="erase_mask.png",transparent=False)
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


kernel = getStructuringElement(MORPH_ELLIPSE, (3, 3))
def post_process(mask: np.ndarray) -> np.ndarray:
    mask = morphologyEx(mask, MORPH_OPEN, kernel)
    mask = GaussianBlur(mask, (5, 5), sigmaX=2, sigmaY=2, borderType=BORDER_DEFAULT)
    mask = np.where(mask < 127, 0, 255).astype(np.uint8)  # convert again to binary
    return mask

def naive_cutout(im , msk ) :
    empty = Image.new("RGBA", (im.size), 0)
    cutout = Image.composite(im, empty, msk)
    return cutout

def get_consumable_credits_for_image_generation_sd(number_of_image):
    return number_of_image * 10



def normalize(img ,mean ,std ,size ,*args,**kwargs)  :
    im = img.convert("RGB").resize(size, Image.LANCZOS)
    im_ary = np.array(im)
    im_ary = im_ary / np.max(im_ary)
    tmpImg = np.zeros((im_ary.shape[0], im_ary.shape[1], 3))
    tmpImg[:, :, 0] = (im_ary[:, :, 0] - mean[0]) / std[0]
    tmpImg[:, :, 1] = (im_ary[:, :, 1] - mean[1]) / std[1]
    tmpImg[:, :, 2] = (im_ary[:, :, 2] - mean[2]) / std[2]
    tmpImg = tmpImg.transpose((2, 0, 1))
    return {
        inner_session.get_inputs()[0]
        .name: np.expand_dims(tmpImg, 0)
        .astype(np.float32)
    }

# def background_remove(instance):
#     try:
#         image_path=instance.original_image.path
#     except:
#         image_path=instance.image.path
#     img = Image.open(image_path)
#     ort_outs = inner_session.run(None,normalize(img, (0.485, 0.456, 0.406), (0.229, 0.224, 0.225), (320, 320)),)
#     pred = ort_outs[0][:, 0, :, :]
#     ma = np.max(pred)
#     mi = np.min(pred)
#     pred = (pred - mi) / (ma - mi)
#     pred = np.squeeze(pred)
#     mask = Image.fromarray((pred * 255).astype("uint8"), mode="L")
#     mask = mask.resize(img.size, Image.LANCZOS)
#     mask = Image.fromarray(post_process(np.array(mask)))
#     mask_store = convert_image_url_to_file(mask,no_pil_object=False,name="mask.png")
#     cutout = naive_cutout(img, mask)
#     img_byte_arr = cutout.getvalue()
#     instance.mask=mask_store
#     instance.save()
#     return core.files.File(core.files.base.ContentFile(img_byte_arr),"background_remove.png")


# from rembg import remove
def background_remove(instance):
    try:
        image_path=instance.original_image.path
    except:
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
    
    # eraser_transparent_mask=convert_transparent_for_image(im_mask,255)
    # instance.eraser_transparent_mask=eraser_transparent_mask
    instance.mask=mask_store
    instance.save()
    
    # img = Image.open(image_path)
    # output = remove(img)
    # img_byte_arr = output.getvalue()
    # bck_gur_res=core.files.File(core.files.base.ContentFile(img_byte_arr),"background_remove.png")
    bck_gur_res=background_merge(y0,user_image)
    return bck_gur_res


def sd_status_check(ids,url):
    payload = json.dumps({"key":STABLE_DIFFUSION_PUBLIC_API,"request_id": ids})
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()

 
from celery.decorators import task

@task(queue='default')
def stable_diffusion_public(instance): #prompt,41,height,width,negative_prompt
    from ai_workspace.api_views import UpdateTaskCreditStatus  ###for avoiding circular error
    sd_instance=StableDiffusionAPI.objects.get(id=instance.id)
    model="sdxl"
    consumble_credits_to_image_generate= get_consumable_credits_for_image_generation_sd(number_of_image=1)
    if sd_instance.width==sd_instance.height==512:
        print("512")
        model="sdv1"
    print(model)
    models={"sdxl" :{'model_name':"sdxl" ,"url":"https://stablediffusionapi.com/api/v4/dreambooth",
                     "fetch_url":"https://stablediffusionapi.com/api/v4/dreambooth/fetch" },
            "sdv1": {'model_name': "stable-diffusion-v1-5","url":"https://stablediffusionapi.com/api/v3/text2img",
                     "fetch_url":"https://stablediffusionapi.com/api/v3/fetch/{}"}}
    
    print( models[model]['model_name'])
    data = {
            "key":STABLE_DIFFUSION_PUBLIC_API ,
            "model_id": models[model]['model_name'],
            "prompt": sd_instance.prompt,
            "width": str(sd_instance.width),"height":str(sd_instance.height),
            "samples": "1","num_inference_steps":sd_instance.steps,   
            "seed": random.randint(0,99999999999),
            "guidance_scale": 7,
            "safety_checker": "yes","multi_lingual": "no",
            "panorama": "no","self_attention": "yes","upscale": "no",
            "embeddings_model": None,"webhook": None,"track_id": None,
            "enhance_prompt":'no','tomesd':'yes',
            'scheduler':'DDIMScheduler', "self_attention":'no','use_karras_sigmas':"no"
         } # DDIMScheduler EulerAncestralDiscreteScheduler  PNDMScheduler ,
   
    if sd_instance.negative_prompt:
        data['negative_prompt']=sd_instance.negative_prompt
    payload = json.dumps(data) 
    headers = {'Content-Type': 'application/json'}
    response = requests.request("POST", models[model]['url'], headers=headers, data=payload)
    x=response.json()
    process=False
    while True:
        print("processing")
        sd_instance.status="PENDING"
        sd_instance.save()
        res_id=response.json()['id']
        fetch_url=models[model]['fetch_url']
        if model=='sdv1':
            fetch_url=fetch_url.format(res_id)
        x=sd_status_check(ids=res_id,url=fetch_url) 
        if not x['status']=='processing' or x['status']=='success':
            process=True
            break
    if process:
        image=convert_image_url_to_file(image_url=x['output'][0],no_pil_object=True)
        sd_instance.generated_image=image
        sd_instance.image=image
        sd_instance.save()
        im=Image.open(sd_instance.generated_image.path)
        sd_instance.thumbnail=create_thumbnail_img_load(base_dimension=300,image=im)
        sd_instance.status="DONE"
        sd_instance.save()
        print("finished_generate")
        debit_status, status_code = UpdateTaskCreditStatus.update_credits(sd_instance.user,consumble_credits_to_image_generate)
        # return 
    else:
        sd_instance.status="ERROR"
        raise serializers.ValidationError({'msg':"error on processing SD"})
 

#########stabilityai
def stable_diffusion_api(prompt,weight,steps,height,width,style_preset,sampler,negative_prompt,version_name):
    url = "https://api.stability.ai/v1/generation/{}/text-to-image".format(version_name)

    body = {
    "steps": steps,
    "width": width,
    "height": height,
    "seed": 0,
    "cfg_scale": weight,
    "samples": sampler,
    "text_prompts": [
        {
        "text":prompt,
        "weight": 1
        },
        {
        "text": negative_prompt,
        "weight": -1
        }
    ],
    }

    headers = {"Accept": "application/json","Content-Type": "application/json","Authorization": "Bearer sk-cOAr0wUc8dGtN21bNKww39A0Gl6ABIzjX3GhHksQTC0cTXh5",}

    response = requests.post(url,headers=headers,json=body,)

    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))

    data = response.json()
    data =base64.b64decode(response.json()['artifacts'][0]['base64'])
    image = core.files.File(core.files.base.ContentFile(data),"stable_diffusion_stibility_image.png")
    return image

 



 
########################################################################################################


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



 # data={
    # "key": "45405da04e97b0c596e7",
    # "model_id": "sdxl",
    # "prompt": prompt,
    # "width": "1024",
    # "height": "1024",
    # "samples": "1",
    # "num_inference_steps": "30",
    # "safety_checker": "no",
    # "enhance_prompt": "yes",
    # "seed": None,
    # "guidance_scale": 7.5,
    # "multi_lingual": "no",
    # "panorama": "no",
    # "self_attention": "no",
    # "upscale": "no",
    # "embeddings_model": None,
    # "tomesd": "yes",
    # "use_karras_sigmas": "yes",
    # "vae": None,
    # "lora_strength": None,
    # "lora_model": None,
    # "scheduler": "UniPCMultistepScheduler",
    # "webhook": None,
    # "track_id": None
    # }


