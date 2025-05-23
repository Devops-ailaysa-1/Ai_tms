 
import backoff
from google.genai import types
from abc import ABC
from django.core.cache import cache
 
from ai_staff.models import AdaptiveSystemPrompt
import logging
from ai_workspace.enums import AdaptiveFileTranslateStatus
logger = logging.getLogger('django')
from django.conf import settings

GOOGLE_GEMINI_API =  settings.GOOGLE_GEMINI_API
GOOGLE_GEMINI_MODEL = settings.GOOGLE_GEMINI_MODEL

safety_settings=[
            types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="BLOCK_LOW_AND_ABOVE",   
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="BLOCK_LOW_AND_ABOVE",  
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="BLOCK_LOW_AND_ABOVE",  
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_LOW_AND_ABOVE",  
            ),
        ]

 
class LLMClient:
    def __init__(self, provider, api_key, model_name):
        self.provider = provider.lower()
        self.api_key = api_key
        self.model_name = model_name

        try:

            if self.provider == "anthropic":
                from anthropic import Anthropic
                self.client = Anthropic(api_key=api_key)

            elif self.provider == "openai":
                import openai
                openai.api_key = api_key
                self.client = openai

            elif self.provider == "gemini":
                from google import genai

                client = genai.Client(api_key=GOOGLE_GEMINI_API)
                self.client = client

            else:
                raise ValueError(f"Unsupported provider: {provider}")
            
        except ImportError as e:
            raise ImportError(f"Missing required package for {provider}: {e}")

        except Exception as e:
            raise RuntimeError(f"Failed to initialize client for {provider}: {e}")

    def send_request(self, messages, system_instruction,max_tokens=4000, stream=False):

        if self.provider == "anthropic":
            return self._handle_anthropic(messages, max_tokens, stream)
        
        elif self.provider == "openai":
            return self._handle_openai(messages, max_tokens, stream)
        
        elif self.provider == "gemini":
            return self._handle_genai(messages,system_instruction)
        
        else:
            raise ValueError("Unknown provider")

    def _handle_anthropic(self, messages, max_tokens, stream):
        if stream:
            streamed_output = ""
            with self.client.messages.stream(
                model=self.model_name,
                messages=messages,
                max_tokens=max_tokens,
            ) as stream:
                for text in stream.text_stream:
                    streamed_output += text
            usage = stream.get_final_message().usage
            return usage.input_tokens, usage.output_tokens, streamed_output.strip()
        else:
            response = self.client.messages.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_tokens,
            )
            return None, None, response.content[0].text.strip()

    def _handle_openai(self, messages, max_tokens, stream):
        
        chat_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages]
        
        response = self.client.ChatCompletion.create(
                                                        model=self.model_name,
                                                        messages=chat_messages,
                                                        max_tokens=max_tokens,
                                                        stream=stream
                                                    )

        if stream:
            output = ""
            for chunk in response:
                if "choices" in chunk and chunk["choices"][0]["delta"].get("content"):
                    output += chunk["choices"][0]["delta"]["content"]
            return None, None, output.strip()
        else:
            content = response.choices[0].message["content"]
            usage = response.usage
            return usage.prompt_tokens, usage.completion_tokens, content.strip()
    


    @backoff.on_exception(backoff.expo, Exception, max_tries=2, jitter=backoff.full_jitter)
    def _handle_genai(self, messages, system_instruction):

        if messages:

            from google import genai
            client = genai.Client(api_key = GOOGLE_GEMINI_API)

            contents = [
                        types.Content(
                            role="user",
                            parts=[types.Part.from_text(text=messages)]
                        )
            ]

            generate_content_config = types.GenerateContentConfig(
                max_output_tokens=65532,  
                response_mime_type="text/plain",
                candidate_count=1,
                safety_settings = safety_settings,
                system_instruction = system_instruction ,
                top_p=1.0, top_k=0,
                #thinking_config=types.ThinkingConfig(thinking_budget=0),
            )


            stream_output = ""
            for chunk in client.models.generate_content_stream(
                                                                model = GOOGLE_GEMINI_MODEL,
                                                                contents = contents ,
                                                                config = generate_content_config ):
                stream_output+=chunk.text
            
            total_tokens = client.models.count_tokens( model = GOOGLE_GEMINI_MODEL, contents=stream_output)
             

            # res = client.models.generate_content(
            #     model = os.environ['GOOGLE_GEMINI_MODEL'],   
            #     contents = contents,
            #     config = generate_content_config,
            # ) 
            # res.candidates[0].content.parts[0].text  
 
            return stream_output , total_tokens.total_tokens
 
        else:
            return None





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
        return cache.get(cache_key, None)

    
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
 
        return cache.set(cache_key, progress, timeout=3600)  # expires in 1 hour
    
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

            result_content_prompt,token = self.api_client.send_request(messages = combined_text, system_instruction=system_prompt)

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
 
    def safe_request(self,messages, system_instruction, retries=2):
        for _ in range(retries):
            response_text, token_count = self.api_client.send_request(messages=messages, system_instruction=system_instruction)
            if response_text:
                return response_text, token_count
        return None, None

    def trans(self):
 
        system_prompt = AdaptiveSystemPrompt.objects.get(stages = "stage_2").prompt
        system_prompt = system_prompt.format(style_prompt= self.style_prompt, target_language= self.target_language, source_language=self.source_language)
    
        if self.glossary_lines:
            gloss_prompt = AdaptiveSystemPrompt.objects.get(stages = "gloss_adapt").prompt
            system_prompt += f"\n{gloss_prompt}\n{self.glossary_lines}."

        progress_counter = 1 
        try:
            for stage_result_instance in self.all_stage_result_instance:
                messages = stage_result_instance.source_text
                if messages:
                    if not stage_result_instance.stage_02:
 
                        response_text , total_count = self.safe_request(messages = messages, system_instruction =system_prompt)
 

                        if response_text:
                            stage_result_instance.stage_02 = response_text
                            stage_result_instance.stage_2_output_token = total_count
                            self.task.adaptive_file_translate_status = AdaptiveFileTranslateStatus.ONGOING
                            self.task.save()
                            stage_result_instance.save()
                        
                        else:
                            logging.error(f"response_text is empty for id from task_stage_results model {stage_result_instance.id}")
                    else:
                        print("already there")
                    
                else:
                    stage_result_instance.stage_02 = messages
                    stage_result_instance.save()
    
                percent = int((progress_counter/self.total)*100)
                self.set_progress(stage = "stage_02", stage_percent=percent)
                progress_counter += 1
            
 
            
        except Exception as e:
            self.task.adaptive_file_translate_status = AdaptiveFileTranslateStatus.FAILED
            self.task.save()
            logger.error("Adaptive segment translation failed and task marked as FAILED")
            logger.exception("Exception occurred during translation")

 

    def stage_3(self):
         
        system_prompt = AdaptiveSystemPrompt.objects.get(stages = "stage_3").prompt
        system_prompt = system_prompt.format(source_language = self.source_language,  target_language = self.target_language )
         
        if self.glossary_lines:
            gloss_prompt = AdaptiveSystemPrompt.objects.get(stages = "gloss_adapt").prompt
            system_prompt += f"\n{gloss_prompt}\n{self.glossary_lines}."

        progress_counter = 1 
        try:
            for stage_result_instance in self.all_stage_result_instance:
                source_text = stage_result_instance.source_text
                if source_text:
                    if not stage_result_instance.stage_03:
                        messages = f"{self.source_language}\n{source_text}\n\n{self.target_language}\n{stage_result_instance.stage_02}"
 
 
                        response_text , total_count = self.safe_request(messages = messages, system_instruction = system_prompt)

                        if response_text:
                            stage_result_instance.stage_03 = response_text
                            stage_result_instance.stage_3_output_token = total_count
                            self.task.adaptive_file_translate_status = AdaptiveFileTranslateStatus.ONGOING
                            self.task.save()
                            stage_result_instance.save()
                        
                        else:
                            logging.error(f"response_text is empty for id from task_stage_results model {stage_result_instance.id}")
                    else:
                        print("already there stage 3")
                    
                else:
                    stage_result_instance.stage_02 = messages
                    stage_result_instance.save()
    
                percent = int((progress_counter/self.total)*100)
                self.set_progress(stage = "stage_03", stage_percent=percent)
                progress_counter += 1
        

            
 
            
        except Exception as e:
            self.task.adaptive_file_translate_status = AdaptiveFileTranslateStatus.FAILED
            self.task.save()
            logger.error("Adaptive segment translation failed and task marked as FAILED in stage 3")
            logger.exception("Exception occurred during translation")

    def stage_4(self):
        progress_counter = 1
        for _ in self.all_stage_result_instance:
            percent = int((progress_counter/self.total)*100)
            self.set_progress(stage = "stage_04", stage_percent=percent)
    
        self.task.adaptive_file_translate_status = AdaptiveFileTranslateStatus.COMPLETED
        self.task.save()



    

 
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
            
            style_guideline = self.style_analysis.process(all_paragraph=segments )
            if style_guideline:
                task_adaptive_instance = TaskStageResults.objects.create(task = task_obj, style_guide_stage_1 =style_guideline,
                                                                         group_text_units=self.group_text_units,celery_task_batch=batch_no)
                
            else:
                raise RuntimeError("style not created")
            

            if self.group_text_units:
                segments = self.group_strings_max_words(segments, max_words=150)
                all_segment_obj = [AllStageResult(source_text=i,task_stage_result=task_adaptive_instance) for i in segments]
                AllStageResult.objects.bulk_create(all_segment_obj)
                
                logging.info("all_segments are created")
        
        else:
            task_adaptive_instance = task_adaptive_instance.last()

            if self.group_text_units and  task_adaptive_instance.each_task_stage.all().exists():
                segments = self.group_strings_max_words(segments, max_words=150)
                all_segment_obj = [AllStageResult(source_text=i,task_stage_result=task_adaptive_instance) for i in segments]
                AllStageResult.objects.bulk_create(all_segment_obj)
                
                logging.info("all_segments are created from created style")
        
        if self.gloss_terms:
            glossary_lines = "\n".join([f'- "{src}" → "{tgt}"' for src, tgt in self.gloss_terms.items()])
        else:
            glossary_lines = None
            
        self.initial_translation = InitialTranslation(api_client= self.client, task_adaptive_instance= task_adaptive_instance,
                                                      glossary_lines= glossary_lines, source_language=self.source_language,
                                                      target_language = self.target_language,task_progress = self.task_progress )

        translated_segments = self.initial_translation.trans()
        print("done stage 2")
        self.initial_translation.stage_3()
        print("done stage 3")
        self.initial_translation.stage_4()
        print("done stage 4")

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