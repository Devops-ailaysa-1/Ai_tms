import requests
import pytest
from ai_auth.models import AiUser
# from model_bakery import baker
import json
from rest_framework.test import APIClient
from ai_auth.models import CampaignUsers

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




def rm_none_keys(kwargs):
    # for key in list(kwargs.keys()):
    #     if kwargs[key] is None:
    #         del kwargs[key]

    return {k: v for k, v in kwargs.items() if v is not None}



@pytest.mark.django_db
class TestSignup:
    # @pytest.fixture(autouse=True)
    # @pytest.mark.parametrize("input,status", [(("stephenlangtest+22@gmail.com","#1223&22","stephentest22",
    #                                         101,None,None,None),201),
    #                             (("stephenlangtest+23@gmail.com","#1223&23","stephentest23",
    #                                         101,None,None,None),201)])
    def test_signup(self,signup_test_data): 
        endpoint = '/auth/dj-rest-auth/registration/'
        print("signuptestdata",signup_test_data)
        input = signup_test_data[0]
        status = signup_test_data[1]
        kwargs = {
            "email":input[0],
            "password":input[1],
            "fullname":input[2],
            "country":input[3],
            "campaign":input[4],
            "source_language":input[5],
            "target_language":input[6]
            }
        data = rm_none_keys(kwargs)
        # expected_json = {'email': 'stephenlangtest+loc45v@gmail.com',
        # 'password': 'admin@1000'}
        response = APIClient().post(
            endpoint,
            data=data,
            format='json'
        )
        res_data= response.json()

        print("respons data",res_data)
        assert response.status_code == status
        assert res_data.get('access_token',None) != None,"access token not found"
        assert res_data.get('user',None) != None ,"user not returned"
        if res_data.get('user',None):
            assert res_data.get('user').get('country') == kwargs.get('country')
            assert res_data.get('user').get('fullname') == kwargs.get('fullname')
            assert res_data.get('user').get('email') == kwargs.get('email')

        if data.get('source_language'):
            assert res_data.get('user').get('is_vendor') == True
        
        if data.get('campaign'):
            camp_users = CampaignUsers.objects.filter(user__email =input[0])
            assert  camp_users.count()>0,"camp_users not created"



           


@pytest.mark.django_db
class TestSignin:
    # @pytest.fixture(autouse=True)
    # @pytest.mark.parametrize("input,status", [(("stephenlangtest+22@gmail.com","#1223&22","stephentest22",
    #                                         101,None,None,None),201),
    #                             (("stephenlangtest+23@gmail.com","#1223&23","stephentest23",
    #                                         101,None,None,None),201)])
    def test_signin(self,signin_test_data): 
        endpoint = "/auth/dj-rest-auth/login/"

        print("signintestdata",signin_test_data)
        input = signin_test_data[0]
        status = signin_test_data[1]
        kwargs = {
            "email":input[0],
            "password":input[1]
            }
        data = rm_none_keys(kwargs)
        # expected_json = {'email': 'stephenlangtest+loc45v@gmail.com',
        # 'password': 'admin@1000'}
        response = APIClient().post(
            endpoint,
            data=data,
            format='json'
        )
        res_data= response.json()

        print("respons data",res_data)
        assert res_data.get("access_token",None) != None
        assert res_data.get("user",None) != None
        assert response.status_code == status
        user_keys = ['pk', 'deactivate', 'is_internal_member', 
                  'is_vendor', 'email', 'fullname', 'country']

        if res_data.get("user",None) != None:
            user_d =  res_data.get("user")
            for i in user_keys:
                assert user_d.res_data.get(i,None) != None
                


        # assert res_data.get('access_token',None) != None,"access token not found"
        # assert res_data.get('user',None) != None ,"user not returned"
        # if res_data.get('user',None):
        #     assert res_data.get('user').get('country') == kwargs.get('country')
        #     assert res_data.get('user').get('fullname') == kwargs.get('fullname')
        #     assert res_data.get('user').get('email') == kwargs.get('email')

        # if data.get('source_language'):
        #     assert res_data.get('user').get('is_vendor') == True
        
        # if data.get('campaign'):
        #     camp_users = CampaignUsers.objects.filter(user__email =input[0])
        #     assert  camp_users.count()>0,"camp_users not created"



# class TestSignin:
#     # @pytest.fixture(autouse=True)
#     def test_apisignin(self,api_client):
#         endpoint = "/auth/dj-rest-auth/login/"
#         payload={'email': 'ailaysademo@gmail.com',
#         'password': 'Ai_demo#4321'}
#         # header = {'Authorization': f'Bearer {pytest.access_token}'}
#         # assert (response.status_code == 200), "Status code is not 200. Rather found : " + str(response.status_code)
#         #client=
#         response =api_client().post(
#             endpoint,
#             payload,
#             format='json'
#         )
#         data= response.json()
#         assert response.status_code == 200
#         assert data.get('access_token',None) != None,"access token not found"
#         if data.get('access_token',None):
#             pytest.access_token = data.get('access_token')
#             pytest.refresh_token = data.get('refresh_token')
