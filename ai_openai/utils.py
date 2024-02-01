import json,logging,mimetypes,os,openai,asyncio, math
import re,requests,time,urllib.request
from django.contrib.auth import settings
from django.http import HttpResponse
from ai_auth.models import UserCredits
from ai_tms.settings import OPENAI_API_KEY ,OPENAI_MODEL
from ai_staff.models import Languages
from django.db.models import Q
from io import BytesIO
from PIL import Image
logger = logging.getLogger('django')
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
@backoff.on_exception(backoff.expo,(openai.error.RateLimitError,openai.error.APIConnectionError,),max_tries=2)
def get_prompt(prompt ,model_name , max_token ,n ):
    #max_token = 256
    temperature=0.7
    frequency_penalty = 1
    presence_penalty = 1
    top_p = 1
    response = openai.Completion.create(model=model_name, prompt=prompt.strip(),temperature=temperature,
                                        max_tokens=int(max_token),top_p=top_p,frequency_penalty=frequency_penalty,
                                        presence_penalty=presence_penalty,n=n)    # stop = ['#'],#logit_bias = {"50256": -100}        
    choic=[]
    for i in response["choices"]:
        choic.append({'text':i['message']['content']})
    response["choices"]=choic
    return response

@backoff.on_exception(backoff.expo,(openai.error.RateLimitError,openai.error.APIConnectionError,),max_tries=2)
def get_prompt_freestyle(prompt):
    response = openai.Completion.create(model="text-curie-001",prompt=prompt.strip(),temperature=0.7,max_tokens=300,
                                        top_p=1,frequency_penalty=1,presence_penalty=1,n=1,)#logit_bias = {"50256": -100}
    return response

model_edit = os.getenv('OPENAI_EDIT_MODEL')

def get_prompt_edit(input_text ,instruction ):
    response = openai.Edit.create(model=model_edit, input=input_text.strip(),instruction=instruction,) # temperature=0.7,
                # top_p=1,    
    return response
    
#DALLE
@backoff.on_exception(backoff.expo,(openai.error.RateLimitError,openai.error.APIConnectionError,),max_tries=2)
def get_prompt_image_generations(prompt,size,no_of_image):
    #prompt = "Generate an image based on the following text description: " + prompt
    print("Prompt--------->",prompt)
    # try:
    response = openai.Image.create(prompt=prompt,n=no_of_image,size=size) 
         
     
        # response = {'error':"Your requested prompt was rejected as a result of our safety system. Your prompt may contain text that is not allowed by our safety system."}
    return response


def get_img_content_from_openai_url(image_url):
    r = requests.get(image_url)
    pil_img = Image.open(BytesIO(r.content))
    img_byte_arr = BytesIO()
    pil_img.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr

@backoff.on_exception(backoff.expo, openai.error.RateLimitError , max_time=30,max_tries=1)
def get_prompt_gpt_turbo_1106(messages):
    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo-1106",messages=messages)
    return completion


OPEN_AI_GPT_MODEL = "gpt-3.5-turbo"   #"gpt-3.5-turbo" gpt-4 
TEXT_DAVINCI = "text-davinci-003"

@backoff.on_exception(backoff.expo, openai.error.RateLimitError , max_time=30,max_tries=1)
def get_prompt_chatgpt_turbo(prompt,n,max_token=None):
    print("<--------------------------Inside------------------------------------->")
    print("Max tokens------------>",max_token)
    if max_token:
        completion = openai.ChatCompletion.create(model=OPEN_AI_GPT_MODEL,messages=[{"role":"user","content": prompt}],n=n,max_tokens=int(max_token))
    else:
        completion = openai.ChatCompletion.create(model=OPEN_AI_GPT_MODEL,messages=[{"role":"user","content": prompt}],n=n)
    return completion

async def generate_text(prompt):
    response = await openai.Completion.acreate(engine=TEXT_DAVINCI,prompt=prompt,max_tokens=150,n=1,top_p=1,
                                               frequency_penalty=1,presence_penalty=1,temperature=0.7,)
    return response

async def generate_texts(outline_section_prompt_list , title ,tone ,keyword):
    coroutines=[]
    for prompt in outline_section_prompt_list:
        prompt='Create a paragraph for {} for a title {} with keywords {} in {} tone'.format(prompt,title,keyword,tone)
        coroutines.append(generate_text(prompt))
    return await asyncio.gather(*coroutines)

def blog_generator(outline_section_prompt_list ,title,tone,keyword):
    results = asyncio.run(generate_texts(outline_section_prompt_list ,title ,tone ,keyword))
    return  results

############
async def generate_outline_response(prompt,n):
    response = await openai.ChatCompletion.acreate(model=OPEN_AI_GPT_MODEL,messages=[{"role":"user","content": prompt[0]}],
                                                   n=n,max_tokens=170)
    return response 
 
async def outline_co(prompt,n):
    coroutines=[]
    prompt = [prompt]#+" and every outline should be less than three words."]
    coroutines.append(generate_outline_response(prompt,n))
    return await asyncio.gather(*coroutines)

def outline_gen(prompt,n):
    results = asyncio.run(outline_co(prompt,n))
    return results[0]
######################

from docx import Document
from ai_openai.html2docx_custom import HtmlToDocx
import re
document = Document()
new_parser = HtmlToDocx()
new_parser.table_style = 'TableGrid'


def replace_hex_color(match):
    hex_color = match.group(1)
    red, green, blue = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    rgb_color = f"rgb({red}, {green}, {blue})"
    return rgb_color

def replace_hex_colors_with_rgb(html):
    hex_color_regex = re.compile("'#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})'")
    html = hex_color_regex.sub(replace_hex_color, html)
    return html


# updatedHtml = replace_hex_colors_with_rgb("html_file")  
# htmlupdates = updatedHtml.replace('<br />', '')
# new_parser.add_html_to_document(htmlupdates, document)
# document.save('file_name.docx')s




def get_summarize(text,bb_instance):
    from .serializers import AiPromptSerializer
    from ai_openai.serializers import openai_token_usage
    prompt = '''Input text: {}
Instructions:
1. Summarize the input text in a concise manner while capturing key points and main ideas.
2. Extract up to 10 keywords or key phrases that represent important concepts or topics discussed in the input text.
3. Please ensure that the summary is no longer than 200 words and that the keywords are relevant and representative of the input text.

Summary:
'''.format(text)

    response = get_prompt_chatgpt_turbo(prompt=prompt,max_token =200,n=1)
    summary = response["choices"][0]["message"]["content"]
    token_usage = openai_token_usage(response)
    token_usage_to_reduce = get_consumable_credits_for_openai_text_generator(token_usage.total_tokens)
    print("TUR--------------->",token_usage_to_reduce)
    AiPromptSerializer().customize_token_deduction(bb_instance,token_usage_to_reduce,user=bb_instance.book_creation.user)
    print("Summary---------------->",summary)
    return summary 