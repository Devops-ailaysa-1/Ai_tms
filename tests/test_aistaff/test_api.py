import requests
import pytest
from ai_staff.models import Currencies
from ai_auth.models import AiUser
from rest_framework.test import APIClient
from ai_workspace.models import Task
# from model_bakery import baker
import json

# from rest_framework.test import APIClient

test_base_url ="http://localhost:8087"

pytestmark = pytest.mark.django_db


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


#     # def test_list(self, api_client):



#     #     assert response.status_code == 200
#     #     assert len(json.loads(response.content)) == 3





# @pytest.fixture()
# @pytest.mark.run(order=1)
# def test_api_signup(api_client):
#     endpoint = "/auth/dj-rest-auth/registration/"
#     payload={'email': 'stephenlangtest+test2@gmail.com',
#     'password': 'test@123456#','fullname':'test2','country':101}
#     # assert (response.status_code == 200), "Status code is not 200. Rather found : " + str(response.status_code)
#     response = api_client().post(
#         endpoint,
#         data=payload,
#         format='json'
#     )
#     data= response.json()
#     print("conten",response.content)
#     print("json",response.json())
#     # assert data.get('access_token',None) != None,"access token not found"
#     assert response.status_code in [201,200]
#     assert data.get('access_token',None) != None,"access token not found"
#     if data.get('access_token',None):
#         pytest.access_token = data.get('access_token')
#     assert AiUser.objects.count()==2
#     # return data.get('access_token',None)

@pytest.mark.run2
@pytest.mark.run1
@pytest.mark.django_db()
@pytest.mark.run(order=2)
class TestSignin:
    # @pytest.fixture(autouse=True)
    def test_apisignin(self,api_client):
        endpoint = "/auth/dj-rest-auth/login/"
        payload={'email': 'ailaysademo@gmail.com',
        'password': 'Ai_demo#4321'}
        # header = {'Authorization': f'Bearer {pytest.access_token}'}
        # assert (response.status_code == 200), "Status code is not 200. Rather found : " + str(response.status_code)
        #client=
        response =api_client().post(
            endpoint,
            payload,
            format='json'
        )
        data= response.json()
        print(data)
        assert response.status_code == 200
        assert data.get('access_token',None) != None,"access token not found"
        if data.get('access_token',None):
            pytest.access_token = data.get('access_token')
            pytest.refresh_token = data.get('refresh_token')

# @pytest.mark.django_db
# @pytest.mark.run(order=2)
# class TestCurrencies:
#     # @pytest.fixture(autouse=True)
#     def test_currencies(self):
#         # Currencies.objects.create(currency_code="INR",currency="INDIAN RUPEE")
#         endpoint = '/app/currencies/'
#         # expected_json = {'email': 'stephenlangtest+loc45v@gmail.com',
#         # 'password': 'admin@1000'}
#         client = APIClient()
#         client.credentials(HTTP_AUTHORIZATION='Bearer ' + pytest.access_token)
#         response = client.get(
#             endpoint
#         )
#         assert response.status_code == 200
#         print(response.json()[0])

#         assert response.json()[0]['currency_code'] == 'AED'

@pytest.mark.run1
@pytest.mark.django_db
@pytest.mark.run(order=3)
class TestCountries:
    # @pytest.fixture(autouse=True)
    def test_countries(self,api_client):
        # Currencies.objects.create(currency_code="INR",currency="INDIAN RUPEE")
        print("token",pytest.access_token)
        endpoint = '/app/countries/'
        # expected_json = {'email': 'stephenlangtest+loc45v@gmail.com',
        # 'password': 'admin@1000'}
        client = api_client()
        client.credentials(HTTP_AUTHORIZATION='Bearer '+ pytest.access_token)
        response = client.get(
            endpoint
        )
        print(response.json())
        assert response.status_code == 200
        print(response.json()[0])
        print("token",pytest.access_token)
        assert response.json()[0] != None


@pytest.mark.run1
@pytest.mark.django_db
@pytest.mark.run(order=4)
def test_mtengines(api_client):
    endpoint = '/app/mt_engines/'
    client = api_client()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {pytest.access_token}')
    response = client.get(
    endpoint
    )
    assert response.status_code == 200
    print(response.json()[0])
    #print("token",pytest.access_token)
    assert response.json()[0]['name'] == 'Google_Translate'


@pytest.mark.run2
@pytest.mark.run1
# @pytest.mark.django_db()
@pytest.mark.run(order=6)
def test_express_project(api_client,db_no_rollback):
    endpoint = '/workspace/project/express/setup/?filter=express'
    client = api_client()
    payload = {"source_language":17,"target_languages":77,"project_name":"express test","mt_engine":1,
    "text_data":"checking the credits detucted for Express text format"}
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {pytest.access_token}")
    response =client.post(
    endpoint,
    payload
    )
    assert response.status_code == 200
    print(response.content)
    print(response.json())
    assert response.json()['Res'][0]['task_id'] != None
    pytest.task_id = response.json()['Res'][0]['task_id']

    


    #print("token",pytest.access_token)
