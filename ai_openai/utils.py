import json,logging,mimetypes,os
import re,requests,time,urllib.request
from django.contrib.auth import settings
from django.http import HttpResponse
from ai_auth.models import UserCredits
from ai_tms.settings import OPENAI_API_KEY ,OPENAI_MODEL
from ai_staff.models import Languages
from django.db.models import Q
import math
logger = logging.getLogger('django')




def ceil_round_off(token_len):
    import math
    return math.ceil(len(token_len)/4)
    

import openai
openai.api_key = os.getenv('OPENAI_API_KEY')


    
def get_consumable_credits_for_openai_text_generator(total_token):
    total_consumable_token_credit = math.ceil(total_token/12)     
    return total_consumable_token_credit
 

def openai_text_trim(text):
    reg_text = re.search("(\s+)(?=\.[^.]+$)",text, re.MULTILINE)
    if reg_text:
        text = text[:reg_text.start()]+"."
    return text


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
                #stop = ['\n\n\n'],
                n=n,
                #logit_bias = {"50256": -100}
                )
    return response

def get_prompt_freestyle(prompt):
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

model_edit = os.getenv('OPENAI_EDIT_MODEL')

def get_prompt_edit(input_text ,instruction ):
    response = openai.Edit.create(
                model=model_edit, 
                input=input_text.strip(),
                instruction=instruction,
                # temperature=0.7,
                # top_p=1,
                )
    return response
    
#DALLE
def get_prompt_image_generations(prompt,size,n):
    try:
        response = openai.Image.create(prompt=prompt,n=n,size=size)
    except:
        response = {'error':"Your requested prompt was rejected as a result of our safety system. Your prompt may contain text that is not allowed by our safety system."}
    return response