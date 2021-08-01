from .serializers import (DocumentSerializer, SegmentSerializer, DocumentSerializerV2,
                          SegmentSerializerV2, MT_RawSerializer, DocumentSerializerV3)
from ai_workspace.serializers import TaskSerializer
from .models import Document, Segment, MT_RawTranslation
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
import json, os
import pickle
import logging
from rest_framework.exceptions import APIException
from rest_framework.pagination import PageNumberPagination
from django.http import  HttpResponse, JsonResponse
from .okapi_configs import CURRENT_SUPPORT_FILE_EXTENSIONS_LIST
from rest_framework.permissions import IsAuthenticated
from django.http import  FileResponse

logging.basicConfig(filename="server.log", filemode="a", level=logging.DEBUG, )

spring_host = os.environ.get("SPRING_HOST")

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
                     'extension', 'processor_name', 'output_file_path']
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
            doc = requests.post(url=f"http://{spring_host}:8080/getDocument/", data={
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
    @staticmethod
    def get_object(segment_id):
        qs = Segment.objects.all()
        segment = get_object_or_404(qs, id = segment_id)
        return segment

    @staticmethod
    def get_update(segment, data,request):
        segment_serlzr =  SegmentSerializerV2(segment, data=data, partial=True, context={"request": request})
        if segment_serlzr.is_valid(raise_exception=True):
            segment_serlzr.save()
            return segment_serlzr

    def update(self, request, segment_id):
        segment = self.get_object(segment_id)
        segment_serlzr = self.get_update(segment, request.data, request)
        return Response(segment_serlzr.data, status=201)

class MT_RawView(views.APIView):

    @staticmethod
    def get_data(request, segment_id):
        mt_raw = MT_RawTranslation.objects.filter(segment_id=segment_id).first()
        if mt_raw:
            return MT_RawSerializer(mt_raw), 200

        mt_raw_serlzr = MT_RawSerializer(data = {"segment": segment_id}, context={"request": request})
        if mt_raw_serlzr.is_valid(raise_exception=True):
            # mt_raw_serlzr.validated_data[""]
            mt_raw_serlzr.save()
            return mt_raw_serlzr, 201

    def get(self, request, segment_id):
        data, status_code = self.get_data(request, segment_id)
        return Response(data.data, status=status_code)

class DocumentToFile(views.APIView):
    permission_classes = [IsAuthenticated]
    @staticmethod
    def get_object(document_id):
        qs = Document.objects.all()
        document = get_object_or_404(qs, id=document_id)
        return  document

    def get(self, request, document_id):
        res = self.document_data_to_file(request, document_id)
        if res.status_code in [200, 201]:
            file_path = res.text
            if os.path.isfile(res.text):
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as fh:
                        response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
                        response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                        return response
            # return JsonResponse({"output_file_path": res.text}, status=201)
        return JsonResponse({"msg": "something went to wrong in okapi file processing"}, status=409)

    @staticmethod
    def document_data_to_file(request, document_id):
        output_type = request.GET.get("output_type", "")
        document = DocumentToFile.get_object(document_id)
        doc_serlzr = DocumentSerializerV3(document)
        data = doc_serlzr.data
        if 'fileProcessed' not in data:
            data['fileProcessed'] = True
        if 'numberOfWords' not in data: # we can remove this duplicate field in future
            data['numberOfWords'] = 0
        task = document.task_set.first()
        ser = TaskSerializer(task)
        task_data = ser.data
        DocumentViewByTask.correct_fields(task_data)
        output_type = output_type if output_type in OUTPUT_TYPES else "ORIGINAL"

        pre, ext = os.path.splitext(task_data["output_file_path"])
        if output_type == "XLIFF":
            ext = ".xliff"
        if output_type == "TMX":
            ext = ".tmx"
        task_data["output_file_path"] = pre + ext

        params_data = {**task_data, "output_type": output_type}
        res_paths = {"srx_file_path":"okapi_resources/okapi_default_icu4j.srx",
                     "fprm_file_path": None
                     }
        res = requests.post(
            f'http://{spring_host}:8080/getTranslatedAsFile/',
            data={
                'document-json-dump': json.dumps(data),
                "doc_req_res_params": json.dumps(res_paths),
                "doc_req_params": json.dumps(params_data),
            }
        )
        return res

OUTPUT_TYPES = dict(
    ORIGINAL = "ORIGINAL",
    XLIFF = "XLIFF",
    TMX = "TMX",
)

def output_types(request):
    return JsonResponse(OUTPUT_TYPES, safe=False)

