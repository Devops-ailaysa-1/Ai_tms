from github import Github
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import StringIO, BytesIO
import sys

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
        contents = repo.get_contents(file_path, ref= ref_branch)
        file_contents = []

        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(repo.get_contents(file_content.path))
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

class DjRestUtils:

    def get_a_inmemoryuploaded_file():
        io = BytesIO()
        with open("/home/langscape/Documents/translate_status_api.txt", "rb") as f:
            io.write(f.read())
        io.seek(0)
        im = InMemoryUploadedFile(io, None, "text.txt", "text/plain",
                sys.getsizeof(io), None)
        return im



