from .serializers import DocumentSerializer, SegmentSerializer, DocumentSerializerV2, SegmentSerializerV2
from ai_workspace.serializers import TaskSerializer
from .models import Document, Segment
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
import logging
from rest_framework.exceptions import APIException
from rest_framework.pagination import PageNumberPagination
from django.http import  HttpResponse, JsonResponse
from .okapi_configs import CURRENT_SUPPORT_FILE_EXTENSIONS_LIST
from rest_framework.permissions import IsAuthenticated

logging.basicConfig(filename="server.log", filemode="a", level=logging.DEBUG, )

class IsUserCompletedInitialSetup(permissions.BasePermission):

    def has_permission(self, request, view):
        # user = (get_object_or_404(AiUser, pk=request.user.id))
        if request.user.user_permissions.filter(codename="user-attribute-exist").first():
            return True

class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = 'Service temporarily unavailable, try again later.'



class DocumentViewByTask(views.APIView, PageNumberPagination):
    permission_classes = [IsAuthenticated]
    PAGE_SIZE = page_size =  20

    def get_object(self, task_id):
        tasks = Task.objects.all()
        return get_object_or_404(tasks, id=task_id)

    @staticmethod
    def exact_required_fields_for_okapi_get_document():
        # {'source_file_path': '/home/langscape/Documents/ailaysa_github/Ai_TMS/media/u98163/u98163p2/source/test1.txt',
        #  'source_language': 'sq', 'target_language': 'hy', 'document_url': '/workspace_okapi/document/4/',
        #  'filename': 'test1.txt', 'extension': '.txt', 'processor_name': 'plain-text-processor'}
        fields = ['source_file_path', 'source_language', 'target_language',
                     'extension', 'processor_name']
        return fields

    erfogd = exact_required_fields_for_okapi_get_document

    @staticmethod
    def correct_fields(data):
        check_fields = DocumentViewByTask.erfogd()
        remove_keys = []
        for i in data.keys():
            if i in check_fields:
                check_fields.remove(i)
            else:
                remove_keys.append(i)
        print("remove keys--->", remove_keys)
        [data.pop(i) for i in remove_keys]
        if check_fields != []:
            raise ValueError("OKAPI request fields not setted correctly!!!")

    @staticmethod
    def create_document_for_task_if_not_exists(task, request):
        document = task.document
        if (not document) and  (not Document.objects.filter(job=task.job, file=task.file).all()):
            ser = TaskSerializer(task)
            data = ser.data
            DocumentViewByTask.correct_fields(data)
            print("data--->", data)
            params_data = {**data, "output_type": None}
            res_paths = {"srx_file_path":"okapi_resources/okapi_default_icu4j.srx",
                         "fprm_file_path": None
                         }
            doc = requests.post(url="http://localhost:8080/getDocument/", data={
                "doc_req_params":json.dumps(params_data),
                "doc_req_res_params": json.dumps(res_paths)
            })
            if doc.status_code == 200 :
                doc_data = doc.json()
                print("doc_data---->", doc_data)
                serializer = (DocumentSerializerV2(data={**doc_data,\
                                    "file": task.file.id, "job": task.job.id,
                                }, context={"request": request}))
                if serializer.is_valid(raise_exception=True):
                    document = serializer.save()
                    task.document = document
                    task.save()
            else:
                logging.debug(msg=f"error raised while process the document, the task id is {task.id}")
                raise  ValueError("Something went wrong in okapi file processing!!!")

        elif (not document):
            document = Document.objects.get(job=task.job, file=task.file)
            task.document = document
            task.save()
        return document

    def get(self, request, task_id, format=None):
        task = self.get_object(task_id=task_id)
        document = self.create_document_for_task_if_not_exists(task, request)
        # page_segments = self.paginate_queryset(document.segments, request, view=self)
        # segments_ser = SegmentSerializer(page_segments, many=True)
        # return self.get_paginated_response(segments_ser.data)
        return Response(DocumentSerializerV2(document).data, status=201)

class SegmentsView(views.APIView, PageNumberPagination):
    PAGE_SIZE = page_size =  20

    def get_object(self, document_id):
        document = get_object_or_404(
            Document.objects.all(), id=document_id
        )
        return document

    def get(self, request, document_id):
        document = self.get_object(document_id=document_id)
        segments = document.segments
        len_segments = segments.count()
        page_len = self.paginate_queryset(range(1,len_segments+1), request)
        print(page_len)
        page_segments = self.paginate_queryset(segments, request, view=self)
        segments_ser = SegmentSerializer(page_segments, many=True)
        [i.update({"segment_count":j}) for i,j in  zip(segments_ser.data, page_len)]
        return self.get_paginated_response(segments_ser.data)

def get_supported_file_extensions(request):
    return JsonResponse(CURRENT_SUPPORT_FILE_EXTENSIONS_LIST, safe=False)

class SourceTMXFilesCreate(views.APIView):
    def get_queryset(self, project_id):
        project_qs = Project.objects.all()
        project = get_object_or_404(project_qs, id=project_id)
        return  project.files_and_jobs_set

    def post(self, request, project_id):
        jobs, files = self.get_queryset(project_id=project_id)
        
class SegmentsUpdateView(viewsets.ViewSet):
    def get_object(self, segment_id):
        qs = Segment.objects.all()
        segment = get_object_or_404(qs, id = segment_id)
        return segment

    def update(self, request, segment_id):
        segment = self.get_object(segment_id)
        segment_serlzr =  SegmentSerializerV2(segment, data=request.data, partial=True, context={"request": request})
        if segment_serlzr.is_valid(raise_exception=True):
            segment_serlzr.save()
            return Response(segment_serlzr.data, status=201)

