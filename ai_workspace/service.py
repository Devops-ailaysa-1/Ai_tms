from .models import File
from .utils import DjRestUtils

class Service:

    @staticmethod
    def get_file_object(project):
        file = File()
        file.usage_type_id = 1
        file.file = DjRestUtils\
            .get_a_inmemoryuploaded_file("test", "test.txt")
        file.project = project
        file.save()
        return file

    @staticmethod
    def get_project_object():
        pass
