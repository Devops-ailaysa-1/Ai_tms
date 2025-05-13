import os
import random
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import StringIO, BytesIO
import sys
import string
import re
from indicnlp.tokenize.sentence_tokenize import sentence_split
import nltk
from ai_staff.models import AdaptiveSystemPrompt

async def detect_lang(text):
    from googletrans import Translator
    detector = Translator()
    return await detector.detect(text)

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
from anthropic import Anthropic, AnthropicVertex
import re
import logging
from langdetect import detect
import langcodes
from json_repair import repair_json
logger = logging.getLogger('django')

from django.core.cache import cache



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

    def send_request(self, messages, max_tokens=40000):
        # response = self.client.messages.create(
        #     model=self.model_name,
        #     # system=[
        #     #     {
        #     #     "type": "text",
        #     #     "text": system_prompt,
        #     #     "cache_control": {"type": "ephemeral"}
        #     #     },                        
        #     #     # {"type": "text",
        #     #     # "text": self.tag_prompt,
        #     #     # },
        #     # ],
        #     messages=messages,
        #     max_tokens=max_tokens,
        #     # temperature=0.3,
        #     # extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"}
        # )
        # return response.content[0].text.strip() if response.content else None
        streamed_output = ""
        with self.client.messages.stream(
            max_tokens=60_000,
            # system=[{"type": "text",
            #         "text": system_prompt},                        
        
            #         ],
            messages=messages,
            model=self.model_name,
        ) as stream:
            for text in stream.text_stream:
                streamed_output += text  
            
        token_usage = stream.get_final_message().usage
        input_token = token_usage.input_tokens
        output_token = token_usage.output_tokens
       
        return (input_token, output_token, streamed_output.strip())

class TranslationStage(ABC):
    def __init__(self, anthropic_api, target_language, source_language, group_text_units=False, task_progress=None):
        self.api = anthropic_api
        self.target_language = target_language
        self.source_language = source_language
        self.group_text_units = group_text_units
        self.task_progress = task_progress
        self.set_progress()

    @abstractmethod
    def process(self, segment, **kwargs):
        pass
    
    def continue_conversation_assistant(self,assistant_message):
        return {
        "role": "assistant",
        "content": assistant_message
    }

    def continue_conversation_user(self,user_message):
        return {
            "role": "user",
            "content": user_message
        }

    def group_strings_max_words(self, segments, max_words=200):
        grouped = []
        temp = []
        word_count = 0

        for segment in segments:
            segment_word_count = len(segment.split())

            if word_count + segment_word_count > max_words:
                grouped.append("\n\n".join(temp))
                temp = [segment]
                word_count = segment_word_count
            else:
                temp.append(segment)
                word_count += segment_word_count

        if temp:
            grouped.append("\n\n".join(temp))

        return grouped

    def get_progress(self):
        cache_key = f"adaptive_progress_{self.task_progress.id}"
        return cache.get(cache_key, None)

    
    def set_progress(self,stage=None,stage_percent=None):
        stage_weights = {"stage_01": 0.1, "stage_02": 0.4, "stage_03": 0.25, "stage_04": 0.25}
        data = self.get_progress()
        if data!=None:
            # data = self.get_progress()
            # get_stage = data.get(stage)
            if stage_percent != None and stage != None:
                data[stage] = stage_percent
                data["total"] = int(sum(data[stage_key] * stage_weights[stage_key] for stage_key in stage_weights.keys())) 
                progress = data
            else:
                 return None              
        else:
            progress={"stage_01": 0, "stage_02": 0, "stage_03": 0, "stage_04": 0,"total": 0}
      
        cache_key = f"adaptive_progress_{self.task_progress.id}"
        print("progress",progress)
        return cache.set(cache_key, progress, timeout=3600)  # expires in 1 hour
    
    def update_progress_db(self):
        data = self.get_progress()
        if data!=None and self.task_progress.progress_percent!=data['total']:
             self.task_progress.progress_percent = data['total']
             self.task_progress.save()


    def mock_api(self,segments,stage=None):
        if isinstance(segments,list) and len(segments) > 0:
            total = len(segments) 
            progress_counter = 1 
            for i in segments:
                time.sleep(1)
                percent = int((progress_counter/total)*100)
                self.set_progress( stage=stage, stage_percent=percent)
                progress_counter += 1
        else:
            time.sleep(10)
            self.set_progress(stage=stage, stage_percent=100)
        return "Mocked response from Anthropic API"
    

