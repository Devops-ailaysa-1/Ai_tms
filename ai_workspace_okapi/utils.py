from .okapi_configs import ALLOWED_FILE_EXTENSIONSFILTER_MAPPER as afemap
from .okapi_configs import LINGVANEX_LANGUAGE_MAPPER as llmap, EMPTY_SEGMENT_CHARACTERS
import os, mimetypes, requests, uuid, json, xlwt, boto3, urllib,difflib
from django.http import JsonResponse, Http404, HttpResponse
from django.contrib.auth import settings
from xlwt import Workbook
from django.core.files import File as DJFile
from google.cloud import translate_v2 as translate
from ai_auth.models import AiUser
from PyPDF2 import PdfFileReader
from pptx import Presentation
import string
import backoff


spring_host = os.environ.get("SPRING_HOST")

# from ai_workspace_okapi.models import SelflearningAsset
def special_character_check(s): 
    return all(i in string.punctuation or i.isdigit() if i!=" " else True for i in s.strip())
client = translate.Client()

class DebugVariables(object): # For Class Functions only to use
    def __init__(self,flags):
        self.flags = flags
    def __call__(self, original_func):
        decorator_self = self
        def wrappee( self_func , *args, **kwargs):
            out = original_func(self_func , *args,**kwargs)
            function_name = original_func.__qualname__
            for i in self.flags :
                if type(i) == str :
                    print ( f'{i} = {self_func.__getattribute__( i )} in {function_name}' )
                if type(i) == tuple :
                    print( f'{i[0]} = {i[1](self_func.__getattribute__( i[0] ))} in {function_name}' )

            return  out
        return wrappee


def get_file_extension(file_path):
    return  (os.path.splitext(file_path)[-1]
            if len(os.path.splitext(file_path))>=1
            else None)

def get_processor_name(file_path):  # Full File Path Assumed
    file_ext = get_file_extension(file_path=file_path) # .doc [Sample]
    if file_ext:
        for key in afemap.keys():
            if file_ext in key:
                return {"processor_name": afemap.get(key, "")}
        else:
            return {"processor_name": ""}
    else:
        raise ValueError("File extension cannot be null and empty!!!")

def get_runs_and_ref_ids(format_pattern, run_reference_ids):
    coll = []
    start_series = 57616

    for i, j  in zip(format_pattern, run_reference_ids):
        tag_type_no = 57601 if i == "(" else 57602
        coll.append( [f'{chr(tag_type_no)}{chr(start_series)}',j])
        start_series += 1

    return coll

def set_ref_tags_to_runs(text_content, runs_and_ref_ids):

    run_tags, run_id_tags = [], []
    for run, ref_id in runs_and_ref_ids:
        if "\ue101" in run:
            run_id_tag = "<"+str(ref_id)+">"
            if not run in text_content:
                run = run.replace("\ue101", "\ue103")
        else:
            run_id_tag = "</"+str(ref_id)+">"
            if not run in text_content:
                run = run.replace("\ue102", "\ue103")
        run_tags.append(run)
        run_id_tags.append(run_id_tag)
        text_content = text_content.replace(run, run_id_tag)

    return (text_content, run_tags, ''.join(run_id_tags))

def set_runs_to_ref_tags(source_content, text_content, runs_and_ref_ids):


    if not text_content:
        return text_content

    ids_list = [id for run, id in runs_and_ref_ids]; ids_set = set(ids_list)

    ids_dict =  { id:ids_list.count(id) for id in ids_set}

    ids_dict_for_single_tag = {id:run for run, id in runs_and_ref_ids}

    for id, count in ids_dict.items():
        if count == 2:
            open_tag = "<"+str(id)+">"
            close_tag = "</"+str(id)+">"

            if ((
                not(
                    (open_tag in text_content) and \
                    (close_tag in text_content)\
                    )\
                ) or \
                (text_content.index(open_tag)>text_content\
                .index(close_tag))):
                text_content = text_content.replace(open_tag,'')
                text_content = text_content.replace(close_tag, '')
                # text_content = open_tag + close_tag + text_content
                text_content = text_content + open_tag + close_tag

        else:
            run = ids_dict_for_single_tag.get(id)
            if "\ue101" in run:
                tag = "<" + str(id) + ">"
            else:
                tag = "</" + str(id) + ">"

            if tag not in text_content:
                # text_content = tag+text_content
                text_content = text_content + tag


    missed_ref_ids = []

    for run, ref_id in runs_and_ref_ids:

        if "\ue101" in run:
            run_id_tag = "<"+str(ref_id)+">"
            if not run in source_content:
                run = run.replace("\ue101", "\ue103")
        else:
            run_id_tag = "</"+str(ref_id)+">"
            if not run in source_content:
                run = run.replace("\ue102", "\ue103")

        text_content = text_content.replace(run_id_tag, run)

    return text_content

