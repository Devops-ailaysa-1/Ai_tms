from github import Github
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import StringIO, BytesIO
import sys
import pickle
from pymongo import MongoClient
cli = MongoClient ( 'localhost', 27017)

from datetime import datetime
import time

class GithubUtils:

    @staticmethod
    def get_content_of_file(repo, ref_branch, file_path):
        print(repo, ref_branch, file_path)
        contents = repo.get_contents(file_path, ref=ref_branch)
        return contents

    @staticmethod
    def get_branches(repo):
        branches = []
        for branch in repo.get_branches():
            branches.append(branch.name)
        return branches

    @staticmethod
    def get_file_contents(repo, ref_branch, file_path=""):
        print("ref_branch--->", ref_branch)
        print("path---->", file_path)
        contents = repo.get_contents(file_path, ref= ref_branch)
        file_contents = []

        while contents:
            file_content = contents.pop(0)
            print("content---->", file_content)
            if file_content.type == "dir":
                contents.extend(repo.get_contents(file_content.path, ref=ref_branch))
            else:
                file_contents.append(file_content)

        return file_contents

    @staticmethod
    def get_github_username():
        pass

    @staticmethod
    def get_repositories(github):
        repositories = [ ]
        for repo in github.get_user().get_repos():
            repositories.append(
                [repo.name, repo.fullname]
            )
        return repositories

    @staticmethod
    def get_repo(github_token, git_user, repo_name):
        g = Github(github_token)
        return g.get_user(git_user).get_repo(repo_name)

    @staticmethod
    def create_new_branch(repo, branch_name, from_commit_hash):
        ref_branch = repo.create_git_ref(
            f"refs/heads/{branch_name}", sha=from_commit_hash)
        return ref_branch

    @staticmethod
    def updatefile_in_branch(repo, file_path, branch_name,
        commit_message="more +++++ tests", content="more ----- tests"):

        content =  repo.get_contents(file_path, ref=branch_name)
        now_str = datetime.today().strftime("%Y_%m_%d_%H_%M_") \
                  + str(int(time.time()))
        new_unique_branch ="ailaysa_"+ now_str +"_localisation"
        return repo.update_file(content.path,
            commit_message, content, content.sha, new_unique_branch)

class DjRestUtils:

    def get_a_inmemoryuploaded_file():
        io = BytesIO()
        with open("/home/langscape/Documents/translate_status_api.txt", "rb") as f:
            io.write(f.read())
        io.seek(0)
        im = InMemoryUploadedFile(io, None, "text.txt", "text/plain",
                sys.getsizeof(io), None)
        return im

    def convert_content_to_inmemoryfile(filecontent, file_name):
        # text/plain hardcoded may be needs to be change as generic...
        io = BytesIO()
        io.write(filecontent)
        io.seek(0)
        im = InMemoryUploadedFile(io, None, file_name,
                                  "text/plain", sys.getsizeof(io), None)
        return im

class MongoDbUtils:
    @staticmethod
    def get_pickle_load_data(db_name, coll_name):

        db = cli[db_name]
        coll = db[coll_name]
        data = coll.find_one()

        return pickle.loads(data["data"])

class ApiViewService:
    @staticmethod
    def get_pickle_load_data():
        return MongoDbUtils\
            .get_pickle_load_data(db_name="samples",
                coll_name="github_hook_data")


    # secret = '1234'
    # signature_header = request.headers['X-Hub-Signature']
    # sha_name, github_signature = signature_header.split('=')
    # if sha_name != 'sha1':
    #     print('ERROR: X-Hub-Signature in payload headers was not sha1=****')
    #     print("match--->", False)
    #
    # # Create our own signature
    # body = request.body
    # local_signature = hmac.new(secret.encode('utf-8'), msg=body, digestmod=hashlib.sha1)
    #
    # # See if they match
    # print("match-->", hmac.compare_digest(local_signature.hexdigest(), github_signature))