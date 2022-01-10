from django.test import TestCase
from rest_framework.test import APITestCase
# Create your tests here.
import requests

from integerations.github_.models import GithubOAuthToken
from ai_auth.models import AiUser

from api_automation.service import Service

class GithubApiTestCase(APITestCase):
    fixtures = ["fixtures.json"]

    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjQxNzU3Nzc0LCJqdGkiOiI3MmU2ZjNhYmFkYjg0Njg5ODQ3Njk5NTVjNTM0OTcwNSIsInVzZXJfaWQiOjI2fQ.eQ-3jjAI2_14Gw6mztIMYCuyXd2bSux7yymRkTTrEQk"

    # def setUp(self) -> None:
    #     self.token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjQxNzQ5Nzg0LCJqdGkiOiI5YTZjYTU4ZGUwODc0NjM2YTFiNTlhMDIyYTc5MmZmMyIsInVzZXJfaWQiOjI2fQ.IANbDs8XYMhCuB92jO_OmLMyXhJjdrka5PXwOyOG4EE"
    #     self.client.credentials(HTTP_AUTHORIZATION="Bearer "+self.token)
    # #
    #     self.client.login(email="maintnandha---@gmail.com", \
    #                       password="test-1234")
    # # def test_user(self):
    # #     self.c

    def test_git_oauth_token_api(self):
        url = "/integerations/github/"

        print(self.token)

        data= {'oauth_token': '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'}
        res = self.client.post(path=url, data=data, \
                HTTP_AUTHORIZATION="Bearer "+self.token)

        print("data---->", res.data)

        res = self.client.post(path=url, data=data, \
                HTTP_AUTHORIZATION="Bearer "+self.token)

        # print("data---->", res.data)

        self.assertTrue(res.status_code==400)

        res = self.client.get(path=url, data=data, \
                HTTP_AUTHORIZATION="Bearer "+self.token)

        detail_url = "/integerations/github/1"
        res = self.client.get(path=detail_url,  \
                HTTP_AUTHORIZATION="Bearer "+self.token)
        self.assertTrue(res.status_code == 200)
        self.assertTrue(res.data.get("username") == "Nandhakumarpro")

