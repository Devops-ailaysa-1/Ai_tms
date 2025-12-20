import json
import backoff
from google.genai import types
from google.genai.types import  Part
from google import genai
from django.conf import settings
import logging
import requests
import os
import struct
import base64
import mimetypes
from google.oauth2 import service_account
logger = logging.getLogger('django')
from ai_workspace import exceptions
from ai_workspace.schema import pib_trans_result_schema,pib_transcription_result


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
    
    @backoff.on_exception(backoff.expo,Exception,max_tries=5,jitter=backoff.full_jitter)
    def _handle_vertex_ai_pib(self, messages, system_instruction):
        logger.info("Inside _handle_vertex_ai_pib method")

        contents = [ types.Content( role="user", parts=[ types.Part.from_text(text=system_instruction+"\n\n"+messages)]  ) ]

        print("contents----->",contents)
     

        credentials_nebius = service_account.Credentials.from_service_account_file(AI_RESEARCH_VERTEX_AI_JSON_PATH, scopes=["https://www.googleapis.com/auth/cloud-platform"])
 
        client = genai.Client(project=AI_RESEARCH_VERTEX_AI,vertexai=True,location=AI_RESEARCH_VERTEX_AI_LOCATION,credentials=credentials_nebius,)

        config = types.GenerateContentConfig(temperature=0.7,top_p=0.95,response_mime_type="application/json",
            response_schema=pib_trans_result_schema,thinking_config=types.ThinkingConfig(thinking_budget=5000))#,system_instruction=system_instruction,

        full_text_parts = []

        for chunk in client.models.generate_content_stream(model=AI_RESEARCH_VERTEX_AI_MODEL_LINK,contents=contents,config=config,):
            if chunk.text:
                full_text_parts.append(chunk.text)

        full_text = "".join(full_text_parts).strip()

        if not full_text:
            return "", 0
        
        try:
            parsed = json.loads(full_text)
            return parsed.get("translated_result", full_text), 0
        except json.JSONDecodeError:
            return full_text, 0





    @backoff.on_exception(backoff.expo, Exception, max_tries=5, jitter=backoff.full_jitter)
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
                {"role": "system", "content": system_instruction +"do not miss any do not add any extra information other than what is asked only give the resultant translated sentence or paragraph or word do not give any acknowledgement."},
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




def nebius_chat_validation( system_prompt , message):
    try:
 
        payload = {
            "model": "openai/gpt-oss-120b",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": (
                        [{"type": "text", "text": message}]
                        if isinstance(message, str)
                        else message
                    ),
                },
            ],
            "max_tokens": 19188,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "valid_translation_schema",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "valid_translation_result": {
                                "type": "string",
                                "description": "The final validated translation output.",
                            }
                        },
                        "required": ["valid_translation_result"],
                        "additionalProperties": False,
                    },
                },
            },
        }

        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Authorization": f"Bearer {NEBIUS_API_KEY}",
        }

        response = requests.post(NEBIUS_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        valid_translation_result = json.loads(response.json()['choices'][0]['message']['content'])['valid_translation_result']
        print("Validated Translation Result:", valid_translation_result)

        return  valid_translation_result
    except Exception as e:
        logger.error(f"Error in nebius_chat_validation: {e}")
        return message


 


######################


def gemini_mp3(speech_file):
    with open(speech_file, 'rb') as fd:
        content = fd.read()
    client = genai.Client(api_key = GOOGLE_GEMINI_API)
    
    generate_content_config = types.GenerateContentConfig( thinking_config=types.ThinkingConfig(thinking_budget=256),
                                                          response_mime_type="application/json",
                                                          response_schema=pib_transcription_result)

    prompt = """
    Process the audio file and generate a detailed transcription.
    subtitle structure 
    Example
    1
    00:00:02,000 --> 00:00:05,000
    Good morning everyone
    """
    full_text = ""
    for chunk in client.models.generate_content_stream(
        config = generate_content_config,
        model="gemini-2.5-flash",
        contents=[
            prompt,
            Part.from_bytes(
                data=content,
                mime_type="audio/mp3",
            ),
        ],
    ):
        if chunk.text:
            full_text+=chunk.text 

    html_parts = []

    for i in json.loads(full_text)["result"]:
        html_parts.append(
            f"<p>{i['timestamp']}<br>{i['transcription_result']}</p>"
        )

    all_subtitle = "".join(html_parts)
    
    return all_subtitle




##############################
def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """Generates a WAV file header for the given audio data and parameters.

    Args:
        audio_data: The raw audio data as a bytes object.
        mime_type: Mime type of the audio data.

    Returns:
        A bytes object representing the WAV file header.
    """
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size

    # http://soundfile.sapp.org/doc/WaveFormat/

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",          # ChunkID
        chunk_size,       # ChunkSize (total file size - 8 bytes)
        b"WAVE",          # Format
        b"fmt ",          # Subchunk1ID
        16,               # Subchunk1Size (16 for PCM)
        1,                # AudioFormat (1 for PCM)
        num_channels,     # NumChannels
        sample_rate,      # SampleRate
        byte_rate,        # ByteRate
        block_align,      # BlockAlign
        bits_per_sample,  # BitsPerSample
        b"data",          # Subchunk2ID
        data_size         # Subchunk2Size (size of audio data)
    )
    return header + audio_data

def parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
    """Parses bits per sample and rate from an audio MIME type string.

    Assumes bits per sample is encoded like "L16" and rate as "rate=xxxxx".

    Args:
        mime_type: The audio MIME type string (e.g., "audio/L16;rate=24000").

    Returns:
        A dictionary with "bits_per_sample" and "rate" keys. Values will be
        integers if found, otherwise None.
    """
    bits_per_sample = 16
    rate = 24000

    # Extract rate from parameters
    parts = mime_type.split(";")
    for param in parts: # Skip the main type part
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                # Handle cases like "rate=" with no value or non-integer value
                pass # Keep rate as default
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass # Keep bits_per_sample as default if conversion fails

    return {"bits_per_sample": bits_per_sample, "rate": rate}




def gemini_text_to_speech(text_path,language,voice_gender):
    from ai_staff.models import AdaptiveSystemPrompt
    client = genai.Client(api_key = GOOGLE_GEMINI_API)
    with open(text_path,'r') as fp:
        text = fp.read()
    print(text)

    voice_name = "Achernar" if voice_gender== "FEMALE" else "Achird"
    
    voice_prompt = AdaptiveSystemPrompt.objects.get(task_name="text_to_speech").prompt.format(language_name=language)
    print(voice_prompt)
    print("-------")
    print(voice_gender)
    model = "gemini-2.5-flash-preview-tts"

    contents = [ types.Content(role="user",parts=[types.Part.from_text(text=text)])]

    generate_content_config = types.GenerateContentConfig(temperature=1,
        response_modalities=["audio"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name))))
    
     
    for chunk in client.models.generate_content_stream(model=model,contents=contents, config=generate_content_config):
 
        if ( chunk.candidates is None or chunk.candidates[0].content is None or chunk.candidates[0].content.parts is None ):
            continue
        if chunk.candidates[0].content.parts[0].inline_data and chunk.candidates[0].content.parts[0].inline_data.data:
 
            inline_data = chunk.candidates[0].content.parts[0].inline_data
            data_buffer = inline_data.data
 
            data_buffer = convert_to_wav(inline_data.data, inline_data.mime_type)
 
            return data_buffer
             
        else:
            return None