from ai_workspace.utils import write_stage_response_in_excel
import backoff
from google.genai import types
from abc import ABC, abstractmethod
from django.core.cache import cache
import time,os
from ai_staff.models import AdaptiveSystemPrompt
import logging
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

                client = genai.Client(api_key=os.environ['gemini_api_key'])
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
        print("messages")
        print(messages)

        print("system_instruction")
        print(system_instruction)


        print(self.model_name)

        if messages:

            print(os.environ['gemini_api_key'])
            
            from google import genai
            client = genai.Client(api_key = os.environ['gemini_api_key'])



            contents = [
                        types.Content(
                            role="user",
                            parts=[types.Part.from_text(text="Hi this is Test")]
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
        # self.stage_weight = 10
        self.stage_percent = 0
        self.stage = "stage_1"
        self.max_word = 1_000

    def process(self, all_paragraph, document=None, batch_no=None, batch_instance=None):
        system_prompt = AdaptiveSystemPrompt.objects.get(stages=self.stage).prompt

 

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
        self.stage = "stage_02"

    def process(self, segments, style_prompt, gloss_terms, d_batches, document=None, batch_no=None, batch_instance=None):
        # system_prompt = AdaptiveSystemPrompt.objects.get(stages=self.stage).prompt
        # system_prompt = system_prompt.format(style_prompt=style_prompt, target_language=self.target_language)
        
 

        if gloss_terms:
            gloss_prompt = AdaptiveSystemPrompt.objects.get(stages=self.stage).prompt
            glossary_lines = "\n".join([f'- "{src}" → "{tgt}"' for src, tgt in gloss_terms.items()])
            translation_prompt += f"{gloss_prompt}\n{glossary_lines}."

        if self.group_text_units:
            segments = self.group_strings_max_words(segments, max_words=150)

        message_list = []
        response_result = []
        total = len(segments)
        progress_counter = 1 
        if (True if os.getenv("LLM_TRANSLATE_ENABLE",False) == 'True' else False):
            for para in segments:
                para_message = translation_prompt.format(self.source_language, self.target_language, style_prompt,self.target_language,self.target_language,self.target_language,para)
                 
                message_list.append(self.continue_conversation_user(user_message=para_message))
                response_text = self.api.send_request(message_list)
                response_result.append(response_text)
 
 
                message_list = []
                percent = int((progress_counter/total)*100)
                self.set_progress(stage=self.stage, stage_percent=percent)
                progress_counter += 1
                
        else:
            self.mock_api(segments,self.stage)
         
        return (segments, response_result)

 
class RefinementStage1(TranslationStage):
    def __init__(self, anthropic_api, target_language, source_language, group_text_units=False, task_progress=None):
        super().__init__(anthropic_api, target_language, source_language, group_text_units,task_progress)
        self.stage_percent = 0
        self.stage = "stage_03"

    def process(self, segments, source_text, gloss_terms, document=None, batch_no=None, batch_instance=None):
        # system_prompt = AdaptiveSystemPrompt.objects.get(stages=self.stage).prompt
        # system_prompt = system_prompt.format(target_language=self.target_language)

 

        if gloss_terms:
            glossary_lines = "\n".join([f'- "{src}" → "{tgt}"' for src, tgt in gloss_terms.items()])
            refinement_prompt += f"\nNote: While translating, make sure to translate the specific words as such if mentioned in the glossary pairs.Ensure that the replacements maintain the original grammatical categories like tense, aspect, modality,voice and morphological features.\nGlossary:\n{glossary_lines}."


        message_list = []
        response_result = []
        total = len(segments)
        progress_counter = 1 
        if (True if os.getenv("LLM_TRANSLATE_ENABLE",False) == 'True' else False):
            for trans_text, original_text in zip(segments, source_text):
                #user_text = """Source text:\n{source_text}\n\nTranslation text:\n{translated_text}""".format(source_text=original_text,
                #                                                                                                    translated_text=trans_text)
                para_message = refinement_prompt.format(self.source_language, self.target_language,original_text,trans_text,self.target_language)
                message_list.append(self.continue_conversation_user(user_message=para_message))
                response_text = self.api.send_request(message_list)
                response_result.append(response_text)
 
 
                percent = int((progress_counter/total)*100)
                self.set_progress(stage=self.stage, stage_percent=percent)
                progress_counter += 1
        else:
            raise "Switch to Production"

         
        return response_result


# Final refinement (Stage 4)
class RefinementStage2(TranslationStage):
    def __init__(self, anthropic_api, target_language, source_language, group_text_units=False, task_progress=None):
        super().__init__(anthropic_api, target_language, source_language, group_text_units,task_progress)
        self.stage_percent = 0
        self.stage = "stage_04"

    def process(self, segments, source_text, gloss_terms, document=None, batch_no=None, batch_instance=None):
        # system_prompt = AdaptiveSystemPrompt.objects.get(stages=self.stage).prompt
        # system_prompt = system_prompt.format(target_language=self.target_language)

 

        if gloss_terms:
            glossary_lines = "\n".join([f'- "{src}" → "{tgt}"' for src, tgt in gloss_terms.items()])
            final_refinement_prompt += f"\nNote: While translating, make sure to translate the specific words as such if mentioned in the glossary pairs.Ensure that the replacements maintain the original grammatical categories like tense, aspect, modality,voice and morphological features.\nGlossary:\n{glossary_lines}."
            

        message_list = []
        response_result = []
        total = len(segments)
        progress_counter = 1 

        if (True if os.getenv("LLM_TRANSLATE_ENABLE",False) == 'True' else False):
            for para in segments:
                para_message = final_refinement_prompt.format(para,self.target_language,self.target_language,self.target_language,self.target_language,
                                                              self.target_language)
 
                message_list.append(self.continue_conversation_user(user_message=para_message))
                response_text = self.api.send_request(message_list)
                response_result.append(response_text)
                if os.getenv('ANALYTICS') == 'True':
                    write_stage_response_in_excel(document.project, document.task_obj.id, batch_no,system_prompt, user_message=json.dumps(message_list, ensure_ascii=False), translated_result=response_text, stage=self.stage, input_token=input_token, output_token=output_token)
                    logger.info(f"Stage 4 data written to excel")
 
                message_list = []
                percent = int((progress_counter/total)*100)
                self.set_progress(stage=self.stage, stage_percent=percent)
                progress_counter += 1

        else:
            raise "Switch to Production"
         
        return response_result

 
class AdaptiveSegmentTranslator:
    def __init__(self, provider, source_language, target_language, api_key, model_name, gloss_terms, task_progress, group_text_units=False, document=None):
        
        self.client = LLMClient(provider, api_key, model_name)
        self.source_language = source_language
        self.target_language = target_language
        self.gloss_terms = gloss_terms
        self.task_progress = task_progress
        self.document = document

        self.style_analysis = StyleAnalysis(self.client, target_language, source_language, group_text_units, self.task_progress)
        #self.initial_translation = InitialTranslation(self.client, target_language, source_language, group_text_units, self.task_progress)
        #self.refinement_stage_1 = RefinementStage1(self.client, target_language, source_language, group_text_units, self.task_progress)
        #self.refinement_stage_2 = RefinementStage2(self.client, target_language, source_language, group_text_units, self.task_progress)

    def process_batch(self, segments, d_batches, batch_no):

 
        
        style_guideline = self.style_analysis.process(segments, self.document, batch_no, self.task_progress)
        #segments,translated_segments = self.initial_translation.process(segments, style_guideline, self.gloss_terms, d_batches, self.document, batch_no, self.task_progress)
        #self.initial_translation.update_progress_db()
        #refined_segments = self.refinement_stage_1.process(translated_segments, segments, self.gloss_terms, self.document,batch_no, self.task_progress)
        #final_segments = self.refinement_stage_2.process(refined_segments, segments, self.gloss_terms, self.document,batch_no, self.task_progress)
        #self.refinement_stage_2.update_progress_db()
        return style_guideline
    



    # def process_batch(self, segments, d_batches, batch_no):
    #     from ai_workspace.models import TaskStageResults
    #     style_guideline = self.style_analysis.process(segments, self.document, batch_no, self.task_progress)
    #     store_result = TaskStageResults.objects.filter(task=self.document.task_obj, celery_task_batch=batch_no).first()

    #     if not store_result:
    #         store_result = TaskStageResults.objects.create(task=self.document.task_obj,celery_task_batch=batch_no, stage_01=style_guideline, group_text_units=self.group_text_units)
    #     else:
    #         store_result.group_text_units = self.group_text_units
    #         store_result.stage_01 = style_guideline

    #     segments,translated_segments = self.initial_translation.process(segments, style_guideline, self.gloss_terms, d_batches, self.document, batch_no, self.task_progress)
    #     store_result.stage_02 = translated_segments
    #     self.initial_translation.update_progress_db()
    #     refined_segments = self.refinement_stage_1.process(translated_segments, segments, self.gloss_terms, self.document,batch_no, self.task_progress)
    #     store_result.stage_03 = refined_segments
    #     final_segments = self.refinement_stage_2.process(refined_segments, segments, self.gloss_terms, self.document,batch_no, self.task_progress)
    #     self.refinement_stage_2.update_progress_db()
    #     store_result.stage_04 = final_segments
    #     store_result.save()
    #     return final_segments

     