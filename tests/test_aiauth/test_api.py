import requests
import pytest
from ai_auth.models import AiUser
# from model_bakery import baker
import json
from rest_framework.test import APIClient

# test_base_url ="http://localhost:8087"

# pytestmark = pytest.mark.django_db

# @pytest.mark.django_db
# @pytest.mark.usefixtures('token_assign')

    # return data.get('access_token',None)


# def test_api_get():
#     url = f"{test_base_url}/auth/dj-rest-auth/login/"
#     payload={'email': 'stephenlangtest+loc45v@gmail.com',
#     'password': 'admin@1000'}
#     response = requests.request("POST", url, data=payload)


#     assert (response.status_code == 200), "Status code is not 200. Rather found : " + str(response.status_code)
#     data= response.json()
#     assert data.get('access_token',None) != None,"access token not found"

#         # if record['id'] == 4:
#         #     assert record['first_name'] == "Eve",\
#         #         "Data not matched! Expected : Eve, but found : " + str(record['first_name'])
#         #     assert record['last_name'] == "Holt",\
#         #         "Data not matched! Expected : Holt, but found : " + str(record['last_name'])


# @pytest.mark.dependency()


# def test_express_pro():
#     url = f"{test_base_url}/workspace/project/express/setup/?filter=express"
#     payload={'source_language': 17,'target_languages':77,'project_name':'Express test',
#     'mt_engine':1,'text_data':'checking the credits detucted for Express text format'}
#     response = requests.request("POST", url, data=payload)
#     assert (response.status_code == 200), "Status code is not 200. Rather found : " + str(response.status_code)
#     data= response.json()
#     assert data.get('Res',None) != None,"Response Not Found"


# @pytest.mark.usefixtures('auth_obj')
# @pytest.mark.usefixtures('dummy_user')
# @pytest.mark.django_db
# class TestAuthenticate:
#     @pytest.fixture(autouse=True)
#     def test_get_user(self):
#         endpoint = '/auth/dj-rest-auth/login/'
#         expected_json = {'email': 'stephenlangtest+loc45v@gmail.com',
#         'password': 'admin@1000'}
#         response = APIClient().post(
#             endpoint,
#             data=expected_json,
#             format='json'
#         )
#         assert response.status_code == 200


    # def test_list(self, api_client):



    #     assert response.status_code == 200
    #     assert len(json.loads(response.content)) == 3


