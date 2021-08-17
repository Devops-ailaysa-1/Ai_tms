from .okapi_configs import ALLOWED_FILE_EXTENSIONSFILTER_MAPPER as afemap
import os

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

def set_runs_to_ref_tags(text_content, runs_and_ref_ids):
    if not text_content: return text_content

    for run, ref_id in runs_and_ref_ids:
        if "\ue101" in run:
            run_id_tag = "<"+str(ref_id)+">"
            if not run in text_content:
                run = run.replace("\ue101", "\ue103")
        else:
            run_id_tag = "</"+str(ref_id)+">"
            if not run in text_content:
                run = run.replace("\ue102", "\ue103")
        text_content = text_content.replace(run_id_tag, run)
    return text_content


