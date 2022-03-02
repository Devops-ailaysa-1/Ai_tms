from .okapi_configs import ALLOWED_FILE_EXTENSIONSFILTER_MAPPER as afemap
import os, mimetypes, requests, uuid, json, xlwt
from django.http import JsonResponse, Http404, HttpResponse
from django.contrib.auth import settings
from xlwt import Workbook


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
                text_content = open_tag+close_tag+text_content

        else:
            run = ids_dict_for_single_tag.get(id)
            if "\ue101" in run:
                tag = "<" + str(id) + ">"
            else:
                tag = "</" + str(id) + ">"

            if tag not in text_content:
                text_content = tag+text_content


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

