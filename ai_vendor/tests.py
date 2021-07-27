from ai_staff.models import Currencies, VendorLegalCategories
import unittest
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from django.test.client import Client
from . import views
from .models import Languages, VendorsInfo
from ai_auth.models import AiUser
import requests
from django.urls import reverse


# class VendorInfoTestCase(APITestCase):

#     def setUp(self):
#         # print("****************")
        
#         # source_Langauge = Languages.objects.create(
#         #   Language='English', language_code='en', locale_code="en", combined_code="en-US" )

#         type = VendorLegalCategories.objects.create(name="Company/Agency")
#         currency = Currencies.objects.create(currency="United States dollar")
#         native_lang = Languages.objects.create(language="English")

#         # target_Langauge = Languages.objects.create(
#         #   Language='Tamil', language_code='ta', locale_code="ta", combined_code="ta-IN" )

#         # ai_user = AiUser.objects.create(
#         #   email='ai.vendor@dispostable.com', password='@!/@y$@123' )

#         # print(Languages.objects.all())
#         # self.glossary = Glossary.objects.create(
#         #   glossary_Name='Medical', notes='NA', source_Langauge=source_Langauge,
#         #     target_Langauge=target_Langauge, user=user
#         #    )

#         self.vendor_info = VendorsInfo.objects.create(
#            type=type, currency=currency, native_lang=native_lang
#            )

#         self.BASE_URL = "http://localhost:8000/"
#         self.c = Client()
       

#     def test_get_vendor_info(self):

#         # payload={'type': 1, 'currency':144, 'native_lang':27}


        
        
       

#         # url = f'{self.BASE_URL}/vendor/vendor_info/'
#         url = f'http://localhost:8000/vendor/vendor_info/'
        
	
#         headers = {
# 		'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjI3Mjk3ODczLCJqdGkiOiJhMTcxNzk3ZDA3NTQ0NTFmYjk3MjdkYWIyNzk3MGFhNCIsInVzZXJfaWQiOjF9.Ykn358kk4vgcWviAac8ZXTJOnEZa2fvuPfSxdfeGM5g',
# 		# 'Cookie': 'csrftoken=S2ppXsmmQ109Kyi9BXw9ltfJlmAGPWM7kf5eXJzZ5S5Paymon735s0B4hRbCs33W; sessionid=3slct6l46ztaw64sbnd55zaqz51z9wk8'
# 		}
#         # response = self.c.get(url)
#         response = requests.request("PUT", url, headers=headers, data=payload)
#         self.assertEqual(200, response.status_code)


class VendorsInfoTestCase(APITestCase):

    list_url = reverse('vendor-info')    
  
    def setUp(self):
        self.user = AiUser.objects.create(  email="ilango@ailaysa.com",
                                            password = "admin@1000" )
    
    def user_authentication(self):
        pass
        
    
    # def test_vendorinfo_creation(self):
    #     self.BASE_URL = "http://localhost:8000/vendor/"
    #     data = {
    #         "type" : 1, "currency" : 2, "native_lang" : 17, "year_of_experience" : 5 
    #     }
    #     response = self.client.post(f"{self.BASE_URL}vendor_info/", data)
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_vendorinfo_list(self):
        # self.BASE_URL = "http://localhost:8000/vendor/"
        # data = {
        #     "type" : 1, "currency" : 2, "native_lang" : 17, "year_of_experience" : 5 
        # }
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