# Style analysis (Stage 1)
class StyleAnalysis(TranslationStage):
    def __init__(self, anthropic_api, target_language, source_language, group_text_units=False, task_progress=None):
        super().__init__(anthropic_api, target_language, source_language, group_text_units, task_progress)
        # self.stage_weight = 10
        self.stage_percent = 0
        self.stage = "stage_01"

    def process(self, all_paragraph, document=None, batch_no=None, batch_instance=None):
        system_prompt = AdaptiveSystemPrompt.objects.get(stages=self.stage).prompt
        combined_text = ''
        combined_text_list = []
        for single_paragraph in all_paragraph:
            para = single_paragraph
            if len("".join(combined_text_list)) < 1400:
                combined_text_list.append(para)
            else:break
        combined_text = "".join(combined_text_list)

        # system_prompt = AdaptiveSystemPrompt.objects.get(stages=self.stage).prompt
        prompt = f"""Analyze the following text and provide a comprehensive description of its:
        1. Writing tone and style
        2. Emotional conduct
        3. Technical level
        4. Target audience
        5. Key contextual elements
        
        Format your response as a translation guidance prompt that can be used to maintain these elements.
        Make sure you generate only the prompt as an output.no feedback or any sort of additional information should be generated.
        
        Text to analyze:
        {combined_text}"""




        if (True if os.getenv("LLM_TRANSLATE_ENABLE",False) == 'True' else False):
            if combined_text:
                messages = [self.continue_conversation_user(prompt)]
                input_token, output_token,result_content_prompt = self.api.send_request(messages)
                self.style_text = result_content_prompt
                self.set_progress(stage=self.stage, stage_percent=100)
                if os.getenv('ANALYTICS') == 'True':
                    write_stage_response_in_excel(document.project, document.task_obj.id, batch_no,system_prompt, user_message=json.dumps(messages, ensure_ascii=False), translated_result=result_content_prompt, stage=self.stage,input_token=input_token, output_token=output_token)
                    logger.info(f"Stage 1 data written to excel")
                return result_content_prompt
            else:
                self.style_text = None
                return None
        else:
            # self.set_progress(stage=self.stage, stage_percent=100)
            self.mock_api(combined_text,self.stage)
            return None

# Initial translation (Stage 2)
class InitialTranslation(TranslationStage):
    def __init__(self, anthropic_api, target_language, source_language, group_text_units=False, task_progress=None):
        super().__init__(anthropic_api, target_language, source_language, group_text_units,task_progress)
        # self.stage_weight = 40
        self.stage_percent = 0
        self.stage = "stage_02"

    def process(self, segments, style_prompt, gloss_terms, d_batches, document=None, batch_no=None, batch_instance=None):
        system_prompt = AdaptiveSystemPrompt.objects.get(stages=self.stage).prompt
        system_prompt = system_prompt.format(style_prompt=style_prompt, target_language=self.target_language)


        translation_prompt = """Translate the following text while adhering to the provided style guidelines. Ensure the translation closely resembles the source sentence in meaning, tone, and structure.    
    
        
        Style Guidelines:
        {0}
        
        Ensure both accuracy and natural fluency while translating.
        The translation should read as if it were originally written in {1}, maintaining authentic {2} syntax and style.
        Choose words and expressions that are semantically and pragmatically appropriate for the target language, considering the full context.
        The translation should preserve the original meaning while using natural, idiomatic {3} expressions. 
        final output should only be the translated text. no feedbacks or any sort of additional information should be provided.
     

        Note: Only translate on the given target language 
        
        Text to translate:
        {4}"""



        if gloss_terms:
            glossary_lines = "\n".join([f'- "{src}" → "{tgt}"' for src, tgt in gloss_terms.items()])
            system_prompt += f"\nNote: While translating, make sure to translate the specific words as such if mentioned in the glossary pairs.Ensure that the replacements maintain the original grammatical categories like tense, aspect, modality,voice and morphological features.\nGlossary:\n{glossary_lines}."

        if self.group_text_units:
            segments = self.group_strings_max_words(segments, max_words=200)

        message_list = []
        response_result = []
        total = len(segments)
        progress_counter = 1 
        if (True if os.getenv("LLM_TRANSLATE_ENABLE",False) == 'True' else False):
            for para in segments:
                para_message = translation_prompt.format(style_prompt,self.target_language,self.target_language,self.target_language,para)
                message_list.append(self.continue_conversation_user(user_message=para_message))
                input_token, output_token,response_text = self.api.send_request(message_list)
                response_result.append(response_text)
                if os.getenv('ANALYTICS') == 'True':
                    write_stage_response_in_excel(document.project, document.task_obj.id, batch_no,system_prompt, user_message=json.dumps(message_list, ensure_ascii=False), translated_result=response_text, stage=self.stage, input_token=input_token, output_token=output_token)
                    logger.info(f"Stage 2 data written to excel")
                #message_list.append(self.continue_conversation_assistant(assistant_message=response_text))
                #if len(message_list) > 4:
                 #   message_list = []
                message_list = []
                percent = int((progress_counter/total)*100)
                self.set_progress(stage=self.stage, stage_percent=percent)
                progress_counter += 1
                
        else:
            self.mock_api(segments,self.stage)
        return (segments, response_result)


