import backoff
from google.genai import types
from django.conf import settings
import logging
logger = logging.getLogger('django')

GOOGLE_GEMINI_API =  settings.GOOGLE_GEMINI_API
GOOGLE_GEMINI_MODEL = settings.GOOGLE_GEMINI_MODEL
ANTHROPIC_MODEL_NAME = settings.ANTHROPIC_MODEL_NAME
ANTHROPIC_API_KEY = settings.ANTHROPIC_API_KEY
OPENAI_MODEL_NAME_ADAPT = settings.OPENAI_MODEL_NAME_ADAPT
OPENAI_API_KEY = settings.OPENAI_API_KEY
ALTERNATE_GEMINI_MODEL = settings.ALTERNATE_GEMINI_MODEL


safety_settings=[
            types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="BLOCK_NONE",   
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="BLOCK_NONE",  
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="BLOCK_NONE",  
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_NONE",  
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
                self.client = Anthropic(api_key=ANTHROPIC_API_KEY)

            elif self.provider == "openai":
                import openai
                openai.api_key = OPENAI_API_KEY 
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
            return self._handle_anthropic(messages,system_instruction)
        
        elif self.provider == "openai":
            return self._handle_openai(messages, system_instruction)
        
        elif self.provider == "gemini":
            return self._handle_genai(messages,system_instruction)
        
        else:
            raise ValueError("Unknown provider")
        
    @backoff.on_exception(backoff.expo, Exception, max_tries=3, jitter=backoff.full_jitter)
    def _handle_anthropic(self,messages, system_instruction):
        
        print("model",ANTHROPIC_MODEL_NAME)
        
        streamed_output = ""
        with self.client.messages.stream(
            model= ANTHROPIC_MODEL_NAME,
            messages=[{"role": "user", "content": messages}],
            system=system_instruction,
            max_tokens=60_000
            
        ) as stream:
            for text in stream.text_stream:
                streamed_output += text
        usage = stream.get_final_message().usage.output_tokens  
        return streamed_output , usage
 

    def _handle_openai(self, messages, system_instruction):
        print("model",OPENAI_MODEL_NAME_ADAPT)
        usage = 0
        completion = self.client.ChatCompletion.create(
        model= OPENAI_MODEL_NAME_ADAPT,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": messages}
        ], stream=True )
        output_stream = ""
        for chunk in completion:
            if "content" in chunk.choices[0].delta and chunk.choices[0].delta.content:
                output_stream = output_stream + chunk.choices[0].delta.content
            else:
                output_stream = output_stream + " "
        output_stream = output_stream.strip() 
        return output_stream ,usage
    
    @backoff.on_exception(backoff.expo, Exception, max_tries=3, jitter=backoff.full_jitter)
    def try_stream(self,client,model_name,contents,generate_content_config):
        stream_output = ""
 
        for chunk in client.models.generate_content_stream(model = model_name,
                                                           contents = contents,
                                                           config = generate_content_config ):
            stream_output+=chunk.text
        return stream_output
 
 
 

    @backoff.on_exception(backoff.expo, Exception, max_tries=3, jitter=backoff.full_jitter)
    def _handle_genai(self, messages, system_instruction):
 
        if messages and system_instruction:

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
                candidate_count=1, safety_settings = safety_settings,
                system_instruction = system_instruction, top_p=1.0, top_k=0,
                #thinking_config=types.ThinkingConfig(thinking_budget=0),
            )

            try:

                stream_output_result = self.try_stream(client=client,
                                                   model_name=GOOGLE_GEMINI_MODEL, contents=contents,
                                                   generate_content_config=generate_content_config)
            except:
            #if not stream_output_result:
                stream_output_result = self.try_stream(client=client,
                                                   model_name=ALTERNATE_GEMINI_MODEL, contents=contents,
                                                   generate_content_config=generate_content_config)
 

            total_tokens = client.models.count_tokens( model = GOOGLE_GEMINI_MODEL, contents=stream_output_result)
            return stream_output_result , total_tokens.total_tokens
            
        else:
            return None