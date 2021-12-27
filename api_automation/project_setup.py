import requests
from api_automation.account_setup import AccountSetup
from api_automation.open_file import MainWindow
from api_automation.base_utils import BaseUtils
from api_automation.base import *
# from api_automation.utils import Service

class ProjectSetup(BaseUtils):
    file_name = ''
    project_id = None

    def __init__(self, service,account_setup_init=True):

        self.token = service.get_a_access_token()

    def create_project(self):
        self.file_name = MainWindow.run()
        url = f"{BASE_URL}/workspace/project_setup/"

        payload = {'project_name': 'pa0010',
                   'source_language': '17',
                   'target_languages': '[28,29]'}
        files = [
            ('files', open(self.file_name, 'rb'))
        ]

        headers = {
            'Authorization': f'Bearer {self.token}',
        }

        response = requests.request("POST", url, headers=headers, data=payload, files=files)

        data = self.json_dump_str_to_data(response.text)

        print(data)

        # print("file__name---->", self.file_name)

    def get_list_of_projects(self):
        url = f"{BASE_URL}/workspace/project_setup/"

        payload = {}
        files = {}
        headers = {
            'Authorization': f'Bearer {self.token}',}

        response = requests.request("GET", url, headers=headers, data=payload, files=files)

        projects = self.json_dump_str_to_data(response.text)["results"]

        return projects


    def run(self):
        # self.create_project()
        self.get_list_of_projects()

if __name__ == "__main__":
    ps = ProjectSetup()
    ps.run()