# Refinement 1 (Stage 3)
class RefinementStage1(TranslationStage):
    def __init__(self, anthropic_api, target_language, source_language, group_text_units=False, task_progress=None):
        super().__init__(anthropic_api, target_language, source_language, group_text_units,task_progress)
        # self.stage_weight = 0.25
        self.stage_percent = 0
        self.stage = "stage_03"

    def process(self, segments, source_text, gloss_terms, document=None, batch_no=None, batch_instance=None):
        system_prompt = AdaptiveSystemPrompt.objects.get(stages=self.stage).prompt
        system_prompt = system_prompt.format(target_language=self.target_language)

        refinement_prompt = """Review and refine the following translation from English to {0}.
        
        Source:
        {1}
        
        Translation:
        {2}
        
        For the provided source and target sentence ensure 
            the translation is smooth and correct.Make sure the tone, style of the
            source sentence is followed in the target sentence. 
            ensure grammar and punctuation are correct. Ensure the translated {3} text is perfect resembling the source text
            Make necessary translation corrections if needed.
            strictly, Result must be only the final target translation.
            no feebacks or any sort of additional information should be provided."""

        if gloss_terms:
            glossary_lines = "\n".join([f'- "{src}" → "{tgt}"' for src, tgt in gloss_terms.items()])
            system_prompt += f"\nNote: While translating, make sure to translate the specific words as such if mentioned in the glossary pairs.Ensure that the replacements maintain the original grammatical categories like tense, aspect, modality,voice and morphological features.\nGlossary:\n{glossary_lines}."


        message_list = []
        response_result = []
        total = len(segments)
        progress_counter = 1 
        if (True if os.getenv("LLM_TRANSLATE_ENABLE",False) == 'True' else False):
            for trans_text, original_text in zip(segments, source_text):
                #user_text = """Source text:\n{source_text}\n\nTranslation text:\n{translated_text}""".format(source_text=original_text,
                #                                                                                                    translated_text=trans_text)
                para_message = refinement_prompt.format(self.target_language,original_text,trans_text,self.target_language)
                message_list.append(self.continue_conversation_user(user_message=para_message))
                input_token, output_token,response_text = self.api.send_request(message_list)
                response_result.append(response_text)
                if os.getenv('ANALYTICS') == 'True':
                    write_stage_response_in_excel(document.project, document.task_obj.id, batch_no,system_prompt, user_message=json.dumps(message_list, ensure_ascii=False), translated_result=response_text, stage=self.stage, input_token=input_token, output_token=output_token)
                    logger.info(f"Stage 3 data written to excel")
                # message_list.append(self.continue_conversation_assistant(assistant_message=response_text))
                #if len(message_list) > 4:
                #    message_list = []
                message_list = []
                percent = int((progress_counter/total)*100)
                self.set_progress(stage=self.stage, stage_percent=percent)
                progress_counter += 1
        else:
            self.mock_api(segments,self.stage)

        return response_result


