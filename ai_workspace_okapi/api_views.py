from .serializers import DocumentSerializer, SegmentSerializer
from ai_workspace.serializers import TaskSerializer
from .models import Document
from rest_framework import viewsets
from rest_framework import views
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from ai_auth.models import AiUser, UserAttribute
from ai_staff.models import AiUserType
from django.http import HttpResponse
from ai_workspace.models import Task
from rest_framework.response import  Response
from django.db.models import F
import requests
import json
import pickle

class IsUserCompletedInitialSetup(permissions.BasePermission):

    def has_permission(self, request, view):
        # user = (get_object_or_404(AiUser, pk=request.user.id))
        if request.user.user_permissions.filter(codename="user-attribute-exist").first():
            return True

class DocumentView(views.APIView):
    def get_object(self):
        tasks = Task.objects.all()
        return tasks

    def get(self, request, task_id, format=None):
        tasks = self.get_object()
        task = get_object_or_404(tasks, id=task_id)
        document = task.document
        if (not document) and  (not Document.objects.filter(job=task.job, file=task.file).all()):
            ser = TaskSerializer(task)
            params_data = {**ser.data, "output_type": None}
            res_paths = {"srx_file_path":"okapi_resources/okapi_default_icu4j.srx",
                         "fprm_file_path": None
                         }
            doc = requests.post(url="http://localhost:8080/getDocument/", data={
                "doc_req_params":json.dumps(params_data),
                "doc_req_res_params": json.dumps(res_paths)
            })
            if doc.status_code == 200 :
                doc_data = doc.json()
                serializer = (DocumentSerializer(data={**doc_data,\
                                    "file": task.file.id, "job": task.job.id,
                                }))
                if serializer.is_valid(raise_exception=True):
                    document = serializer.save()
                    task.document = document
                    task.save()
            else:
                raise ValueError("Something went wrong in okapi file processing!!!")

        if not document:
            document = Document.objects.get(job=task.job, file=task.file)
            task.document = document
            task.save()

        segments_ser = SegmentSerializer(document.segments, many=True)
        return Response(segments_ser.data, status=201)

