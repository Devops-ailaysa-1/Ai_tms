from django.test import TestCase
from rest_framework.test import APITestCase
# Create your tests here.
import requests

from integerations.github_.models import GithubOAuthToken
from ai_auth.models import AiUser

from api_automation.service import Service

class GithubApiTestCase(APITestCase):
    fixtures = ["fixtures.json"]

    def test_username_attr(self):
        user = AiUser.objects.first()
        username_attr_exist = False
        try:
            print("username---->", user.username)
            username_attr_exist = True
        except:
            pass

        self.assertTrue(username_attr_exist)