# Final refinement (Stage 4)
class RefinementStage2(TranslationStage):
    def __init__(self, anthropic_api, target_language, source_language, group_text_units=False, task_progress=None):
        super().__init__(anthropic_api, target_language, source_language, group_text_units,task_progress)
        # self.stage_weight = 0.25
        self.stage_percent = 0
        self.stage = "stage_04"

    def process(self, segments, gloss_terms, document=None, batch_no=None, batch_instance=None):
        system_prompt = AdaptiveSystemPrompt.objects.get(stages=self.stage).prompt
        system_prompt = system_prompt.format(target_language=self.target_language)

        final_refinement_prompt = """Text:{0}

        Focus the {1} content and rewrite it as if it is originally conceived and written in {2} itself. The text should be in the modern standard {3}. The changes must only be in syntax. The core words, terminologies, named entities, and keywords and their meaning, sense and emphasis shouldn't be changed.
        If no changes are needed, return the same {4} without any acknowledgment. Otherwise, provide the modified {5} sentence.
        Note: No feedback or any sort of additional information should be provided."""

        if gloss_terms:
            glossary_lines = "\n".join([f'- "{src}" → "{tgt}"' for src, tgt in gloss_terms.items()])
            system_prompt += f"\nNote: While translating, make sure to translate the specific words as such if mentioned in the glossary pairs.Ensure that the replacements maintain the original grammatical categories like tense, aspect, modality,voice and morphological features.\nGlossary:\n{glossary_lines}."
            

        message_list = []
        response_result = []
        total = len(segments)
        progress_counter = 1 

        if (True if os.getenv("LLM_TRANSLATE_ENABLE",False) == 'True' else False):
            for para in segments:
                para_message = final_refinement_prompt.format(para,self.target_language,self.target_language,self.target_language,self.target_language,
                                                              self.target_language)
                # instruct_text = """{} sentence: {}""".format(self.target_language,para)
                message_list.append(self.continue_conversation_user(user_message=para_message))
                input_token, output_token, response_text = self.api.send_request(message_list)
                response_result.append(response_text)
                if os.getenv('ANALYTICS') == 'True':
                    write_stage_response_in_excel(document.project, document.task_obj.id, batch_no,system_prompt, user_message=json.dumps(message_list, ensure_ascii=False), translated_result=response_text, stage=self.stage, input_token=input_token, output_token=output_token)
                    logger.info(f"Stage 4 data written to excel")
                #message_list.append(self.continue_conversation_assistant(assistant_message=response_text))
                # if len(message_list) > 4:
                message_list = []
                percent = int((progress_counter/total)*100)
                self.set_progress(stage=self.stage, stage_percent=percent)
                progress_counter += 1

        else:
            self.mock_api(segments,self.stage)
        return response_result


