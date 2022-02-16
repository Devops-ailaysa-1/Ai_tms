import requests
from api_automation.base import *
from api_automation.base_utils import BaseUtils

import requests
import json


class AccountSetup(BaseUtils):

    token = ''

    def __init__(self, email=None, pwd=None):
        self.USER_EMAIL = email if email else USER_EMAIL
        self.USER_PASSWORD = pwd if pwd else USER_PASSWORD

    def run(self):
        self.login()

    def signup(self):
        url = f"{BASE_URL}/auth/dj-rest-auth/registration/"

        payload = {'email': USER_EMAIL,
                   'password': USER_PASSWORD,
                   'fullname': USER_FULLNAME,
                   'country': COUNTRY}

        headers, files = {}, []

        response = requests.request("POST", url, headers=headers,
                                    data=payload, files=files)

        self.token = self.get_key_from_data(response.text, "access_token")

    def login(self):

        url = f"{BASE_URL}/auth/dj-rest-auth/login/"

        payload = {'email': self.USER_EMAIL,
            'password': self.USER_PASSWORD }

        print("payload----->", payload)

        headers, files = {}, []

        response = requests.request("POST", url, headers=headers,
            data=payload, files=files)



        data = json.loads(response.text)

        print("data---->", data)

        self.token = data["access_token"]

if __name__ == "__main__":
    account_setup = AccountSetup()
    account_setup.run()

