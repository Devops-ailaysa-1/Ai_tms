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

#Create AiUser and email verification
@pytest.mark.django_db
@pytest.fixture
def user():
    user=AiUser.objects.create_user(email='testuser@gmail.com', password='testpassword')
    EmailAddress.objects.create(email ='testuser@gmail.com', verified = True, primary = True, user = user)
    return user

#get access token for the user
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

# @pytest.mark.django_db
# def test_logout(api_client, user, access_token):
#     api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
#     print(user,access_token)
#     url = f"{BASE_URL}auth/dj-rest-auth/logout/"
#     data = {'email': 'testuser@gmail.com', 'password': 'testpassword'}
#     response = api_client.post(url, format='json')
#     print(response.json())
#     assert response.data["detail"]=="Successfully logged out."
#     assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
def test_choicelist_post(api_client, user, access_token):
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    # # Perform a POST request with the authenticated user
    post_url = f"{BASE_URL}workspace_okapi/choicelist/"
    data = {'language': '77', 'name': 'azar',}
    response = api_client.post(post_url, data, format='multipart')
    print(response.json())
    assert response.status_code == 200
    assert response.data['language'] == 77
    assert response.data['name'] == 'azar'
