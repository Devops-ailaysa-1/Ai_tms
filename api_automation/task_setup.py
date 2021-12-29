from api_automation.base import *
# from api_automation.utils import s
import requests
from api_automation.base import *

class TaskSetup:


    def __init__(self, service):
        self.service = service
        self.token = service.get_a_access_token()

    def create_task(self, create):
        url = f"{BASE_URL}/workspace/tasks/"
        file, job = self.service.get_a_file_and_job_id()

        print(file, job)

        if create:
            payload = {'file': file,
                       'job': job}
            files = [

            ]

            headers = {
                'Authorization': f'Bearer {self.token}',
            }

            response = requests.request("POST", url, headers=headers, data=payload, files=files)

            return self.service.json_dump_str_to_data(response.text)


    def run(self, create=False):
        self.create_task(create)

if __name__ == "__main__":
    ts = TaskSetup(service)
    ts.run()