class SpacesService:

    def get_client():
        session = boto3.session.Session()
        client = session.client(
            's3',
            region_name='ams3',
            endpoint_url='https://ailaysa.ams3.digitaloceanspaces.com',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        return client

    def put_object(output_file_path, f_stream, bucket_name="media"):
        client = SpacesService.get_client()
        obj = client.put_object(
            Bucket=bucket_name,
            Key=output_file_path,
            Body=f_stream.read()
        )

    def delete_object(file_path, bucket_name="media"):
        client = SpacesService.get_client()
        client.delete_object(Bucket=bucket_name, Key=file_path)


def download_file(file_path):
    filename = os.path.basename(file_path)
    fl = open(file_path, 'rb')
    mime_type, _ = mimetypes.guess_type(file_path)
    response = HttpResponse(fl, content_type=mime_type)
    encoded_filename = urllib.parse.quote(os.path.basename(file_path), \
                                          encoding='utf-8')
    response['Content-Disposition'] = 'attachment;filename*=UTF-8\'\'{}' \
        .format(encoded_filename)
    response['X-Suggested-Filename'] = encoded_filename
    #response['Content-Disposition'] = "attachment; filename=%s" % filename
    response['Access-Control-Expose-Headers'] = 'Content-Disposition'
    return response

bl_title_format = {
    'bold': True,
    'font_color': 'black',
}

bl_cell_format = {
    'text_wrap': True,
    'align': 'left',
}

def get_aws_lang_code(lang_code):
    if lang_code == "zh-Hans":
        return lang_code[:2]
    elif lang_code == "zh-Hant":
        return "zh-TW"
    else:
        return lang_code

def ms_translation(source_string, source_lang_code, target_lang_code):

    # Add your subscription key and endpoint
    subscription_key = os.getenv("MST_KEY")
    endpoint = os.getenv("MST_API")

    # Add your location, also known as region. The default is global.
    # This is required if using a Cognitive Services resource.
    location = os.getenv("MST_LOCATION")

    path = 'translate'
    constructed_url = endpoint + path

    params = {
        'api-version': '3.0',
        'from': source_lang_code,
        'to': [target_lang_code]
    }

    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    # You can pass more than one object in body.
    body = [{
        'text': source_string
    }]

    request = requests.post(constructed_url, params=params, headers=headers, json=body)
    return request.json()[0]["translations"][0]["text"]

    # print(json.dumps(response, sort_keys=True, ensure_ascii=False, indent=4, separators=(',', ': ')))

def aws_translate(source_string, source_lang_code, target_lang_code):
    translate = boto3.client(service_name = 'translate',
                             region_name = os.getenv('aws_iam_region_name'),
                             aws_access_key_id = os.getenv("aws_iam_access_key_id"),
                             aws_secret_access_key = os.getenv("aws_iam_secret_access_key")
                                )
    source_lang_code = get_aws_lang_code(source_lang_code)
    target_lang_code = get_aws_lang_code(target_lang_code)
    return translate.translate_text( Text = source_string,
                                     SourceLanguageCode = source_lang_code,
                                     TargetLanguageCode = target_lang_code)["TranslatedText"]

def lingvanex(source_string, source_lang_code, target_lang_code):
    url = os.getenv("lingvanex_translate_url")
    sl_code = (f'{source_lang_code}',)
    tl_code = (f'{target_lang_code}',)

    data = {

        "from": llmap.get(sl_code, ""),
        "to": llmap.get(tl_code, ""),
        "data": source_string,
        "platform": "api",
        "enableTransliteration": 'false'
    }

    headers = {
        'accept': 'application/json',
        'Authorization': os.getenv("lingvanex_mt_api_key"),
        'Content-Type': 'application/json',
    }

    r = requests.post(url, headers=headers, json=data)
    return r.json()["result"]

 
@backoff.on_exception(backoff.expo,(requests.exceptions.RequestException,requests.exceptions.ConnectionError,),max_tries=2)
def get_translation(mt_engine_id, source_string, source_lang_code, 
                    target_lang_code, user_id=None, cc=None, from_open_ai = None):
    from ai_workspace.api_views import get_consumable_credits_for_text,UpdateTaskCreditStatus
    from ai_auth.tasks import record_api_usage

    mt_called = True

    if user_id==None:
        user,uid,email,initial_credit = None,None,None,None

    else:
        user = AiUser.objects.get(id=user_id)
        uid = user.uid
        email= user.email
        initial_credit = user.credit_balance.get("total_left")

    if cc == None:
        if isinstance(source_string,list):
            for src_text in source_string:
                cc=0
                cc+= get_consumable_credits_for_text(src_text,target_lang_code,source_lang_code)
        else:
            cc = get_consumable_credits_for_text(source_string,target_lang_code,source_lang_code)

    print("Init-------->",initial_credit)
    print("cc-------->",cc)
    print("from_open_ai---------->",from_open_ai)
    print("source----------->",source_string)
    
    
    if isinstance(source_string,str) and special_character_check(source_string)  :
        print("Inside--->")
        mt_called = False
        translate = source_string

    elif user and not from_open_ai and initial_credit < cc:
            print("Insufficient")
            translate = ''
    
    # FOR GOOGLE TRANSLATE
    elif mt_engine_id == 1:
        record_api_usage.apply_async(("GCP","Machine Translation",uid,email,len(source_string)), queue='low-priority')
        translate = client.translate(source_string,
                                target_language=target_lang_code,
                                format_="text").get("translatedText")
    # FOR MICROSOFT TRANSLATE
    elif mt_engine_id == 2:
        record_api_usage.apply_async(("AZURE","Machine Translation",uid,email,len(source_string)), queue='low-priority')
        translate = ms_translation(source_string, source_lang_code, target_lang_code)

    # AMAZON TRANSLATE
    elif mt_engine_id == 3:
        record_api_usage.apply_async(("AWS","Machine Translation",uid,email,len(source_string)), queue='low-priority')
        translate = aws_translate(source_string, source_lang_code, target_lang_code)

    # LINGVANEX TRANSLATE
    elif mt_engine_id == 4:
        record_api_usage.apply_async(("LINGVANEX","Machine Translation",uid,email,len(source_string)), queue='low-priority')
        translate = lingvanex(source_string, source_lang_code, target_lang_code)
    
    print("Mt called------->",mt_called)
    if mt_called == True and from_open_ai == None:
        if user:
            debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, cc)
            print("status_code---------->",status_code)
            print("Debited----------->",cc,user.credit_balance.get("total_left"))
    else:
        print('Not debited in this func')
    print("Translate---------->",translate)
    return translate
    


