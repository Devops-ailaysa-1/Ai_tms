 

from abc import ABC
from django.core.cache import cache
from ai_workspace.llm_client import LLMClient
from ai_staff.models import AdaptiveSystemPrompt
import logging,time
from ai_workspace.enums import AdaptiveFileTranslateStatus ,BatchStatus
logger = logging.getLogger('django')
#from ai_workspace.api_views import UpdateTaskCreditStatus
from ai_workspace.models import AllStageResult
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.db import transaction
from django.conf import settings
from django.db.models import Q


ADAPTIVE_INDIAN_LANGUAGE =  settings.ADAPTIVE_INDIAN_LANGUAGE

# def credits_consum_adaptive(user,consumable_credits):
#     if consumable_credits < user.credit_balance.get("total_left"):
#         UpdateTaskCreditStatus.update_credits(user, consumable_credits)
#     else:
#         logger.info("Insufficient credits for segment translation")
#         raise ValueError("Insufficient credits for segment translation")


class TranslationStage(ABC):
    def __init__(self, anthropic_api, target_language, source_language, group_text_units=False, task_progress=None):
        self.api = anthropic_api
        self.target_language = target_language
        self.source_language = source_language
        self.group_text_units = group_text_units
        self.task_progress = task_progress
        self.set_progress()


    def get_prompt_by_stage(self,stage ):
        return AdaptiveSystemPrompt.objects.get(stages=stage).prompt
    
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



    def get_progress(self):
        cache_key = f"adaptive_progress_{self.task_progress.id}"
        res = cache.get(cache_key, None)
        return res
    
 
    def set_progress(self,stage=None,stage_percent=None,no_of_stage=4):
        

        data = self.get_progress()
        if data != None:
            no_of_stage = data["no_of_stages"]
        else:
            no_of_stage = no_of_stage
        
        if data!=None:
            if no_of_stage == 4 :
                stage_weights = {"stage_01": 0.1, "stage_02": 0.4, "stage_03": 0.25, "stage_04": 0.25}
            else:
                stage_weights = {"stage_01": 0.1, "stage_02": 0.5, "stage_04": 0.4}
            if stage_percent != None and stage != None:
                data[stage] = stage_percent
                data["total"] = int(sum(data[stage_key] * stage_weights[stage_key] for stage_key in stage_weights.keys())) 
                progress = data
            else:
                 return None              
        else:
            if no_of_stage == 4:
                progress={"stage_01": 0, "stage_02": 0, "stage_03": 0, "stage_04": 0,"total": 0,"no_of_stages":4}
            else:
                progress={"stage_01": 0, "stage_02": 0, "stage_04": 0,"total": 0,"no_of_stages":3}
      
        cache_key = f"adaptive_progress_{self.task_progress.id}"
        logger.info(f"Setting progress for {cache_key} with data: {progress}")
        return cache.set(cache_key, progress, timeout=3600)         
      
    
    def update_progress_db(self):
        data = self.get_progress()
        if data!=None and self.task_progress.progress_percent!=data['total']:
            self.task_progress.progress_percent = data['total']
            self.task_progress.save()

 

