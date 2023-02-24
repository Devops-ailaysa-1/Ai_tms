# from django.test import TestCase
# from django.urls import reverse
# from rest_framework import status
# from base_test import BaseTestCase
# from ai_auth.models import AiUser
# from django.db import models, IntegrityError
# import time
# import requests
# from faker import Faker
# from django.db import connections



# fake = Faker()

# class DataProvider:
#     email = fake.email()
#     password = fake.password()
#     container = {}

#     def is_key_exist(func):
#         def decorator(self, key):
#             if key not in self.container:
#                 return func(self, key)
#             else:
#                 return self.container[key]
#         return decorator

#     @is_key_exist
#     def ai_user(self, key):
#         ai_user = AiUser()
#         ai_user.email = self.email
#         ai_user.set_password(self.password)
#         ai_user.save()
#         self.container[key] = ai_user
#         return self.container[key]
#     # def login()





# class UnitTest(BaseTestCase):
# 	#////////////////// AilaysaUser Model \\\\\\\\\\\\\\\\\\\\\


#     def test_project_setup(self):
#         data_provider = DataProvider()
#         print(data_provider.ai_user("user1"))
#         print("connections---->", [ conn.alias for conn in connections.all()] )
#         url = "http://localhost:8000/workspace/project_setup/"

#         payload = {'project_name': fake.name(),
#         'jobs': '[{"source_language":2, "target_language":1}]'}
#         files = [
#           ('files', open('TestFiles/test2.txt','rb')),
#           ('files', open('TestFiles/test1.txt','rb'))
#         ]
#         headers = {
#           'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjI2OTcyODgzLCJqdGkiOiJkNTE3MTVmM2ZlNTQ0MzE2OTI2MzZjZDgzZjM2YTRkMSIsInVzZXJfaWQiOjE0Nn0.YvP9nyFCqAfUgtlPlXOZCKbur2JFwo2Yri0rzkSsgsI',
#           'Cookie': 'sessionid=54qxoqd8zpwn340zlym6tmzdzqq6njh8; csrftoken=WME3OBUPxLWqnFZkFCbivcVk3yB3SGWFfx5ThvIijAgNKQjQ74O2XMRDDQc0m79m'
#         }

#         response = requests.request("POST", url, headers=headers, data = payload, files = files)

#         time.sleep(10)
#         self.assertEqual(201, response.status_code)
