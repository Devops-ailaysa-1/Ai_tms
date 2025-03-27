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

# def print_key_value(keys, values):
# 	for i, j in zip(keys, values):
# 		print(f'{i}--->{j}')


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
from django.conf import settings
TRANSLATABLE_KEYS_FEDERAL = settings.TRANSLATABLE_KEYS_FEDERAL.split(" ")
HTML_MIME_FEDARAL = settings.HTML_MIME_FEDARAL.split(" ")


MIME_TYPE_FEDARAL = {'html': 'html', 'text': 'text'}
LIST_KEYS_FEDARAL={'media':['caption']}# , 'news_tags':['name']}


####Need to add credit check and function to get MT for each key####################
def federal_json_translate(json_file,tar_code,src_code,user,translate=True):
	from ai_workspace_okapi.utils import get_translation
	
	try:json_data = json_file['news'][0]
	except: json_data = json_file
	json_file_copy = copy.deepcopy(json_data)
	for key,value in json_file_copy.items():
		if key in TRANSLATABLE_KEYS_FEDERAL:
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


# For voice projects and tasks
def split_file_by_size(input_file, output_directory, lang_code, max_size):
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
            part_number += 1
            current_content = []
            current_size = 0

        current_content.append(sentence)
        current_size += sentence_size

    if current_content:
        output_file = f"{output_directory}/output_{part_number}.txt"
        with open(output_file, 'w', encoding='utf-8') as output:
            output.write("\n".join(current_content))







################################## For Federal Flow #####################################
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

########################################################################################## 


import json
import pypandoc
from docx import Document

 
def html_to_docx(html_content, docx_filename):
	if html_content == None:
		html_content = "<p>"

	html_content = html_content.replace('\n', '<br>')
    # Convert HTML to DOCX using pypandoc
	pypandoc.convert_text(html_content, 'docx', format='html',outputfile=docx_filename)
   


def add_additional_content_to_docx(docx_filename, additional_content):
    doc = Document(docx_filename)
    for key, value in additional_content.items():
        if key!='story':
            doc.add_paragraph(f'{key.capitalize()}:')
            doc.add_paragraph(f'{value}')
    doc.save(docx_filename)


############################# Project Filter #################################################

from django.db.models import Q, Prefetch, Count, F
import time
def progress_filter(queryset,value,users):
	from ai_workspace.models import TaskAssign

	queryset = queryset.filter(project_type_id=8) #News project

	queryset = queryset.prefetch_related(
        Prefetch('project_jobs_set__job_tasks_set__task_info', queryset=TaskAssign.objects.all())
    )
	
	if value == 'inprogress':
		if users:
			pr_ids = queryset.filter(Q(project_jobs_set__job_tasks_set__task_info__status__in = [1,2,4])\
			|Q(project_jobs_set__job_tasks_set__task_info__client_response = 2),\
			project_jobs_set__job_tasks_set__task_info__task_assign_info__isnull=False,\
			project_jobs_set__job_tasks_set__task_info__assign_to__in = users).distinct().values_list('id',flat=True)
		else:
			pr_ids = queryset.filter(Q(project_jobs_set__job_tasks_set__task_info__status__in = [1,2,4])|\
			Q(project_jobs_set__job_tasks_set__task_info__client_response = 2)).distinct().values_list('id', flat=True)
	elif value == 'submitted':
		if users:
			qs = queryset.filter(Q(project_jobs_set__job_tasks_set__task_info__status = 3),\
			project_jobs_set__job_tasks_set__task_info__task_assign_info__isnull=False,\
			project_jobs_set__job_tasks_set__task_info__assign_to__in = users).distinct()
			# Need to change this with annotate
			filtered_qs = [i.id for i in qs if i.get_tasks.filter(task_info__status=3,task_info__assign_to__in=users).count() == i.get_tasks.filter(task_info__client_response=1,task_info__assign_to__in=users).count()]
		else:
			qs = queryset.filter(Q(project_jobs_set__job_tasks_set__task_info__status = 3)).distinct()
			# Need to change this with annotate
			filtered_qs = [i.id for i in qs if i.get_tasks.filter(task_info__status=3).count() == i.get_tasks.filter(task_info__client_response=1).count()]
		pr_ids = qs.exclude(id__in=filtered_qs).values_list('id',flat=True)
		
	elif value == 'approved':
		if users:
			pr_ids = queryset.filter(Q(project_jobs_set__job_tasks_set__task_info__client_response = 1),\
			project_jobs_set__job_tasks_set__task_info__task_assign_info__isnull=False,\
			project_jobs_set__job_tasks_set__task_info__assign_to__in = users).distinct().values_list('id',flat=True)
		else:
			pr_ids = queryset.filter(Q(project_jobs_set__job_tasks_set__task_info__client_response = 1)).distinct().values_list('id',flat=True)

	queryset = queryset.filter(id__in = pr_ids)

	return queryset

