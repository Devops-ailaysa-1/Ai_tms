from ai_workspace.utils import write_stage_response_in_excel
import backoff
from google.genai import types
from abc import ABC, abstractmethod
from django.core.cache import cache
import time,os
from ai_staff.models import AdaptiveSystemPrompt
import logging
from ai_workspace.models import AllStageResult 

logger = logging.getLogger('django')


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

                client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
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
            client = genai.Client(api_key = os.environ['GEMINI_API_KEY'])

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
            )

            res = client.models.generate_content(
                model = os.environ['GOOGLE_GEMINI_MODEL'],   
                contents = contents,
                config = generate_content_config,
            )
 
            return res.candidates[0].content.parts[0].text
 
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

    def __init__(self, anthropic_api, target_language, source_language, group_text_units=False, task_progress=None):

        super().__init__(anthropic_api, target_language, source_language, group_text_units, task_progress)
        
        self.stage_percent = 0
        self.max_word = 1_000

    def process(self, all_paragraph, document=None, batch_no=None, batch_instance=None):
        system_prompt = AdaptiveSystemPrompt.objects.get(stages = "stage_01").prompt

        combined_text = ''
        combined_text_list = []

        for single_paragraph in all_paragraph:
 
            if len(" ".join(combined_text_list).split()) < self.max_word:   
                combined_text_list.append(single_paragraph)
            else:
                break

        combined_text = "".join(combined_text_list)

 
        if combined_text:

            result_content_prompt = self.api.send_request(messages = combined_text, system_instruction=system_prompt)

            if result_content_prompt:
                self.set_progress(stage=self.stage, stage_percent=100)
                return result_content_prompt
            
            else:        
                return None
 




# Initial translation (Stage 2)
class InitialTranslation(TranslationStage):

    def __init__(self, anthropic_api, target_language, source_language, group_text_units=False, task_progress=None):

        super().__init__(anthropic_api, target_language, source_language, group_text_units,task_progress)
        self.stage_percent = 0
 

    def process(self, task_adaptive_instance, segments, style_prompt, gloss_terms, d_batches, document=None, batch_no=None, task_progress=None):

        # all_stage_result_instance = AllStageResult.objects.filter(task_stage_result=task_adaptive_instance)

        # if all_stage_result_instance:
        #     all_stage_result_instance = all_stage_result_instance.last()
        # else:
        #     all_stage_result_instance = AllStageResult.objects.create(task_stage_result=task_adaptive_instance)

        system_prompt = AdaptiveSystemPrompt.objects.get(stages = "stage_02").prompt
        system_prompt = system_prompt.format(style_prompt=style_prompt, target_language=self.target_language, source_language=self.source_language)
    
        if gloss_terms:
            gloss_prompt = AdaptiveSystemPrompt.objects.get(stages = self.stage).prompt
            glossary_lines = "\n".join([f'- "{src}" → "{tgt}"' for src, tgt in gloss_terms.items()])
            system_prompt += f"\n{gloss_prompt}\n{glossary_lines}."


        total = len(segments)
        progress_counter = 1 

        for para in segments:
            response_text = self.api.send_request(messages = para, system_instruction = system_prompt)
            if response_text:
                all_stage_result_instance =0
                
 
             
            percent = int((progress_counter/total)*100)
            self.set_progress(stage=self.stage, stage_percent=percent)
            progress_counter += 1
        
        return segments

 
class AdaptiveSegmentTranslator:
    def __init__(self, provider, source_language, target_language, api_key, model_name, gloss_terms, task_progress, group_text_units=False, document=None):
        
        self.client = LLMClient(provider, api_key, model_name)
        self.source_language = source_language
        self.target_language = target_language
        self.gloss_terms = gloss_terms
        self.task_progress = task_progress
        self.document = document
        self.group_text_units = group_text_units

        self.style_analysis = StyleAnalysis(self.client, target_language, source_language, group_text_units, self.task_progress)
        self.initial_translation = InitialTranslation(self.client, target_language, source_language, group_text_units, self.task_progress)
        #self.refinement_stage_1 = RefinementStage1(self.client, target_language, source_language, group_text_units, self.task_progress)
        #self.refinement_stage_2 = RefinementStage2(self.client, target_language, source_language, group_text_units, self.task_progress)

    def process_batch(self, segments, d_batches, batch_no):
        from ai_workspace.models import TaskStageResults, AllStageResult

        task_obj = self.document.task_obj

        task_adaptive_instance = TaskStageResults.objects.filter(task=task_obj)

        ##### style guidance  

        if not task_adaptive_instance:
            
            style_guideline = self.style_analysis.process(segments, self.document, batch_no, self.task_progress)

            if style_guideline:

                task_adaptive_instance = TaskStageResults.objects.create(task = task_obj , style_guide_stage_1 = style_guideline ,
                                                                         group_text_units=self.group_text_units,celery_task_batch=batch_no)
                
            else:
                raise RuntimeError("style not created")
            

            if self.group_text_units:
                segments = self.group_strings_max_words(segments, max_words=150)


        translated_segments = self.initial_translation.process(task_adaptive_instance = task_adaptive_instance ,
                                                                        segments = segments, gloss_terms = self.gloss_terms, 
                                                                        d_batches=d_batches, document = self.document, batch_no = batch_no,
                                                                        task_progress = self.task_progress)
        
        # self.initial_translation.update_progress_db()
        # refined_segments = self.refinement_stage_1.process(translated_segments, segments, self.gloss_terms, self.document,batch_no, self.task_progress)
        # store_result.stage_03 = refined_segments
        # final_segments = self.refinement_stage_2.process(refined_segments, segments, self.gloss_terms, self.document,batch_no, self.task_progress)
        # self.refinement_stage_2.update_progress_db()
        # store_result.stage_04 = final_segments
        # return final_segments
        print(translated_segments, "This is translated segments Stage_02")
        return translated_segments
