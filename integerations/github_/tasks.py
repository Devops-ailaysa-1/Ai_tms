from celery import shared_task
from .models import ContentFile, FileConnector, Branch, DownloadProject
from django.db.models import Q
from ai_workspace.models import Task
from ai_workspace_okapi.api_views import DocumentViewByTask
from ai_workspace.serializers import TaskSerializer
import json
from django.contrib.auth import settings
import os, requests
from ai_workspace_okapi.serializers import TextUnitIntgerationUpdateSerializer

spring_host = os.environ.get("SPRING_HOST")
def update_segments(file):
    tasks = Task.objects.filter(file=file).all()
    task1 = tasks.first()

    ser = TaskSerializer(task1)
    data = ser.data
    DocumentViewByTask.correct_fields(data)
    # print("data--->", data)
    params_data = {**data, "output_type": None}
    res_paths = {"srx_file_path": "okapi_resources/okapi_default_icu4j.srx",
                 "fprm_file_path": None,
                 "use_spaces": settings.USE_SPACES
                 }
    doc = requests.post(url=f"http://{spring_host}:8080/getDocument/", data={
        "doc_req_params": json.dumps(params_data),
        "doc_req_res_params": json.dumps(res_paths)
    })

    if doc.status_code != 200:
        raise ValueError("something went to wrong in file processing...")

    for task in tasks:
        if task.document:
            text = doc.json().get("text")
            text_aligned =  [{ "text_unit_segment_set": v ,
                "document": task.document.id, "okapi_ref_translation_unit_id": k}
                for k, v in text.items()]
            ts = TextUnitIntgerationUpdateSerializer(data=text_aligned,many=True)
            if ts.is_valid(raise_exception=True):
                ts.save()

@shared_task
def update_files(repo_fullname, branch_name, file_path, new_commit_hash):
    # you should limit the qs for the specific user in future
    branches = Branch.objects.filter(branch_name=branch_name,
                repo__repository_fullname=repo_fullname).all()

    for branch in branches:
        dp = DownloadProject.objects.filter(branch=branch).first()
        if dp:
            dp.commit_hash = new_commit_hash
            dp.save()


    for content_file in ContentFile.objects.filter( Q(file_path=file_path) &\
        Q(branch__branch_name=branch_name) &\
        Q(branch__repo__repository_fullname=repo_fullname)).all():

        content = content_file.get_content_of_file.decoded_content

        fc = FileConnector.objects.filter(contentfile=content_file).first()

        if fc:
            for controller  in fc.controller.all():
                file = controller.file

                with file.file.open("wb") as f:
                    f.write(content)
                update_segments(file)

        # for k, values in text.items():
        #     text_unit = TextUnit.objects.filter(document=doc, okapi_ref_translation_unit_id=k).first()
        #     if text_unit:
        #         lenv = len(values)
        #         count = 0
        #         while count < lenv:
        #             segment = text_unit.text_unit_segment_set.filter(source=values[count].get("source")).first()
        #             print("--->", segment)
        #             if segment:
        #                 values.pop(count)
        #                 lenv -= 1
        #                 continue
        #             count += 1

        #
        # for file  in content_file.contentfile_files_set.all():
        #     file.update_file(file_content=content)


# {'tu11': [],
#  'tu22': [],
#  'tu33': [],
#  'tu44': [],
#  'tu55': [],
#  'tu66': [],
#  'tu77': [],
#  'tu88': [],
#  'tu99': [{'source': '',
#    'target': None,
#    'coded_source': '\ue103\ue110',
#    'merge_segment_count': 0,
#    'random_tag_ids': '[]',
#    'coded_brace_pattern': '(',
#    'coded_ids_sequence': '[1]'}],
#  'tu1010': [{'source': ' One more bug added...',
#    'target': None,
#    'coded_source': '\ue103\ue110 One more bug added...',
#    'merge_segment_count': 0,
#    'random_tag_ids': '[]',
#    'coded_brace_pattern': ')',
#    'coded_ids_sequence': '[1]'}]}

