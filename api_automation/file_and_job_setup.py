from api_automation.base import *
# from api_automation.utils import s
import requests


class FilesAndJobsSetup:

    def __init__(self, service):
        self.service = service
        self.token = service.get_a_access_token()

    def get_files_jobs_in_a_project(self, project_id=None):

        if not project_id:
            project_id = self.service.get_a_last_project_id()

        url = f'{BASE_URL}/workspace/files_jobs/{project_id}'


        payload = {}
        headers = {
            'Authorization': f'Bearer {self.token}',
        }

        response = requests.request("GET", url, headers=headers, data = payload)

        return self.service.json_dump_str_to_data(response.text)

    # def create_task(self):

    def run(self):
        self.get_files_jobs_in_a_project()

if __name__ == "__main__":
    fj = FilesAndJobsSetup()
    fj.run()
