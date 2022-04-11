from .okapi_configs import ALLOWED_FILE_EXTENSIONSFILTER_MAPPER as afemap
import os, mimetypes, requests, uuid, json, xlwt, boto3
from django.http import JsonResponse, Http404, HttpResponse
from django.contrib.auth import settings
from xlwt import Workbook
from google.cloud import translate_v2 as translate

client = translate.Client()

class DebugVariables(object): # For Class Functions only to use
    def __init__(self,flags):
        self.flags = flags
    def __call__(self, original_func):
        decorator_self = self
        def wrappee( self_func , *args, **kwargs):
            # print ('in decorator before wrapee with flag ',decorator_self.flag)
            out = original_func(self_func , *args,**kwargs)
            # print ( 'in decorator after wrapee with flag ',decorator_self.flag)
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
                # print ( os.path.splitext(  value.name  )[-1] )
                return {"processor_name": afemap.get(key, "")}
        else:
            return {"processor_name": ""}
    else:
        raise ValueError("File extension cannot be null and empty!!!")

def get_runs_and_ref_ids(format_pattern, run_reference_ids):
    # print("Format pattern ---> ", format_pattern)
    # print("Reference tag list ---> ", run_reference_ids)
    coll = []
    start_series = 57616
    # print("Zipped ---> ", zip(format_pattern, run_reference_ids))
    for i, j  in zip(format_pattern, run_reference_ids):
        tag_type_no = 57601 if i == "(" else 57602
        coll.append( [f'{chr(tag_type_no)}{chr(start_series)}',j])
        start_series += 1

    # print("Return list ---> ", coll)
    return coll

def set_ref_tags_to_runs(text_content, runs_and_ref_ids):
    # print("Text content (Coded source) ===> ", text_content)

    #    On the west coast of the island of Sumatra, the province has an area of 42,012.89 km2, and
    #   it had a population of 4,846,909 at the 2010 census[4] and 5,534,472 at the 2020 census.[5]  The province
    #   includes the Mentawai Islands off the coast and borders the provinces of North Sumatra to the north, Riau and Jambi to the
    #   east, and Bengkulu to the southeast.



    # [['\ue101\ue110', 1], ['\ue101\ue111', 2], ['\ue102\ue112', 2], ['\ue102\ue113', 1], ['\ue101\ue114', 3], ['\ue102\ue115', 3], ['\ue101\ue116', 4], ['\ue102\ue117', 4],
    # ['\ue102\ue118', 5], ['\ue102\ue119', 6], ['\ue101\ue11a', 7], ['\ue102\ue11b', 7], ['\ue102\ue11c', 8], ['\ue102\ue11d', 9], ['\ue101\ue11e', 10], ['\ue101\ue11f', 11],
    # ['\ue102\ue120', 11], ['\ue101\ue121', 12], ['\ue102\ue122', 12],
    # ['\ue101\ue123', 13], ['\ue102\ue124', 13], ['\ue101\ue125', 14], ['\ue102\ue126', 14], ['\ue101\ue127', 15], ['\ue102\ue128', 15], ['\ue102\ue129', 10]]

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

    # print("Final text content ====>", text_content)

    # <1> On the west coast of the island of <2>Sumatra</2>, the province has an area of 42,012.89 km</1><3>2</3><4>, and it had a
    # population of 4,846,909 at the 2010 census</4></5>[4]</6><7> and 5,534,472 at the 2020 census.</7></8>[5]</9><10>  The province
    # includes the <11>Mentawai Islands</11> off the coast and borders the provinces of <12>North Sumatra</12> to the north, <13>Riau</13> and <14>Jambi</14> to
    # the east, and <15>Bengkulu</15> to the southeast.</10>


    # print("Run tags ===>", run_tags)

    # ['\ue101\ue110', '\ue101\ue111', '\ue102\ue112', '\ue102\ue113', '\ue101\ue114', '\ue102\ue115', '\ue101\ue116', '\ue102\ue117', '\ue103\ue118', '\ue103\ue119',
    # '\ue101\ue11a', '\ue102\ue11b', '\ue103\ue11c', '\ue103\ue11d', '\ue101\ue11e', '\ue101\ue11f', '\ue102\ue120', '\ue101\ue121', '\ue102\ue122', '\ue101\ue123',
    # '\ue102\ue124', '\ue101\ue125', '\ue102\ue126', '\ue101\ue127', '\ue102\ue128', '\ue102\ue129']

    # print("Joined run tags ===>", "".join(run_id_tags))

    # <1><2></2></1><3></3><4></4></5></6><7></7></8></9><10><11></11><12></12><13></13><14></14><15></15></10>

    return (text_content, run_tags, ''.join(run_id_tags))

