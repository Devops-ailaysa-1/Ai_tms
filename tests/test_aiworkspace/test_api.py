from tests import load_files,get_test_file,get_test_file_path
import pytest,os
from django.core.files.uploadedfile import SimpleUploadedFile
from pathlib import Path
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import AccessToken
from ai_auth.models import AiUser
from allauth.account.models import EmailAddress


BASE_URL="http://localhost:8083/"


# @pytest.mark.run1
# @pytest.mark.django_db
# @pytest.mark.run(order=12)
# def test_express_save(api_client,db_no_rollback):
#     test_get_assign_info(api_client,db_no_rollback)
#     endpoint = "/workspace/project/quick/setup/"
    
#     # with open("test/files/",'r') as f:
#     load_files()

#     # payload = {"source_language":17,"target_languages":77 \
#     #             "project_name":"File sample"}
#     # files= 
    
#     client = api_client()
#     client.credentials(HTTP_AUTHORIZATION=f'Bearer {pytest.access_token}')
#     response =client.post(
#     endpoint,
#     payload,
#     format='multipart'
#     )
#     print(response.json())
#     assert response.status_code == 200


# # @pytest.mark.run2
# @pytest.mark.perm1
# @pytest.mark.django_db()
# @pytest.mark.run(order=6)

# def test_create_project(api_client):
#     endpoint = '/workspace/project/quick/setup/'
#     client = api_client()
#     #file = get_test_file_path("test-en.txt")
#     # tmp_file = SimpleUploadedFile(
#     #                 "file.jpg", "file_content", content_type="image/jpg")
#     payload = {"source_language":17,"target_languages":77,"project_name":"express test","mt_engine":1,
#     "files":('test-en.txt', open('tests/files/test-en.txt', 'rb'))}
#     client.credentials(HTTP_AUTHORIZATION=f"Bearer {pytest.access_token}")

#     response =client.post(
#     endpoint,
#     payload,
#     )
#     assert response.status_code == 201
#     print(response.content)
#     print(response.json())
#     # assert response.json()['Res'][0]['task_id'] != None
#     # pytest.task_id = response.json()['Res'][0]['task_id']


# create a API client

# @pytest.fixture
# def api_client():
#     return APIClient()

# Create AiUser and email verification
# @pytest.mark.django_db
# @pytest.fixture
# def user():
#     user=AiUser.objects.create_user(email='testuser@gmail.com', password='testpassword')
#     EmailAddress.objects.create(email ='testuser@gmail.com', verified = True, primary = True, user = user)
#     return user

# get access token for the user
# @pytest.fixture
# @pytest.mark.django_db
# def access_token(user):
#     return AccessToken.for_user(user)

# # create using Api endpoints
# @pytest.mark.django_db
# def test_create_user(api_client):
#     url=f"{BASE_URL}auth/dj-rest-auth/registration/"
#     data={"email":'testuser@gmail.com',"password":'testpassword',"password2":'testpassword','fullname':"TEST","country":101,"source_language":17,"target_language":77}
#     response = api_client.post(url, data, format='json')
#     # print(response.json())
#     assert response.status_code == status.HTTP_201_CREATED
#     assert response.data["user"]["email"]=='testuser@gmail.com'
#     assert 'access_token' in response.data
#     assert response.data["access_token"]!=None

# user login
# @pytest.mark.django_db
# def test_login(api_client, user, access_token):
#     # Login and get an access token
#     print(user,access_token)
#     login_url = f"{BASE_URL}auth/dj-rest-auth/login/"
#     data = {'email': 'testuser@gmail.com', 'password': 'testpassword'}
#     response = api_client.post(login_url, data, format='json')
#     print(response.json())
#     # check the access token 
#     assert 'access_token' in response.data
#     assert response.status_code == status.HTTP_200_OK

# @pytest.mark.django_db
# def test_get_user(api_client,access_token,user):
#     api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
#     url=f"{BASE_URL}auth/dj-rest-auth/user/"
#     response=api_client.get(url,format='json')
#     # print(response.json())
#     assert response.status_code == 200
#     assert response.data["email"]==user.email

# @pytest.mark.django_db
# def test_logout(api_client, user, access_token):
#     api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
#     print(user,access_token)
#     url = f"{BASE_URL}auth/dj-rest-auth/logout/"
#     data = {'email': 'testuser@gmail.com', 'password': 'testpassword'}
#     response = api_client.post(url, format='json')
#     # print(response.json())
#     assert response.data["detail"]=="Successfully logged out."
#     assert response.status_code == status.HTTP_200_OK

# @pytest.fixture(scope='function')
# @pytest.mark.django_db
# def setup_database():
#     # Replace with logic to set up initial database data for each test
#     api_client= APIClient()
#     url=f"{BASE_URL}auth/dj-rest-auth/registration/"
#     data={"email":'testuser@gmail.com',"password":'testpassword',"password2":'testpassword','fullname':"TEST","country":101,"source_language":17,"target_language":77}
#     response = api_client.post(url, data, format='json')
#     api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access_token"]}')
#     yield


@pytest.fixture
def api_client():
    user=AiUser.objects.get(id=1)
    access_token=AccessToken.for_user(user)
    api_client= APIClient()
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    yield api_client


# @pytest.fixture(autouse=True)
# # @pytest.mark.django_db
# def api_client():
#     api_client= APIClient()
#     url=f"{BASE_URL}auth/dj-rest-auth/registration/"
#     data={"email":'testuser@gmail.com',"password":'testpassword',"password2":'testpassword','fullname':"TEST","country":101,"source_language":17,"target_language":77}
#     response = api_client.post(url, data, format='json')
#     api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access_token"]}')
#     yield api_client
#     # print ("log_out")
#     # return api_client