def text_to_speech(ssml_file,target_language,filename,voice_gender,voice_name):
    from ai_staff.models import MTLanguageLocaleVoiceSupport
    from google.cloud import texttospeech
    gender = texttospeech.SsmlVoiceGender.MALE if voice_gender == 'MALE' else  texttospeech.SsmlVoiceGender.FEMALE
    voice_name = voice_name if voice_name else MTLanguageLocaleVoiceSupport.objects.filter(language__locale__locale_code = target_language).first().voice_name
    #filename = filename + "_out"+ ".mp3"
    path, name = os.path.split(ssml_file)

    client = texttospeech.TextToSpeechClient()
    with open(ssml_file, "r") as f:
        ssml = f.read()
        input_text = texttospeech.SynthesisInput(ssml=ssml)
    #print("Len of input text in API---------------->",len(input_text))
    voice = texttospeech.VoiceSelectionParams(
        name=voice_name,language_code=target_language, ssml_gender=gender
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,sample_rate_hertz=24000
    )
    response = client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )
    with open(filename,"wb") as out:
        out.write(response.audio_content)
    f2 = open(filename, 'rb')
    file_obj = DJFile(f2)
    return file_obj,f2
    # dir = os.path.join(path,"Audio")
    # if not os.path.exists(dir):
    #     os.mkdir(dir)
    # with open(os.path.join(dir,filename), "wb") as out:
    #     out.write(response.audio_content)
    #     print('Audio content written to file',filename)
    # return os.path.join(dir,filename)


