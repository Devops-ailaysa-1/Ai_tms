# from django.test import TestCase
# from rest_framework.test import APITestCase
# # Create your tests here.
# import requests

# from integerations.github_.models import GithubOAuthToken, Repository, Branch
# from ai_workspace.models import Project
# from ai_auth.models import AiUser
# from guardian.shortcuts import assign_perm
# from guardian.models import UserObjectPermission

# from unittest import skip, skipIf

# from api_automation.service import Service
# import random

# def get_a_token():
#     return  Service.get_a_access_token(
#         email="maintnandha---@gmail.com",
#         pwd="test-1234"
#     )

# SKIP = not True

# class GithubApiTestCase(
#    APITestCase
# ):

#     fixtures = ["fixtures.json"]

#     token = get_a_token()

#     # def setUp(self) -> None:
#     #     self.token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjQxNzQ5Nzg0LCJqdGkiOiI5YTZjYTU4ZGUwODc0NjM2YTFiNTlhMDIyYTc5MmZmMyIsInVzZXJfaWQiOjI2fQ.IANbDs8XYMhCuB92jO_OmLMyXhJjdrka5PXwOyOG4EE"
#     #     self.client.credentials(HTTP_AUTHORIZATION="Bearer "+self.token)
#     # #
#     #     self.client.login(email="maintnandha---@gmail.com", \
#     #                       password="test-1234")
#     # # def test_user(self):
#     # #     self.c
#     @skipIf(SKIP, "temprorary fix skip" if SKIP else "not skipped")
#     def test_git_oauth_token_api(self):
#         url = "/integerations/github/"

#         gt = GithubOAuthToken.objects.filter(oauth_token = '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',
#                                           ai_user__email="maintnandha---@gmail.com").first()
#         if gt:
#             gt.delete()

#         data= {'oauth_token': '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'}
#         res = self.client.post(path=url, data=data, \
#                 HTTP_AUTHORIZATION="Bearer "+self.token)

#         msg = res.json() if res.status_code == 400 else res.data
#         self.assertTrue(res.status_code == 201, msg="response--->"+ str(msg))
#         self.assertTrue(res.data.get('oauth_token')==\
#                         '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')
#         ### Again Inserting
#         res = self.client.post(path=url, data=data, \
#                 HTTP_AUTHORIZATION="Bearer "+self.token)

#         self.assertTrue(res.status_code == 400)
#         print("error msg--->", res.json())

#         gt = GithubOAuthToken.objects.filter(oauth_token =\
#             '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', ai_user__email=\
#             "maintnandha---@gmail.com").first()

#         url = f"/integerations/github/repository/{gt.id}"

#         res = self.client.get(url,HTTP_AUTHORIZATION="Bearer "+self.token)

#         self.assertTrue(res.status_code == 200, msg=res.data)
#         self.assertTrue(res.data.get("count")>0,
#             msg="res--->"+ str(res.data.get("count"))+"repositories count "
#                         "is empty or zero!!!")

#         # res = self.client.post(path=url, data=data, \
#         #         HTTP_AUTHORIZATION="Bearer "+self.token)
#         #
#         # # print("data---->", res.data)
#         #
#         # self.assertTrue(res.status_code==400)

#         # res = self.client.get(path=url, data=data, \
#         #         HTTP_AUTHORIZATION="Bearer "+self.token)
#                 # pk = res.data.get("id")
#                 #
#                 # detail_url = f"/integerations/github/{pk}"
#                 # res = self.client.get(path=detail_url,  \
#                 #         HTTP_AUTHORIZATION="Bearer "+self.token)
#                 #
#                 #
#                 #
#                 # self.assertTrue(res.status_code == 200,
#                 #                 msg="status code----> "+ str(res.status_code))
#                 # self.assertTrue(res.data.get("username") == "Nandhakumarpro")

#     @skipIf(not SKIP, "temprorary fix skip")
#     def test_run(self):
#         gt = GithubOAuthToken.objects.filter(oauth_token = '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',
#                                           ai_user__email="maintnandha---@gmail.com").first()

#         print("gt---->", gt)

#         print("count--->", GithubOAuthToken.objects.count())
#         gt = GithubOAuthToken.objects.first()
#         user = gt.ai_user
#         print("user_email, token = ", user.email, gt.oauth_token)
#         print("perm---->", user.has_perm("change_githuboauthtoken", gt))
#         print("permissions count---->", UserObjectPermission.objects.count())
#         print("user perm count----->", UserObjectPermission.objects.filter(user=user).count())

#     #@skipIf(not SKIP, "temprorary fix skip")

# class TestCasesV2(APITestCase):

#     fixtures = ["fixtures.json"]
#     token = get_a_token()

#     def test_branch_api(self):
#         repo = Repository.objects.last()
#         if not repo:
#             gt = GithubOAuthToken.objects.filter(oauth_token= \
#                     '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', ai_user__email= \
#                     "maintnandha---@gmail.com").first()

#             url = f"/integerations/github/repository/{gt.id}"
#             res = self.client.get(url,HTTP_AUTHORIZATION="Bearer "+self.token)
#             repo = Repository.objects.last()
#         repo_id = repo.id

#         url = f"/integerations/github/repository/branch/{repo_id}"

#         res = self.client.get(url,HTTP_AUTHORIZATION="Bearer "+self.token)

#         self.assertTrue(res.status_code == 200, msg=res.data)
#         self.assertTrue(res.data.get("count")>0,
#             msg="res--->"+ str(res.data.get("count"))+"Branches count "
#                         "is empty or zero!!!")
#         print("data---->", res.data)
#         print("test_branch_api passed")

#     def test_content_file_api(self):
#         for branch in Branch.objects.all():
#             print("branch--->", branch.id)
#         url = f"/integerations/github/repository/branch/contentfile/12"
#         res = self.client.get(url, HTTP_AUTHORIZATION="Bearer " + self.token)
#         self.assertTrue(res.status_code == 200, msg=res.data)
#         self.assertTrue(res.data.get("count")>0,
#             msg="res--->"+ str(res.data.get("count"))+"Branches count "
#                         "is empty or zero!!!")
#         print("res--->", res.data)

#         files_id = []
#         for result in res.data.get("results"):
#             if random.choice([True, False]):
#                 files_id.append(result["id"])

#         target_languages = [2,3, 4, 5]

#         data = {"localizable_ids":files_id, "project_name": "test-11", "source_language": 1,
#                 "target_languages": target_languages}

#         res = self.client.post(url, HTTP_AUTHORIZATION="Bearer " + self.token, data=data)
#         self.assertTrue(res.status_code == 200, msg="create project, file, job, task is not success!!!")
#         project_id = res.data.get("id")
#         self.assertTrue((Project.objects.get(id=project_id).tasks_count == len(files_id)* len(target_languages)),
#                         msg="created task count is not matching with requested input data!!!")