# Style analysis (Stage 1)
class StyleAnalysis:
    def __init__(self, user,task,api_client):
         
        self.stage_percent = 0
        self.max_word = 1_000
        self.user = user
        self.task = task
        self.api_client = api_client


    def safe_request(self,messages, system_instruction, retries=2):
        for _ in range(retries):
            response_text, token_count = self.api_client.send_request(messages=messages, system_instruction=system_instruction)
            if response_text:
                return response_text, token_count
        return None, None
         
    def process(self, all_paragraph):
        from ai_workspace.models import TaskStyle
        
        if not TaskStyle.objects.filter(task = self.task).exists():
            system_prompt = AdaptiveSystemPrompt.objects.get(stages = "stage_1").prompt
            task_instance = TaskStyle.objects.create(task=self.task)

            combined_text = ''
            combined_text_list = []

            for single_paragraph in all_paragraph:
    
                if len(" ".join(combined_text_list).split()) < self.max_word:   
                    combined_text_list.append(single_paragraph)
                else:
                    break

            combined_text = "".join(combined_text_list)
            if combined_text:

                try:
                    result_content_prompt,token = self.safe_request(messages = combined_text, system_instruction=system_prompt)
                    task_instance.style_guide = result_content_prompt
                    task_instance.style_output_token=token
                    task_instance.save()
 
                    logger.info("Adaptive style created")
                    print("result_content_prompt",result_content_prompt)
                    return result_content_prompt
 
                except Exception as e:
                    self.task.adaptive_file_translate_status =AdaptiveFileTranslateStatus.FAILED
                    self.task.save()
                    logger.error("Adaptive style failed and task marked as FAILED")
                    logger.exception(f"Exception occurred during style {e}")
        else:
            logger.info("Adaptive style already exists")
             
            return None

 




