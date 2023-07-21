from tests import load_files,get_test_file,get_test_file_path
import pytest,os
from django.core.files.uploadedfile import SimpleUploadedFile
from pathlib import Path
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

from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import AccessToken
from django.urls import reverse
import pytest
from ai_auth.models import AiUser
from allauth.account.models import EmailAddress


# create a API client

@pytest.fixture
def api_client():
    return APIClient()

# Create AiUser and email verification
@pytest.mark.django_db
@pytest.fixture
def user():
    user=AiUser.objects.create_user(email='testuser@gmail.com', password='testpassword')
    EmailAddress.objects.create(email ='testuser@gmail.com', verified = True, primary = True, user = user)
    return user

# get access token for the user
@pytest.fixture
@pytest.mark.django_db
def access_token(user):
    return AccessToken.for_user(user)

# create using Api endpoints
@pytest.mark.django_db
def test_create_user(api_client):
    url=f"{BASE_URL}auth/dj-rest-auth/registration/"
    data={"email":'testuser@gmail.com',"password":'testpassword',"password2":'testpassword','fullname':"TEST","country":101,"source_language":17,"target_language":77}
    response = api_client.post(url, data, format='json')
    print(response.json())
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["user"]["email"]=='testuser@gmail.com'
    assert 'access_token' in response.data
    assert response.data["access_token"]!=None

# user login
@pytest.mark.django_db
def test_login(api_client, user, access_token):
    # Login and get an access token
    print(user,access_token)
    login_url = f"{BASE_URL}auth/dj-rest-auth/login/"
    data = {'email': 'testuser@gmail.com', 'password': 'testpassword'}
    response = api_client.post(login_url, data, format='json')
    print(response.json())
    # check the access token 
    assert 'access_token' in response.data
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_get_user(api_client,access_token,user):
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    url=f"{BASE_URL}auth/dj-rest-auth/user/"
    response=api_client.get(url,format='json')
    print(response.json())
    assert response.status_code == 200
    assert response.data["email"]==user.email

@pytest.mark.django_db
def test_logout(api_client, user, access_token):
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    print(user,access_token)
    url = f"{BASE_URL}auth/dj-rest-auth/logout/"
    data = {'email': 'testuser@gmail.com', 'password': 'testpassword'}
    response = api_client.post(url, format='json')
    print(response.json())
    assert response.data["detail"]=="Successfully logged out."
    assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_choicelist_create(api_client, user, access_token):
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    # # Perform a POST request with the authenticated user
    post_url = f"{BASE_URL}workspace_okapi/choicelist/"
    data = {'language': '77', 'name': 'azar',}
    response = api_client.post(post_url, data, format='multipart')
    print(response.json())
    assert response.status_code == 200
    assert response.data['language'] == 77
    assert response.data['name'] == 'azar'

    data = {'language': '77', 'name': 'azar_05',}
    response = api_client.post(post_url, data, format='multipart')
    print(response.json())
    assert response.status_code == 200


    get_response=api_client.get(f"{BASE_URL}workspace_okapi/choicelist/",format="json")
    print(get_response.json())
    assert get_response.status_code==200
    # assert len(get_response.data["results"])==2

    
    pk=get_response.data["results"][0]["id"]
    print(pk)

    data={"name":"azar_01"}
    put_response=api_client.put(f"{BASE_URL}workspace_okapi/choicelist/{pk}/",data)
    print(put_response.json(),"********************")
    print(pk)
    get_response=api_client.get(f"{BASE_URL}workspace_okapi/choicelist/{pk}/",format="json")
    print(get_response.json())
    assert put_response.status_code == 200
    assert get_response.data['name'] == 'azar_01'

# @pytest.fixture(scope="session")
# @pytest.mark.django_db
# def access_token():
#     api_client=APIClient()
#     url=f"{BASE_URL}auth/dj-rest-auth/registration/"
#     data={"email":'testuser@gmail.com',"password":'testpassword',"password2":'testpassword','fullname':"TEST","country":101,"source_language":17,"target_language":77}
#     sign_up = api_client.post(url, data, format='json')
#     login_url = f"{BASE_URL}auth/dj-rest-auth/login/"
#     data = {'email': 'testuser@gmail.com', 'password': 'testpassword'}
#     response = api_client.post(login_url, data, format='json')
#     access_token=response.data['access_token']
#     # print(access_token)
#     return access_token

# # @pytest.fixture(scope='session')
# # def setup_choicelist(api_client,access_token):
# #         token = access_token
# #         api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
# #         url = f"{BASE_URL}"  # Replace 'endpoint' with the actual endpoint URL you want to test
# #         data = {'language': '77', 'name': 'azar',} # Replace with the data you want to send in the request
# #         response = api_client.post(url, data)
# #         print(response.json())
# #         pk=response.data['id']
# #         return pk
        

# import pytest
# from rest_framework.test import APIClient

# # @pytest.mark.django_db
# class TestChoiceList:
#     API_BASE_URL = f"{BASE_URL}workspace_okapi/choicelist/" 
   
#     # def __init__(self):
#     #     self.pk= None

#     @pytest.fixture
#     def api_client(self,access_token):
#         token = access_token
#         api_client=APIClient()
#         api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
#         return api_client
#         # return APIClient()
#     # @pytest.fixture    
#     # def setup_choicelist(api_client,access_token):
#     #     token = access_token
#     #     api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
#     #     url = f"{BASE_URL}"  # Replace 'endpoint' with the actual endpoint URL you want to test
#     #     data = {'language': '77', 'name': 'azar',} # Replace with the data you want to send in the request
#     #     response = api_client.post(url, data)
#     #     print(response.json())
#     #     pk=response.data['id']
#     #     return pk
     
#     @pytest.mark.first
#     @pytest.mark.django_db
#     def test_post_endpoint(self, api_client):
#         url = f"{self.API_BASE_URL}"  # Replace 'endpoint' with the actual endpoint URL you want to test
#         data = {'language': '77', 'name': 'azar',} # Replace with the data you want to send in the request
#         response = api_client.post(url, data)
#         print(response.json())
#         self.pk=response.data['id']
#         assert response.status_code == 200
#         # Add more assertions to verify the response content if needed

#     # @pytest.mark.django_db
#     def test_get_endpoint(self, api_client):
#         # api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
#         get_response=api_client.get(f"{BASE_URL}workspace_okapi/choicelist/",format="json")
#         print(get_response.json(),"*******************")
#         assert get_response.status_code==200
#         assert len(get_response.data["results"])==1
    
#     # @pytest.mark.django_db
#     def test_put_endpoint(self, api_client,setup_choicelist):
#         pk=setup_choicelist
#         print(self.pk,"---------------------")
#         url = f"{self.API_BASE_URL}/{pk}"  # Replace 'endpoint' with the actual endpoint URL you want to test
#         data = {'name': 'azar_01',} # Replace with the data you want to send in the request
#         response = api_client.put(url, data)
#         assert response.status_code == 200
#         # Add more assertions to verify the response content if needed
#     # @pytest.mark.django_db
#     def test_delete_endpoint(self, api_client,setup_choicelist):
#         pk=setup_choicelist
#         url = f"{self.API_BASE_URL}/{pk}"  # Replace 'endpoint' with the actual endpoint URL you want to test
#         response = api_client.delete(url)
#         assert response.status_code == 204
#         # Add more assertions to verify the response content if needed

    # ... Add more test cases as needed
















