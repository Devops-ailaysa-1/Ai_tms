import json,logging,mimetypes,os,openai,asyncio, math
import re,requests,time,urllib.request
from django.contrib.auth import settings
from django.http import HttpResponse
from ai_auth.models import UserCredits
from ai_tms.settings import OPENAI_API_KEY ,OPENAI_MODEL
from ai_staff.models import Languages,LanguagesLocale
from django.db.models import Q
from io import BytesIO
from PIL import Image
from wiktionaryparser import WiktionaryParser
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage

logger = logging.getLogger('django')
openai.api_key = os.getenv('OPENAI_API_KEY')


MISTRAL_AI_API_KEY = os.getenv('MISTRAL_AI_API_KEY')
print("MISTRAL_AI_API_KEY",MISTRAL_AI_API_KEY)
mistral_client = MistralClient(api_key=MISTRAL_AI_API_KEY)






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


# @backoff.on_exception(backoff.expo, openai.error.RateLimitError , max_time=30,max_tries=1)
# def get_prompt_chatgpt_4(prompt,n,max_token=None):
    


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
                                                   n=n,max_tokens=1200)
    return response 
 
async def outline_co(prompt,n):
    print("N-------------------------->",n)
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




def get_summarize(text,bb_instance,lang):
    from .serializers import AiPromptSerializer
    from ai_openai.serializers import openai_token_usage
    from ai_workspace_okapi.utils import get_translation
    from ai_workspace.api_views import UpdateTaskCreditStatus ,get_consumable_credits_for_text
    print("Lang----------->",lang)
    if lang != 'en':
        consumable_credits_for_article_gen = get_consumable_credits_for_text(text,'en',lang)
        consumable = max(round(consumable_credits_for_article_gen/3),1) 
        text=get_translation(1,text,lang,"en",user_id=bb_instance.book_creation.user.id,cc=consumable)

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


def get_chapters(pr_response):
    data = pr_response
    print("DT------------>",data)
    print("Type---------->",type(data))
    try:
        data = json.loads(data)
    except json.JSONDecodeError as e:
        print("JSON decoding error:", e)
    chapters = []
    for title in data:
        chapters.append(title)
    print("Chapters------------->",chapters)
    return chapters 

def get_sub_headings(title, pr_response):
    value = None
    data = pr_response
    #json_str_corrected = data.replace("'", '"')
    try:
        data = json.loads(data)
    except json.JSONDecodeError as e:
        print("JSON decoding error:", e)
    print("subheading data------------>",data)
    if title in data:
        value = data.get(title)
    return value
        
        
        
def search_wikipedia(search_term,lang):
    # Search for the given search term
    endpoint = f"https://{lang}.wikipedia.org/w/api.php"
    search_params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": search_term
    }
    search_response = requests.get(endpoint, params=search_params)
    search_data = search_response.json()
    search_results = search_data['query']['search']
    
    # If there are search results, get the content of the first article
    if search_results:
        title = search_results[0]['title']
        page_params = {
            "action": "query",
            "format": "json",
            "prop": "extracts",
            "titles": title
        }
        URL=f"https://{lang}.wikipedia.org/wiki/{title}"
        page_response = requests.get(endpoint, params=page_params)
        page_data = page_response.json()
        page_id = list(page_data['query']['pages'].keys())[0]
        content = page_data['query']['pages'][page_id]['extract']
        return {"Title": title, "Content": content, "URL": URL}
    else:
        print("No search results found.")
        return {}


def search_wiktionary(search_term,lang):
    try:
        language = LanguagesLocale.objects.filter(locale_code = lang).first().language.language
    except:
        language = LanguagesLocale.objects.filter(locale_code = 'en').first().language.language
    user_input=search_term.strip()
    parser = WiktionaryParser()
    print("Search term--------->",search_term)
    print("Lang---------->",lang)
    parser.set_default_language(language)
    word = parser.fetch(user_input)
    if word:
        if word[0].get('definitions')==[]:
            word=parser.fetch(user_input.lower())
    res=[]
    for i in word:
        defin=i.get("definitions")
        for j,k in enumerate(defin):
            out=[]
            pos=k.get("partOfSpeech")
            text=k.get("text")
            rel=k.get('relatedWords')
            out=[{'pos':pos,'definitions':text}]
            res.extend(out)
    URL=f"https://{lang}.wiktionary.org/wiki/{search_term}" if res else ""
    data = {'URL': URL, 'res': res}
    return data


def google_custom_search(query):
    api_key = os.getenv('GOOGLE_CUSTOM_SEARCH')
    cx = os.getenv('GOOGLE_CUSTOM_ENGINE')
    url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx}&q={query}"
    response = requests.get(url)
    res = []
    if response.status_code == 200:
        search_results = response.json()
        if search_results.get('items'):
            for item in search_results['items']:
                title = item['title']
                link = item['link']
                description = item['snippet'] if 'snippet' in item else ''
                dt = {'title':title,'link':link,'description':description}
                res.append(dt)
        else:
            print("No Results Found")
    else:
        print("Error:", response.status_code, response.text)
    return res


def bing_search(query):
    subscription_key = os.getenv('MST_SEARCH_KEY')
    search_url = os.getenv('MST_SEARCH_ENDPOINT') + "v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params = {"q": query, "count": 10, "textDecorations": True, "textFormat": "HTML"}
    response = requests.get(search_url, headers=headers, params=params)
    print(response.status_code)
    res = []
    if response.status_code == 200:
        if response.json().get('webPages'):
            search_results = response.json()['webPages']['value']
            if search_results:
                for result in search_results:
                    name = result['name'] if 'name' in result else ''
                    description = result['snippet'] if 'snippet' in result else ''
                    url = result['url'] if 'url' in result else ''
                    dt = {'title':name,'link':url,'description':description}
                    res.append(dt)
        else:
            print("No Results Found")
    else:
        print("Error:", response.status_code, response.text)
    return res   


def bing_news_search(query):
    subscription_key = os.getenv('MST_SEARCH_KEY')
    search_url = os.getenv('MST_SEARCH_ENDPOINT') + "v7.0/news/search"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params = {"q": query, "count":10,'freshness': 'Day'}
    response = requests.get(search_url, headers=headers, params=params)
    res = []
    # Check if the request was successful
    if response.status_code == 200:
        # Extract needed data of recent news articles
        news_articles = response.json()['value']
        if news_articles:
            for article in news_articles:
                title = article['name'] if 'name' in article else ''
                description = article.get('description', '')
                url = article['url'] if 'url' in article else ''
                thumbnail_url = article['image']['thumbnail']['contentUrl'] if 'image' in article and 'thumbnail' in article['image'] else ''
                dt = {'title':title,'link':url,'description':description,'thumbnail_url':thumbnail_url}
                res.append(dt)
        else:
            print("No Results Found")
    else:
        print("Error:", response.status_code, response.text)
    return res




def mistral_chat_api(prompt):
    model = "open-mixtral-8x7b"
    mistral_client = MistralClient(api_key=MISTRAL_AI_API_KEY)
    messages = [ChatMessage(role="user", content=prompt)]
    chat_response = client.chat(model=model,messages=messages)
    return chat_response.choices[0].message.content


    

