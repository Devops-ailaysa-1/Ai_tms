from gitlab import Gitlab


class GitlabUtils:

    @staticmethod
    def get_gitlab_obj(token):
        g = Gitlab("http://gitlab.com", token)
        try:
            g.auth()
            return g
        except:
            raise ValueError("Auth token is invalid")

    @staticmethod
    def get_branches(repo): # project
        branches = []
        for branch in repo.branches.list():
            branches.append(branch.name)
        return branches

    @staticmethod
    def get_repo(token, repo_name):
        g=  GitlabUtils.get_gitlab_obj(token=token)
        repo = g.projects.get(repo_name)
        return repo

    @staticmethod
    def get_file_contents(repo, ref_branch, file_path=""):

        contents = repo.repository_tree(path=file_path, ref= ref_branch)
        file_contents = []

        while contents:
            file_content = contents.pop(0)
            if file_content.get("type") == "tree":
                contents.extend(repo.repository_tree
                    (file_content.get("path"), ref=ref_branch))
            else:
                size = repo.files.get(file_path=file_content.get("path"), ref=ref_branch).size
                file_contents.append((file_content, size))

        return file_contents


