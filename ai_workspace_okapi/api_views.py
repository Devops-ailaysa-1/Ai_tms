from .serializers import DocumentSerializer
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


class IsUserCompletedInitialSetup(permissions.BasePermission):

    def has_permission(self, request, view):
        # user = (get_object_or_404(AiUser, pk=request.user.id))
        if request.user.user_permissions.filter(codename="user-attribute-exist").first():
            return True

    # protected String processor_name;
    # protected String source_language;
    # protected String target_language;
    # protected String output_type;
    # protected String source_file_path;
    # protected String extension;
    #
    # protected  String srx_file_path;
    # protected  String fprm_file_path;

class DocumentView(views.APIView):
    def get_object(self):
        tasks = Task.objects.all()
        return tasks

    def get(self, request, task_id, format=None):
        tasks = self.get_object()
        task = get_object_or_404(tasks, id=task_id)
        ser = TaskSerializer(task)
        params_data = {**ser.data, "output_type": None}
        res_paths = {"srx_file_path":"okapi_resources/okapi_default_icu4j.srx",
                     "fprm_file_path": None
                     }
        doc = requests.post(url="http://localhost:8080/getDocument/", data={
            "doc_req_params":json.dumps(params_data),
            "doc_req_res_params": json.dumps(res_paths)
        })
        print(doc.json())
        return Response({**ser.data, "output_type": None}, status=201)

