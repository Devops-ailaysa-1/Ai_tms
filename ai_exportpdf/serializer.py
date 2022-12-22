from statistics import mode
from rest_framework import serializers
from .models import Ai_PdfUpload



class PdfFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ai_PdfUpload
        fields = "__all__"

    
    def create(self,validated_data):
        validated_data['pdf_file_name'] = str(validated_data['pdf_file'])
        validated_data['file_name'] = str(validated_data['pdf_file'])
        instance = Ai_PdfUpload.objects.create(**validated_data)
        return instance
            
# class PdfFileDownloadLinkSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Ai_PdfUpload
#         fields = ('id' , 'docx_file_urls')

class PdfFileStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ai_PdfUpload
        fields = ('id' ,'pdf_language','counter','pdf_no_of_page' ,'pdf_task_id' ,'docx_url_field','status' ,'docx_file_name','file_name', 'pdf_file_name')
 


from statistics import mode
from rest_framework import serializers
from ai_exportpdf.models import (AiPrompt ,AiPromptResult , ModelGPTName ,PromptCategories ,
                        PromptSubCategories,PromptStartPhrases , Languages,PromptTones ,TokenUsage)

from ai_openai import utils
class AiPromptSerializer(serializers.ModelSerializer):
 
    class Meta:
        model = AiPrompt
        fields = ('prompt_string','description','model_gpt_name','catagories','sub_catagories','start_phrase',
            'source_prompt_lang','Tone' ,'response_copies','product_name','keywords',
            'response_charecter_limit')

    def create(self, validated_data):
        print("validated_data--->" , validated_data)
        prompt = ''
        instance = AiPrompt.objects.create(**validated_data)
        sub_catagories = instance.sub_catagories
        start_phrase = PromptStartPhrases.objects.get(sub_category = sub_catagories)
        instance.start_phrase = start_phrase
        instance.save()
        # print("start_phrase-->" ,start_phrase.start_phrase)
        # print("sub-->" , start_phrase.sub_category.sub_category)
        # print("cat-->" , start_phrase.sub_category.category.category)
        # print("punc-->" , start_phrase.punctuation)
        # print("tone-->" , instance.Tone)
        # print("product_name-->" , instance.product_name)

        if start_phrase.sub_category.sub_category and start_phrase.sub_category.category.category:
            prompt = start_phrase.start_phrase+" "
        else: 
            print("free style prompt")

        if instance.product_name:
            prompt+=instance.product_name

        if start_phrase.punctuation:
            prompt+=start_phrase.punctuation
        print("prompt-->" ,prompt )

        openai_response =utils.get_prompt(prompt,instance.model_gpt_name , 
                                instance.response_charecter_limit ,instance.response_copies )

        generated_text = openai_response.get('choices' ,None)
        response_id =openai_response.get('id' , None)
        token_usage = openai_response.get('usage' ,None) 
        prompt_token = token_usage['prompt_tokens']
        total_tokens=token_usage['total_tokens']
        completion_tokens=token_usage['completion_tokens']
        no_of_outcome = instance.response_copies

        token_usage=TokenUsage.objects.create(user_input_token=instance.response_charecter_limit,prompt_tokens=prompt_token,
                                    total_tokens=total_tokens , completion_tokens=completion_tokens,  
                                     no_of_outcome=no_of_outcome )
        if generated_text:
            print("generated_text" , generated_text)
            text_gen_openai_array = []
            for i in generated_text:
                if i['text']:
                    text_gen_openai_array.append(i['text'].strip())
                    AiPromptResult.objects.create(prompt = instance , start_phrase= start_phrase,
                                        result_lang = instance.source_prompt_lang , response_id = response_id,
                                        token_usage=token_usage)
         
        return instance


 

class AiPromptResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiPromptResult
        fields = '__all__'

    # def create(self, validated_data):
    #     print("validated_data--->" , validated_data)
    #     return super().create(validated_data)
