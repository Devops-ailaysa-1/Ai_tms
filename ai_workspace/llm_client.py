import json
import backoff
from google.genai import types
from google import genai
from django.conf import settings
import logging
import requests
import os
from google.oauth2 import service_account
logger = logging.getLogger('django')
from ai_workspace import exceptions

GOOGLE_GEMINI_API =  settings.GOOGLE_GEMINI_API
GOOGLE_GEMINI_MODEL = settings.GOOGLE_GEMINI_MODEL
ANTHROPIC_MODEL_NAME = settings.ANTHROPIC_MODEL_NAME
ANTHROPIC_API_KEY = settings.ANTHROPIC_API_KEY
OPENAI_MODEL_NAME_ADAPT = settings.OPENAI_MODEL_NAME_ADAPT
OPENAI_API_KEY = settings.OPENAI_API_KEY
ALTERNATE_GEMINI_MODEL = settings.ALTERNATE_GEMINI_MODEL
ADAPTIVE_STYLE_LLM_MODEL =  settings.ALTERNATE_GEMINI_MODEL

AI_RESEARCH_VERTEX_AI_MODEL_LINK = settings.AI_RESEARCH_VERTEX_AI_MODEL_LINK
AI_RESEARCH_VERTEX_AI_LOCATION = settings.AI_RESEARCH_VERTEX_AI_LOCATION
AI_RESEARCH_VERTEX_AI_JSON_PATH =  settings.AI_RESEARCH_VERTEX_AI_JSON_PATH
AI_RESEARCH_VERTEX_AI = settings.AI_RESEARCH_VERTEX_AI

print("AI_RESEARCH_VERTEX_AI_MODEL_LINK",AI_RESEARCH_VERTEX_AI_MODEL_LINK)
print("AI_RESEARCH_VERTEX_AI_LOCATION",AI_RESEARCH_VERTEX_AI_LOCATION)
print("AI_RESEARCH_VERTEX_AI_JSON_PATH",AI_RESEARCH_VERTEX_AI_JSON_PATH)
print("AI_RESEARCH_VERTEX_AI",AI_RESEARCH_VERTEX_AI)



NEBIUS_API_KEY = os.getenv('NEBIUS_API_KEY')
NEBIUS_API_URL = os.getenv('NEBIUS_API_URL')
PIB_NEBIUS_API_KEY = os.getenv('PIB_NEBIUS_API_KEY')
PIB_NEBIUS_API_URL = os.getenv('PIB_NEBIUS_API_URL')

import string
def is_numbers_or_punctuation(text: str) -> bool:
    text = text.strip()
    if not text:
        return False
    allowed = set(string.digits + string.punctuation+".")
    return all(c in allowed for c in text)


