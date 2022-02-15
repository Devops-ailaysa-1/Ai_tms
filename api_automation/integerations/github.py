
import requests
from api_automation.base import *

class Github:


    def __init__(self, service):
        self.service = service
        self.token = service.get_a_access_token()

    def create_github_oauth_record(self):
        url = f"{BASE_URL}/integerations/github/"

        payload = {}

        print("token---->" ,self.token)

        headers = {
            'Authorization':  f'Bearer {self.token}'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        print(response.text.encode('utf8'))

        return self.service.json_dump_str_to_data(response.text)

    def get_github_oauth_records(self):
        url = f"{BASE_URL}/integerations/github/"

        payload = {}

        print("token---->" ,self.token)

        headers = {
            'Authorization':  f'Bearer {self.token}'
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        print("response---->" , response)
        return self.service.json_dump_str_to_data(response.text)

    def run(self, create=False):
        if create:
            return  self.create_github_oauth_record()
        return self.get_github_oauth_records()