# Initial translation (Stage 2)
class InitialTranslation(TranslationStage):

    def __init__(self, user,api_client, task_adaptive_instance ,source_language, target_language,task_progress,style_prompt):
        
        self.stage_percent = 0
        self.all_stage_result_instance =  task_adaptive_instance.each_task_stage.all()
        self.style_prompt = style_prompt
        self.task = task_adaptive_instance.task
 
        self.total = len(self.all_stage_result_instance)

        self.source_language = source_language
        self.target_language = target_language
        
        self.task_progress = task_progress 
        self.api_client = api_client
        self.claude_client = LLMClient(provider= "anthropic", style=False)
        self.user = user
        self.job_ins = self.task.job

        self.source_language_ins = self.job_ins.source_language
        self.target_language_ins = self.job_ins.target_language

        self.project_ins = self.job_ins.project
        self.user = self.project_ins.ai_user

        self.source_code = self.source_language_ins.locale_code

        self.gloss_prompt = self.get_prompt_by_stage(stage = "gloss_adapt")




    def get_glossary(self, user_input):
        from ai_glex.models import GlossarySelected, TermsModel
        from ai_workspace_okapi.api_views import matching_word
        from ai_glex.api_views import job_lang_pair_check

        gloss_selected = GlossarySelected.objects.filter(project=self.project_ins)
        if not gloss_selected:
            return None
        
        gloss_projects = [gloss.glossary.project for gloss in gloss_selected] if gloss_selected else []
        gloss_job_ins = []
        for gp in gloss_projects:
            is_pair = job_lang_pair_check(gp.project_jobs_set.all(), self.source_language_ins.id, self.target_language_ins.id)
            if is_pair:
                gloss_job_ins.append(is_pair)

        # glossary_selected = GlossarySelected.objects.filter(project=self.project_ins, glossary__project__project_type__id=3).values_list('glossary_id', flat=True)

        

        # # Get glossary job instance based on language pair
        # gloss_proj = self.task.proj_obj.individual_gloss_project.project
        # gloss_job_list = gloss_proj.project_jobs_set.all()
        # gloss_job_ins = job_lang_pair_check(gloss_job_list, self.source_language_ins.id, self.target_language_ins.id)
        gloss_selected = gloss_selected.values_list('glossary_id', flat=True)
        queryset = TermsModel.objects.filter(glossary__in=gloss_selected, job__in=gloss_job_ins)
        matching_exact_queryset = matching_word(user_input=user_input, lang_code=self.source_code)
        filtered_terms = queryset.filter(matching_exact_queryset)

        if filtered_terms.exists():
            all_gloss = "\n".join(f"{term.sl_term}  → {term.tl_term}" for term in filtered_terms)
            print("all_gloss--->",all_gloss)
            return all_gloss

        return None
 



    def safe_request(self,messages, system_instruction, retries=2):
        for _ in range(retries):
            response_text, token_count = self.api_client.send_request(messages=messages, system_instruction=system_instruction)
            if response_text:
                return response_text, token_count
        return None, None
    
    def safe_request_claude(self,messages, system_instruction, retries=2):
        for _ in range(retries):
            response_text, token_count = self.claude_client.send_request(messages=messages, system_instruction=system_instruction)
            if response_text:
                return response_text, token_count
        return None, None
 

    def process_stage_result(self, stage_result_instance, system_prompt):

        messages = stage_result_instance.source_text 

        if not messages:
            stage_result_instance.stage_2 = messages
            return stage_result_instance
        
        gloss = self.get_glossary(user_input=messages)
        if gloss:
            
            stage_result_instance.glossary_text = gloss
            stage_result_instance.save()
            system_prompt += f"\n{self.gloss_prompt}\n{gloss}."
 

        if stage_result_instance.stage_2:
            logging.info(f"Already processed: {stage_result_instance.id}")
            return None
        try:
            response_text, total_count = self.safe_request(messages=messages, system_instruction= system_prompt)
            #credits_consum_adaptive(user=self.user,consumable_credits=total_count) ######## reducing the credit for stage 2 ######


            if response_text:
                stage_result_instance.stage_2 = response_text
                stage_result_instance.stage_2_output_token = total_count
                return stage_result_instance
            else:
                stage_result_instance.stage_2_error_type = "LLM_ERROR"
                stage_result_instance.stage_2_error_message = "Response text is empty"
                # stage_result_instance.save()
                logging.error(f"response_text is empty for id from task_stage_results model {stage_result_instance.id}")
                return stage_result_instance
                # raise ValueError("response_text is empty for id from task_stage_results model {stage_result_instance.id}")
                
                # return None
        except BaseException as e:
            stage_result_instance.stage_2_error_type = "OTHER"
            stage_result_instance.stage_2_error_message = str(e)
            logging.error(f"Error processing stage 2 for id {stage_result_instance.id}: {e}")
            return stage_result_instance


    def process_stage_result_stage_3(self,stage_result_instance, system_prompt):
        
        if not stage_result_instance.source_text:
            stage_result_instance.stage_3 = stage_result_instance.source_text
            return stage_result_instance
        
        if stage_result_instance.stage_3:
            logging.info(f"Already processed: {stage_result_instance.id}")
            return None
        
        messages = f"{self.source_language} Source:\n{stage_result_instance.source_text}\n{self.target_language} Translation:\n{stage_result_instance.stage_2}"

        if stage_result_instance.glossary_text:
            system_prompt += f"\n{self.gloss_prompt}\n{stage_result_instance.glossary_text}."
        

        try:
            response_text, total_count = self.safe_request(messages=messages, system_instruction=system_prompt)
        #credits_consum_adaptive(user=self.user,consumable_credits=total_count) ######## reducing the credit for stage 3 ######
    
            if response_text:
                stage_result_instance.stage_3 = response_text
                stage_result_instance.stage_3_output_token = total_count
                return stage_result_instance
        
            else:
                stage_result_instance.stage_3_error_type = "LLM_ERROR"
                stage_result_instance.stage_3_error_message = "Response text is empty"
                # stage_result_instance.save()
                logging.error(f"response_text is empty for id from task_stage_results model {stage_result_instance.id}")
                return stage_result_instance
        except BaseException as e:
            stage_result_instance.stage_4_error_type = "OTHER"
            stage_result_instance.stage_4_error_message = str(e)
            logging.error(f"Error processing stage 3 for id {stage_result_instance.id}: {e}")
            return stage_result_instance


    
        
    def process_stage_result_stage_4(self,stage_result_instance, system_prompt):
        if not stage_result_instance.source_text:
            stage_result_instance.stage_4 = stage_result_instance.source_text
            return stage_result_instance
        
        if stage_result_instance.stage_4:
            logging.info(f"Already processed: {stage_result_instance.id}")
            return None
        
        if stage_result_instance.stage_3:
            messages = stage_result_instance.stage_3    
        else:
            messages = stage_result_instance.stage_2
            logging.info(f"stage_2 message is added in stage 4 process")

        if messages:
            if stage_result_instance.glossary_text:
                system_prompt += f"\n{self.gloss_prompt}\n{stage_result_instance.glossary_text}."

            messages = f"\n\n{self.source_language} :{stage_result_instance.source_text} \n\n{self.target_language} :{messages} " 

            try:
    
                response_text, total_count = self.safe_request(messages= messages, system_instruction= system_prompt)
            
                if response_text:
                    stage_result_instance.stage_4 = response_text
                    stage_result_instance.stage_4_output_token = total_count
                    return stage_result_instance
                else:
                    stage_result_instance.stage_4_error_type = "LLM_ERROR"
                    stage_result_instance.stage_4_error_message = "Response text is empty"
                    # stage_result_instance.save()
                    logging.error(f"response_text is empty for id from task_stage_results model {stage_result_instance.id}")
                    return stage_result_instance
            except BaseException as e:
                    stage_result_instance.stage_4_error_type = "OTHER"
                    stage_result_instance.stage_4_error_message = str(e)
                    return stage_result_instance

            
        else:
            logging.error(f"empty message")
            return None


    def check_for_error(self, batch, stage_name):
        filter_kwargs={f"{stage_name}_error_type__isnull":False}
        results = AllStageResult.objects.filter(task_stage_result__segment_batch=batch).filter(**filter_kwargs)
        if results.exists():
            raise ValueError(f"Errors found in {stage_name} stage for batch {batch.id}")
        
    def trans(self):
 
        system_prompt = self.get_prompt_by_stage(stage = "stage_2")
 
        if self.style_prompt:
            system_prompt = system_prompt.format(style_prompt= self.style_prompt, target_language= self.target_language, source_language=self.source_language)
        else:
 
            raise RuntimeError("no style")
 
    
 
        progress_counter = 1 
        updated_instances = []

        try:
            self.task.adaptive_file_translate_status = AdaptiveFileTranslateStatus.ONGOING
            self.task.save()
            with ThreadPoolExecutor(max_workers=4) as executor:  
                future_to_instance = {
                    executor.submit(self.process_stage_result, instance, system_prompt): instance
                    for instance in self.all_stage_result_instance
                }

                for future in as_completed(future_to_instance):
                    result = future.result()
                    if result:
                        updated_instances.append(result)

                    
                    percent = int((progress_counter / self.total) * 100)
                    self.set_progress(stage="stage_02", stage_percent=percent)
                    progress_counter += 1
 
            
            logging.info("✅ Done inference. stage Trans")


            if updated_instances:
                with transaction.atomic():
                    BATCH_SIZE = 3
                    for i in range(0, len(updated_instances), BATCH_SIZE):
                            AllStageResult.objects.bulk_update(
                                updated_instances[i:i + BATCH_SIZE],
                                ['stage_2', 'stage_2_output_token', 'stage_2_error_type', 'stage_2_error_message']
                            )

                    logging.info("✅ Bulk updated all stage_02 results.")
                    self.check_for_error(stage_name='stage_2',batch=self.task_progress)
                    self.update_progress_db()
     
        except BaseException as e:
            self.task.adaptive_file_translate_status = AdaptiveFileTranslateStatus.FAILED
            self.task.save()      
            self.task_progress.status = BatchStatus.FAILED
            self.task_progress.error_type = "OTHER"
            self.task_progress.error_message = str(e)
            self.task_progress.save()

            logger.error("Adaptive segment translation failed and task marked as FAILED")
            logger.exception(f"Exception occurred during translation {e}")
            raise ValueError(f"Exception occurred during translation stage_2 {e}")

 
    def refine(self):

        system_prompt = self.get_prompt_by_stage(stage = "stage_3")
        system_prompt = system_prompt.format(target_language= self.target_language, source_language=self.source_language)
    
        progress_counter = 1 
        updated_instances = []

        try:
            
            self.task.adaptive_file_translate_status = AdaptiveFileTranslateStatus.ONGOING
            self.task.save()


            with ThreadPoolExecutor(max_workers=4) as executor:  
                future_to_instance = {
                    executor.submit(self.process_stage_result_stage_3, instance, system_prompt): instance
                    for instance in self.all_stage_result_instance
                }

                for future in as_completed(future_to_instance):
                    result = future.result()
                    if result:
                        updated_instances.append(result)
                    
                    percent = int((progress_counter / self.total) * 100)
                    self.set_progress(stage="stage_03", stage_percent=percent)
                    progress_counter += 1
 
            
            logging.info("✅ Done inference. stage 3")
            
            if updated_instances:
                with transaction.atomic():
                    BATCH_SIZE = 3
                    for i in range(0, len(updated_instances), BATCH_SIZE):
                        AllStageResult.objects.bulk_update(
                                updated_instances[i:i + BATCH_SIZE],
                                ['stage_3', 'stage_3_output_token', 'stage_3_error_type', 'stage_3_error_message']
                            )

                    logging.info("✅ Bulk updated all stage_03 results.")
                    self.update_progress_db()
                    self.check_for_error(stage_name='stage_3',batch=self.task_progress)
            
        except BaseException as e:
            self.task.adaptive_file_translate_status = AdaptiveFileTranslateStatus.FAILED
            self.task.save()

            self.task_progress.status = BatchStatus.FAILED
            self.task_progress.error_type = "OTHER"
            self.task_progress.error_message = str(e)
            self.task_progress.save()

            logger.error("Adaptive segment translation failed and task marked as FAILED")
            logger.exception(f"Exception occurred during translation {e}")
            raise ValueError(f"Exception occurred during translation stage_3 {e}")



    def rewrite(self):
        system_prompt = self.get_prompt_by_stage(stage = "stage_4")
        system_prompt = system_prompt.format(target_language= self.target_language )
 
 
        progress_counter = 1 
        updated_instances = []

        try:
            
            self.task.adaptive_file_translate_status = AdaptiveFileTranslateStatus.ONGOING
            self.task.save()

            with ThreadPoolExecutor(max_workers=4) as executor:  
                future_to_instance = {
                    executor.submit(self.process_stage_result_stage_4, instance, system_prompt): instance
                    for instance in self.all_stage_result_instance
                }

                for future in as_completed(future_to_instance):
                    result = future.result()
                    if result:
                        updated_instances.append(result)
                   
                    percent = int((progress_counter / self.total) * 100)
                    self.set_progress(stage="stage_04", stage_percent=percent)
                    progress_counter += 1
            
            logging.info("✅ Done inference. stage 4")

            

            if updated_instances:
                with transaction.atomic():
                    BATCH_SIZE = 3
                    for i in range(0, len(updated_instances), BATCH_SIZE):
                        AllStageResult.objects.bulk_update(
                                updated_instances[i:i + BATCH_SIZE],
                                ['stage_4', 'stage_4_output_token','stage_4_error_type', 'stage_4_error_message']
                            )

 
                    logging.info("✅ Bulk updated all stage_04 results.")
                self.check_for_error(stage_name='stage_4',batch=self.task_progress)
                
            self.task.adaptive_file_translate_status = AdaptiveFileTranslateStatus.COMPLETED
            self.task.save()
            logger.info("✅ Done Adaptive segment translation")
            self.update_progress_db()
            
 
     
        except BaseException as e:
            self.task.adaptive_file_translate_status = AdaptiveFileTranslateStatus.FAILED
            self.task.save()

            self.task_progress.status = BatchStatus.FAILED
            self.task_progress.error_type = "OTHER"
            self.task_progress.error_message = str(e)
            self.task_progress.save()

            logger.error("Adaptive segment translation failed and task marked as FAILED")
            logger.exception(f"Exception occurred during translation {e}")
            raise ValueError(f"Exception occurred during translation stage_4 {e}")
    


 