class AdaptiveSegmentTranslator:
    def __init__(self, source_language, target_language, api_key, model_name, gloss_terms, task_progress, group_text_units=False, document=None):
        self.api = AnthropicAPI(api_key, model_name)
        self.source_language = source_language
        self.target_language = target_language
        self.gloss_terms = gloss_terms
        self.task_progress = task_progress
        self.document = document

        # Translation stages (New stages can be added)
        self.style_analysis = StyleAnalysis(self.api, target_language, source_language, group_text_units, self.task_progress)
        self.initial_translation = InitialTranslation(self.api, target_language, source_language, group_text_units, self.task_progress)
        self.refinement_stage_1 = RefinementStage1(self.api, target_language, source_language, group_text_units, self.task_progress)
        self.refinement_stage_2 = RefinementStage2(self.api, target_language, source_language, group_text_units, self.task_progress)

    def process_batch(self, segments, d_batches, batch_no):
        style_guideline = self.style_analysis.process(segments, self.document, batch_no, self.task_progress)
        # self.task_progress.progress_percent += 10
        # self.task_progress.save()
        # stage_result_ins.stage_01 = style_guideline
        
        segments,translated_segments = self.initial_translation.process(segments, style_guideline, self.gloss_terms, d_batches, self.document, batch_no, self.task_progress)
        # progress_data = self.get_progress()
        # self.task_progress.progress_percent += 40
        # self.task_progress.save()
        # stage_result_ins.stage_02 = translated_segments
        self.initial_translation.update_progress_db()
        refined_segments = self.refinement_stage_1.process(translated_segments, segments, self.gloss_terms, self.document,batch_no, self.task_progress)
        # self.task_progress.progress_percent += 25
        # self.task_progress.save()
        # stage_result_ins.stage_03 = refined_segments
        final_segments = self.refinement_stage_2.process(refined_segments, self.gloss_terms, self.document,batch_no, self.task_progress)
        # self.task_progress.progress_percent += 25
        # self.task_progress.save()
        # stage_result_ins.stage_04 = final_segments
        # stage_result_ins.save()
        self.refinement_stage_2.update_progress_db()
        return final_segments
    

    def extract_tags(self, text):
        """Extract all XML-like tags (e.g. <1>, </1>, <n>, </n>)."""
        return re.findall(r"</?[a-zA-Z0-9]+>", text)

    def handle_batch_translation_tags(self, segments, translated_segments):
        """
        Validate and clean up XML-like tags in translated segments based on original source segments.
        Ensures that translated output has all required tags and removes unexpected ones.
        """
        try:
            if isinstance(translated_segments, str):
                try:
                    json_ts = json.loads(translated_segments)
                except json.JSONDecodeError as e:
                    try:
                        json_ts = repair_json(translated_segments,return_objects=True)
                        logger.info(f"Failed to parse JSON from translation output, repaired with json_repair! {e}")
                    except json.JSONDecodeError as e:
                        logger.info(f"Failed to parse JSON from translation output {e}!")
                        return translated_segments
            else:
                json_ts = translated_segments

            text_lang = self.get_first_translated_text_and_language(json_ts)
            if text_lang != self.target_language:
                logger.info(
                    f"Language mismatch detected. First segment language: {text_lang}, target language: {self.target_language}"
                )

            segment_map = {seg["segment_id"]: seg for seg in segments}

            for translated in json_ts:
                segment_id = translated.get("segment_id")
                translated_text = translated.get("translated_text", "")

                source_segment = segment_map.get(segment_id)
                if not source_segment:
                    logger.error(f"[Segment {segment_id}] Source segment not found.")
                    continue

                if not translated_text:
                    logger.error(f"[Segment {segment_id}] Translated text is empty.")
                    continue

                source_tags = set(self.extract_tags(source_segment.get("tagged_source", "")))
                translated_tags = set(self.extract_tags(translated_text))

                missing_tags = source_tags - translated_tags
                extra_tags = translated_tags - source_tags

                if missing_tags:
                    logger.error(f"[Segment {segment_id}] Missing tags: {missing_tags}")

                if extra_tags:
                    logger.error(f"[Segment {segment_id}] Unwanted tags: {extra_tags}")

                # Clean translated text from unexpected tags
                cleaned_parts = []
                for part in re.split(r"(</?[a-zA-Z0-9]+>)", translated_text):
                    if re.fullmatch(r"</?[a-zA-Z0-9]+>", part):
                        if part in source_tags:
                            cleaned_parts.append(part)
                        else:
                            logger.info(f"[Segment {segment_id}] Removed unexpected tag: {part}")
                    else:
                        cleaned_parts.append(part)

                translated["translated_text"] = "".join(cleaned_parts).strip()

            return json_ts  

        except Exception as e:
            logger.exception(f"Unhandled error during tag validation in batch translation - {e}")
            return translated_segments

    
    # translated_paragraphs = response_text.strip().split("\n\n")
    # ids = list(text_unit_dict.keys())

    # if len(ids) != len(translated_paragraphs):
    #     raise ValueError("Mismatch between original and translated paragraph counts")

    # for i, text_unit_id in enumerate(ids):
    #     translated_para = translated_paragraphs[i]
    #     # Save the translation to the related MergedTextUnit
    #     MergedTextUnit.objects.filter(text_unit_id=text_unit_id).update(target_para=translated_para)


    def get_first_translated_text_and_language(self,translated_segments):
        from ai_staff.models import LanguagesLocale
        translated_text = translated_segments[0]["translated_text"]
        language_code = detect(translated_text)    
        try:
            language_name = LanguagesLocale.objects.get(locale_code=language_code)
            language_name = language_name.language.language
        except LanguagesLocale.DoesNotExist:
            language_name = ''
        
        return language_name


# from google import genai

# def translate_with_gemini_fallback(segments_data, source_lang, target_lang):
#     try:
#         prompt = f"""
#             You are a professional translator.

#             Input: A list of segment sentences in {source_lang}.
#             Output: The same list rewritten in Modern Standard {target_lang}, preserving meaning, tone, and technical terms.

#             **Format output strictly as JSON.**
#             Each translated item must be formatted like:
#             {{
#             "segment_id": int,
#             "translated_text": str
#             }}

#             Do NOT return any markdown or extra comments. Output must be a plain JSON array only.

#             Translate and rewrite this list:

#             {json.dumps(segments_data, ensure_ascii=False)}
#         """

#         client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
#         response = client.models.generate_content(
#             model='gemini-2.0-flash',
#             contents=prompt,
#         )
#         print(response.text, "Formatted by fallback gemini")
#         return response.text
    
#     except Exception as e:
#         print(e)
#         return []


