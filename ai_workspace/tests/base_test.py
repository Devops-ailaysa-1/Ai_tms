# from rest_framework.test import APITestCase
# from django.contrib.auth import settings
# import os
# import shutil


# class BaseTestCase(APITestCase):
#     def setUp(self):
#         if not os.path.exists("./my_test_media"):
#             os.mkdir("./my_test_media")
#         settings.MEDIA_ROOT = "./my_test_media"
#         self.BASE_URL = "http://localhost:8000/"

#     def tearDown(self):
#         shutil.rmtree("./my_test_media")
