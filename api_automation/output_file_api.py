from api_automation.base import *
# from api_automation.utils import s
import requests
from api_automation.base import *


class OutputFile:

    def __init__(self, service):
        self.service = service
        self.token = service.get_a_access_token()

    def get_output_file_response(self):
        doc_id = self.service.get_a_document_id()
        url = f"{BASE_URL}/workspace_okapi/document/to/file/{doc_id}?token={self.token}"
        headers = {
            'Authorization': f'Bearer {self.token}',
        }

        payload = {}
        files = {}
        response = requests.request("GET", url, headers=headers, data = payload, files = files)

        print(response.text.encode('utf8'))

    def run(self):
        self.get_output_file_response()