def number_of_words_insert(segment):
	words_inserts = re.findall(r'<ins class="changed-word">(.+?)</ins>', segment)
	words_insert_with_classes =  re.findall(r'<ins>(.+?)</ins>', segment)  
	len_words_inserts = 0
	for words_insert in words_inserts:
		len_words_inserts= len_words_inserts+len(words_insert.split(" "))
	for words_insert_with_class in words_insert_with_classes:
		len_words_inserts=len_words_inserts+ len(words_insert_with_class.split(" "))
	return len_words_inserts

def number_of_words_delete(segment):
    words_deletes = re.findall(r'<del>(.+?)</del>', segment)  
    words_delete_class =  re.findall(r'<del class="removed-word">(.+?)</del>', segment) 
    len_words_deletes = 0
    for i in words_deletes:
        len_words_deletes=len_words_deletes+ len(i.split(" "))
    for j in words_delete_class:
        len_words_deletes=len_words_deletes+ len(j.split(" "))		
    return len_words_deletes

# import time
# from functools import wraps

# def time_decorator(func):
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         start_time = time.time()
#         result = func(*args, **kwargs)
#         end_time = time.time()
#         execution_time = end_time - start_time
#         print(f"Function '{func.__name__}' executed in {execution_time:.6f} seconds")
#         return result
#     return wrapper



import json
from abc import ABC, abstractmethod
import os
from anthropic import Anthropic

# Handles API interaction
class AnthropicAPI:
    def __init__(self, api_key, model_name):
        self.client = Anthropic(api_key=api_key)
        self.model_name = model_name
        self.tag_prompt = """
            Tag Translation Guidelines: 
            - Preserve Tags: Keep all tags (<n>, </n>) exactly as in the original sentence.  
            - Correct Placement: Place tags in the translated sentence where they correspond naturally based on the target language's structure.  
            - No Changes:** Do not add, remove, or modify tags.  
            - Match Tag Count: Ensure the same number of tags in both the source and translated sentence.  
            - Output Format: Provide only the translated sentence with correctly placed tags, without any extra text.  

            Example:  
            Input: "Original sentence with <1>tags</1> here."  
            Output (Translated): "Translated sentence with <1>tags</1> in the correct place."   
        """

    def send_request(self, system_prompt, messages, max_tokens=2000):
        response = self.client.messages.create(
            model=self.model_name,
            system=[
                {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"}
                },                        
                {"type": "text",
                "text": self.tag_prompt,
                },
            ],
            messages=messages,
            max_tokens=max_tokens
        )
        return response.content[0].text.strip() if response.content else None


class TranslationStage(ABC):
    def __init__(self, anthropic_api, target_language, source_language):
        self.api = anthropic_api
        self.target_language = target_language
        self.source_language = source_language

    @abstractmethod
    def process(self, segment, **kwargs):
        pass


# Style analysis (Stage 1)
class StyleAnalysis(TranslationStage):
    def process(self, segments):
        system_prompt = """Analyze the following text and provide a comprehensive description of its:
        1. Writing tone and style
        2. Emotional conduct
        3. Technical level
        4. Target audience
        5. Key contextual elements
        
        Format your response as a translation guidance prompt that can be used to maintain these elements. 
        Make sure you generate only the prompt as an output. No feedback or any sort of additional information should be generated."""

        combined_text = " ".join([seg['source'] for seg in segments])
        messages = [{"role": "user", "content": combined_text}]
        return self.api.send_request(system_prompt, messages)


