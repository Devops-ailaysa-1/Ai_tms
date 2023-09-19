from tests import load_files,get_test_file,get_test_file_path
import pytest,os
from django.core.files.uploadedfile import SimpleUploadedFile
from pathlib import Path

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


# @pytest.mark.run2
@pytest.mark.perm1
@pytest.mark.django_db()
@pytest.mark.run(order=6)

def test_create_project(api_client):
    endpoint = '/workspace/project/quick/setup/'
    client = api_client()
    #file = get_test_file_path("test-en.txt")
    # tmp_file = SimpleUploadedFile(
    #                 "file.jpg", "file_content", content_type="image/jpg")
    payload = {"source_language":17,"target_languages":77,"project_name":"express test","mt_engine":1,
    "files":('test-en.txt', open('tests/files/test-en.txt', 'rb'))}
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {pytest.access_token}")

    response =client.post(
    endpoint,
    payload,
    )
    assert response.status_code == 201
    print(response.content)
    print(response.json())
    # assert response.json()['Res'][0]['task_id'] != None
    # pytest.task_id = response.json()['Res'][0]['task_id']