def set_runs_to_ref_tags(source_content, text_content, runs_and_ref_ids):

    # source_content
    #    On the west coast of the island of Sumatra, the province has an area of 42,012.89 km2, and
    #   it had a population of 4,846,909 at the 2010 census[4] and 5,534,472 at the 2020 census.[5]  The province
    #   includes the Mentawai Islands off the coast and borders the provinces of North Sumatra to the north, Riau and Jambi to the
    #   east, and Bengkulu to the southeast.


    #text_content

    #    சுமத்ரா தீவின் <15>மேற்கு</15> கடற்கரையில், மாகாணம் 42,012.89 கிமீ2 பரப்பளவைக் கொண்டுள்ளது, மேலும் இது 2010 <12>மக்கள்</12> தொகை கணக்கெடுப்பின்படி
    #    4,846,909 மற்றும் 2020 மக்கள்தொகை கணக்கெடுப்பின்படி 5,534,472 மக்கள்தொகையைக் கொண்டிருந்தது.[5] இந்த மாகாணமானது கடற்கரையிலிருந்து மெண்டவாய் தீவுகளை
    #    உள்ளடக்கியது மற்றும் வடக்கே வடக்கு சுமத்ரா           ரியாவ்                   
    #                   களையும்  தென்கிழக்கில்  பெங்குலு            பெங்குலு      
    #                                          கரையோர.<2></2><11>
    #    </11><13></13><14></14>


    # runs_and_ref_ids
    # # [['\ue101\ue110', 1], ['\ue101\ue111', 2], ['\ue102\ue112', 2], ['\ue102\ue113', 1], ['\ue101\ue114', 3], ['\ue102\ue115', 3], ['\ue101\ue116', 4], ['\ue102\ue117', 4],
    #     # ['\ue102\ue118', 5], ['\ue102\ue119', 6], ['\ue101\ue11a', 7], ['\ue102\ue11b', 7], ['\ue102\ue11c', 8], ['\ue102\ue11d', 9], ['\ue101\ue11e', 10], ['\ue101\ue11f', 11],
    #     # ['\ue102\ue120', 11], ['\ue101\ue121', 12], ['\ue102\ue122', 12],
    #     # ['\ue101\ue123', 13], ['\ue102\ue124', 13], ['\ue101\ue125', 14], ['\ue102\ue126', 14], ['\ue101\ue127', 15], ['\ue102\ue128', 15], ['\ue102\ue129', 10]]


    if not text_content:
        return text_content

    ids_list = [id for run, id in runs_and_ref_ids]; ids_set = set(ids_list)

    # print("ids_list ===> ", ids_list)

    #  [1, 2, 2, 1, 3, 3, 4, 4, 5, 6, 7, 7, 8, 9, 10, 11, 11, 12, 12, 13, 13, 14, 14, 15, 15, 10]

    ids_dict =  { id:ids_list.count(id) for id in ids_set}

    # print("ids_dict ===> ", ids_dict)

    #  {1: 2, 2: 2, 3: 2, 4: 2, 5: 1, 6: 1, 7: 2, 8: 1, 9: 1, 10: 2, 11: 2, 12: 2, 13: 2, 14: 2, 15: 2}

    ids_dict_for_single_tag = {id:run for run, id in runs_and_ref_ids}

    # print("ids_dict_for_single_tag ===> ", ids_dict_for_single_tag)

    #  {1: '\ue102\ue113', 2: '\ue102\ue112', 3: '\ue102\ue115', 4: '\ue102\ue117', 5: '\ue102\ue118', 6: '\ue102\ue119', 7: '\ue102\ue11b', 8: '\ue102\ue11c',
    #  9: '\ue102\ue11d', 10: '\ue102\ue129', 11: '\ue102\ue120', 12: '\ue102\ue122', 13: '\ue102\ue124', 14: '\ue102\ue126', 15: '\ue102\ue128'}

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


def download_file(file_path):

    filename = os.path.basename(file_path)
    fl = open(file_path, 'rb')
    mime_type, _ = mimetypes.guess_type(file_path)
    response = HttpResponse(fl, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response

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
    return translate.translate_text( Text = source_string,
                                     SourceLanguageCode = source_lang_code,
                                     TargetLanguageCode = target_lang_code)["TranslatedText"]


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


class OkapiUtils:
    def get_translated_file_(self):
        pass

def download_file(file_path):
    filename = os.path.basename(file_path)
    fl = open(file_path, 'rb')
    mime_type, _ = mimetypes.guess_type(file_path)
    response = HttpResponse(fl, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response

bl_title_format = {
    'bold': True,
    'font_color': 'black',
}

bl_cell_format = {
    'text_wrap': True,
    'align': 'left',
}
