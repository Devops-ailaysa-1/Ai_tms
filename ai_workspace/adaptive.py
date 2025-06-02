 

from abc import ABC
from django.core.cache import cache
from ai_workspace.llm_client import LLMClient
from ai_staff.models import AdaptiveSystemPrompt
import logging,time
from ai_workspace.enums import AdaptiveFileTranslateStatus ,BatchStatus
logger = logging.getLogger('django')
from django.conf import settings
from ai_workspace.models import AllStageResult
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.db import transaction
 

class TranslationStage(ABC):
    def __init__(self, anthropic_api, target_language, source_language, group_text_units=False, task_progress=None):
        self.api = anthropic_api
        self.target_language = target_language
        self.source_language = source_language
        self.group_text_units = group_text_units
        self.task_progress = task_progress
        self.set_progress()

    # @abstractmethod
    # def process(self, segment, **kwargs):
    #     pass

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
    
 
    def set_progress(self,stage=None,stage_percent=None):
        stage_weights = {"stage_01": 0.1, "stage_02": 0.4, "stage_03": 0.25, "stage_04": 0.25}
        data = self.get_progress()
        if data!=None:
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
        return cache.set(cache_key, progress, timeout=3600)         
      
    
    def update_progress_db(self):
        data = self.get_progress()
        if data!=None and self.task_progress.progress_percent!=data['total']:
            self.task_progress.progress_percent = data['total']
            self.task_progress.save()

 

# Style analysis (Stage 1)
class StyleAnalysis(TranslationStage):
    def __init__(self,api_client,task_progress):
         
        self.stage_percent = 0
        self.max_word = 1_000
        self.api_client = api_client
        self.task_progress = task_progress
         

    def process(self, all_paragraph):
        
        system_prompt = AdaptiveSystemPrompt.objects.get(stages = "stage_1").prompt

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
                result_content_prompt,token = self.api_client.send_request(messages = combined_text, system_instruction=system_prompt)

            except Exception as e:
                self.task.adaptive_file_translate_status = AdaptiveFileTranslateStatus.FAILED
                self.task.save()

                self.task_progress.status = BatchStatus.FAILED
                self.task_progress.save()

                logger.error("Adaptive segment translation failed and task marked as FAILED")
                logger.exception(f"Exception occurred during translation {e}")

            if result_content_prompt:
                self.set_progress(stage = "stage_01" , stage_percent=100)
                
                return result_content_prompt
            
            else:        
                return None