credentials_nebius = service_account.Credentials.from_service_account_file(AI_RESEARCH_VERTEX_AI_JSON_PATH,scopes=["https://www.googleapis.com/auth/cloud-platform"])

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
    def __init__(self, provider,model,style):
        self.provider = provider.lower()
        self.style = style
        self.model = model
 

        try:
            if self.provider == "anthropic":
                from anthropic import Anthropic
                self.client = Anthropic(api_key=ANTHROPIC_API_KEY)

            elif self.provider == "openai":
                import openai
                openai.api_key = OPENAI_API_KEY
                self.client = openai

            elif self.provider == "gemini":
                

                client = genai.Client(api_key=GOOGLE_GEMINI_API)
                self.client = client

            elif self.provider == "nebius":
                # Nebius uses requests library, no specific client initialization needed
                self.client = None
            elif self.provider == "pib_nebius":
                # Nebius uses requests library, no specific client initialization needed
                self.client = None

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

        elif self.provider == "nebius":
            return self._handle_nebius(messages, system_instruction, max_tokens)

        else:
            raise ValueError("Unknown provider")
        
    @backoff.on_exception(backoff.expo, Exception, max_tries=3, jitter=backoff.full_jitter)
    def _handle_anthropic(self,messages, system_instruction):
        streamed_output = ""
        with self.client.messages.stream(
            model= self.model, #ANTHROPIC_MODEL_NAME,
            messages=[{"role": "user", "content": messages}],
            system=system_instruction,
            max_tokens=60_000
            
        ) as stream:
            for text in stream.text_stream:
                streamed_output += text
        usage = stream.get_final_message().usage.output_tokens  
        # logger.info(f"Streamed output claude: {streamed_output}")
        return streamed_output , usage
 

    def _handle_openai(self, messages, system_instruction):

        usage = 0
        completion = self.client.ChatCompletion.create(
        model= self.model,#OPENAI_MODEL_NAME_ADAPT,
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
    def _handle_vertex_ai_pib(self, messages, system_instruction, max_tokens=60000):

        print("clled vetex ai")
        
        if is_numbers_or_punctuation(messages):
            return messages, 0
        
    

        client = genai.Client(project = AI_RESEARCH_VERTEX_AI,  vertexai=True, location=AI_RESEARCH_VERTEX_AI_LOCATION,credentials = credentials_nebius )

        generate_content_config = types.GenerateContentConfig(temperature = 1, top_p = 0.95, system_instruction = system_instruction)
        full_text = ""

        for chunk in client.models.generate_content_stream(model = AI_RESEARCH_VERTEX_AI_MODEL_LINK, contents = messages,  config = generate_content_config):
             if chunk.text:
                 full_text+=chunk.text
        print(full_text)
        return full_text,0




    @backoff.on_exception(backoff.expo, Exception, max_tries=3, jitter=backoff.full_jitter)
    def _handle_nebius(self, messages, system_instruction, max_tokens=60000):
        """
        Handle Nebius API requests using the gemma model 27b with fast model
        """
        if is_numbers_or_punctuation(messages):
            return messages,0
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Authorization": f"Bearer {NEBIUS_API_KEY}",
        }

        data = {
            "model": self.model,  # Use the model specified in the constructor
            "messages": [
                {"role": "system", "content": system_instruction},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": messages}
                    ]
                }
            ],
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(NEBIUS_API_URL, headers=headers, json=data, timeout=120)
            

            response_data = response.json()

            # Extract the generated text from the response
            if 'choices' in response_data and len(response_data['choices']) > 0:
                output_text = response_data['choices'][0]['message']['content']
            else:
                raise ValueError("No response content found in Nebius API response")

            # Extract usage information if available
            usage = response_data.get('usage', {}).get('completion_tokens', 0)

            logger.info(f"Nebius API response status: {response.status_code}")
            return output_text, usage

        except requests.exceptions.RequestException as e:
            logger.error(f"Nebius API request failed: {e}")
            raise RuntimeError(f"Failed to get response from Nebius API: {e}")
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to parse Nebius API response: {e}")
            raise RuntimeError(f"Invalid response format from Nebius API: {e}")


    
    @backoff.on_exception(backoff.expo, Exception, max_tries=2, jitter=backoff.full_jitter)
    def gemini_stream(self,client,model_name, contents, generate_content_config):
        stream_output = ""
 
        for chunk in client.models.generate_content_stream(model = model_name,  contents = contents, config = generate_content_config ):
            

            # logger.info(f"Chunk received: {chunk}")    
            if chunk.text==None:
                raise  exceptions.EmptyChunkFoundException("Empty chunk found in stream output")
              
            stream_output+=chunk.text


        return stream_output
    

    @backoff.on_exception(backoff.expo, Exception, max_tries=2, jitter=backoff.full_jitter)
    def gemini_direct(self,client, model_name, contents, generate_content_config):
        
        response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=generate_content_config,
                )
        # logger.info(f"------------------------------------------------------------------------------")
        # logger.info(f"output response: {response}")

        if not response.candidates or not response.candidates[0].content or not response.candidates[0].content.parts:
            logger.error(f"No content parts found in response candidates, input text is :{contents}")
            raise exceptions.EmptyChunkFoundException("Empty chunk found in direct output")
        else:
            output_text = response.candidates[0].content.parts[0].text
        
        total_token_usage = response.usage_metadata.total_token_count

        logger.info(f"Prompt tokens: {response.usage_metadata.prompt_token_count}, Candidates tokens (output): {response.usage_metadata.candidates_token_count}  \
            Total tokens: {response.usage_metadata.total_token_count}")


        return output_text, total_token_usage
 
 

    @backoff.on_exception(backoff.expo, Exception, max_tries=2, jitter=backoff.full_jitter)
    def _handle_genai(self, messages, system_instruction):
 
        if messages and system_instruction:

 
            client = genai.Client(api_key = GOOGLE_GEMINI_API)

            contents = [
                        types.Content(
                            role="user",
                            parts=[types.Part.from_text(text=messages)]
                        )
            ]

            generate_content_config = types.GenerateContentConfig(
                 thinking_config=types.ThinkingConfig(thinking_budget=200),
                 
                response_mime_type="text/plain",
                candidate_count=1, safety_settings = safety_settings,
                #response_mime_type="application/json",
                system_instruction = system_instruction)

 
 
            if settings.ADAPTIVE_RESPONSE_STREAM:
                try:
                    output_text = self.gemini_stream(client=client,  model_name=self.model, contents=contents, generate_content_config=generate_content_config)
                
                    total_tokens = client.models.count_tokens(model = self.model, contents=output_text)
            
                except exceptions.EmptyChunkFoundException as e:
                    logger.error(f"Empty chunk found in stream output: {e}")
                    output_text,total_tokens = self.gemini_direct(client=client,
                                                        model_name=self.model, contents=contents,
                                                        generate_content_config=generate_content_config)
            else:
                output_text,total_tokens = self.gemini_direct(client=client,
                                                    model_name=self.model, contents=contents,
                                                    generate_content_config=generate_content_config)
 
            return output_text , total_tokens
        else:
            return None