def word_count_find(task):
    import requests
    from .serializers import TaskSerializer
    from ai_workspace_okapi.api_views import DocumentViewByTask  
    from ai_workspace_okapi.utils import get_res_path
    from os.path import exists


    spring_host = os.environ.get("SPRING_HOST")
    data = TaskSerializer(task).data
    DocumentViewByTask.correct_fields(data)
    params_data = {**data, "output_type": None}

    res_paths = get_res_path(params_data["source_language"])

    doc = requests.post(url=f"http://{spring_host}:8080/getDocument/", data={
        "doc_req_params": json.dumps(params_data),
        "doc_req_res_params": json.dumps(res_paths)
    })
    if doc.status_code == 200:
        doc_data = doc.json()
        return doc_data.get('total_word_count')


def merge_source_text_by_text_unit(document_id):
    from ai_workspace_okapi.models import MergedTextUnit
    from ai_workspace_okapi.models import TextUnit, Segment
    text_units = TextUnit.objects.filter(document_id=document_id)

    for text_unit in text_units:
        source_paragraph = ""
        
        segments = text_unit.text_unit_segment_set.all()
        
        if not segments:
            continue  

        for seg in segments:
            if seg.source:
                source_paragraph += seg.source + " "

        MergedTextUnit.objects.create(
            text_unit=text_unit,
            source_para=source_paragraph.strip(),
        )


def re_initiate_failed_batch(task, project):
    from ai_workspace.models import TrackSegmentsBatchStatus
    from ai_workspace_okapi.models import MergedTextUnit
    from ai_workspace.enums import BatchStatus
    from ai_workspace.models import Task
    from ai_auth.tasks import get_glossary_for_task
    from ai_auth.tasks import adaptive_segment_translation

    try:
        task_id = task.id
        get_terms_for_task = get_glossary_for_task(project, task)
        failed_task_batches = TrackSegmentsBatchStatus.objects.filter(document=task.document, status=BatchStatus.FAILED)
        task = Task.objects.select_related('job__source_language', 'job__target_language').get(id=task.id)
        source_lang = task.job.source_language.language
        target_lang = task.job.target_language.language

        for failed_task_batch in failed_task_batches:
            merged_text_units = MergedTextUnit.objects.filter(text_unit__id__range=(failed_task_batch.seg_start_id, failed_task_batch.seg_end_id))
            para = []
            metadata = {}
            for text_unit in merged_text_units:
                para.append(text_unit.source_para)
                metadata[text_unit.text_unit.id] = text_unit.source_para
            
            adaptive_segment_translation.apply_async(
                args=(para, metadata, source_lang, target_lang, get_terms_for_task, task_id, False,),
                kwargs={
                    'failed_batch': True,
                    'celery_task_id': failed_task_batch.celery_task_id,
                },
                queue='high-priority'
            )
            failed_task_batch.status = BatchStatus.ONGOING
            failed_task_batch.progress_percent = 0
            failed_task_batch.save()
    except Exception as e:
        print("Error in re_initiate_failed_batch:", e)



import os
from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter
from zipfile import BadZipFile


def write_stage_response_in_excel(
    project_id,
    task_id,
    batch_no,
    system_prompt,
    user_message,
    translated_result,
    stage,
    base_dir="Translation_Results",
    input_token=None,
    output_token=None
):
    os.makedirs(base_dir, exist_ok=True)

    project_task_folder = os.path.join(base_dir, f"{project_id}_{task_id}")
    os.makedirs(project_task_folder, exist_ok=True)

    file_path = os.path.join(project_task_folder, f"{batch_no}.xlsx")

    try:
        if os.path.exists(file_path):
            wb = load_workbook(file_path)
        else:
            wb = Workbook()
    except BadZipFile:
        print(f"Warning: {file_path} is not a valid Excel file. Recreating.")
        wb = Workbook()

    if "Sheet" in wb.sheetnames and wb["Sheet"].max_row == 1:
        wb.remove(wb["Sheet"])

    sheet_name = batch_no
    if sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
    else:
        ws = wb.create_sheet(title=sheet_name)
        ws.append(["Result", "User_Message", "System_Message", "Stage", "Input_Token", "Output_Token"])

    ws.append([translated_result, user_message, system_prompt, stage, input_token, output_token])

    for column_cells in ws.columns:
        max_length = max(len(str(cell.value)) for cell in column_cells if cell.value)
        col_letter = get_column_letter(column_cells[0].column)
        ws.column_dimensions[col_letter].width = max_length + 2

    wb.save(file_path)
    print(f"Data written to: {file_path}")


