import json,logging,mimetypes,os
import re,requests,time,urllib.request
from django.contrib.auth import settings
from django.http import HttpResponse
from ai_auth.models import UserCredits
from ai_tms.settings import OPENAI_API_KEY ,OPENAI_MODEL
from ai_staff.models import Languages
from django.db.models import Q
import math
from rest_framework import serializers
import requests
from io import BytesIO
from PIL import Image
logger = logging.getLogger('django')
import openai
from googletrans import Translator
detector = Translator()

def lang_detect(user_text):
    return detector.detect(user_text).lang

openai.api_key = os.getenv('OPENAI_API_KEY')
def ceil_round_off(token_len):
    import math
    return math.ceil(len(token_len)/4)
    
    
def get_consumable_credits_for_openai_text_generator(total_token):
    total_consumable_token_credit = math.ceil(total_token/12)     
    return total_consumable_token_credit
 
def get_consumable_credits_for_image_gen(image_resolution,number_of_image):
    print("ImgRes------->",image_resolution)
    print("No---------->",number_of_image)
    if image_resolution == 1:
        return number_of_image * 70
    if image_resolution == 2:
        return number_of_image * 75
    if image_resolution == 3:
        return number_of_image * 85

def openai_text_trim(text):
    reg_text = re.search("(\s+)(?=\.[^.]+$)",text, re.MULTILINE)
    if reg_text:
        text = text[:reg_text.start()]+"."
    return text

import backoff
@backoff.on_exception(backoff.expo, openai.error.RateLimitError)
def get_prompt(prompt ,model_name , max_token ,n ):

    #max_token = 256
    temperature=0.7
    frequency_penalty = 1
    presence_penalty = 1
    top_p = 1

    response = openai.Completion.create(
                model=model_name, 
                prompt=prompt.strip(),
                temperature=temperature,
                max_tokens=int(max_token),
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                # stop = ['#'],
                n=n,
                #logit_bias = {"50256": -100}
                )
    return response

@backoff.on_exception(backoff.expo, openai.error.RateLimitError)
def get_prompt_freestyle(prompt):
    try:
        response = openai.Completion.create(
                    model="text-curie-001",
                    prompt=prompt.strip(),
                    temperature=0.7,
                    max_tokens=300,
                    top_p=1,
                    frequency_penalty=1,
                    presence_penalty=1,
                    n=1,
                    #logit_bias = {"50256": -100}
                    )
        return response
    except:
        raise serializers.ValidationError({'msg':'internal_error'},code=200) 
model_edit = os.getenv('OPENAI_EDIT_MODEL')

@backoff.on_exception(backoff.expo, openai.error.RateLimitError)
def get_prompt_edit(input_text ,instruction ):
    try:
        response = openai.Edit.create(
                    model=model_edit, 
                    input=input_text.strip(),
                    instruction=instruction,
                    # temperature=0.7,
                    # top_p=1,
                    )
        return response
    except:
        raise serializers.ValidationError({'msg':'internal_error'},code=200)
#DALLE
def get_prompt_image_generations(prompt,size,no_of_image):
    try:
        response = openai.Image.create(prompt=prompt,n=no_of_image,size=size) 
    except:
        response = {'error':"Your requested prompt was rejected as a result of our safety system. Your prompt may contain text that is not allowed by our safety system."}
    return response


def get_img_content_from_openai_url(image_url):
    r = requests.get(image_url)
    pil_img = Image.open(BytesIO(r.content))
    img_byte_arr = BytesIO()
    pil_img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr