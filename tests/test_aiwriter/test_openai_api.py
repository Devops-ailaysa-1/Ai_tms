import pytest
import math
from ai_tms.settings import  OPENAI_MODEL
from ai_openai.utils import get_prompt

import json
import pytest
from pathlib import Path
from django.urls import reverse
from ai_staff.models import PromptStartPhrases ,PromptSubCategories , PromptTones , PromptCategories

 
@pytest.mark.parametrize("prompt,model_name,max_token,n",[
    ('A Girl Like the Moon',OPENAI_MODEL,256,1) ,
    ('The Moon as a Face',OPENAI_MODEL,126,3) ,
    ('A dance to the music',OPENAI_MODEL,56,2)
    ])   
def test_openai_api(prompt,model_name,max_token,n):
    res =  get_prompt(prompt=prompt ,model_name=model_name , max_token=max_token ,n=n )
    assert res != None
    assert isinstance(res["choices"], list)  
    assert len(res["choices"]) == n 
    assert res["choices"][0]['text'] != None 
    assert res["model"] == OPENAI_MODEL
    assert res['usage']["total_tokens"] == res["usage"]["prompt_tokens"] + res["usage"]["completion_tokens"]



 

@pytest.fixture
def json_data(datadir):
    file_path = datadir / "prompt_start_phrases.json"
    with open(file_path, "r") as f:
        return json.load(f)

@pytest.fixture
def load_data_to_db(json_data, django_db_reset_sequences):
    for item in json_data:
        PromptStartPhrases.objects.create(**item)




@pytest.mark.django_db
def test_row_count_promptstartphrases():
    assert PromptStartPhrases.objects.all().nocache().count() ==  58 
    
@pytest.mark.django_db
def test_row_count_promptsubcategories():
    assert PromptSubCategories.objects.all().nocache().count() == 59
    

@pytest.mark.django_db
def test_row_count_prompt_tones():
    assert PromptTones.objects.all().nocache().count() == 4

@pytest.mark.django_db
def test_row_count_promptcategories():
     assert PromptCategories.objects.all().nocache().count() == 9
     


    
    