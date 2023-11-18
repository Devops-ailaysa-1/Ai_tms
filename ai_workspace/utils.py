import os
import random
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import StringIO, BytesIO
import sys
import string


class DjRestUtils:

    def get_a_inmemoryuploaded_file():
        io = BytesIO()
        with open("/home/langscape/Documents/translate_status_api.txt", "rb") as f:
            io.write(f.read())
        io.seek(0)
        im = InMemoryUploadedFile(io, None, "text.txt", "text/plain",
                sys.getsizeof(io), None)
        return im

    def convert_content_to_inmemoryfile(filecontent, file_name):
        # text/plain hardcoded may be needs to be change as generic...
        io = BytesIO()
        io.write(filecontent)
        io.seek(0)
        im = InMemoryUploadedFile(io, None, file_name,
                                  "text/plain", sys.getsizeof(io), None)
        return im

def create_dirs_if_not_exists(path):
	if not os.path.isdir(path):
		os.makedirs(path)
		return  path
	return create_dirs_if_not_exists(path+random.choice(["-", "_","@", "!"])+str(random.randint(1,100)))

def print_key_value(keys, values):
	for i, j in zip(keys, values):
		print(f'{i}--->{j}')


def create_assignment_id():
	from ai_workspace.models import TaskAssignInfo
	chars=string.ascii_uppercase + string.digits
	size=6
	rand_id = "AS-"+''.join(random.choice(chars) for _ in range(size))
	pr = TaskAssignInfo.objects.filter(assignment_id = rand_id)
	if not pr:
		return  rand_id
	return create_assignment_id()



def create_task_id():
	from ai_workspace.models import Task
	chars=string.ascii_uppercase + string.digits
	size=6
	rand_id = "TK-"+''.join(random.choice(chars) for _ in range(size))
	pr = Task.objects.filter(ai_taskid = rand_id)
	if not pr:
		return  rand_id
	return create_task_id()


def create_ai_project_id_if_not_exists(user):
	from ai_workspace.models import Project
	rand_id = user.uid+"p"+str(random.randint(1,10000))
	pr = Project.objects.filter(ai_project_id = rand_id)
	if not pr:
		return  rand_id
	return create_ai_project_id_if_not_exists(user)
# //////////////// References \\\\\\\\\\\\\\\\\\\\

# random.choice([1,2,3])  ---> 2
# random.choice([1,2,3])  ---> 2
# random.choices([1,2,3])  ---> [2]
import math

def roundup(x):
    return int(math.ceil(x / 15.0)) * 15



def get_consumable_credits_for_text_to_speech(total_chars):
    return round(total_chars/20)

def get_consumable_credits_for_speech_to_text(total_seconds):#######Minimum billable 15 seconds##########
    return round(roundup(total_seconds)/3)

def task_assing_role_ls(task_assign_info_ls):
	from ai_auth.signals import assign_object
	from ai_auth.utils import get_assignment_role
	from ai_workspace.models import TaskAssignInfo
	from ai_workspace.models import AiRoleandStep
	objs = TaskAssignInfo.objects.filter(id__in=task_assign_info_ls)
	for instance in objs:
		role = get_assignment_role(instance,instance.task_assign.step,instance.task_assign.reassigned)
		# role= AiRoleandStep.objects.get(step=instance.task_assign.step).role.name
		assign_object.send(
			sender=TaskAssignInfo,
			instance = instance,
			user=instance.task_assign.assign_to,
			role = role
		)


import copy,json

TRANSLATABLE_KEYS_FEDARAL=os.getenv("TRANSLATABLE_KEYS_FEDARAL").split(" ")
HTML_MIME_FEDARAL=os.getenv("HTML_MIME_FEDARAL").split(" ")


MIME_TYPE_FEDARAL = {'html': 'html', 'text': 'text'}
LIST_KEYS_FEDARAL={'media':['caption'] , 'news_tags':['name']}

# print(TRANSLATABLE_KEYS_FEDARAL)
# print(HTML_MIME_FEDARAL)
# print(MIME_TYPE_FEDARAL)
# print(LIST_KEYS_FEDARAL)

import json

