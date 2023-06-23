from django.test import TestCase
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
import pytest
from ai_auth.models import AiUser
from allauth.account.models import EmailAddress
# from Accounts.models import Email addresses

from  rest_framework.test import APIClient


client = APIClient()

# @pytest.mark.django_db
# def test_sample():
#     # in_word=request.POST.get('source',None)
#     # edited_word=request.POST.get('edited',None)
#     data={'source':'this','edited':'that'}
#     response = client.post("/workspace_okapi/selflearn/3554/",data)
#     assert response.status_code == 201


@pytest.fixture()
@pytest.mark.django_db
def user_token():
    user=client.post("/auth/dj-rest-auth/registration/",{'email':'azar52@gmail.com', 'password':'test@1000','fullname':'azar','country':101})
    email=AiUser.objects.get(email='azar52@gmail.com')
    print(email,email.id)
    em=EmailAddress.objects.get(email ='azar52@gmail.com', user =email)
    em.verified=True
    em.save()
    print(em,'============')
    log=client.post("/auth/dj-rest-auth/login/",{'email':'azar52@gmail.com', 'password':'test@1000'})
    print(log.json())
    response=log.json()
    # response = client.post("/workspace_okapi/selflearn/",HTTP_AUTHORIZATION=f"Token {user_token}")
    # assert log.status_code == 200
    return response['access_token']

# @pytest.mark.django_db
# def test_user(client):
#     user=client.post("/auth/dj-rest-auth/registration/",{'email':'azar52@gmail.com', 'password':'test@1000','fullname':'azar','country':101})
#     email=AiUser.objects.get(email='azar52@gmail.com')
#     print(email,email.id)
#     em=EmailAddress.objects.get(email ='azar52@gmail.com', user =email)
#     em.verified=True
#     em.save()
#     print(em,'============')
#     log=client.post("/auth/dj-rest-auth/login/",{'email':'azar52@gmail.com', 'password':'test@1000'})
#     print(log.json())
#     response=log.json()
#     # response = client.post("/workspace_okapi/selflearn/",HTTP_AUTHORIZATION=f"Token {user_token}")
#     assert log.status_code == 200
#     return response['access_token']
# from  django.test.Client import admin_client




import pytest

@pytest.mark.django_db
def test_self_learn_list(admin_client,user_token):
    print(user_token)
    email=AiUser.objects.get(email='azar52@gmail.com')
    print('==============',email,email.id)
    
    # self=client.get('/workspace_okapi/selflearn/',HTTP_AUTHORIZATION=f'Bearer {user_token}')
    self=admin_client.get('/workspace_okapi/selflearn/',HTTP_AUTHORIZATION=f'Bearer {user_token}')
    # print(self.json())
    HTTP_AUTHORIZATION=f'Bearer {user_token}'
    print(HTTP_AUTHORIZATION)
    print(self)
    assert self.status_code==200



# @pytest.mark.django_db
# def test_self_learn_create(admin_client,user_token):
#     print(user_token)
#     email=AiUser.objects.get(email='azar52@gmail.com')
#     print('==============',email,email.id)
#     data={'source':'this','edited':'that'}
#     self=client.post('/workspace_okapi/selflearn/3555/',data,HTTP_AUTHORIZATION=f'Bearer {user_token}')
#     # self=admin_client.get('/workspace_okapi/selflearn/')
#     # print(self.json())
#     HTTP_AUTHORIZATION=f'Bearer {user_token}'
#     print(HTTP_AUTHORIZATION)
#     print(self)
#     assert self.status_code==200

















"""
# CREATE PROJECT
from ai_workspace.models import ProjectSteps

@pytest.mark.django_db
@pytest.mark.run()
def test_createproject(admin_client,user_token):
    path='tests/files/test-en.txt'
    data={
        'source_language':77,
        'target_languages':17,
        'project_name':"test_project",
        "files":path,
        "mt_engine":1
    }
    project=ProjectSteps.objects.create(project='new',steps="new1")
    print('user token',user_token)
    create=client.post('/workspace/project/quick/setup/',data,HTTP_AUTHORIZATION=f'Bearer {user_token}')

    print(create.json())
    assert create.status_code==201

"""
