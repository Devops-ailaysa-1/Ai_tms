import os
import random
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import StringIO, BytesIO
import sys
import string
import re
from indicnlp.tokenize.sentence_tokenize import sentence_split
import nltk


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
LIST_KEYS_FEDARAL={'media':['caption']}# , 'news_tags':['name']}


####Need to add credit check and function to get MT for each key####################
def federal_json_translate(json_file,tar_code,src_code,user,translate=True):
	from ai_workspace_okapi.utils import get_translation
	
	try:json_data = json_file['news'][0]
	except: json_data = json_file
	json_file_copy = copy.deepcopy(json_data)
	# for json_data in json_file:
	# 	json_file_copy = copy.deepcopy(json_data)
	for key,value in json_file_copy.items():
		if key in TRANSLATABLE_KEYS_FEDARAL:
			format_ = MIME_TYPE_FEDARAL['html'] if key in HTML_MIME_FEDARAL else MIME_TYPE_FEDARAL['text']
			if type(value) == list:
				if key in  LIST_KEYS_FEDARAL.keys(): #news_tags media
					for lists in LIST_KEYS_FEDARAL[key]:
						for list_names in json_file_copy[key]:
							if lists in list_names.keys():
								if translate:
									list_names[lists] = get_translation(mt_engine_id=1,source_string=list_names[lists],target_lang_code=tar_code,
																		source_lang_code=src_code,format_=format_,user_id=user.id)			
			else:
				if translate:
					json_file_copy[key] = get_translation(mt_engine_id=1,source_string=json_file_copy[key],target_lang_code=tar_code,
														source_lang_code=src_code,format_=format_,user_id=user.id)
	return  json_file_copy


def split_file_by_size(input_file, output_directory, lang_code, max_size):
    print("LangCode------------->",lang_code.split('-')[0])
    from .api_views import cust_split
    with open(input_file, 'r', encoding='utf-8') as file:
        content = file.read()
    lang_code = lang_code.split('-')[0]
    if lang_code in ['zh','ja']:
        sentences = cust_split(content)
    elif lang_code in ['hi', 'bn', 'or', 'ne', 'pa']:
        sentences = sentence_split(content, lang_code, delim_pat='auto')
    else:
        sentences = nltk.sent_tokenize(content)

    part_number = 1
    current_size = 0
    current_content = []

    for sentence in sentences:
        sentence_size = len(sentence.encode('utf-8'))

        if current_size + sentence_size > max_size and current_content:
            output_file = f"{output_directory}/output_{part_number}.txt"
            with open(output_file, 'w', encoding='utf-8') as output:
                output.write("\n".join(current_content))
            print(f"File {output_file} created with {current_size} bytes")
            part_number += 1
            current_content = []
            current_size = 0

        current_content.append(sentence)
        current_size += sentence_size

    if current_content:
        output_file = f"{output_directory}/output_{part_number}.txt"
        with open(output_file, 'w', encoding='utf-8') as output:
            output.write("\n".join(current_content))
        print(f"File {output_file} created with {current_size} bytes")








def split_dict(single_data):
    trans_keys = ["keywords","description","image_caption","heading","newsId","authorName","location","story"]
    trans_key_get_list = {"media":"caption"}#, "news_tags":"name"}
    trans_keys_dict = {}
    json_data = single_data.get('news')[0] if single_data.get('news') else None
    if not json_data:
        json_data = single_data
    for key,value in  json_data.items():
        if key in trans_keys:
            trans_keys_dict[key] = value
        if key in list(trans_key_get_list.keys()):
            trans_list=[]
            for i in value:
                if trans_key_get_list[key] in i.keys():
                    trans_list.append({trans_key_get_list[key] :i[trans_key_get_list[key]]})
            trans_keys_dict[key] = trans_list
    return trans_keys_dict



def merge_dict(translated_json,raw_json):
	#print("Tar---------->",translated_json)
	#print("Raw---------->", raw_json)
	raw_json_trans = copy.deepcopy(raw_json)
	translated_json_copy = copy.deepcopy(translated_json)
	for key,values in list(LIST_KEYS_FEDARAL.items()):
		if key in list(raw_json_trans.keys()):
			for count,j in enumerate(raw_json_trans[key]):
				if values[count] in j.keys():
					j.update(translated_json_copy[key][count])
		if key in translated_json_copy:
			translated_json_copy.pop(key)
	raw_json_trans.update(translated_json_copy)
	return raw_json_trans

	 


import json
import pypandoc
from docx import Document
#import markdown
#pypandoc.pandoc_download.download_pandoc()
 
def html_to_docx(html_content, docx_filename):
	print("Html------------>",html_content)
	if html_content == None:
		html_content = "<p>"

	html_content = html_content.replace('\n', '<br>')
    # Convert HTML to DOCX using pypandoc
	pypandoc.convert_text(html_content, 'docx', format='html',outputfile=docx_filename)
   


def add_additional_content_to_docx(docx_filename, additional_content):
    # Open the existing DOCX file using python-docx
    doc = Document(docx_filename)
    for key, value in additional_content.items():
        print(key)
        if key!='story':
            doc.add_paragraph(f'{key.capitalize()}:')# {value}')
            doc.add_paragraph(f'{value}')
    doc.save(docx_filename)

from django.db.models import Q
def progress_filter(queryset,value,users):
	print("BE------------------------->",queryset.count())
	if value == 'inprogress':
		if users:
			queryset_1 = queryset.filter(Q(project_jobs_set__job_tasks_set__task_info__status__in = [1,2,4])|Q(project_jobs_set__job_tasks_set__task_info__client_response = 2),project_jobs_set__job_tasks_set__task_info__assign_to__in = users)
			queryset = queryset_1.filter(Q(project_jobs_set__job_tasks_set__task_info__task_assign_info__isnull=False))
		else:
			queryset = queryset.filter(Q(project_jobs_set__job_tasks_set__task_info__status__in = [1,2,4])|\
			Q(project_jobs_set__job_tasks_set__task_info__client_response = 2))
	elif value == 'submitted':
		if users:
			qs_1 = queryset.filter(Q(project_jobs_set__job_tasks_set__task_info__status = 3),project_jobs_set__job_tasks_set__task_info__assign_to__in = users)
			qs = qs_1.filter(Q(project_jobs_set__job_tasks_set__task_info__task_assign_info__isnull=False))
		else:
			qs = queryset.filter(Q(project_jobs_set__job_tasks_set__task_info__status = 3))
		filtered_qs = [i.id for i in qs if i.get_tasks.filter(task_info__status=3).count() == i.get_tasks.filter(task_info__client_response=1).count()]
		queryset = qs.exclude(id__in=filtered_qs)
	elif value == 'approved':
		if users:
			queryset_1 = queryset.filter(Q(project_jobs_set__job_tasks_set__task_info__client_response = 1),project_jobs_set__job_tasks_set__task_info__assign_to__in = users)
			queryset = queryset_1.filter(Q(project_jobs_set__job_tasks_set__task_info__task_assign_info__isnull=False))
		else:
			queryset = queryset.filter(Q(project_jobs_set__job_tasks_set__task_info__client_response = 1))
	print("Af---------------------->",queryset.count())
	return queryset
# # Example usage:
# sample_json_data = {"name": "John Doe", "age": 30, "body": "<p>New York</p>"}

# # Convert HTML to DOCX
# html_to_docx(sample_json_data['body'], 'output.docx')

# # Add additional content to the DOCX file
# add_additional_content_to_docx('output.docx', sample_json_data)