# choice_list_module TestCase
@pytest.mark.django_db(transaction=True)
def test_choicelist(api_client):
    # # Perform a POST request with the authenticated user
    # api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    end_point=  f"{BASE_URL}workspace_okapi/choicelist/"

    # post
    data = {'language': '77', 'name': 'azar',}
    response = api_client.post(end_point, data, format='multipart')
    print(response.json())
    assert response.status_code == 200
    assert response.data['language'] == 77
    assert response.data['name'] == 'azar'

    data = {'language': '77', 'name': 'azar_05',}
    response = api_client.post(end_point, data, format='multipart')
    print(response.json())
    assert response.status_code == 200

    #get_list
    get_response=api_client.get(end_point,format="json")
    print(get_response.json())
    assert get_response.status_code==200
    assert len(get_response.data["results"])==2
    pk=get_response.data["results"][0]["id"]
    print(pk)
    
    # put method
    data={"name":"azar_01"}
    put_response=api_client.put(f"{end_point}{pk}/",data)
    print(put_response.json(),"********************")
    assert put_response.status_code == 200

    # retrive method
    get_response=api_client.get(f"{end_point}{pk}/")
    print(get_response.json())
    assert get_response.status_code==200
    assert get_response.data['name'] == 'azar_01'

    #delete method
    del_response=api_client.delete(f"{end_point}{pk}/")
    del_response.status_code==204
    get_response=api_client.get(end_point,format="json")
    print(get_response)
    assert pk not in [i['id'] for i in get_response.data["results"]]


# self_learning_module TestCase

@pytest.fixture
# @pytest.mark.django_db
def choice_list_id(api_client):
    url=f"{BASE_URL}workspace_okapi/choicelist/"
    data = {'language': '77', 'name': 'azar',}
    response = api_client.post(url, data, format='multipart')
    print(response.json())
    get_response=api_client.get(url,format="json")
    print(get_response.json())
    pk=get_response.data["results"][0]["id"]
    print(pk)
    yield response.data["id"]
    print('destroy')
    # return response.data["id"]

data=[{"source_word":"apple","edited_word":"app"},{"source_word":"apple","edited_word":"apply"}]
@pytest.mark.parametrize("data,status",[(data[0], 200), (data[1], 200)])
@pytest.mark.django_db
def test_selflearn(api_client,choice_list_id,data,status):
    end_point=  f"{BASE_URL}workspace_okapi/selflearn/"
    # data={"source_word":"apple","edited_word":"app","choice_list_id":choice_list_id}
    #  create selflearn asset
    data["choice_list_id"]=choice_list_id
    res=api_client.post(end_point,data,format='multipart')
    print(res.data["choice_list"])
    assert res.data["choice_list"] == choice_list_id
    assert res.data["source_word"]==data["source_word"]
    assert res.status_code==status

    # get list
    get_response=api_client.get(end_point)
    print(get_response.json())
    assert len(get_response.data["results"])>0
    assert get_response.status_code==200
    pk=get_response.data["results"][0]["id"]

    # update
    data={"edited_word":"application"}
    upd_response=api_client.put(f"{end_point}{pk}/",data)
    assert upd_response.status_code==200
    assert upd_response.data['id']==pk and upd_response.data['edited_word']==data["edited_word"]

    # delete
    del_response=api_client.delete(f"{end_point}{pk}/")
    del_response.status_code==204
    get_response=api_client.get(end_point,format="json")
    print(get_response)
    assert pk not in [i['id'] for i in get_response.data["results"]]


import json
@pytest.fixture
def test_data():
    with open('fixtures/SelflearningAsset.json') as f:
        data = json.load(f)
    return data

@pytest.fixture
def get_choicelist():
    with open('fixtures/ChoiceLists.json') as f:
        data = json.load(f)
    return data

@pytest.mark.django_db
def test_choice(api_client,get_choicelist):
    print(get_choicelist)
    end_point=  f"{BASE_URL}workspace_okapi/choicelist/1/"
    get_response=api_client.get(end_point,format="json")
    print("-----------",get_response.json())
    # assert get_choicelist[0]["fields"]==get_response.json()
    assert get_response.status_code==200

@pytest.mark.django_db
def test_putchoice(api_client,get_choicelist):
    print(get_choicelist)
    data={"name":"azar"}
    end_point=  f"{BASE_URL}workspace_okapi/choicelist/1/"   
    get_response=api_client.put(end_point,data)
    print("-----------",get_response.json())
    assert get_choicelist[0]["fields"]["name"]!=get_response.data["name"]
    assert get_response.status_code==200

@pytest.mark.django_db
def test_get_items(api_client, test_data):
    items = test_data
    end_point=  f"{BASE_URL}workspace_okapi/selflearn/"
    response = api_client.get(end_point)
    assert response.status_code == 200

data=[{"source_word":"apple","edited_word":"app"},{"source_word":"apple","edited_word":"apply"}]
@pytest.mark.django_db
@pytest.mark.parametrize("data,status",[(data[0], 200), (data[1], 200)])
def test_post_item(api_client, test_data,data,status,choice_list_id):
    end_point=  f"{BASE_URL}workspace_okapi/selflearn/"
    data["choice_list_id"]=choice_list_id
    response = api_client.post(end_point, json=data)
    assert response.status_code == status



# choicelistselected

@pytest.mark.django_db
def test_choicelistselected(api_client):
    endpoint=f"{BASE_URL}workspace_okapi/choicelistselected/"
    query_params={"project":5478}
    response=api_client.get(endpoint+"?project=5478")
    assert response.status_code==200
    print(response.data)