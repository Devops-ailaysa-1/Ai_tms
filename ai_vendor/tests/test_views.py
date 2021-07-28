from ai_auth.models import AiUser
from .test_setup import TestSetUp
import pdb
from ..models import AiUser, Currencies, VendorLegalCategories, VendorsInfo
import requests

class TestViews(TestSetUp):

    def test_user_login(self):
        # print("SELF SIGN UP DATA--->", self.signup_data)
        user = self.client.post(self.signup_url, self.signup_data, format="json")
        self.assertEqual(user.status_code, 201)
        # email = user.json()["email"]
        response = self.client.post(self.login_url, self.login_data, format="json")
        # pdb.set_trace()
        self.assertEqual(response.status_code, 200)

        user2 = self.client.post(self.signup_url, self.signup_data, format="json")
        print(user2.status_code)
        if user2.status_code in [200,201]:
            self.assertRaises("same user signup successful. This should be fixed...")

    def test_get_vendorsinfo(self):
        
        currency = Currencies.objects.create(currency="Euro", currency_code="EU")
        type = VendorLegalCategories.objects.create(name="Company")
        VendorsInfo.objects.create(skype="abc123", proz_link="www.proz.in", currency=currency, type=type, user_id=self.user_id)
        # response = requests.request("GET", self.vendor_info_url, headers=self.headers)
        response = self.client.get(self.vendor_info_url, headers=self.headers)
        print("GET RESPONSE--->", response.json())
        print("SKYPE-->", response.json()["skype"])
        # print("RESPONSE TYPE-->", type(response))
        if response.status_code in [200, 201, 204]:
            result = response.json()
            print("RESULT-->", result)

        if self.assertEqual(response.status_code, 200):
            self.assertIsInstance(result, list)
    
    def test_post_vendorsinfo(self):        
        data = {
                "skype":"pqr123",
                "proz_link" : "abcd.com"
        }
        response = self.client.post(self.vendor_info_url, headers=self.headers, data=data, format="json")
        print("POST RESPONSE--->", response)
        # response = requests.request("POST", self.url, headers=self.headers, data=data)
        result = response.json()
        # print("POST RESULT--->", result)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(result["skype"] , "pqr123")
        self.assertIsInstance(result, list)
    
    def test_update_vendorsinfo(self):
        pk = "1"
        data = {
            "skype":"efg123"
        }
        response = self.client.put(self.vendor_info_url + f"/{pk}", data=data, headers=self.headers, format="json")
        # response = requests.request("PUT", self.url, headers=self.headers, data=data)
        result = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(result["skype"], "efg123")