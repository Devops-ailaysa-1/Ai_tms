from rest_framework.test import APITestCase
from django.contrib.auth import settings
import os 
import shutil


class BaseTestCase(APITestCase):
	def setUp(self):
		settings.MEDIA_ROOT = "./my_test_media"

	def tearDown(self):
		shutil.rmtree("./my_test_media")