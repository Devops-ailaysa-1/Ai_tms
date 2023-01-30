import pytest
import math
from ai_tms.settings import  OPENAI_MODEL
from ai_openai.utils import get_prompt

from ai_staff.models import PromptStartPhrases

def test_sqrt():
   num = 25
   assert math.sqrt(num) == 5
   
@pytest.mark.parametrize("prompt,model_name,max_token,n",[
    ('this is test1',OPENAI_MODEL,256,1) ,
    ('this is test2',OPENAI_MODEL,126,3) ,
    ('this is test3',OPENAI_MODEL,56,2)
    ])   
def test_openai_api(prompt,model_name,max_token,n):
    res =  get_prompt(prompt='this is test' ,model_name=model_name , max_token=max_token ,n=n )
    assert res != None
    assert isinstance(res["choices"], list)  
    assert len(res["choices"]) == n 
    assert res["choices"][0]['text'] != None 
    assert res["model"] == OPENAI_MODEL
    assert res["usage"]["prompt_tokens"] < res["usage"]["completion_tokens"]
    assert res['usage']["total_tokens"] == res["usage"]["prompt_tokens"] + res["usage"]["completion_tokens"]
    

# def test_row_count():
#     print(PromptStartPhrases.objects.all() )
#     assert PromptStartPhrases.objects.count() == pytest.approx(10, abs=1)