class AdaptiveSegmentTranslator(TranslationStage):
    
    def __init__(self, provider, 
                 source_language, 
                 target_language, 
                 task_progress, 
                 group_text_units=False, document=None):
        
        from ai_workspace.models import TaskStyle
        
        self.client = LLMClient(provider = provider,style=False)
        self.source_language = source_language
        self.target_language = target_language
         
        self.task_progress = task_progress
        self.document = document
        self.task_obj = self.document.task_obj
        self.group_text_units = group_text_units
        self.user = self.task_progress.project.ai_user
        self.style_guideline = TaskStyle.objects.get(task=self.task_obj).style_guide 
         
        
    def deduct_credits_adaptive(self,segments):
        from ai_workspace_okapi.api_views import MT_RawAndTM_View
        from ai_workspace.api_views import UpdateTaskCreditStatus
        consumable_credits = MT_RawAndTM_View.get_adaptive_consumable_credits_multiple_segments(self.task_obj.document, None, segments)
        if consumable_credits < self.user.credit_balance.get("total_left"):
            UpdateTaskCreditStatus.update_credits(self.user, consumable_credits)
        else:
            logger.info("Insufficient credits for segment translation")
            raise ValueError("Insufficient credits for segment translation")

    def process_batch(self, segments, d_batches, batch_no):
        from ai_workspace.models import TaskStageResults, AllStageResult

        logger.info(f"batch_no {batch_no}")
        logger.info(f"len of the text----> {len(segments)}")
 
        if self.target_language in ADAPTIVE_INDIAN_LANGUAGE.split(" "):
            self.set_progress(no_of_stage=4)
            no_of_stage = 4
        else:
            self.set_progress(no_of_stage=3)
            no_of_stage = 3

        self.set_progress(stage = "stage_01" , stage_percent=100)
        task_adaptive_instance = TaskStageResults.objects.create(task = self.task_obj, group_text_units=self.group_text_units, celery_task_batch = batch_no,segment_batch= self.task_progress)
            
        
        splited_segment = self.split_paragraph_to_chunks(paragraphs = segments, max_words=500)
        logger.info(f"segment paragraph after split {len(splited_segment)}")

        all_segment_obj = [AllStageResult(source_text=i, task_stage_result= task_adaptive_instance,no_of_stages_used=no_of_stage) for i in splited_segment]
        AllStageResult.objects.bulk_create(all_segment_obj, batch_size=3)
        
        logging.info("all_segments are created")
 
        
        self.update_progress_db()
        self.initial_translation = InitialTranslation(user= self.user , api_client= self.client,
                                                      task_adaptive_instance= task_adaptive_instance,
                                                      source_language = self.source_language,
                                                      target_language = self.target_language,
                                                      task_progress = self.task_progress, style_prompt= self.style_guideline )

        self.initial_translation.trans()
        
        logging.info("done stage 2")
 
        if self.target_language in ADAPTIVE_INDIAN_LANGUAGE.split(" "):
            
            self.initial_translation.refine()
            logging.info(f"done stage 3 {self.target_language}")

            self.initial_translation.rewrite()
            logging.info(f"done stage 4 {self.target_language}")
            

        else:
            self.initial_translation.rewrite()
            logging.info(f"done in first stage {self.target_language}")
            # self.set_progress(stage="stage_03", stage_percent=100)
            # self.set_progress(stage="stage_04", stage_percent=100)

        self.deduct_credits_adaptive(segments=segments)


        self.task_progress.status = BatchStatus.COMPLETED
        self.task_progress.save()

        logger.info("Adaptive segment translation was completed and saved to DB")

        return None



    def process_batch_retry(self, segments, d_batches, batch_no):
        from ai_workspace.models import TaskStageResults, AllStageResult

        logger.info(f"batch_no {batch_no}")
        logger.info(f"len of the text----> {len(segments)}")


        # progress_data = self.get_progress()
 
        # if progress_data ==None:
        if self.target_language in ADAPTIVE_INDIAN_LANGUAGE.split(" "):
            self.set_progress(no_of_stage=4)
            no_of_stage = 4
        else:
            self.set_progress(no_of_stage=3)
            no_of_stage = 3

        self.set_progress(stage = "stage_01" , stage_percent=100)
        # task_adaptive_instance = TaskStageResults.objects.create(task = self.task_obj, group_text_units=self.group_text_units, celery_task_batch = batch_no,segment_batch= self.task_progress)
            
        task_adaptive_instance = TaskStageResults.objects.get(task = self.task_obj,segment_batch= self.task_progress)



        # splited_segment = self.split_paragraph_to_chunks(paragraphs = segments, max_words=500)

        # logger.info(f"segment paragraph after split {len(splited_segment)}")

        # all_segment_obj = [AllStageResult(source_text=i, task_stage_result= task_adaptive_instance,no_of_stages_used=no_of_stage) for i in splited_segment]
        # AllStageResult.objects.bulk_create(all_segment_obj, batch_size=3)

        segment_results = task_adaptive_instance.each_task_stage.all()

        error_results  = segment_results.filter(Q(stage_2_error_type__isnull=False) | Q(stage_3_error_type__isnull=False) | Q(stage_4_error_type__isnull=False))


        self.all_stage_result_instance =  task_adaptive_instance.each_task_stage.all() 
        self.total = len(self.all_stage_result_instance)
                
        self.update_progress_db()
        self.initial_translation = InitialTranslation(user= self.user , api_client= self.client,
                                                      task_adaptive_instance= task_adaptive_instance,
                                                      source_language = self.source_language,
                                                      target_language = self.target_language,
                                                      task_progress = self.task_progress, style_prompt= self.style_guideline )

        self.initial_translation.trans()
        
        logging.info("done stage 2")
 
        if self.target_language in ADAPTIVE_INDIAN_LANGUAGE.split(" "):
            
            self.initial_translation.refine()
            logging.info(f"done stage 3 {self.target_language}")

            self.initial_translation.rewrite()
            logging.info(f"done stage 4 {self.target_language}")
            

        else:
            self.initial_translation.rewrite()
            logging.info(f"done in first stage {self.target_language}")
            # self.set_progress(stage="stage_03", stage_percent=100)
            # self.set_progress(stage="stage_04", stage_percent=100)

        self.deduct_credits_adaptive(segments=segments)

        self.task_progress.status = BatchStatus.COMPLETED
        self.task_progress.save()

        logger.info("Adaptive segment translation was completed and saved to DB")

        return None


    def group_strings_max_words(self, segments, max_words):
        grouped = []
        temp = []
        word_count = 0
 
        for segment in segments:
            segment_word_count = len(segment.split())

            if word_count + segment_word_count > max_words:
                if temp:
                    grouped.append("\n\n".join(temp))
                temp = [segment]
                word_count = segment_word_count
            else:
                temp.append(segment)
                word_count += segment_word_count

        if temp:
            grouped.append("\n\n".join(temp))

        return grouped


    def split_paragraph_to_chunks(self,paragraphs, max_words):
        all_words = []
        for text in paragraphs:
            all_words.extendparagraphs(text.split())   

        chunks = []
        current_chunk = []

        for word in all_words:
            current_chunk.append(word)
            if len(current_chunk) >= max_words:
                chunks.append(" ".join(current_chunk))
                current_chunk = []

    
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks
