from argparse import ArgumentParser
from api_automation import account_setup,\
    project_setup, file_and_job_setup, task_setup,\
    document_setup, output_file_api
from api_automation.utils import Service


parser = ArgumentParser(description="API testing automation scripts...")

parser.add_argument("-as", "--account_setup", type=bool, default=False,\
                    help="account setup initialize....")
parser.add_argument("-ps", "--project_setup", type=bool, default=False,\
                    help="project setup initailize....")
parser.add_argument("-fjs", "--file_and_job_setup", type=bool, default=False,\
                    help="file and jobs list get  ....")

parser.add_argument("-ts", "--task_get", type=bool, default=False,\
                    help="task referring file and job get ....")

parser.add_argument("-ts+c", "--task_create", type=bool, default=False,\
                    help="task setup initialize ....")

parser.add_argument("-ds", "--document_setup", type=bool, default=False,
                    help = "document data get from task url...")

parser.add_argument("-of", "--output_file", type=bool, default=False,
                    help="output file response check...")


args = parser.parse_args()

print("acoount setup----->", args.account_setup)

if __name__ == "__main__":

    if args.account_setup:
        as_ = account_setup.AccountSetup()
        as_.run()

    if args.file_and_job_setup:
        fjs = file_and_job_setup.FilesAndJobsSetup(service=Service)
        fjs.run()

    # if args.

    if args.task_get or args.task_create:
        ts = task_setup.TaskSetup(service=Service)
        ts.run(args.task_create)

    if args.document_setup:
        ds = document_setup.DocumentSetup(service=Service)
        ds.run()

    if args.output_file:
        of = output_file_api.OutputFile(service=Service)
        of.run()