def get_res_path(source_lang):

    res_paths = {"srx_file_path": "okapi_resources/okapi_default_icu4j.srx",
                 "fprm_file_path": None,
                 "use_spaces": settings.USE_SPACES,
                 "empty_segment_chars": EMPTY_SEGMENT_CHARACTERS,
                 }

    if source_lang in ['hi','bn','or','ne','pa']:
        res_paths["srx_file_path"] = "okapi_resources/indian_lang.srx"
        return res_paths

    elif source_lang in ['zh-Hans','zh-Hant','ja']:
        res_paths["srx_file_path"] = "okapi_resources/zh_and_ja.srx"
        return res_paths

    elif source_lang in ['th']:
        res_paths["srx_file_path"] = "okapi_resources/thai.srx"
        return res_paths

    elif source_lang in ['ta']:
        res_paths["srx_file_path"] = "okapi_resources/tamil.srx"
        return res_paths
    elif source_lang in ['kn']:
        res_paths["srx_file_path"] = "okapi_resources/kannada.srx"
        return res_paths
    elif source_lang in ['te']:
        res_paths["srx_file_path"] = "okapi_resources/telugu.srx"
        return res_paths
    elif source_lang in ['ml']:
        res_paths["srx_file_path"] = "okapi_resources/malayalam.srx"
        return res_paths
    elif source_lang in ['km']:
        res_paths["srx_file_path"] = "okapi_resources/khmer.srx"
        return res_paths
    else:
        return res_paths

def text_to_speech_long(ssml_file,target_language,filename,voice_gender,voice_name):
    from ai_staff.models import MTLanguageLocaleVoiceSupport
    from google.cloud import texttospeech
    gender = texttospeech.SsmlVoiceGender.MALE if voice_gender == 'MALE' else  texttospeech.SsmlVoiceGender.FEMALE
    voice_name = voice_name if voice_name else \
        MTLanguageLocaleVoiceSupport.objects.filter(language__locale__locale_code = target_language).first().voice_name
    #filename = filename + "_out"+ ".mp3"
    path, name = os.path.split(ssml_file)
    client = texttospeech.TextToSpeechClient()
    with open(ssml_file, "r") as f:
        ssml = f.read()
        input_text = texttospeech.SynthesisInput(ssml=ssml)
    #print("File----------->",ssml_file)
    #print("Len of input text in API---------------->",len(ssml))
    voice = texttospeech.VoiceSelectionParams(
        name=voice_name,language_code=target_language, ssml_gender=gender
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,sample_rate_hertz=24000
    )
    response = client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )
    #print("Response------------>",response)
    if len(response.audio_content) != 0:
        with open(filename,"wb") as out:
            out.write(response.audio_content)
            print('Audio content written to file',filename)

def split_check(segment_id):
    from ai_workspace_okapi.models import SplitSegment
    split_seg = SplitSegment.objects.filter(id=segment_id).first()
    if split_seg:
        if split_seg.segment.is_split == True:
            return False
        else:
            return True
    else:
        return True

import difflib

def do_compare_sentence(source_segment,edited_segment,sentense_diff=False):
    diff_words=[]
    pair_words=[]
    if sentense_diff:
        diff=seq_match_seg_diff(source_segment,edited_segment)
        return diff 
    else:
        difftool = difflib.Differ()
        diff = difftool.compare(source_segment.split(),edited_segment.split())
        for line in diff:
            if not line.startswith(" "):
                if line.startswith("-"):
                    diff_words.append(line)
                elif line.startswith("+"):
                    diff_words.append(line)
            for i in range(len(diff_words)-1):
                if diff_words[i][0]=='-' and diff_words[i+1][0]=='+':
                    pair_words.append((diff_words[i][1:].strip(),diff_words[i+1][1:].strip()))
        return pair_words