# @pytest.mark.unit
# @pytest.mark.django_db(transaction=True)
# @pytest.mark.run(order=8)
# def test_refresh_token(api_client):
#     endpoint = "/auth/dj-rest-auth/token/refresh/"
#     payload = {"refresh":pytest.refresh_token}
#     client = api_client()
#     response =client.post(
#     endpoint,
#     payload
#     )
#     assert response.status_code == 200
#     assert response.json().get('access',None) != None
#     pytest.access_token = response.json().get('access')


@pytest.mark.run1
@pytest.mark.django_db
@pytest.mark.run(order=9)
def test_get_user(api_client,db_no_rollback):
    print("task_id", pytest.task_id)
    print("access_token", pytest.access_token)
    endpoint = '/auth/dj-rest-auth/user/'
    client = api_client()
    # payload = {"task_id":pytest.task_id}
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {pytest.access_token}')
    response =client.get(
    endpoint,
    )
    print(response.content)
    print(response.json())
    assert response.status_code == 200
    # assert response.json()['Res'][0]['task_id'] != pytest.task_id



@pytest.mark.run1
@pytest.mark.django_db
@pytest.mark.run(order=10)
def test_get_segments(api_client,db_no_rollback):
    test_express_project(api_client,db_no_rollback)
    print("task_id", pytest.task_id)
    print("access_token", pytest.access_token)
    print("Task",Task.objects.all().count())
    
    print("Task",Task.objects.all().count())
    endpoint = f'/workspace/task_get_segments/?task_id={pytest.task_id}'
    # print("endpoint",endpoint)
    client = api_client()
    # payload = {"task_id":pytest.task_id}
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {pytest.access_token}')
    response =client.get(
    endpoint,
    # payload
    )
    print(response.content)
    print(response.json())
    assert response.status_code == 200
    assert response.json()['Res'][0]['task_id'] == pytest.task_id
    pytest.project_id = response.json()['Res'][0]['project_id']
    pytest.job_id = response.json()['Res'][0]['job_id']


@pytest.mark.run1
@pytest.mark.django_db
@pytest.mark.run(order=11)
def test_get_assign_info(api_client,db_no_rollback):
    test_get_segments(api_client,db_no_rollback)
    endpoint = f'/workspace/task_assign_info/?tasks={pytest.task_id}'
    
    print("Task",Task.objects.all().count())
    client = api_client()
    # payload = {"task_id":pytest.task_id}
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {pytest.access_token}')
    response =client.get(
    endpoint,
    # payload
    )
    print(response.json())
    assert response.status_code == 200



@pytest.mark.run1
@pytest.mark.django_db
@pytest.mark.run(order=12)
def test_express_save(api_client,db_no_rollback):
    test_get_assign_info(api_client,db_no_rollback)
    endpoint = "/workspace/express_save/"
    
    print("Task",Task.objects.all().count())
    payload = {"task_id":pytest.task_id,"target_text":"எக்ஸ்பிரஸ் டெக்ஸ்ட் \
                ஃபார்மேட்டிற்குக் கழிக்கப்பட்ட வரவுகளைச் சரிபார்க்கிறது"}
    client = api_client()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {pytest.access_token}')
    response =client.post(
    endpoint,
    payload
    )
    print(response.json())
    assert response.status_code == 200

@pytest.mark.run1
@pytest.mark.django_db
@pytest.mark.run(order=13)
def test_assign_project(api_client,db_no_rollback):
    test_express_save(api_client,db_no_rollback)
    endpoint = f"/workspace/assign_to/?project={pytest.project_id}&job={pytest.job_id}"
    
    print("Task",Task.objects.all().count())
    client = api_client()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {pytest.access_token}')
    response =client.get(
    endpoint
    )
    print(response.json())
    assert response.status_code == 201

# @pytest.mark.unit
# @pytest.mark.django_db()
# @pytest.mark.run(order=7)
# def test_vendor_dashboard(api_client):
#     endpoint = f'/workspace/task_get_segments/?task_id={pytest.task_id}'
#     client = api_client()


@pytest.mark.run2
# @pytest.mark.django_db
@pytest.mark.run(order=14)
def test_task_assign(api_client,db_no_rollback):
    endpoint = f"/workspace/task_assign_info/"
    test_assign_project(api_client,db_no_rollback)
    print("Task",Task.objects.all().count())
    payload = {"task":pytest.task_id,"instruction":"for editing","assign_to":514
    ,"deadline":"2022-11-30 10:30:34.89767","mtpe_rate":77.00,"mtpe_count_unit":2,
    "currency":63,"step":1}
    client = api_client()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {pytest.access_token}')
    response =client.post(
    endpoint,
    payload
    )
    print(response.json())
    assert response.status_code == 200