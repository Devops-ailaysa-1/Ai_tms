from .okapi_configs import ALLOWED_FILE_EXTENSIONSFILTER_MAPPER as afemap
from .okapi_configs import LINGVANEX_LANGUAGE_MAPPER as llmap
import os, mimetypes, requests, uuid, json, xlwt, boto3, urllib
from django.http import JsonResponse, Http404, HttpResponse
from django.contrib.auth import settings
from xlwt import Workbook
from django.core.files import File as DJFile
from google.cloud import translate_v2 as translate


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
        print("FIle is uploaded successfully!!!")

    def delete_object(file_path, bucket_name="media"):
        client = SpacesService.get_client()
        client.delete_object(Bucket=bucket_name, Key=file_path)
        print("FIle is deleted successfully!!!")

# class OkapiUtils:
#     def get_translated_file_(self):
#         pass

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

    path = '/translate'
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

def get_translation(mt_engine_id, source_string, source_lang_code, target_lang_code):
    # FOR GOOGLE TRANSLATE
    if mt_engine_id == 1:

        return client.translate(source_string,
                                target_language=target_lang_code,
                                format_="text").get("translatedText")
    # FOR MICROSOFT TRANSLATE
    elif mt_engine_id == 2:
        return ms_translation(source_string, source_lang_code, target_lang_code)

    # AMAZON TRANSLATE
    elif mt_engine_id == 3:
        return aws_translate(source_string, source_lang_code, target_lang_code)

    # LINGVANEX TRANSLATE
    elif mt_engine_id == 4:
        return lingvanex(source_string, source_lang_code, target_lang_code)


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
                 "use_spaces": settings.USE_SPACES
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
        res_paths["srx_file_path"] = "okapi_resources/tamil001.srx"
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

# def split_check(segment_id):
#     from .models import Segment
#     return bool((Segment.objects.filter(id=segment_id).first() != None) and \
#                 (Segment.objects.filter(id=segment_id).first().is_split in [None, False]))


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
