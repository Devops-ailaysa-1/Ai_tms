# from ai_auth.models import AiUser
# from rest_framework.test import APITestCase
# from django.urls import reverse
# from faker import Faker
# import pdb
# import requests


# class TestSetUp(APITestCase):

#     def setUp(self):
#         self.base_url = f"http://localhost:8000"
#         # self.signup_url = reverse('/rest_register')
#         # self.login_url = reverse('/auth/dj-rest-auth/login/')
#         self.signup_url = self.base_url + "/auth/dj-rest-auth/registration/"
#         self.login_url = self.base_url + "/auth/dj-rest-auth/login/"
#         self.vendor_info_url = self.base_url + reverse('vendor-info')
#         # print("vendor url--->", self.vendor_info_url)

#         self.fake = Faker()
#         email = self.fake.email()
#         password =  self.fake.password()
#         self.signup_data = {
#                 "email": email,
#                 "password": password,
#                 "fullname" : self.fake.name()
#         }
#         self.login_data = {
#                 "email" : email,
#                 "password" : password,                
#         }

#         res = self.client.post(self.signup_url, self.signup_data, format="json")
#         self.user_id =  res.json()["user"]["pk"]
#         print("USER ID--->", self.user_id)
#         login = self.client.post(self.login_url, data = self.login_data, format="json")

#         content = login.json()
#         access_token = content.get("access_token")
#         self.headers = {
# 		'Authorization': f'Bearer {access_token}',
# # 		# 'Cookie': 'csrftoken=S2ppXsmmQ109Kyi9BXw9ltfJlmAGPWM7kf5eXJzZ5S5Paymon735s0B4hRbCs33W; sessionid=3slct6l46ztaw64sbnd55zaqz51z9wk8'
# 		}
#         # print("TOKEN-->", self.headers)

#         # pdb.set_trace()
#         return super().setUp()
    
#     def tearDown(self):
#         return super().tearDown()