# Initial translation (Stage 2)
class InitialTranslation(TranslationStage):

    def __init__(self, api_client, task_adaptive_instance,glossary_lines ,source_language, target_language,task_progress):

        self.stage_percent = 0
        self.all_stage_result_instance =  task_adaptive_instance.each_task_stage.all()
        self.style_prompt = task_adaptive_instance.style_guide_stage_1
        self.task = task_adaptive_instance.task
        self.glossary_lines = glossary_lines
        self.total = len(self.all_stage_result_instance)
        self.source_language = source_language
        self.target_language = target_language
        self.task_progress = task_progress 
        self.api_client = api_client
        self.claude_client = LLMClient("anthropic", api_key=None, model_name=None)
 
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
 

    def process_stage_result(self,stage_result_instance, system_prompt):
        messages = stage_result_instance.source_text 
        if not messages:
            stage_result_instance.stage_2 = messages
            return stage_result_instance

        if stage_result_instance.stage_2:
            logging.info(f"Already processed: {stage_result_instance.id}")
            return None

        response_text, total_count = self.safe_request(messages=messages, system_instruction=system_prompt)
        
        if response_text:
            stage_result_instance.stage_2 = response_text
            stage_result_instance.stage_2_output_token = total_count
            return stage_result_instance
        else:
            logging.error(f"response_text is empty for id from task_stage_results model {stage_result_instance.id}")
            return None


    def process_stage_result_stage_3(self,stage_result_instance, system_prompt):
        
        if not stage_result_instance.source_text:
            stage_result_instance.stage_3 = stage_result_instance.source_text
            return stage_result_instance
        
        if stage_result_instance.stage_3:
            logging.info(f"Already processed: {stage_result_instance.id}")
            return None
        
        messages = f"{self.source_language} Source:\n{stage_result_instance.source_text}\n{self.target_language} Translation:\n{stage_result_instance.stage_2}"

        response_text, total_count = self.safe_request(messages=messages, system_instruction=system_prompt)
        
        if response_text:
            stage_result_instance.stage_3 = response_text
            stage_result_instance.stage_3_output_token = total_count
            return stage_result_instance
        
        else:
            logging.error(f"response_text is empty for id from task_stage_results model {stage_result_instance.id}")
            return None
        
    def process_stage_result_stage_4(self,stage_result_instance, system_prompt):
        if not stage_result_instance.source_text:
            stage_result_instance.stage_4 = stage_result_instance.source_text
            return stage_result_instance
        
        if stage_result_instance.stage_4:
            logging.info(f"Already processed: {stage_result_instance.id}")
            return None
        
        messages=stage_result_instance.stage_3
        if messages:
            response_text, total_count = self.safe_request(messages=messages ,system_instruction=system_prompt)
        
            if response_text:
                stage_result_instance.stage_4 = response_text
                stage_result_instance.stage_4_output_token = total_count
                return stage_result_instance
            else:
                logging.error(f"response_text is empty for id from task_stage_results model {stage_result_instance.id}")
                return None
            
        else:
            logging.error(f"empty message")
            return None


    def trans(self):
 
        system_prompt = self.get_prompt_by_stage(stage = "stage_2")
        system_prompt = system_prompt.format(style_prompt= self.style_prompt, target_language= self.target_language, source_language=self.source_language)
    
        if self.glossary_lines:
            gloss_prompt = self.get_prompt_by_stage(stage = "gloss_adapt") 
            system_prompt += f"\n{gloss_prompt}\n{self.glossary_lines}."

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
 
            
            logging.info("✅ Done inference. stage 1")

            if updated_instances:
                with transaction.atomic():
                    BATCH_SIZE = 3
                    for i in range(0, len(updated_instances), BATCH_SIZE):
                            AllStageResult.objects.bulk_update(
                                updated_instances[i:i + BATCH_SIZE],
                                ['stage_2', 'stage_2_output_token']
                            )

                    logging.info("✅ Bulk updated all stage_02 results.")
 
     
        except Exception as e:
            self.task.adaptive_file_translate_status = AdaptiveFileTranslateStatus.FAILED
            self.task.save()

            self.task_progress.status = BatchStatus.FAILED
            self.task_progress.save()

            logger.error("Adaptive segment translation failed and task marked as FAILED")
            logger.exception(f"Exception occurred during translation {e}")

 
    def refine(self):

        system_prompt = self.get_prompt_by_stage(stage = "stage_3")
        system_prompt = system_prompt.format(target_language= self.target_language, source_language=self.source_language)
    
        if self.glossary_lines:
            gloss_prompt = self.get_prompt_by_stage(stage = "gloss_adapt") 
            system_prompt += f"\n{gloss_prompt}\n{self.glossary_lines}."

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
                                ['stage_3', 'stage_3_output_token']
                            )

                    logging.info("✅ Bulk updated all stage_03 results.")
 
     
        except Exception as e:
            self.task.adaptive_file_translate_status = AdaptiveFileTranslateStatus.FAILED
            self.task.save()

            self.task_progress.status = BatchStatus.FAILED
            self.task_progress.save()

            logger.error("Adaptive segment translation failed and task marked as FAILED")
            logger.exception(f"Exception occurred during translation {e}")



    def rewrite(self):
        system_prompt = self.get_prompt_by_stage(stage = "stage_4")
        system_prompt = system_prompt.format(target_language= self.target_language )
    
        if self.glossary_lines:
            gloss_prompt = self.get_prompt_by_stage(stage = "gloss_adapt") 
            system_prompt += f"\n{gloss_prompt}\n{self.glossary_lines}."
        
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
                                ['stage_4', 'stage_4_output_token']
                            )

                    #AllStageResult.objects.bulk_update(updated_instances, ['stage_3', 'stage_3_output_token'])
                    logging.info("✅ Bulk updated all stage_04 results.")
            
            self.task.adaptive_file_translate_status = AdaptiveFileTranslateStatus.COMPLETED
            self.task.save()
            logger.info("✅ Done Adaptive segment translation")
            self.update_progress_db()
 
     
        except Exception as e:
            self.task.adaptive_file_translate_status = AdaptiveFileTranslateStatus.FAILED
            self.task.save()

            self.task_progress.status = BatchStatus.FAILED
            self.task_progress.save()
            logger.error("Adaptive segment translation failed and task marked as FAILED")
            logger.exception(f"Exception occurred during translation {e}")
    

 
