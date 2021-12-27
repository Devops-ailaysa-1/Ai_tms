from api_automation.base import *
# from api_automation.utils import s
import requests
from api_automation.base import *


class DocumentSetup:

    def __init__(self, service):
        self.service = service
        self.token = service.get_a_access_token()

    def get_document_data(self):
        document_url = self.service.get_a_document_url()
        url = f"{BASE_URL}{document_url}"

        payload = {}

        headers = {
            'Authorization': f'Bearer {self.token}',
        }

        response = requests.request("GET", url, headers=headers, data = payload)

        return self.service.json_dump_str_to_data(response.text)

    def run(self):
        self.get_document_data()