# Initial translation (Stage 2)
class InitialTranslation(TranslationStage):
    def process(self, segment, style_guideline):
        system_prompt = f"""Translate the following segments of text to {self.target_language} while adhering to the provided style guidelines. Ensure the translation closely resembles the source sentence in meaning, tone, and structure.    
        Style Guidelines: 
        {style_guideline}
        The translation should read as if it were originally written in {self.target_language}, maintaining authentic {self.target_language} syntax and style.
        Choose words and expressions that are semantically and pragmatically appropriate for the target language, considering the full context.
        The translation should preserve the original meaning while using natural, idiomatic {self.target_language} expressions. 
        Final output should only be the translated text with the relevent taggig followed as in the source. no feedback or any sort of additional information should be provided.
        """

        messages = [{"role": "user", "content": segment["tagged_source"]}]
        return self.api.send_request(system_prompt, messages)


# Refinement 1 (Stage 3)
class RefinementStage1(TranslationStage):
    def process(self, segment):
        system_prompt = f"""For the provided tagged source sentences and translated text sentences, ensure the translation is smooth and correct. 
        Make sure the tone, style of the source sentence is followed in the target sentence. Ensure grammar and punctuations are correct. Ensure the translated {self.target_language} text is perfect resembling the source text
        Make necessary translation corrections if needed.
        strictly, Result must be only the final target translation.
        no feedbacks or any sort of additional information should be provided."""

        input_text = f"Source: {segment['tagged_source']}\nInitial Translation: {segment['translated_text']}"
        messages = [{"role": "user", "content": input_text}]
        return self.api.send_request(system_prompt, messages)

# Final refinement (Stage 4)
class RefinementStage2(TranslationStage):
    def process(self, segment):
        system_prompt = f"""Focus the {self.target_language} content and rewrite it as if it is originally conceived and written in {self.target_language} itself.
        The text should be in the modern standard {self.target_language} language. The changes must only be in syntax. The core words, terminologies, named entities, and keywords and their meaning, sense and emphasis shouldn't be changed.
        If no changes are needed, return the same {self.target_language} text without any acknowledgment. Otherwise, provide the modified {self.target_language} sentence along with the tags as such.
        Note: No feedback or any sort of additional information should be provided."""

        input_text = f"Refined Translation: {segment['refined_translation']}"
        messages = [{"role": "user", "content": input_text}]
        return self.api.send_request(system_prompt, messages)


class AdaptiveSegmentTranslator:
    def __init__(self, source_language, target_language, api_key, model_name):
        self.api = AnthropicAPI(api_key, model_name)
        self.source_language = source_language
        self.target_language = target_language

        # Translation stages (New stages can be added)
        self.style_analysis = StyleAnalysis(self.api, target_language, source_language)
        self.initial_translation = InitialTranslation(self.api, target_language, source_language)
        self.refinement_stage_1 = RefinementStage1(self.api, target_language, source_language)
        self.refinement_stage_2 = RefinementStage2(self.api, target_language, source_language)

    def process_batch(self, segments):
        style_guideline = self.style_analysis.process(segments)
        translated_segments = []

        for segment in segments:
            translated_text = self.initial_translation.process(segment, style_guideline)
            translated_segments.append({
                "segment_id": segment["segment_id"],
                "source_text": segment["source"],
                "tagged_source": segment["tagged_source"],
                "translated_text": translated_text
            })

        # print("Initial Translation:")
        # print(json.dumps(translated_segments, indent=2, ensure_ascii=False))

        refined_segments = []
        for segment in translated_segments:
            refined_text = self.refinement_stage_1.process(segment)
            refined_segments.append({
                **segment,
                "refined_translation": refined_text
            })

        # print("\nRefined Translation:")
        # print(json.dumps(refined_segments, indent=2, ensure_ascii=False))

        final_segments = []
        for segment in refined_segments:
            final_text = self.refinement_stage_2.process(segment)
            final_segments.append({
                **segment,
                "final_translation": final_text
            })
        return final_segments
        # print("\nFinal Translation:")
        # print(json.dumps(final_segments, indent=2, ensure_ascii=False))
        