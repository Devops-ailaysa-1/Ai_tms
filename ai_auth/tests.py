from django.test import TestCase
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status


# class TestRegistration(APITestCase):

#     def test_register_user(self):
#         register_data = {
#                 "email" : "testuser@ailaysa.com",
#                 "password" : "password", # checking for weak password
#                 "fullname" : "Test User",
#                 "country" : 101, 
#         }

#         response = self.client.post("auth/dj-rest-auth/registration/", register_data)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # def test_login(self):
    #     response = self.client.post(
    #             reverse("rest_login"),
    #             {
    #                 "email" : "dev3@ailaysa.com",
    #                 "password" : "admin@1000",
    #             }
    #     )
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
