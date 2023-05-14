# import pytest
# import math
# from ai_tms.settings import  OPENAI_MODEL
# from ai_openai.utils import get_prompt
# import requests
# import json
# import pytest
# from pathlib import Path
# from django.urls import reverse
# from ai_staff.models import PromptStartPhrases ,PromptSubCategories , PromptTones , PromptCategories ,AiCustomize
# from rest_framework.test import APIClient
 

# import os
# print("------------>>>>",os.getcwd())
# with open(os.getcwd()+'/tests/test_aiwriter/params.json', 'r') as f:
#     params = json.load(f)

# # @pytest.mark.parametrize("params", params)
# # def test_openai_api(params):
# #     # params = list(params.keys())[0]
# #     prompt = params['prompt']
# #     model_name =OPENAI_MODEL
# #     max_token = params['max_token']
# #     n = params['n']
# #     res =  get_prompt(prompt=prompt ,model_name=model_name , max_token=max_token ,n=n )
# #     assert res != None
# #     assert isinstance(res["choices"], list)  
# #     assert len(res["choices"]) == n 
# #     assert res["choices"][0]['text'] != None 
# #     assert res["model"] == OPENAI_MODEL
# #     assert res['usage']["total_tokens"] == res["usage"]["prompt_tokens"] + res["usage"]["completion_tokens"]



# # @pytest.mark.django_db
# # def test_row_count_promptstartphrases():
# #     assert PromptStartPhrases.objects.all().nocache().count() !=  None 
    
# # @pytest.mark.django_db
# # def test_row_count_promptsubcategories():
# #     assert PromptSubCategories.objects.all().nocache().count() != None
    

# # @pytest.mark.django_db
# # def test_row_count_prompt_tones():
# #     assert PromptTones.objects.all().nocache().count() != None

# # @pytest.mark.django_db
# # def test_row_count_promptcategories():
# #      assert PromptCategories.objects.all().nocache().count() != None
     
# # @pytest.mark.django_db
# # def test_row_count_aicustomize():
# #      assert AiCustomize.objects.all().nocache().count() != None




# @pytest.mark.django_db
# def test_openai_api(api_client):
    
#     payload = {
#         'description':"description",
#         'model_gpt_name': 1,
#         'catagories':1,
#         'sub_catagories':1,
#         'source_prompt_lang':77,
#         'product_name': 'Samsung Watch',
#         'response_copies':3,
#         'keywords':'cost effective, hurry, offer',
#         'response_charecter_limit':256,
#         'get_result_in':17
# }
#     response = api_client().post('/openai/aiprompt/' , payload = payload , content_type="application/json")
    
#     print("resp--->",response.json())  
#     assert response.status_code == 200
 
 
# # @pytest.mark.django_db
# # def test_openai_api(client):
    
# #     payload = {
# #         'description':"description",
# #         'model_gpt_name': 1,
# #         'catagories':3,
# #         'sub_catagories':4,
# #         'source_prompt_lang':77,
# #         'product_name': 'Samsung Watch',
# #         'response_copies':3,
# #         'keywords':'cost effective, hurry, offer',
# #         'response_charecter_limit':256,
# #         'get_result_in':17
        
        
# #     }
    
# #     response = client.post('/openai/aiprompt/' , payload = payload , content_type="application/json")
 
# #     assert response.status_code == 200