def seq_match_seg_diff(words1,words2):
    s1=words1.split()
    s2=words2.split()
    matcher=difflib.SequenceMatcher(None,s1,s2 )
    save_type=[]
    data=[]
    for tag,i1,i2,j1,j2 in matcher.get_opcodes():
        if tag=='equal':
            data.append(" ".join(s2[j1:j2]))
        elif tag=='replace':
            data.append('<ins class="changed-word">'+ " ".join(s2[j1:j2])+'</ins>'+'<del>'+" ".join(s1[i1:i2])+'</del>')
            save_type.append('insert')
        elif tag=='insert':
            data.append('<ins class="changed-word">'+ " ".join(s2[j1:j2])+'</ins>')
            save_type.append('insert')
        elif tag=='delete':
            data.append('<del class="removed-word">'+ " ".join(s1[i1:i2])+'</del>')
            save_type.append('delete')
    if save_type:
        save_type=list(set(save_type))
    return (" ".join(data)," ".join(save_type))

def get_general_prompt(opt,sent):

    if opt == "Rewrite":
        prompt = '''Paraphrase the given text. Text: {} '''.format(sent)

    elif opt == "Simplify":
        prompt = '''Simplify the given text. Text: {}'''.format(sent)

    elif opt == "Shorten":
        prompt = '''Shorten the given text without losing any significant information in it. Text: {}'''.format(sent)                

    return prompt

def get_prompt(sent,subs,cont):
    if subs == []:subs_str = 'English language'
    else: subs_str =  ', '.join(subs)
    if cont == []:cont_str = 'easy-to-understand content'
    else: cont_str = ', '.join(cont)
    if len(sent)<=20:
        prompt = '''Rewrite the given text. Text: {} '''.format(sent)

def get_prompt_sent(opt,sent):

    if opt == "Rewrite":
        if len(sent)>200:
            prompt = '''Split the following text into multiple simple sentences:
                {}'''.format(sent)
        else:
            prompt = '''Paraphrase the given text: {} '''.format(sent)
    elif opt == "Simplify":
        prompt = '''Simplify the given text so that even a non-native English speaker can easily understand it. Text: {}'''.format(sent)

    elif opt == "Shorten":
        prompt = '''Shorten the given text without losing any significant information in it. Text: {}'''.format(sent)                
    return prompt

    # if subs == []:
    #     subs = 'English language'
    # if cont == []:
    #     cont = 'easy-to-understand content'
    # if subs == [] or conts == []: 
    #     if len(sent)>200:
    #         prompt = '''

    #                 As an English language specialist and a writer skilled in creating easy-to-understand content, please perform the following tasks and provide only one final result without any prefix:


    #                 1. Split the given sentence into multiple sentences.
    #                 2. Rewrite each sentence to be understandable for non-native English speakers or language learners while keeping technical terms when possible.
    #                 3. Additionally, simplify each sentence by replacing idioms, phrases, or phrasal verbs with clearer and direct words, without altering the meaning or tone.

    #                 If the provided text contains idioms or phrases, follow steps 1 and 3. Otherwise, follow steps 1 and 2.

    #                 Text: '''+sent 
                       # Please execute the prompt with the necessary inputs, and the final result will only include the rewritten and simplified sentences.
    #     else:
    #         prompt = '''

    #                 As an English language specialist and a writer skilled in creating easy-to-understand content, please perform the following tasks and provide only one final result without any prefix:

    #                 1. Rewrite the provided text to be understandable for non-native English speakers or language learners while keeping technical terms when possible.
    #                 2. Additionally, simplify text by replacing idioms, phrases, or phrasal verbs with clearer and direct words, without altering the meaning or tone.

    #                 If the provided text contains idioms or phrases, follow step 2. Otherwise, follow step 1.

    # #                 Text: '''+sent
    #                   Subject Fields: {} 
    #             Content Types: {} 
    #             Please execute the prompt with the necessary inputs, and the final result will only include the rewritten and simplified sentences.'''.format(sent,subs,cont) 
    # else:


GOOGLE_TRANSLATION_API_PROJECT_ID= os.getenv('GOOGLE_TRANSLATION_API_PROJECT_ID')
GOOGLE_LOCATION =  os.getenv('GOOGLE_LOCATION')

