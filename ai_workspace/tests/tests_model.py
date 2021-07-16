from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from base_test import BaseTestCase
# from management.models import AilzaUser, Project
# from management.utils import print_key_value
from django.db import models, IntegrityError
import time
import requests
from faker import Faker

fake = Faker()

# class DataProvider:

# 	def get_data_ailzauser_model(self):
# 		return {"username": fake.name(), "email": fake.email()}

# 	def user(self):
# 		return AilzaUser.objects.create(**self.get_data_ailzauser_model())

# data_provider = DataProvider()

class UnitTest(BaseTestCase):
	#////////////////// AilaysaUser Model \\\\\\\\\\\\\\\\\\\\\

	# def test_user_create(self):
	# 	data = data_provider.get_data_ailzauser_model()
	# 	count = AilzaUser.objects.count()
	# 	user = AilzaUser.objects.create(**data)
	# 	self.assertEqual(AilzaUser.objects.count(), count+1)
	# 	return user

	# def test_unique_email_create(self):
	# 	raise_error = True
	# 	data = data_provider.get_data_ailzauser_model()
	# 	count = AilzaUser.objects.count()
	# 	try:
	# 		AilzaUser.objects.create(**data)
	# 		AilzaUser.objects.create(**data)
	# 	except IntegrityError as e:
	# 		raise_error = False
	# 	if raise_error:
	# 		raise ValueError("IntegrityError not raised")

	# def test_delete_object_not_fetched_normally(self):
	# 	data = data_provider.get_data_ailzauser_model()
	# 	user = AilzaUser.objects.create(**data)
	# 	email = user.email
	# 	self.assertEqual(AilzaUser.objects.filter(email=email).count(), 1)
	# 	user.delete() 
	# 	self.assertEqual(AilzaUser.objects.filter(email=email).count(), 0)
	# 	self.assertEqual(AilzaUser.objects.dead().filter(email=email).count(), 1)
		
	# def test_user_dir_not_clashes(self):
	# 	data = data_provider.get_data_ailzauser_model()
	# 	email_data_user1 = { "email" : 'williamskirsten@hotmail.com'}
	# 	email_data_user2 = { "email" : 'williamskirsten@gmail.com'}
	# 	user1 = AilzaUser.objects.create( **{**data, **email_data_user1})
	# 	user2 = AilzaUser.objects.create( **{**data, **email_data_user2})
	# 	self.assertNotEqual(user1.allocated_dir, user2.allocated_dir)

	# # //////////////////// Project Model \\\\\\\\\\\\\\\\\\\\\\\\\\\
	# def test_user_project_create(self):
	# 	user = data_provider.user()
	# 	count = Project.objects.count()
	# 	project = Project.objects.create(**dict(ailza_user=user, project_name=fake.name()))
	# 	self.assertEqual(Project.objects.count(), count+1)

	# def test_project_dir_not_same_for_two_projects(self):
	# 	user = data_provider.user()
	# 	project_name = fake.name()
	# 	project1 = Project.objects.create(**dict(ailza_user=user, project_name=project_name))
	# 	project2 = Project.objects.create(**dict(ailza_user=user, project_name=project_name))
	# 	self.assertNotEqual(project1.project_dir_path, project2.project_dir_path)
	# 	print_key_value(['project1.project_dir_path', 'project2.project_dir_path'],[project1.project_dir_path, project2.project_dir_path])
	# # def 

	# # def tearDown(self):

	def test_project_setup(self):
		payload={'project_name': fake.name(),
		'jobs': '[{"source_language":2, "target_language":1}]'}
		files=[
		('files',('46550f2ef1962c82f264afaeaa6574d8.jpg',open('/home/stephen/Downloads/46550f2ef1962c82f264afaeaa6574d8.jpg','rb'),'image/jpeg')),
		('files',('3505715-200.png',open('/home/stephen/Downloads/3505715-200.png','rb'),'image/png'))
		]
		headers = {
		'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjI2MzQ3Mzc1LCJqdGkiOiIzMTIxNWE4MmU4YmI0ZmQ0ODBlZDI4MDBhMGY5MGNiNSIsInVzZXJfaWQiOjE0Mn0.oX7Dgz1HchlccW84ZyJQBL4I8DPn56_UHWvk-_py6Rc',
		# 'Cookie': 'csrftoken=S2ppXsmmQ109Kyi9BXw9ltfJlmAGPWM7kf5eXJzZ5S5Paymon735s0B4hRbCs33W; sessionid=3slct6l46ztaw64sbnd55zaqz51z9wk8'
		}
		url = f'{self.BASE_URL}workspace/project_setup/'
		response = requests.request("POST", url, headers=headers, data=payload, files=files)

		self.assertEqual(201, response.status_code)



