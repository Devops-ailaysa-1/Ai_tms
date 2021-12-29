from api_automation.account_setup import AccountSetup
from api_automation.project_setup import ProjectSetup
from api_automation.file_and_job_setup import FilesAndJobsSetup
from api_automation.task_setup import TaskSetup
from api_automation.document_setup import DocumentSetup
import json

class Service:

    def get_a_access_token():
        account_setup = AccountSetup()
        account_setup.run()

        return account_setup.token

    def get_a_last_project_id():
        project_setup = ProjectSetup(service=Service)
        projects = project_setup.get_list_of_projects()
        return projects[-1]["id"]

    def get_a_file_and_job_id():
        fj = FilesAndJobsSetup(service=Service)
        files_and_jobs = fj.get_files_jobs_in_a_project()
        file, job = files_and_jobs["files"][0]["id"], files_and_jobs["jobs"][0]["id"]

        return file, job

    def get_a_document_url():
        ts = TaskSetup(service=Service)
        task_data = ts.create_task(True)
        return task_data["document_url"]

    def get_a_document_id():
        ds = DocumentSetup(service=Service)
        doc_id = ds.get_document_data()["document_id"]
        return doc_id

    def json_dump_str_to_data(json_dump_str):
        return json.loads(json_dump_str)

    def get_key_from_data(json_dump_str, key):
        return Service.json_dump_str_to_data(json_dump_str)[key]