google_mime_type = {'doc':'application/msword',	 
                    'docx':	'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'pdf':	'application/pdf',
                    'ppt':	'application/vnd.ms-powerpoint'	,
                    'pptx':	'application/vnd.openxmlformats-officedocument.presentationml.presentation'	,
                    'xls':	'application/vnd.ms-excel',
                    'xlsx':	'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'txt':  'application/msword' }


from google.cloud import translate_v3beta1 as translate
from django import core
import requests, os
#from pptx import Presentation

def file_translate(file_path,target_language_code):
    parent = f"projects/{GOOGLE_TRANSLATION_API_PROJECT_ID}/locations/{GOOGLE_LOCATION}"
    file_type = file_path.split("/")[-1].split(".")
    file_format=file_type[-1]
    file_name = file_type[0]
    client = translate.TranslationServiceClient()
    if file_format not in google_mime_type.keys():
        print("file not support")
    mime_type = google_mime_type.get(file_format,None)
    with open(file_path, "rb") as document:
        document_content = document.read()
        document_input_config = {"content": document_content,"mime_type": mime_type,}
    response = client.translate_document(request={
            "parent": parent,
            "target_language_code": target_language_code,
            "document_input_config": document_input_config})
    file_name = file_name+"_"+target_language_code+"."+file_format
    byte_text = response.document_translation.byte_stream_outputs[0]
    file_obj = core.files.File(core.files.base.ContentFile(byte_text),file_name)
    return file_obj,file_name


import subprocess
import io

def page_count_in_docx(docx_path):

    command = [
        'libreoffice',
        '--headless',
        '--convert-to', 'pdf',
        '--outdir', '/tmp',  # Specify an output directory
        docx_path
    ]


    subprocess.run(command, check=True)
    filename = os.path.basename(docx_path)
    file_path = '/tmp/'+filename.split('.')[0]+'.pdf'
    # Read the generated PDF into memory
    pdf = PdfFileReader(open(file_path,'rb') ,strict=False)
    pages = pdf.getNumPages()
    return pages,file_path

# def page_count_in_docx(docx_path):
#     import zipfile
#     import xml.etree.ElementTree as ET
#     namespace = {'ns': 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'}
#     with zipfile.ZipFile(docx_path, 'r') as zip_file: 
#         zip_file_contents = zip_file.namelist()
#         for file_name in zip_file_contents:
#             if file_name.endswith("docProps/app.xml"):
#                 extracted_data = zip_file.read(file_name)
#                 xml_tree = ET.fromstring(extracted_data)
#                 if docx_path.split(".")[-1] in ["docx","doc"]:
#                     element_to_find = 'Pages'
#                 if docx_path.split(".")[-1] in ["ppt","pptx"]:
#                     element_to_find = 'Slides'
#                 found_element = xml_tree.find(f'.//ns:{element_to_find}', namespaces=namespace)
#                 if found_element is not None:
#                     return int(found_element.text)
#                 else:
#                     return None

def count_pptx_slides(pptx_file_path):
    presentation = Presentation(pptx_file_path)
    slide_count = len(presentation.slides)
    return slide_count

def get_word_count(task):
    from ai_workspace.serializers import TaskSerializer
    from ai_workspace_okapi.api_views import DocumentViewByTask
    
    data = TaskSerializer(task).data
    DocumentViewByTask.correct_fields(data)
    params_data = {**data, "output_type": None}
    res_paths = get_res_path(params_data["source_language"])
    doc = requests.post(url=f"http://{spring_host}:8080/getDocument/", data={
        "doc_req_params":json.dumps(params_data),
        "doc_req_res_params": json.dumps(res_paths)
    })
    print("status------------>",doc.status_code)
    if doc.status_code == 200:
        doc_data = doc.json()
        return doc_data.get('total_word_count')
    else:
        return None


def consumption_of_credits_for_page(page_count):
    return page_count * 250

def get_consumption_of_file_translate(task):
    file,ext = os.path.splitext(task.file.file.path)
    if ext == '.pdf':
        pdf = PdfFileReader(open(task.file.file.path,'rb') ,strict=False)
        pages = pdf.getNumPages()
        return consumption_of_credits_for_page(pages)

    if ext == '.docx' or ext == '.doc':
        page_count,file_path = page_count_in_docx(task.file.file.path)
        print("PC----------->",page_count)
        os.remove(file_path)
        return consumption_of_credits_for_page(page_count)

    if ext == '.pptx': #or ext == '.ppt':
        page_count = count_pptx_slides(task.file.file.path)
        return consumption_of_credits_for_page(page_count)

    if ext == '.xlsx':# or ext == '.xls':
        word_count = get_word_count(task)
        return word_count

    else:
        return None



