from celery import shared_task
from .models import ContentFile
from django.db.models import Q

@shared_task
def update_files(repo_fullname, branch_name, file_path):
    for content_file in ContentFile.objects.filter(
        Q(is_localize_registered=True) & Q(file_path=file_path) &\
        Q(branch__branch_name=branch_name) &\
        Q(branch__repo__repository_fullname=repo_fullname)).all():

        content = content_file.get_content_of_file.decoded_content
        for file  in content_file.contentfile_files_set.all():
            file.update_file(file_content=content)