class AdaptiveSegmentTranslator:
    def __init__(self, provider, 
                 source_language, 
                 target_language, 
                 api_key, model_name, 
                 gloss_terms, task_progress, 
                 group_text_units=False, document=None):
        
        self.client = LLMClient(provider, api_key, model_name)
        self.source_language = source_language
        self.target_language = target_language
        self.gloss_terms = gloss_terms
        self.task_progress = task_progress
        self.document = document
        self.group_text_units = group_text_units

        self.style_analysis = StyleAnalysis(api_client = self.client ,task_progress = self.task_progress)
        

        #self.refinement_stage_1 = RefinementStage1(self.client, target_language, source_language, group_text_units, self.task_progress)
        #self.refinement_stage_2 = RefinementStage2(self.client, target_language, source_language, group_text_units, self.task_progress)

    def process_batch(self, segments, d_batches, batch_no):
        from ai_workspace.models import TaskStageResults, AllStageResult

        task_obj = self.document.task_obj
        task_adaptive_instance = TaskStageResults.objects.filter(task=task_obj)

        ##### style guidance  

        if not task_adaptive_instance:
            self.style_analysis.set_progress()
            style_guideline = self.style_analysis.process(all_paragraph=segments )
            if style_guideline:
                task_adaptive_instance = TaskStageResults.objects.create(task = task_obj, style_guide_stage_1 = style_guideline,
                                                                         group_text_units=self.group_text_units,celery_task_batch=batch_no)
                
            else:
                raise RuntimeError("style not created")
            

            if self.group_text_units:
                segments = self.group_strings_max_words(segments, max_words=150)
                all_segment_obj = [AllStageResult(source_text=i,task_stage_result=task_adaptive_instance) for i in segments]
                AllStageResult.objects.bulk_create(all_segment_obj, batch_size=3)
                
                logging.info("all_segments are created")
        
        else:
            task_adaptive_instance = task_adaptive_instance.last()
            self.style_analysis.set_progress(stage = "stage_01" , stage_percent=100)

            # if self.group_text_units and  not task_adaptive_instance.each_task_stage.all().exists():
            #     segments = self.group_strings_max_words(segments, max_words=150)
            #     all_segment_obj = [AllStageResult(source_text=i,task_stage_result=task_adaptive_instance) for i in segments]
            #     AllStageResult.objects.bulk_create(all_segment_obj)
                
            logging.info("all_segments are created from created style")
        
        if self.gloss_terms:
            glossary_lines = "\n".join([f'- "{src}" → "{tgt}"' for src, tgt in self.gloss_terms.items()])
        else:
            glossary_lines = None
            
        self.initial_translation = InitialTranslation(api_client= self.client, task_adaptive_instance= task_adaptive_instance,
                                                      glossary_lines= glossary_lines, source_language=self.source_language,
                                                      target_language = self.target_language,task_progress = self.task_progress )

        self.initial_translation.trans()
        logging.info("done stage 2")
        self.initial_translation.refine()
        logging.info("done stage 3")
        self.initial_translation.rewrite()
        logging.info("done stage 4")

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