def federal_json_translate(json_data,tar_code,src_code):
    print("tar_code-->",tar_code)
    print("src_code-->",src_code)
    
    from ai_workspace_okapi.utils import get_translation
    json_file_copy = copy.deepcopy(json_data)
    for key,value in json_file_copy.items():
        if key in TRANSLATABLE_KEYS_FEDARAL:
            format_ = MIME_TYPE_FEDARAL['html'] if key in HTML_MIME_FEDARAL else MIME_TYPE_FEDARAL['text']
            if type(value) == list:
                if key in  LIST_KEYS_FEDARAL.keys(): #news_tags media
                    for lists in LIST_KEYS_FEDARAL[key]:
                        for list_names in json_file_copy[key]:
                            if lists in list_names.keys():
                                  list_names[lists] = get_translation(mt_engine_id=1,source_string=list_names[lists],target_lang_code=tar_code,
																	source_lang_code=src_code,format_=format_)
            else:
                json_file_copy[key] =  get_translation(mt_engine_id=1,source_string=json_file_copy[key],target_lang_code=tar_code,
														source_lang_code=src_code,format_=format_)
    return  json_file_copy




# def federal_json(json_data,tar_code,src_code):
#     from ai_workspace_okapi.utils import get_translation
#     translated_json_list = []
#     json_data = json_data['news']
#     for i in json_data:
#         json_file_copy = copy.deepcopy(i)
#         for key,value in json_file_copy.items():
#             if key in TRANSLATABLE_KEYS_FEDARAL:
#                 format_ = MIME_TYPE_FEDARAL['html'] if key in HTML_MIME_FEDARAL else MIME_TYPE_FEDARAL['text']
                 
#                 if type(value) == list:
#                     if key in  LIST_KEYS_FEDARAL.keys(): #news_tags media
#                         for lists in LIST_KEYS_FEDARAL[key]:
#                             for list_names in json_file_copy[key]:
#                                 if lists in list_names.keys():
#                                     list_names[lists] = get_translation(mt_engine_id=1,source_string=list_names[lists],target_lang_code=tar_code,
# 																	source_lang_code=src_code,format_=format_)
#                 else:
#                     json_file_copy[key] =  get_translation(mt_engine_id=1,source_string=json_file_copy[key],target_lang_code=tar_code,
# 														source_lang_code=src_code,format_=format_)
#         translated_json_list.append(json_file_copy)
#     return  {'news': translated_json_list}



# def fedaral_json_translate(json_file,tar_code,src_code):
#     with open(json_file,'r') as fp:
#         jf = json.load(fp)
# 	translated_json_list = []
# 	json_files = jf['news']
# 	for json_file in json_files:
# 		json_file_copy=copy.deepcopy(json_file)
# 		for key,value in json_file_copy.items():
# 			if key in TRANSLATABLE_KEYS_FEDARAL:
# 				format_ = MIME_TYPE_FEDARAL['html'] if key in HTML_MIME_FEDARAL else MIME_TYPE_FEDARAL['text']
# 				if type(value) == list:
# 					if key in  LIST_KEYS_FEDARAL.keys(): #news_tags media
# 						for lists in LIST_KEYS_FEDARAL[key]:
# 							for list_names in json_file_copy[key]:
# 								list_names[lists] = get_translation(mt_engine_id=1,source_string=list_names[lists],target_lang_code=tar_code,
# 																	source_lang_code=src_code,format_=format_)
# 				else:
# 					json_file_copy[key] =  get_translation(mt_engine_id=1,source_string=json_file_copy[key],target_lang_code=tar_code,
# 														source_lang_code=src_code,format_=format_)
# 		translated_json_list.append(json_file_copy)
#     return {'news':translated_json_list}


# def generate_list_cache_key(user):
#     print("R---->",user)
#     user_1 = user.team.owner if user.team and user.team.owner.is_agency and (user in user.team.get_project_manager) else user
#     return f'pr_list:{user_1.id}'


# from functools import wraps
# from django.core.cache import cache


# def custom_cache_page(timeout, key_func):
#     def decorator(view_func):
#         @wraps(view_func)
#         def _wrapped_view(request, *args, **kwargs):
#             cache_key = key_func(request.user)
#             response = cache.get(cache_key)
#             if response is None:
#                 response = view_func(request, *args, **kwargs)
#                 cache.set(cache_key, response, timeout)
#             return response
#         return _wrapped_view
#     return decorator











# from functools import wraps
# from django.core.cache import cache
# def custom_cache_page(timeout):
#     def decorator(view_func):
#         @wraps(view_func)
#         def _wrapped_view(request, *args, **kwargs):
#             user = request.user
#             cache_key = get_pr_list_cache_key(user)
#             cached_data = cache.get(cache_key)
#             if cached_data is not None:
#                 return cached_data
#             response = view_func(request, *args, **kwargs)
#             cache.set(cache_key, response, timeout)
#             return response
#         return _wrapped_view
#     return decorator

