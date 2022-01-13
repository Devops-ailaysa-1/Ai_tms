from django.test import TestCase
from rest_framework.test import APITestCase
# Create your tests here.
import requests

from integerations.github_.models import GithubOAuthToken, Repository
from ai_auth.models import AiUser
from guardian.shortcuts import assign_perm
from guardian.models import UserObjectPermission

from unittest import skip, skipIf

from api_automation.service import Service

def get_a_token():
    return  Service.get_a_access_token(
        email="maintnandha---@gmail.com",
        pwd="test-1234"
    )

SKIP = not True

class GithubApiTestCase(APITestCase):
    fixtures = ["fixtures.json"]

    token = get_a_token()

    # def setUp(self) -> None:
    #     self.token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjQxNzQ5Nzg0LCJqdGkiOiI5YTZjYTU4ZGUwODc0NjM2YTFiNTlhMDIyYTc5MmZmMyIsInVzZXJfaWQiOjI2fQ.IANbDs8XYMhCuB92jO_OmLMyXhJjdrka5PXwOyOG4EE"
    #     self.client.credentials(HTTP_AUTHORIZATION="Bearer "+self.token)
    # #
    #     self.client.login(email="maintnandha---@gmail.com", \
    #                       password="test-1234")
    # # def test_user(self):
    # #     self.c
    @skipIf(SKIP, "temprorary fix skip" if SKIP else "not skipped")
    def test_git_oauth_token_api(self):
        url = "/integerations/github/"

        gt = GithubOAuthToken.objects.filter(oauth_token = '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',
                                          ai_user__email="maintnandha---@gmail.com").first()
        if gt:
            gt.delete()

        data= {'oauth_token': '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'}
        res = self.client.post(path=url, data=data, \
                HTTP_AUTHORIZATION="Bearer "+self.token)

        msg = res.json() if res.status_code == 400 else res.data
        self.assertTrue(res.status_code == 201, msg="response--->"+ str(msg))
        self.assertTrue(res.data.get('oauth_token')==\
                        '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')
        ### Again Inserting
        res = self.client.post(path=url, data=data, \
                HTTP_AUTHORIZATION="Bearer "+self.token)

        self.assertTrue(res.status_code == 400)
        print("error msg--->", res.json())

        gt = GithubOAuthToken.objects.filter(oauth_token =\
            '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', ai_user__email=\
            "maintnandha---@gmail.com").first()

        url = f"/integerations/github/repository/{gt.id}"

        res = self.client.get(url,HTTP_AUTHORIZATION="Bearer "+self.token)

        self.assertTrue(res.status_code == 200, msg=res.data)
        self.assertTrue(res.data.get("count")>0,
            msg="res--->"+ str(res.data.get("count"))+"repositories count "
                        "is empty or zero!!!")

        # res = self.client.post(path=url, data=data, \
        #         HTTP_AUTHORIZATION="Bearer "+self.token)
        #
        # # print("data---->", res.data)
        #
        # self.assertTrue(res.status_code==400)

        # res = self.client.get(path=url, data=data, \
        #         HTTP_AUTHORIZATION="Bearer "+self.token)
                # pk = res.data.get("id")
                #
                # detail_url = f"/integerations/github/{pk}"
                # res = self.client.get(path=detail_url,  \
                #         HTTP_AUTHORIZATION="Bearer "+self.token)
                #
                #
                #
                # self.assertTrue(res.status_code == 200,
                #                 msg="status code----> "+ str(res.status_code))
                # self.assertTrue(res.data.get("username") == "Nandhakumarpro")

    @skipIf(not SKIP, "temprorary fix skip")
    def test_run(self):
        gt = GithubOAuthToken.objects.filter(oauth_token = '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',
                                          ai_user__email="maintnandha---@gmail.com").first()

        print("gt---->", gt)

        print("count--->", GithubOAuthToken.objects.count())
        gt = GithubOAuthToken.objects.first()
        user = gt.ai_user
        print("user_email, token = ", user.email, gt.oauth_token)
        print("perm---->", user.has_perm("change_githuboauthtoken", gt))
        print("permissions count---->", UserObjectPermission.objects.count())
        print("user perm count----->", UserObjectPermission.objects.filter(user=user).count())

    #@skipIf(not SKIP, "temprorary fix skip")

class TestCasesV2(APITestCase):

    fixtures = ["fixtures.json"]
    token = get_a_token()

    def test_branch_api(self):
        repo = Repository.objects.last()
        if not repo:
            gt = GithubOAuthToken.objects.filter(oauth_token= \
                    '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', ai_user__email= \
                    "maintnandha---@gmail.com").first()

            url = f"/integerations/github/repository/{gt.id}"
            res = self.client.get(url,HTTP_AUTHORIZATION="Bearer "+self.token)
            repo = Repository.objects.last()
        repo_id = repo.id

        url = f"/integerations/github/repository/branch/{repo_id}"

        res = self.client.get(url,HTTP_AUTHORIZATION="Bearer "+self.token)

        self.assertTrue(res.status_code == 200, msg=res.data)
        self.assertTrue(res.data.get("count")>0,
            msg="res--->"+ str(res.data.get("count"))+"Branches count "
                        "is empty or zero!!!")
        print("data---->", res.data)
        print("test_branch_api passed")


