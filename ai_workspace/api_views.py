import copy
import io
import json
import logging
import mimetypes
import os
import shutil
import zipfile,itertools
from datetime import datetime
from glob import glob
from urllib.parse import urlparse
from ai_auth.tasks import count_update,weighted_count_update
import django_filters
import docx2txt
import nltk
import requests
from delta import html
from django.conf import settings
from django.core.files import File as DJFile
from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.http import Http404, HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, get_list_or_404
from django_filters.rest_framework import DjangoFilterBackend
from filesplit.split import Split
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import storage
from htmldocx import HtmlToDocx
from indicnlp.tokenize.sentence_tokenize import sentence_split
from notifications.signals import notify
from pydub import AudioSegment
from rest_framework import permissions
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from filesplit.split import Split
from ai_auth.utils import authorize_list,filter_authorize, unassign_task
from django_oso.auth import authorize
logger = logging.getLogger('django')
from django.db import models
from django.db.models.functions import Lower
from ai_auth.models import AiUser, UserCredits
from ai_auth.models import HiredEditors
from ai_auth.tasks import mt_only, text_to_speech_long_celery, transcribe_long_file_cel, project_analysis_property
from ai_auth.tasks import write_doc_json_file
from ai_glex.serializers import GlossarySetupSerializer, GlossaryFileSerializer, GlossarySerializer
from ai_marketplace.models import ChatMessage
from ai_marketplace.serializers import ThreadSerializer
from ai_pay.api_views import po_modify
# from controller.serializer_mapper import serializer_map
from ai_staff.models import LanguagesLocale, AilaysaSupportedMtpeEngines,AiCustomize
#from ai_tm.models import TmxFile
from ai_workspace import forms as ws_forms
from ai_workspace.excel_utils import WriteToExcel_lite
from ai_workspace.tbx_read import upload_template_data_to_db, user_tbx_write
from ai_workspace.utils import create_assignment_id
from ai_workspace_okapi.models import Document
from ai_workspace_okapi.utils import download_file, text_to_speech, text_to_speech_long, get_res_path
from ai_workspace_okapi.utils import get_translation
from .models import AiRoleandStep, Project, Job, File, ProjectContentType, ProjectSubjectField, TempProject, TmxFile, ReferenceFiles, \
    Templangpair, TempFiles, TemplateTermsModel, TaskDetails, \
    TaskAssignInfo, TaskTranscriptDetails, TaskAssign, Workflows, Steps, WorkflowSteps, TaskAssignHistory, \
    ExpressProjectDetail
from .models import Task
from .models import TbxFile, Instructionfiles, MyDocuments, ExpressProjectSrcSegment, ExpressProjectSrcMTRaw,\
                    ExpressProjectAIMT, WriterProject,DocumentImages,ExpressTaskHistory
from .serializers import (ProjectContentTypeSerializer, ProjectCreationSerializer, \
                          ProjectSerializer, JobSerializer, FileSerializer, \
                          ProjectSetupSerializer, ProjectSubjectSerializer, TempProjectSetupSerializer, \
                          TaskSerializer, FileSerializerv2, TmxFileSerializer, \
                          PentmWriteSerializer, TbxUploadSerializer, ProjectQuickSetupSerializer, TbxFileSerializer, \
                          VendorDashBoardSerializer, ProjectSerializerV2, ReferenceFileSerializer,
                          TbxTemplateSerializer, \
                          TaskAssignInfoSerializer, TaskDetailSerializer, ProjectListSerializer, \
                          GetAssignToSerializer, TaskTranscriptDetailSerializer, InstructionfilesSerializer,
                          StepsSerializer, WorkflowsSerializer, \
                          WorkflowsStepsSerializer, TaskAssignUpdateSerializer, ProjectStepsSerializer,
                          ExpressProjectDetailSerializer,MyDocumentSerializer,ExpressProjectAIMTSerializer,\
                          WriterProjectSerializer,DocumentImagesSerializer,ExpressTaskHistorySerializer,MyDocumentSerializerNew)
from .utils import DjRestUtils
from django.utils import timezone
from .utils import get_consumable_credits_for_text_to_speech, get_consumable_credits_for_speech_to_text
import regex as re
spring_host = os.environ.get("SPRING_HOST")
from django.db.models import Case, When, F, Value, DateTimeField, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.db.models.query import QuerySet
from ai_auth.utils import get_assignment_role

class IsCustomer(permissions.BasePermission):

    def has_permission(self, request, view):
        # user = (get_object_or_404(AiUser, pk=request.user.id))
        if request.user.user_permissions.filter(codename="user-attribute-exist").first():
            return True

class ProjectView(viewsets.ModelViewSet):
    permission_classes = [IsCustomer]
    serializer_class = ProjectSerializer
    # queryset = Project.objects.all()

    def get_queryset(self):
        return Project.objects.filter(ai_user=self.request.user)

    def create(self, request):
        serializer = ProjectSerializer(data=request.data, context={"request": request})
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except IntegrityError:
                return Response(status=409)
            return Response(serializer.data)

class JobView(viewsets.ModelViewSet):
    serializer_class = JobSerializer

    def get_object(self, many=False):
        objs = []
        obj = None
        if not many:
            try:
                obj = get_object_or_404(Job.objects.all(),\
                    id=self.kwargs.get("pk"))
            except:
                raise Http404
            return  obj

        objs_ids_list =  self.kwargs.get("ids").split(",")

        for obj_id in objs_ids_list:
            print("obj id--->", obj_id)
            try:
                objs.append(get_object_or_404(Job.objects.all(),\
                    id=obj_id))
            except:
                raise Http404
        return objs

    def get_queryset(self):
        return Job.objects.filter(project__ai_user=self.request.user)

    def create(self, request):
        serializer = self.serializer_class(data = request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        print("ak---->", args, kwargs)
        if kwargs.get("many")=="true":
            objs = self.get_object(many=True)
            for obj in objs:
                obj.delete()
            return Response(status=204)
        return super().destroy(request, *args, **kwargs)

class ProjectSubjectView(viewsets.ModelViewSet):
    serializer_class = ProjectSubjectField

    def get_object(self, many=False):
        objs = []
        obj = None
        if not many:
            try:
                obj = get_object_or_404(ProjectSubjectField.objects.all(),\
                    id=self.kwargs.get("pk"))
            except:
                raise Http404
            return  obj

        objs_ids_list =  self.kwargs.get("ids").split(",")

        for obj_id in objs_ids_list:
            print("obj id--->", obj_id)
            try:
                objs.append(get_object_or_404(ProjectSubjectField.objects.all(),\
                    id=obj_id))
            except:
                raise Http404
        return objs


    def get_queryset(self):
        project_id = self.request.query_params.get('project_id')
        return ProjectSubjectField.objects.filter(project__id=project_id)


    def list(self,request):
        queryset = self.get_queryset()
        # pagin_tc = self.paginate_queryset( queryset, request , view=self )
        serializer = ProjectSubjectSerializer(queryset, many=True, context={'request': request})
        # response =self.get_paginated_response(serializer.data)
        return  Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data = request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        print("ak---->", args, kwargs)
        if kwargs.get("many")=="true":
            objs = self.get_object(many=True)
            for obj in objs:
                obj.delete()
            return Response(status=204)
        return super().destroy(request, *args, **kwargs)

class ProjectContentTypeView(viewsets.ModelViewSet):
    serializer_class = ProjectContentTypeSerializer

    def get_object(self, many=False):
        objs = []
        obj = None
        if not many:
            try:
                obj = get_object_or_404(ProjectContentType.objects.all(),\
                    id=self.kwargs.get("pk"))
            except:
                raise Http404
            return  obj

        objs_ids_list =  self.kwargs.get("ids").split(",")

        for obj_id in objs_ids_list:
            print("obj id--->", obj_id)
            try:
                objs.append(get_object_or_404(ProjectContentType.objects.all(),\
                    id=obj_id))
            except:
                raise Http404
        return objs

    def get_queryset(self):
        project_id = self.request.query_params.get('project_id')
        return ProjectContentType.objects.filter(project__id=project_id)

    def list(self,request):
        queryset = self.get_queryset()
        # pagin_tc = self.paginate_queryset( queryset, request , view=self )
        serializer = ProjectContentTypeSerializer(queryset, many=True, context={'request': request})
        # response =self.get_paginated_response(serializer.data)
        return  Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data = request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        if kwargs.get("many")=="true":
            objs = self.get_object(many=True)
            for obj in objs:
                obj.delete()
            return Response(status=204)
        return super().destroy(request, *args, **kwargs)

class FileView(viewsets.ModelViewSet):
    #from ai_workspace_okapi.api_views import DocumentViewByTask
    serializer_class = FileSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, many=False):
        objs = []
        obj = None
        if not many:
            try:
                obj = get_object_or_404(File.objects.all(),\
                    id=self.kwargs.get("pk"))
            except:
                raise Http404
            return  obj

        objs_ids_list =  self.kwargs.get("ids").split(",")

        for obj_id in objs_ids_list:
            print("obj id--->", obj_id)
            try:
                objs.append(get_object_or_404(File.objects.all(),\
                    id=obj_id))
            except:
                raise Http404
        return objs

    def get_queryset(self):
        return File.objects.filter(project__ai_user=self.request.user)

    def create(self, request):
        print(request.data)
        serializer = FileSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=201)

    def destroy(self, request, *args, **kwargs):
        from ai_workspace_okapi.api_views import DocumentViewByTask
        if kwargs.get("many")=="true":
            objs = self.get_object(many=True)
            for obj in objs:
                tasks = obj.file_tasks_set.all()
                for i in tasks:
                    path = DocumentViewByTask.get_json_file_path(i)
                    if os.path.exists(path):
                        print("Exists",path)
                        os.remove(path)
                os.remove(obj.file.path)
                obj.delete()
            return Response(status=204)
        return super().destroy(request, *args, **kwargs)


def integrity_error(func):
    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IntegrityError as e:
            print("error---->", e)
            return Response({'message': "integrirty error"}, 409)

    return decorator






class ProjectSetupView(viewsets.ViewSet, PageNumberPagination):
    serializer_class = ProjectSetupSerializer
    parser_classes = [MultiPartParser, JSONParser]
    permission_classes = [IsAuthenticated]
    page_size = 20


    def get_queryset(self):
        return Project.objects.filter(ai_user=self.request.user).order_by("-id").all()

    @integrity_error
    def create(self, request):
        print("data--->",request.POST.dict())
        print("Files--->",request.FILES.getlist('files'))
        serializer = ProjectSetupSerializer(data={**request.POST.dict(),
            "files":request.FILES.getlist('files')},context={"request":request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=201)

        else:
            return Response(serializer.errors, status=409)

    def list(self,request):
        queryset = self.get_queryset()
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = ProjectSetupSerializer(pagin_tc, many=True, context={'request': request})
        response = self.get_paginated_response(serializer.data)
        print(response)
        return  response


    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()
        project = get_object_or_404(queryset, pk=pk)
        serializer = ProjectSetupSerializer(project)
        return Response(serializer.data)

class ProjectCreateView(viewsets.ViewSet):
    serializer_class = ProjectCreationSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = []

    def get_queryset(self):
        return Project.objects.filter(ai_user_id=8)

    def create(self, request):
        print("data---->",request.data)
        serializer = ProjectCreationSerializer(data={**request.POST.dict(),
            "files":request.FILES.getlist('files')},context={"request":request})
        if serializer.is_valid(raise_exception=True):
            #try:
            serializer.save()
            #except IntegrityError:
              #  return Response(serializer.data, status=409)

            return Response(serializer.data, status=201)

        else:
            return Response(serializer.errors, status=409)

    def list(self,request):
        queryset = self.get_queryset()
        # pagin_tc = self.paginate_queryset( queryset, request , view=self )
        serializer = ProjectCreationSerializer(queryset, many=True, context={'request': request})
        # response =self.get_paginated_response(serializer.data)
        return  Response(serializer.data)


    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()
        project = get_object_or_404(queryset, pk=pk)
        serializer = ProjectCreationSerializer(project)
        return Response(serializer.data)

    def update(self, request, pk=None):
        pass


def text_file_processing(text_data):
    name =  text_data.split()[0]+ ".txt" if len(text_data.split()[0])<=15 else text_data[:5]+ ".txt"
    f1 = open(name, 'w')
    f1.write(text_data)
    f1.close()
    f2 = open(name, 'rb')
    file_obj2 = DJFile(f2)
    return file_obj2,f2,name



class TempProjectSetupView(viewsets.ViewSet):
    serializer_class = TempProjectSetupSerializer
    parser_classes = [MultiPartParser, JSONParser]
    permission_classes = [AllowAny,]

    def get_queryset(self):
        return TempProject.objects.filter(ai_user=self.request.user)

    @integrity_error
    def create(self, request):
        text_data=request.POST.get('text_data')
        if text_data:
            if urlparse(text_data).scheme:
                return Response({"msg":"Url not Accepted"},status=406)
            file_obj2,f2,name = text_file_processing(text_data)
            serializer = TempProjectSetupSerializer(data={**request.POST.dict(),"tempfiles":[file_obj2]})
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                f2.close()
                os.remove(os.path.abspath(name))
                return Response(serializer.data, status=201)
            os.remove(os.path.abspath(name))
            return Response(serializer.errors, status=409)
        else:
            serializer = TempProjectSetupSerializer(data={**request.POST.dict(),
                "tempfiles":request.FILES.getlist('files')})
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=409)

class Files_Jobs_List(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, project_id):
        project = get_object_or_404(Project.objects.all(), id=project_id)
                        # ai_user=self.request.user)
        authorize(self.request, resource=project, actor=self.request.user, action="read")
        #project = filter_authorize(self.request,project,"read",self.request.user)
        jobs = project.project_jobs_set.all()
        jobs = filter_authorize(self.request,jobs,"read",self.request.user)
        contents = project.proj_content_type.all()
        subjects = project.proj_subject.all()
        steps = project.proj_steps.all()
        try:gloss = project.glossary_project
        except:gloss = None
        files = project.project_files_set.filter(usage_type__use_type="source").all()
        glossary_files = project.project_files.all()
        return jobs, files, contents, subjects, steps, project, gloss, glossary_files

    def get(self, request, project_id):
        jobs, files, contents, subjects, steps, project, gloss, glossary_files = self.get_queryset(project_id)
        team_edit = False if project.assigned == True else True
        jobs = JobSerializer(jobs, many=True)
        files = FileSerializer(files, many=True)
        glossary = GlossarySerializer(gloss).data if gloss else None
        glossary_files = GlossaryFileSerializer(glossary_files,many=True)
        contents = ProjectContentTypeSerializer(contents,many=True)
        subjects = ProjectSubjectSerializer(subjects,many=True)
        steps = ProjectStepsSerializer(steps,many=True)
        return Response({"files":files.data,"glossary_files":glossary_files.data,"glossary":glossary,"jobs": jobs.data, "subjects":subjects.data,\
                        "contents":contents.data, "steps":steps.data, "project_name": project.project_name, "team":project.get_team,\
                         "team_edit":team_edit,"project_type_id":project.project_type.id,"mt_engine_id":project.mt_engine_id,'pre_translate':project.pre_translate,\
                         "project_deadline":project.project_deadline, "mt_enable": project.mt_enable, "revision_step_edit":project.PR_step_edit}, status=200)

class TmxFilesOfProject(APIView):
    def get_queryset(self, project_id):
        project_qs = Project.objects.all()
        project = get_object_or_404(project_qs, id=project_id, ai_user=self.request.user)
        files = project.project_files_set.all()
        return files

    def post(self, request, project_id):
        files = self.get_queryset(project_id=project_id)
        res_paths = {"srx_file_path": "okapi_resources/okapi_default_icu4j.srx",
                     "fprm_file_path": None}
        data = []
        for file in files:
            params_data = FileSerializerv2(file).data
            print("params data---->", params_data)
            res = requests.post(
                f"http://{spring_host}:8080/source/createTmx",
                data={
                    "doc_req_params": json.dumps(params_data),
                    "doc_req_res_params": json.dumps(res_paths)
                }
            )

            # if res.status_code in [200, 201]:
            data.append(res.text)
        return JsonResponse({"results":data}, safe=False)

# class ProjectReportAnalysis(APIView):
#     def get_queryset(self, project_id):
#         project_qs = Project.objects.all()
#         project = get_object_or_404(project_qs, id=project_id, ai_user=self.request.user)
#         files = project.project_files_set.all()
#         return files
#
#     def post(self, request, project_id):
#         data = dict(
#             pentm_path = "/home/langscape/Documents/ailaysa_github/Ai_TMS/media/u343460/u343460p1/.pentm/",
#             report_output_path = "/home/langscape/Documents/ailaysa_github/Ai_TMS/media/u343460/u343460p1/tt/report.html",
#             srx_file_path = "/home/langscape/Documents/ailaysa_github/Ai_TMS/okapi_resources/okapi_default_icu4j.srx"
#         )
#         files = self.get_queryset(project_id)
#         batches_data =  FileSerializerv3(files, many=True).data
#         data = {
#             **data,
#             **dict(batches=batches_data)
#         }
#         print("data---->", data)
#         res = requests.post(
#             f"http://{spring_host}:8080/project/report-analysis",
#             data = {"report_params": json.dumps(data)}
#         )
#         if res.status_code in [200, 201]:
#             return JsonResponse({"msg": res.text}, safe=False)
#         else:
#             return JsonResponse({"msg": "something went to wrong"}, safe=False)

class TmxFileView(viewsets.ViewSet):

    @staticmethod
    def TmxToPenseiveWrite(data):
        if len(data)==0:
            return
        project_id = data[0]["project"]
        project = Project.objects.get(id=project_id)
        data = PentmWriteSerializer(project).data
        print("For pentm create  ---> ", data)
        res = requests.post(f"http://{spring_host}:8080/project/pentm/create",
                            data={"pentm_params": json.dumps(data)})
        if res.status_code == 200:
            for tmx_data in res.json():
                print("res--->", res.json())
                instance = project.project_tmx_files.filter(id=tmx_data.get('tmx_id','')).first()
                ser = TmxFileSerializer(instance, data=tmx_data, partial=True)
                if ser.is_valid(raise_exception=True):
                    ser.save()
            return JsonResponse(res.json(), safe=False)
        else:
            return JsonResponse({"msg": "Something wrong with file processing"}, status=res.status_code)

    def create(self, request):
        data = {**request.POST.dict(), "tmx_files": request.FILES.getlist("tmx_files")}
        ser_data = TmxFileSerializer.prepare_data(data)
        ser = TmxFileSerializer(data=ser_data, many=True)
        if ser.is_valid(raise_exception=True):
            ser.save()
            return self.TmxToPenseiveWrite(ser.data)

class TbxUploadView(APIView):
    def post(self, request):
        tbx_files = request.FILES.get('tbx_files')
        project_id = request.POST.get('project', 0)
        doc_id = request.POST.get('doc_id', 0)
        if doc_id != 0:
            job_id = Document.objects.get(id=doc_id).job_id
            project_id = Job.objects.get(id=job_id).project_id
        serializer = TbxUploadSerializer(data={'tbx_files':tbx_files,'project':project_id})
        # print("SER VALIDITY-->", serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)


def docx_save_pdf(pdf_obj):
    from docx import Document
    from htmldocx import HtmlToDocx

    document = Document()
    new_parser = HtmlToDocx()
    new_parser.table_style = 'TableGrid'
    new_parser.add_html_to_document(pdf_obj.html_data, document)
    document.save(pdf_obj.docx_file_name)
    f2 = open(pdf_obj.docx_file_name, 'rb')
    file_obj = DJFile(f2)
    pdf_obj.docx_file_from_writer = file_obj
    pdf_obj.save()



def get_file_from_pdf(pdf_obj_id,pdf_task_id):
    from ai_exportpdf.models import Ai_PdfUpload
    from ai_exportpdf.views import get_docx_file_path
    if pdf_obj_id:
        pdf_obj = Ai_PdfUpload.objects.get(id = pdf_obj_id)
    else:
        pdf_obj = Ai_PdfUpload.objects.filter(task_id = pdf_task_id).last() 
    #print("pdf Before---------->",pdf_obj)
    if pdf_obj.pdf_api_use == "convertio":
        docx_file_path = get_docx_file_path(pdf_obj.id)
        file = open(docx_file_path,'rb')
        file_obj = ContentFile(file.read(),name= os.path.basename(docx_file_path))#name=docx_file_name
        pdf_obj.translation_task_created = True
        pdf_obj.save()
        #print("Pdf------->",pdf_obj.translation_task_created)
    else:
        #docx_save_pdf(pdf_obj)
        file_obj = ContentFile(pdf_obj.docx_file_from_writer.file.read(),name= os.path.basename(pdf_obj.docx_file_from_writer.path))
    return file_obj


# def get_file_from_doc(doc_id):
#     obj = MyDocuments.objects.get(id=doc_id)
#     if obj:

def get_field_type(field_name, queryset):
    stripped_field_name = field_name.lstrip('-')
    if stripped_field_name in queryset.query.annotations:
        return queryset.query.annotations[stripped_field_name].output_field
    return queryset.model._meta.get_field(stripped_field_name)

class CaseInsensitiveOrderingFilter(OrderingFilter):
    
    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)

        if ordering:
            new_ordering = []
            for field in ordering:
                if not isinstance(get_field_type(field, queryset), (models.CharField, models.TextField)):
                    new_ordering.append(field)
                elif field.startswith('-'):
                    new_ordering.append(Lower(field[1:]).desc())
                else:
                    new_ordering.append(Lower(field).asc())
            return queryset.order_by(*new_ordering)

        return queryset



from ai_exportpdf.models import Ai_PdfUpload

class ProjectFilter(django_filters.FilterSet):
    project = django_filters.CharFilter(field_name='project_name',lookup_expr='icontains')
    filter = django_filters.CharFilter(label='glossary or voice',method='filter_not_empty')
    team = django_filters.CharFilter(field_name='team__name',method='filter_team')#lookup_expr='isnull')
    type = django_filters.NumberFilter(field_name='project_type_id')
    class Meta:
        model = Project
        fields = ('project', 'team','type')

    def filter_team(self, queryset, name, value):
        if value=="None":
            lookup = '__'.join([name, 'isnull'])
            return queryset.filter(**{lookup: True})
        else:
            lookup = '__'.join([name, 'icontains'])
            return queryset.filter(**{lookup: value})

    

    def filter_not_empty(self,queryset, name, value):
        if value == "assets":
            queryset = queryset.filter(Q(glossary_project__isnull=False))
        elif value == "voice":
            queryset = queryset.filter(Q(voice_proj_detail__isnull=False))
        elif value == "transcription":
            queryset = queryset.filter(Q(voice_proj_detail__isnull=False)&Q(voice_proj_detail__project_type_sub_category_id = 1))
        elif value == "ai_voice":
            queryset = queryset.filter(Q(voice_proj_detail__isnull=False)&Q(voice_proj_detail__project_type_sub_category_id = 2))
        elif value == "translation":
            queryset = queryset.filter(Q(glossary_project__isnull=True)&Q(voice_proj_detail__isnull=True))#.exclude(project_file_create_type__file_create_type="From insta text")#.exclude(project_type_id = 5)
        print("QRF-->",queryset)
            #queryset = QuerySet(model=queryset.model, query=queryset.query, using=queryset.db)
        #     queryset = queryset.filter(Q(glossary_project__isnull=True)&Q(voice_proj_detail__isnull=True)).filter(project_file_create_type__file_create_type="From insta text")
        # elif value == "assigned":
        #     queryset = queryset.filter(Q(project_jobs_set__job_tasks_set__task_info__task_assign_info__isnull=False))
        # elif value == "express":
        #     queryset = queryset.filter(project_type_id=5)
        return queryset


class QuickProjectSetupView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    paginator = PageNumberPagination()
    serializer_class = ProjectQuickSetupSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter,CaseInsensitiveOrderingFilter]
    ordering_fields = ['project_name','team__name','id']
    filterset_class = ProjectFilter
    search_fields = ['project_name','project_files_set__filename','project_jobs_set__source_language__language',\
                    'project_jobs_set__target_language__language']
    ordering = ('-id')#'-project_jobs_set__job_tasks_set__task_info__task_assign_info__created_at',
    paginator.page_size = 20

    def get_serializer_class(self):
        project_type = json.loads(self.request.POST.get('project_type','1'))
        print("type---->",project_type)
        if project_type == 3:
            return GlossarySetupSerializer
        # if project_type == 4:
        #     return GitProjSetupSerializer
        return ProjectQuickSetupSerializer

    def get_object(self):
        pk = self.kwargs.get("pk", 0)
        try:
            obj = get_object_or_404(Project.objects.all(), id=pk)
        except:
            raise Http404
        return obj

    def get_queryset(self):
        #print(self.request.user)
        pr_managers = self.request.user.team.get_project_manager if self.request.user.team and self.request.user.team.owner.is_agency else [] 
        #print("Mnagers----------->",pr_managers)
        user = self.request.user.team.owner if self.request.user.team and self.request.user.team.owner.is_agency and self.request.user in pr_managers else self.request.user
        queryset = Project.objects.prefetch_related('team','project_jobs_set','team__internal_member_team_info','team__owner','project_jobs_set__job_tasks_set__task_info')\
                    .filter(((Q(project_jobs_set__job_tasks_set__task_info__assign_to = user) & ~Q(ai_user = user))\
                    | Q(project_jobs_set__job_tasks_set__task_info__assign_to = self.request.user))\
                    |Q(ai_user = self.request.user)|Q(team__owner = self.request.user)\
                    |Q(team__internal_member_team_info__in = self.request.user.internal_member.filter(role=1))).distinct()
        return queryset #parent_queryset


    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        print("QR------------>",queryset)
        pagin_tc = self.paginator.paginate_queryset(queryset, request , view=self)
        serializer = ProjectQuickSetupSerializer(pagin_tc, many=True, context={'request': request})
        response = self.get_paginated_response(serializer.data)
        return  response

    
    def retrieve(self, request, pk):
        query = Project.objects.get(id=pk)
        serializer = ProjectQuickSetupSerializer(query, many=False, context={'request': request})
        return Response(serializer.data)

    def create(self, request):
        punctuation='''!"#$%&'``()*+,-./:;<=>?@[\]^`{|}~_'''
        text_data=request.POST.get('text_data')
        ser = self.get_serializer_class()
        pdf_obj_id = request.POST.get('pdf_obj_id',None)
        audio_file = request.FILES.getlist('audio_file',None)
        if text_data:
            if urlparse(text_data).scheme:
                return Response({"msg":"Url not Accepted"},status = 406)
            name =  text_data.split()[0].strip(punctuation)+ ".txt" if len(text_data.split()[0])<=15 else text_data[:5].strip(punctuation)+ ".txt"
            im_file= DjRestUtils.convert_content_to_inmemoryfile(filecontent = text_data.encode(),file_name=name)
            serlzr = ser(data={**request.data,"files":[im_file],"from_text":['true']},context={"request": request})
            
        elif pdf_obj_id:
            files_ = request.FILES.getlist('files')
            file_obj = get_file_from_pdf(pdf_obj_id,None)
            files_.append(file_obj)
            serlzr = ser(data={**request.data,"files":files_},context={"request": request})    
             
        else:
            serlzr = ser(data=\
            {**request.data, "files": request.FILES.getlist("files"),"audio_file":audio_file},context={"request": request})
            
        if serlzr.is_valid(raise_exception=True):
            serlzr.save()
            pr = Project.objects.get(id=serlzr.data.get('id'))
            #project_analysis_property.apply_async((serlzr.data.get('id'),), )
            if pr.pre_translate == True:
                mt_only.apply_async((serlzr.data.get('id'), str(request.auth)), )
            return Response(serlzr.data, status=201)
        return Response(serlzr.errors, status=409)

    def update(self, request, pk, format=None):
        instance = self.get_object()
        ser = self.get_serializer_class()
        task_id=request.POST.get('task_id',None)
        pdf_obj_id = request.POST.get('pdf_obj_id',None)
        pdf_task_id = request.POST.get('pdf_task_id',None)
        team = request.POST.get('team',None)
        req_copy = copy.copy( request._request)
        req_copy.method = "DELETE"

        file_delete_ids = self.request.query_params.get(\
            "file_delete_ids", [])
        job_delete_ids = self.request.query_params.get(\
            "job_delete_ids", [])
        content_delete_ids = self.request.query_params.get(\
            "content_delete_ids", [])
        subject_delete_ids = self.request.query_params.get(\
            "subject_delete_ids", [])
        step_delete_ids = self.request.query_params.get(\
            "step_delete_ids", [])

        if step_delete_ids:
            for task_obj in instance.get_tasks:
                task_obj.task_info.filter(task_assign_info__isnull=True).filter(step_id__in=step_delete_ids).delete()
            instance.proj_steps.filter(steps__in=step_delete_ids).delete()

        if file_delete_ids:
            file_res = FileView.as_view({"delete": "destroy"})(request=req_copy,\
                        pk='0', many="true", ids=file_delete_ids)

        if job_delete_ids:
            job_res = JobView.as_view({"delete": "destroy"})(request=req_copy,\
                        pk='0', many="true", ids=job_delete_ids)

        if content_delete_ids:
            content_res = ProjectContentTypeView.as_view({"delete": "destroy"})(request=req_copy,\
                        pk='0', many="true", ids=content_delete_ids)

        if subject_delete_ids:
            subject_res = ProjectSubjectView.as_view({"delete": "destroy"})(request=req_copy,\
                        pk='0', many="true", ids=subject_delete_ids)
        
        if not team:
            team = True if instance.team else False
        
        if task_id:
            file_obj = update_project_from_writer(task_id)
            serlzr = ser(instance, data=\
                {**request.data, "files":[file_obj],"team":[team]},context={"request": request}, partial=True)
            
        elif pdf_obj_id or pdf_task_id:
            if pdf_obj_id:file_obj = get_file_from_pdf(pdf_obj_id,None)
            else:file_obj = get_file_from_pdf(None,pdf_task_id)
            serlzr = ser(instance, data=\
                {**request.data, "files":[file_obj],"team":[team]},context={"request": request}, partial=True)
            
        else:
            serlzr = ser(instance, data=\
                {**request.data, "files": request.FILES.getlist("files"),"team":[team]},
                context={"request": request}, partial=True)

        if serlzr.is_valid(raise_exception=True):
            serlzr.save()
            # if instance.pre_translate == True:
            #     mt_only.apply_async((serlzr.data.get('id'), str(request.auth)), )    
            #mt_only.apply_async((serlzr.data.get('id'), str(request.auth)), )
            return Response(serlzr.data)
        return Response(serlzr.errors, status=409)

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        if project.assigned == True:
            return Response({'msg':'some tasks are assigned in this project. Unassign and delete'},status=400)
        else:
            project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class VendorDashBoardView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    paginator = PageNumberPagination()
    paginator.page_size = 20

    @staticmethod
    def get_tasks_by_projectid(request, pk):
        project = get_object_or_404(Project.objects.all(),
                    id=pk)
        pr_managers = request.user.team.get_project_manager if request.user.team and request.user.team.owner.is_agency else []
        user_1 = request.user.team.owner if request.user.team and request.user.team.owner.is_agency and request.user in pr_managers else request.user  #####For LSP
        if project.ai_user == request.user:
            print("Owner")
            return project.get_tasks
        if project.team:
            print("Team")
            print(project.team.get_project_manager)
            if ((project.team.owner == request.user)|(request.user in project.team.get_project_manager)):
                return project.get_tasks
            # elif self.request.user in project.team.get_project_manager:
            #     return project.get_tasks
            else:
                return [task for job in project.project_jobs_set.all() for task \
                        in job.job_tasks_set.all() if task.task_info.filter(assign_to = user_1).exists()]#.distinct('task')]
        else:
            print("Indivual")
            return [task for job in project.project_jobs_set.all() for task \
                    in job.job_tasks_set.all() if task.task_info.filter(assign_to = user_1).exists()]#.distinct('task')]


    def get_object(self):
        tasks = Task.objects.order_by("-id").all()
        tasks = get_list_or_404(tasks, file__project__ai_user=self.request.user)
        tasks = authorize_list(tasks,"read",self.request.user)
        return tasks

    def list(self, request, *args, **kwargs):
        tasks = self.get_object()
        #print("TASKS------------>",tasks)
        pagin_queryset = self.paginator.paginate_queryset(tasks, request, view=self)
        serlzr = VendorDashBoardSerializer(pagin_queryset, many=True,context={'request':request})
        return self.get_paginated_response(serlzr.data)

    def retrieve(self, request, pk, format=None):
        #print("%%%%")
        tasks = self.get_tasks_by_projectid(request=request,pk=pk)
        #tasks = authorize_list(tasks,"read",self.request.user)
        serlzr = VendorDashBoardSerializer(tasks, many=True,context={'request':request})
        return Response(serlzr.data, status=200)

class VendorProjectBasedDashBoardView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    paginator = PageNumberPagination()
    paginator.page_size = 20

    def get_object(self, project_id):

        tasks = Task.objects.filter(job__project_id=project_id).all()
        tasks = get_list_or_404(tasks, file__project__ai_user=self.request.user)
        return tasks

    def list(self, request, project_id, *args, **kwargs):
        tasks = self.get_object(project_id)
        # pagin_queryset = self.paginator.paginate_queryset(tasks, request,
        # view=self)
        serlzr = VendorDashBoardSerializer(tasks, many=True,context={'request':request})
        return Response(serlzr.data, status=200)

class TM_FetchConfigsView(viewsets.ViewSet):
    def get_object(self, pk):
        project = get_object_or_404(
            Project.objects.all(), id=pk)
        return project

    def update(self, request, pk, format=None):
        project = self.get_object(pk)
        ser = ProjectSerializerV2(project, data=request.data, partial=True)
        if ser.is_valid(raise_exception=True):
            ser.save()
            return Response(ser.data, status=201)


class ReferenceFilesView(viewsets.ModelViewSet):

    serializer_class = ReferenceFileSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    # https://www.django-rest-framework.org/api-guide/filtering/

    def get_object(self):
        return get_object_or_404(ReferenceFiles.objects.all(),
            id=self.kwargs.get("pk"))

    def get_project(self, project_id):
        try:
            project = get_object_or_404(Project.objects.all(),\
                        id=project_id)
        except:
            raise Http404("project_id should be int type!!!")
        return project

    def get_queryset(self):
        project_id = self.request.query_params.get("project", None)
        project = self.get_project(project_id)
        ref_files = ReferenceFiles.objects.none()
        if project:
            ref_files = project.ref_files
        return ref_files

    def create(self, request):
        files = request.FILES.getlist('ref_files')
        project_id = request.data.get("project", None)
        project = self.get_project(project_id)
        data = \
          [{"project": project_id, "ref_files": file} for file in files]
        ser = ReferenceFileSerializer(data=data, many=True)
        if ser.is_valid(raise_exception=True):
            ser.save()
            return Response(ser.data, status=201)

    def destroy(self, request, *args, **kwargs):
        if kwargs.get("many")=="true":
            objs = self.get_object(many=True)
            for obj in objs:
                obj.delete()
            return Response(status=204)
        return super().destroy(request, *args, **kwargs)

@api_view(["DELETE"])
def test_internal_call(request):
    view = (ReferenceFilesView.as_view({"delete":"destroy"})\
        (request=request._request, pk=0, many="true", ids="6,7")).data
    print("data---->", request.data)
    return Response(view, status=200)


class TbxFileListCreateView(APIView):

    def get(self, request, project_id):
        files = TbxFile.objects.filter(project_id=project_id).all()
        serializer = TbxFileSerializer(files, many=True)
        return Response(serializer.data)

    def post(self, request, project_id):
        data = {**request.POST.dict(), "tbx_file" : request.FILES.getlist('tbx_file'),'project_id':project_id}
        ser_data = TbxFileSerializer.prepare_data(data)
        serializer = TbxFileSerializer(data=ser_data,many=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(serializer.data, status=201)

class TbxFileDetail(APIView):

    def get_object(self, id):
        try:
            return TbxFile.objects.get(id=id)
        except TbxFile.DoesNotExist:
            return HttpResponse(status=404)

    def put(self, request, id):
        tbx_asset = self.get_object(id)
        #tbx_file = request.FILES.get('tbx_file')
        job_id = request.POST.get("job_id", None)
        serializer = TbxFileSerializer(tbx_asset, data={"job" : job_id}, partial=True)
        print("SER VALIDITY-->", serializer.is_valid())
        if serializer.is_valid():
            serializer.save_update()
            return Response(serializer.data, status=200)

    def delete(self, request, id):
        tbx_asset = self.get_object(id)
        tbx_asset.delete()
        return Response(data={"Message": "Removed Terminology asset"}, status=204)

class TmxList(APIView):

    def get(self, request, project_id):
        files = TmxFile.objects.filter(project_id=project_id).all()
        serializer = TmxFileSerializer(files, many=True)
        return Response(serializer.data)


@api_view(['GET',])
def glossary_template_lite(request):
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Glossary_Lite.xlsx'
    xlsx_data = WriteToExcel_lite()
    response.write(xlsx_data)
    return response

class TbxTemplateUploadView(APIView):

    def post(self, request, project_id):

        data = {**request.POST.dict(), "tbx_template_file" : request.FILES.get('tbx_template_file')}
        data.update({'project_id': project_id})
        prep_data = TbxTemplateSerializer.prepare_data(data)

        serializer = TbxTemplateSerializer(data=prep_data)
        print("SER VALIDITY-->", serializer.is_valid())
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            saved_data = serializer.data
            file_id = saved_data.get("id")
            job_id = prep_data["job"]
            if bool(upload_template_data_to_db(file_id, job_id)):
                tbx_file = user_tbx_write(job_id, project_id)
                fl = open(tbx_file, 'rb')
                file_obj1 = DJFile(fl) #,name=os.path.basename(tbx_file))
                serializer2 = TbxFileSerializer(data={'tbx_file':file_obj1,'project':project_id,'job':job_id})
                print("TBX serializer---->", serializer2.is_valid())
                if serializer2.is_valid():
                    serializer2.save()
                else:
                    return Response(serializer2.errors)
                fl.close()
                TemplateTermsModel.objects.filter(job_id = job_id).delete()
                os.remove(os.path.abspath(tbx_file))
                return Response({'msg':"Template File uploaded and TBX created & uploaded","data":serializer.data})#,"tbx_file":tbx_file})
            else:
                return Response({'msg':"Template file seems empty or partially empty. Fill up terms and try again", "data":{}},
                        status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors)

@api_view(['GET',])
def tbx_download(request,tbx_file_id):
    tbx_asset = TbxFile.objects.get(id=tbx_file_id).tbx_file
    return download_file(tbx_asset.path)
    # fl_path = tbx_asset.path
    # filename = os.path.basename(fl_path)
    # print(os.path.dirname(fl_path))
    # fl = open(fl_path, 'rb')
    # mime_type, _ = mimetypes.guess_type(fl_path)
    # response = HttpResponse(fl, content_type=mime_type)
    # response['Content-Disposition'] = "attachment; filename=%s" % filename
    # return response

class UpdateTaskCreditStatus(APIView):

    permission_classes = [IsAuthenticated]

    @staticmethod
    def update_addon_credit(user, actual_used_credits=None, credit_diff=None):
        add_ons = UserCredits.objects.filter(Q(user=user) & Q(credit_pack_type="Addon")).\
                    filter(Q(expiry__isnull=True) | Q(expiry__gte=timezone.now())).order_by('expiry')
        if add_ons.exists():
            case = credit_diff if credit_diff != None else actual_used_credits
            for addon in add_ons:
                if addon.credits_left >= case:
                    addon.credits_left -= case
                    addon.save()
                    case = None
                    break
                else:
                    diff = case - addon.credits_left
                    addon.credits_left = 0
                    addon.save()
                    case = diff
            return False if case != None else True
        else:
            return False

    @staticmethod
    def update_usercredit(user, actual_used_credits):
        present = datetime.now()
        try:

            user_credit = UserCredits.objects.get(Q(user=user) & Q(credit_pack_type__icontains="Subscription") & Q(ended_at=None))

            if present.strftime('%Y-%m-%d %H:%M:%S') <= user_credit.expiry.strftime('%Y-%m-%d %H:%M:%S'):
                if not actual_used_credits > user_credit.credits_left:
                    user_credit.credits_left -= actual_used_credits
                    user_credit.save()
                    return True
                else:
                    credit_diff = actual_used_credits - user_credit.credits_left
                    user_credit.credits_left = 0
                    user_credit.save()
                    from_addon = UpdateTaskCreditStatus.update_addon_credit( user, credit_diff)
                    return from_addon
            else:
                raise Exception

        except Exception as e:
            from_addon = UpdateTaskCreditStatus.update_addon_credit(user, actual_used_credits)
            return from_addon

    @staticmethod
    def update_credits( user, actual_used_credits):
        credit_status = UpdateTaskCreditStatus.update_usercredit(user, actual_used_credits)

        if credit_status:
            msg = "Successfully debited MT credits"
            status = 200
        else:
            msg = "Insufficient credits to apply MT"
            status = 424

        return {"msg" : msg}, status

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_credit_status(request):
    return Response({"credits_left": request.user.credit_balance,}, status=200)

######### Tasks Assign to vendor #################
class TaskView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self,):
        tasks = [ task for project in get_list_or_404(Project.objects.all(), ai_user=self.request.user)
                    for task in project.get_tasks
                  ]
        return  tasks

    def get(self, request):
        tasks = self.get_queryset()
        print(tasks)
        # tasks = Task.objects.filter(assign_to_id=request.user.id)
        tasks_serlzr = TaskSerializer(tasks, many=True)
        return Response(tasks_serlzr.data, status=200)

    @staticmethod
    def get_object(data):
        obj = Task.objects.filter(**data).first()
        return obj

    def post(self, request):
        print(self.request.POST.dict())
        obj = self.get_object({**request.POST.dict()})
        if obj:
            task_ser = TaskSerializer(obj)
            return Response(task_ser.data, status=200)

        task_serlzr = TaskSerializer(data=request.POST.dict(), context={"request":request,
            "assign_to": self.request.POST.get('assign_to', self.request.user.id)})#,"customer":self.request.user.id})
        if task_serlzr.is_valid(raise_exception=True):
            task_serlzr.save()
            return Response({"msg": task_serlzr.data}, status=200)

        else:
            return Response({"msg": task_serlzr.errors}, status=400)

    def delete(self, request, id):
        task = Task.objects.get(id = id)
        if task.task_info.filter(task_assign_info__isnull=False):
            print("assigned")
            return Response(data={"Message":"Task is assigned.Unassign and Delete"},status=400)
        else:
            if len(task.job.project.get_tasks) == 1:
                task.job.project.delete()
            elif task.file:
                if os.path.splitext(task.file.filename)[1] == ".pdf":
                    task.file.delete()
                if task.document:
                    task.document.delete()
                task.delete()
            # else:
            #     print("333333333333333")
            #     if task.document:
            #         print("Inside--------->",task.document)
            #         task.document.delete()
            #     print("Outside")
            #     task.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)



@api_view(['POST',])
@permission_classes([AllowAny])
def create_project_from_temp_project_new(request):
    ai_user_id = request.POST.get("user_id")
    ai_user = AiUser.objects.get(id=ai_user_id)
    temp_proj_id = request.POST.get("temp_project")
    temp_proj =  TempProject.objects.get(temp_proj_id =temp_proj_id)
    files_list = TempFiles.objects.filter(temp_proj_id =temp_proj.id)
    jobs_list = Templangpair.objects.filter(temp_proj_id=temp_proj.id)
    mt_engine = [temp_proj.mt_engine_id]
    source_language = [str(jobs_list[0].source_language_id)]
    target_languages = [str(i.target_language_id) for i in jobs_list]
    files = [DJFile(i.files,name=i.filename) for i in files_list]
    filename,extension = os.path.splitext((files_list[0].filename))
    serializer = ProjectQuickSetupSerializer(data={'project_name':[filename +'-tmp'+ str(temp_proj.id)],\
    'source_language':source_language,'target_languages':target_languages,'files':files,'mt_engine':mt_engine},\
    context={'ai_user':ai_user})
    if serializer.is_valid():
        serializer.save()
        print(serializer.data)
        return JsonResponse({"data":serializer.data},safe=False)
    else:
        return JsonResponse({"data":serializer.errors},safe=False)

##############   PROJECT ANALYSIS BY STORING ONLY COUNT DATA   ###########

class ProjectAnalysisProperty(APIView):

    permission_classes = [IsAuthenticated]

    @staticmethod
    def exact_required_fields_for_okapi_get_document():
        fields = ['source_file_path', 'source_language', 'target_language',
                     'extension', 'processor_name', 'output_file_path']
        return fields

    erfogd = exact_required_fields_for_okapi_get_document

    # erfogd = DocumentViewByTask.exact_required_fields_for_okapi_get_document()

    @staticmethod
    def correct_fields(data):
        check_fields = ProjectAnalysisProperty.erfogd()
        remove_keys = []
        for i in data.keys():
            if i in check_fields:
                check_fields.remove(i)
            else:
                remove_keys.append(i)
        [data.pop(i) for i in remove_keys]
        if check_fields != []:
            raise ValueError("File processing fields not set properly !!!")

    @staticmethod
    def get_data_from_docs(project):
        proj_word_count = proj_char_count = proj_seg_count = 0
        task_words = []

        for task in project.get_mtpe_tasks:
            doc = Document.objects.get(id=task.document_id)
            proj_word_count += doc.total_word_count
            proj_char_count += doc.total_char_count
            proj_seg_count += doc.total_segment_count

            task_words.append({task.id:doc.total_word_count})

        return {"proj_word_count": proj_word_count, "proj_char_count":proj_char_count, "proj_seg_count":proj_seg_count,\
                                "task_words" : task_words }

    @staticmethod
    def get_data_from_analysis(project):
        out = TaskDetails.objects.filter(project_id=project.id).aggregate(Sum('task_word_count'),Sum('task_char_count'),Sum('task_seg_count'))
        task_words = []
        for task in project.get_mtpe_tasks:
            task_words.append({task.id : task.task_details.first().task_word_count})
        return {"proj_word_count": out.get('task_word_count__sum'), "proj_char_count":out.get('task_char_count__sum'), \
                        "proj_seg_count":out.get('task_seg_count__sum'),
                        "task_words":task_words}

    @staticmethod
    def get_analysed_data(project_id):
        project = Project.objects.get(id=project_id)
        if project.is_all_doc_opened:
            return ProjectAnalysisProperty.get_data_from_docs(project)
        else:
            return ProjectAnalysisProperty.get_data_from_analysis(project)

    @staticmethod
    def analyse_project(project_id):
        project = Project.objects.get(id=project_id)
        project_tasks = Project.objects.get(id=project_id).get_mtpe_tasks
        print("ProjectTasks----------->",project_tasks)
        tasks = []
        for _task in project_tasks:
            if _task.task_details.first() == None:
                tasks.append(_task)
        task_words = []
        file_ids = []

        for task in tasks:
            if task.file_id not in file_ids:
                print("Inside api_views If")
                ser = TaskSerializer(task)
                data = ser.data
                ProjectAnalysisProperty.correct_fields(data)
                # DocumentViewByTask.correct_fields(data)
                params_data = {**data, "output_type": None}
                res_paths = get_res_path(params_data["source_language"])
                doc = requests.post(url=f"http://{spring_host}:8080/getDocument/", data={
                    "doc_req_params":json.dumps(params_data),
                    "doc_req_res_params": json.dumps(res_paths)
                })

                try:
                    print("status----->",doc.status_code)
                    if doc.status_code == 200 :
                        doc_data = doc.json()
                        #print("Doc Data---------------->",doc_data)
                        #if doc_data["total_word_count"] >= 50000:

                        task_write_data = json.dumps(doc_data, default=str)
                        write_doc_json_file.apply_async((task_write_data, task.id))

                        task_detail_serializer = TaskDetailSerializer(data={"task_word_count":doc_data.get('total_word_count', 0),
                                                                "task_char_count":doc_data.get('total_char_count', 0),
                                                                "task_seg_count":doc_data.get('total_segment_count', 0),
                                                                "task": task.id,"project":project_id}
                                                                     )

                        if task_detail_serializer.is_valid(raise_exception=True):
                            task_detail_serializer.save()
                        else:
                            print("error-->", task_detail_serializer.errors)
                    else:
                        logger.debug(msg=f"error raised while process the document, the task id is {task.id}")
                        raise  ValueError("Sorry! Something went wrong with file processing.")
                except:
                    print("No entry")
                file_ids.append(task.file_id)

            else:
                print("*************  File taken only once  **************")
                tasks = [i for i in Task.objects.filter(file_id=task.file_id)]
                task_details = TaskDetails.objects.filter(task__in = tasks).first()
                task_details.pk = None
                task_details.task_id = task.id
                task_details.save()
                # task_words.append({task.id : task_details.task_word_count})

        [task_words.append({task.id : task.task_details.first().task_word_count})for task in project.get_mtpe_tasks]
        out = TaskDetails.objects.filter(project_id=project_id).aggregate(Sum('task_word_count'),Sum('task_char_count'),Sum('task_seg_count'))
        print("Out--------->",out)
        return {"proj_word_count": out.get('task_word_count__sum'), "proj_char_count":out.get('task_char_count__sum'), \
                        "proj_seg_count":out.get('task_seg_count__sum'),
                        "task_words":task_words}

    @staticmethod
    def get(project_id):

        if bool(Project.objects.get(id=project_id).is_proj_analysed):
            return ProjectAnalysisProperty.get_analysed_data(project_id)
        else:
            return ProjectAnalysisProperty.analyse_project(project_id)

#######################################

class ProjectAnalysis(APIView):

    permission_classes = [IsAuthenticated]
    def get(self, request, project_id):
        return Response(ProjectAnalysisProperty.get(project_id))

#########################################


## PROJECT ANALYSIS FOR WEIGHTED WORD COUNT
# class AnalyseProject(APIView):
#     permission_classes = [IsAuthenticated]
#
#     def get(self, reqeust, project_id):



def msg_send(sender,receiver,task,step):
    obj = Task.objects.get(id=task)
    work = "Post Editing" if int(step) == 1 else "Reviewing"
    proj = obj.job.project.project_name
    thread_ser = ThreadSerializer(data={'first_person':sender.id,'second_person':receiver.id})
    if thread_ser.is_valid():
        thread_ser.save()
        thread_id = thread_ser.data.get('id')
    else:
        thread_id = thread_ser.errors.get('thread_id')
    #print("Thread--->",thread_id)
    if thread_id:
        message = "You have been assigned a new task in "+proj+ " for "+ work +"."
        msg = ChatMessage.objects.create(message=message,user=sender,thread_id=thread_id)
        notify.send(sender, recipient=receiver, verb='Message', description=message,thread_id=int(thread_id))

class TaskAssignUpdateView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def update(self, request,pk=None):
        task = request.POST.get('task')
        step = request.POST.get('step')
        reassigned = request.POST.get('reassigned',False)
        file = request.FILES.getlist('instruction_file')
        req_copy = copy.copy( request._request)
        req_copy.method = "DELETE"

        file_delete_ids = self.request.query_params.get(\
            "file_delete_ids", [])

        # if not reassigned:reassigned = False
        # else: reassigned = True
        print("Reassigned-------->",reassigned)
        if file_delete_ids:
            file_res = InstructionFilesView.as_view({"delete": "destroy"})(request=req_copy,\
                        pk='0', many="true", ids=file_delete_ids)
        if not task:
            return Response({'msg':'Task Id required'},status=status.HTTP_400_BAD_REQUEST)
        # try:
        task_assign = TaskAssign.objects.get(Q(task_id = task) & Q(step_id = step) & Q(reassigned=reassigned))
        if file:
            serializer =TaskAssignUpdateSerializer(task_assign,data={**request.POST.dict(),'files':file},context={'request':request},partial=True)
        else:
            serializer =TaskAssignUpdateSerializer(task_assign,data={**request.POST.dict()},context={'request':request},partial=True)
        if serializer.is_valid():
            serializer.save()
            if request.POST.get('account_raw_count'):
                print("##################RAw")
                weighted_count_update.apply_async((None,None,task_assign.task_assign_info.assignment_id,),)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # except:
            # return Response({'msg':'Task Assign details not found'},status=status.HTTP_400_BAD_REQUEST)
        return Response(task, status=status.HTTP_200_OK)



@api_view(['POST',])
@permission_classes([IsAuthenticated])
def bulk_task_accept(request):
    task_accept_detail = request.POST.get('task_accept_detail')
    task_accept_detail = json.loads(task_accept_detail)
    for i in task_accept_detail:
        try:
            task_assign = TaskAssign.objects.get(Q(task_id = i.get('task')) & Q(step_id = i.get('step')) & Q(reassigned=i.get('reassigned'))) 
            print("TaskAssign--------->",task_assign)
            serializer =  TaskAssignUpdateSerializer(task_assign,data={'task_ven_status':'task_accepted'},context={'request':request},partial=True)
            if serializer.is_valid():
                serializer.save()
            else:
                print("Error--------->",serializer.errors)
        except:
            pass
    return Response({'msg':'Task Accept Succeded'})

class TaskAssignInfoCreateView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self,request):
        tasks = request.GET.getlist('tasks')
        step = request.GET.get('step')
        reassigned = request.GET.get('reassigned',False)
        try:
            task_assign_info = TaskAssignInfo.objects.filter(Q(task_assign__task_id__in = tasks) & Q(task_assign__reassigned = reassigned))
            # task_assign_info = TaskAssignInfo.objects.filter(Q(task_assign__task_id__in = tasks) & Q(task_assign__step_id =step))
        except TaskAssignInfo.DoesNotExist:
            return HttpResponse(status=404)
        # print('trtrt',task_assign_info)
        ser = TaskAssignInfoSerializer(task_assign_info,many=True)
        return Response(ser.data)

    def history(self,instance):
        segment_count=0 if instance.task_assign.task.document == None else instance.task_assign.task.get_progress.get('confirmed_segments')
        task_history = TaskAssignHistory.objects.create(task_assign =instance.task_assign,\
                                                        previous_assign_id=instance.task_assign.assign_to_id,\
                                                        task_segment_confirmed=segment_count,unassigned_by=self.request.user)


    def reassign_check(self,tasks):
        user = self.request.user.team.owner if self.request.user.team else self.request.user
        #plan = get_plan_name(self.request.user)
        #team = self.request.user.team
        if user.is_agency == True:
            for i in tasks:
                print(i)
                if TaskAssignInfo.objects.filter(task_assign__task = i).filter(task_assign__reassigned=False).exists() == False:
                    return "There is no assign. you can't reassign" 
            return None
        else:
            return "user is not an agency. Reassign is not allowed"
        

        

    @integrity_error
    def create(self,request):
        step = request.POST.get('step')
        task_assign_detail = request.POST.get('task_assign_detail')
        files=request.FILES.getlist('instruction_file')
        sender = self.request.user
        receiver = request.POST.get('assign_to')
        reassign = request.POST.get('reassigned') 
        print("Reassign----->",reassign)
        Receiver = AiUser.objects.get(id = receiver)
        data = request.POST.dict()
        ################################Need to change########################################
        user = request.user.team.owner  if request.user.team  else request.user
        if Receiver.email == 'ailaysateam@gmail.com':
            HiredEditors.objects.get_or_create(user_id=user.id,hired_editor_id=receiver,defaults = {"role_id":2,"status":2,"added_by_id":request.user.id})
        ##########################################################################################
        # task = request.POST.getlist('task')
        hired_editors = sender.get_hired_editors if sender.get_hired_editors else []

        # job_id = Task.objects.get(id=tasks[0]).job.id
        assignment_id = create_assignment_id()
        extra = {'assignment_id':assignment_id,'files':files}
        final =[]
        task_assign_detail = data.pop('task_assign_detail')
        task_assign_detail = json.loads(task_assign_detail)
        tasks = list(itertools.chain(*[d['tasks'] for d in task_assign_detail]))
        print("Tasks------->",tasks)
        # For authorization
        tsks = Task.objects.filter(id__in=tasks)
        for tsk in tsks:
            authorize(request, resource=tsk, actor=request.user, action="read")

        if reassign == 'true':
            print("Inside")
            msg = self.reassign_check(tasks)
            print("Msg------>",msg)
            if msg:
                return Response({'Error':msg},status=400)
        # tasks= task_assign_detail[0].get('tasks')
        for i in task_assign_detail:
            i.update(data)
            i.update(extra)
            final.append(i)
        with transaction.atomic():
            serializer = TaskAssignInfoSerializer(data=final,context={'request':request},many=True)
            if serializer.is_valid():
                serializer.save()
                weighted_count_update.apply_async((receiver,sender.id,assignment_id),)
                try:msg_send(sender,Receiver,tasks[0],step)
                except:pass
                # if Receiver in hired_editors:
                #     ws_forms.task_assign_detail_mail(Receiver,assignment_id)
                # notify.send(sender, recipient=Receiver, verb='Task Assign', description='You are assigned to new task.check in your project list')
                return Response({"msg":"Task Assigned"})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def update(self, request,pk=None):
    #     task = request.POST.get('task')
    #     step = request.POST.get('step')
    #     file = request.FILES.getlist('instruction_file')
    #     req_copy = copy.copy( request._request)
    #     req_copy.method = "DELETE"
    #
    #     if not task:
    #         return Response({'msg':'Task Id required'},status=status.HTTP_400_BAD_REQUEST)
    #
    #     file_delete_ids = self.request.query_params.get(\
    #         "file_delete_ids", [])
    #
    #     if file_delete_ids:
    #         file_res = InstructionFilesView.as_view({"delete": "destroy"})(request=req_copy,\
    #                     pk='0', many="true", ids=file_delete_ids)
    #
    #     task_assign = TaskAssign.objects.filter(Q(task_id = task) & Q(step_id = step)).first()
    #     task_assign_info = TaskAssignInfo.objects.get(task_assign_id = task_assign.id)
    #     if file:
    #         serializer =TaskAssignInfoSerializer(task_assign_info,data={**request.POST.dict(),'files':file},context={'request':request},partial=True)
    #     else:
    #         serializer =TaskAssignInfoSerializer(task_assign_info,data={**request.POST.dict()},context={'request':request},partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #     else:
    #         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #     return Response(task, status=status.HTTP_200_OK)
    # def update(self, request,pk=None):
    #     task = request.POST.getlist('task')
    #     file = request.FILES.get('instruction_file')
    #     assign_to = request.POST.get('assign_to',None)
    #     if not task:
    #         return Response({'msg':'Task Id required'},status=status.HTTP_400_BAD_REQUEST)
    #     ###############################Need to change############################################
    #     if assign_to:
    #         Receiver = AiUser.objects.get(id = assign_to)
    #         user = request.user.team.owner  if request.user.team  else request.user
    #         if Receiver.email == 'ailaysateam@gmail.com':
    #             HiredEditors.objects.get_or_create(user_id=user.id,hired_editor_id=assign_to,defaults = {"role_id":2,"status":2,"added_by_id":request.user.id})
    #     ###########################################################################################
    #     for i in task:
    #         try:
    #             task_assign_info = TaskAssignInfo.objects.get(task_id = i)
    #             if file:
    #                 serializer =TaskAssignInfoSerializer(task_assign_info,data={**request.POST.dict(),'instruction_file':file},context={'request':request},partial=True)
    #             else:
    #                 serializer =TaskAssignInfoSerializer(task_assign_info,data={**request.POST.dict()},context={'request':request},partial=True)
    #             if serializer.is_valid():
    #                 serializer.save()
    #             else:
    #                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #         except TaskAssignInfo.DoesNotExist:
    #             print('not exist')
    #     return Response(task, status=status.HTTP_200_OK)

    def delete(self,request):
        task = request.GET.getlist('task')
        steps = request.GET.getlist('step')
        reassigned = request.GET.get('reassigned',False)
        print("reassign---->",reassigned)
        task_assign_info_ids = request.GET.getlist('task_assign_info')
        if task and steps:
            assigns = TaskAssignInfo.objects.filter(Q(task_assign__task_id__in=task) & Q(task_assign__step_id__in=steps) & Q(task_assign__reassigned=reassigned))
        if task_assign_info_ids:
            assigns = TaskAssignInfo.objects.filter(id__in = task_assign_info_ids )
        for obj in assigns:
            authorize(request, resource=obj, actor=request.user, action="read")
            try:
                po_modify(obj.id,['unassigned',])
            except BaseException as e:
                logger.error(f"po unassign error id :{obj.id} -ERROR:{str(e)}")
            user = obj.task_assign.task.job.project.ai_user
            with transaction.atomic():
                try:self.history(obj)
                except:pass
                if obj.task_assign.reassigned == True:
                    print("Inside IF")
                    obj.task_assign.assign_to = self.request.user.team.owner if self.request.user.team else self.request.user #if unassigned..it is assigned back to LSP 
                    obj.task_assign.status = 1
                    obj.task_assign.client_response = None
                    obj.task_assign.save()
                    role = get_assignment_role(obj.task_assign.step,obj.task_assign.reassigned)
                    assigned_user = obj.task_assign.assign_to
                    unassign_task(assigned_user,role,obj.task_obj)   
                    obj.delete()
                else:
                    print("Inside Else")
                    reassigns = TaskAssign.objects.filter(Q(task=obj.task_assign.task) & Q(step=obj.task_assign.step) & Q(reassigned = True))
                    print("reassigns in delete---------->",reassigns)
                    if reassigns:
                        try:obj_1 = reassigns.first().task_assign_info
                        except:obj_1=None
                        print("obj------->",obj_1)
                        if obj_1:
                            self.history(obj_1)
                            print("Usr------>",user)
                            obj_1.task_assign.assign_to = user
                            obj_1.task_assign.status = 1
                            obj_1.task_assign.client_response = None
                            obj_1.task_assign.save()
                            print("YYYYYYY-------->",obj_1.task_assign)
                            obj_1.delete()
                        else:
                            print("Usr111------>",user)
                            rr = reassigns.first()
                            rr.assign_to = user
                            rr.save()
                            print("save")
                    assigned_user = obj.task_assign.assign_to
                    print("Usrrr------>",user)
                    obj.task_assign.assign_to = user
                    obj.task_assign.status = 1
                    obj.task_assign.client_response = None
                    obj.task_assign.save()
                    # role= AiRoleandStep.objects.get(step=obj.task_assign.step).role.name
                    role = get_assignment_role(obj.task_assign.step,obj.task_assign.reassigned)
                    unassign_task(assigned_user,role,obj.task_obj)             
                    obj.delete()
                
        return Response({"msg":"Tasks Unassigned Successfully"},status=200)


@api_view(['GET',])
@permission_classes([IsAuthenticated])
def get_assign_to_list(request):
    project = request.GET.get('project')
    job_id = request.GET.get('job',None)
    proj = Project.objects.get(id = project)
    jobs = Job.objects.filter(id = job_id) if job_id else proj.get_jobs
    internalmembers = []
    hirededitors = []
    try:
        internal_team = proj.ai_user.team.internal_member_team_info.filter(role = 2).order_by('id')
        for i in internal_team:
            try:profile = i.internal_member.professional_identity_info.avatar_url
            except:profile = None
            internalmembers.append({'name':i.internal_member.fullname,'id':i.internal_member_id,\
                                    'status':i.get_status_display(),'avatar': profile})
    except:
        print("No team")
    external_team = proj.ai_user.team.owner.user_info.filter(role=2) if proj.ai_user.team else proj.ai_user.user_info.filter(role=2)
    print(external_team)
    hirededitors = find_vendor(external_team,jobs)
    return JsonResponse({'internal_members':internalmembers,'Hired_Editors':hirededitors})

def find_vendor(team,jobs):
    for j in team:
        for job in jobs:
            try:profile = j.hired_editor.professional_identity_info.avatar_url
            except:profile = None
            vendor = j.hired_editor.vendor_lang_pair.filter(Q(source_lang_id=job.source_language.id)&Q(target_lang_id=job.target_language.id)&Q(deleted_at=None))
            if vendor:
                externalmembers.append({'name':j.hired_editor.fullname,'id':j.hired_editor_id,'status':j.get_status_display(),"avatar":profile,\
                                        'lang_pair':job.source_language.language+'->'+job.target_language.language,\
                                        'unique_id':j.hired_editor.uid})
    return externalmembers
    # if proj.team:
    #     internal_team = proj.team.internal_member_team_info.filter(role = 2)
    #     for i in internal_team:
    #         internalmembers.append({'name':i.internal_member.fullname,'id':i.internal_member_id,'status':i.status})
    #     external_team = proj.team.owner.user_info.filter(role =2)
    #     print(external_team)
    #     HiredEditors = find_vendor(external_team,job)
    # else:
    #     external_team = proj.ai_user.user_info.filter(role=2)
    #     print(external_team)
    #     HiredEditors = find_vendor(external_team,job)

    # return JsonResponse({'internal_members':internalmembers,'Hired_Editors':hirededitors})

# def find_vendor(team,job):
#     externalmembers=[]
#     for j in team:
#         try:
#             profile = j.hired_editor.professional_identity_info.avatar_url
#         except:
#             profile = None
#         vendor = j.hired_editor.vendor_lang_pair.filter(Q(source_lang_id=job.source_language.id)&Q(target_lang_id=job.target_language.id)&Q(deleted_at=None))
#         if vendor:
#             externalmembers.append({'name':j.hired_editor.fullname,'id':j.hired_editor_id,'status':j.get_status_display(),"avatar":profile})
#     return externalmembers

# class ProjectListFilter(django_filters.FilterSet):

#     def filter(self, qs, value):
#         print("$$$$$$$$$$$$$$",value)
#         tt =  (pr for pr in qs if pr.get_assignable_tasks_exists == True)
#         qs = super().filter(tt, value)
#         return qs


class ProjectListView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectListSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    paginator = PageNumberPagination()
    paginator.page_size = 20
    search_fields = ['project_name','id']
    #filterset_class = ProjectListFilter

    def get_queryset(self):
        print(self.request.user)
        queryset = Project.objects.prefetch_related('project_jobs_set','project_jobs_set__job_tasks_set__task_info').filter(Q(ai_user = self.request.user)|Q(team__owner = self.request.user)\
                    |Q(team__internal_member_team_info__in = self.request.user.internal_member.filter(role=1))).distinct().order_by('-id').only('id','project_name')
        return queryset


    def list(self,request):
        queryset = self.filter_queryset(self.get_queryset())
        #filtered = [pr for pr in queryset if pr.get_assignable_tasks_exists == True]
        pagin_tc = self.paginator.paginate_queryset(queryset, request , view=self)
        serializer = ProjectListSerializer(pagin_tc, many=True, context={'request': request})
        data_1 = [i for i in serializer.data if i.get('assignable')==True ]
        response = self.get_paginated_response(data_1)
        return response
        # queryset = self.get_queryset()
        # filtered = (pr for pr in queryset if pr.get_assignable_tasks_exists == True)
        # serializer = ProjectListSerializer(filtered, many=True, context={'request': request})
        # return  Response(serializer.data)

        

# @permission_classes([IsAuthenticated])
# @api_view(['GET',])
# def get_file_project_list(request):
class WriterProjectListView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectListSerializer
    paginator = PageNumberPagination()
    paginator.page_size = 20

    def list(self,request):
        queryset = Project.objects.filter(Q(ai_user = request.user)|Q(team__owner = request.user)\
                        |Q(team__internal_member_team_info__in = request.user.internal_member.filter(role=1))).filter(project_type_id__in=[1,2]).distinct().order_by('-id')
        pagin_tc = self.paginator.paginate_queryset(queryset, request , view=self)
        serializer = ProjectListSerializer(pagin_tc, many=True, context={'request': request})
        response = self.get_paginated_response(serializer.data)
        return response



@permission_classes([IsAuthenticated])
@api_view(['GET',])####changed
def tasks_list(request):
    job_id = request.GET.get("job")
    project_id = request.GET.get('project')
    if job_id:
        job = Job.objects.get(id = job_id)
        project_id = job.project.id
    vbd = VendorDashBoardView
    res = vbd.get_tasks_by_projectid(request=request,pk=project_id)
    if job_id:
        res = [i for i in res if i.job == job ]
    print("res----->",res)
    try:
        tasks=[]
        for task in res:
            if (task.job.target_language == None):
                if (task.file.get_file_extension == '.mp3'):
                    tasks.append(task)
                else:pass
            else:tasks.append(task)
        print("Tasks----------->",tasks)
        ser = VendorDashBoardSerializer(tasks,many=True,context={'request':request})
        return Response(ser.data)
    except:
        return JsonResponse({"msg":"something went wrong"})


    # for i in tasks:
    #     task_list.append({'id':i.id,'task':i.job,'file':i.file})
    # return Response(task_list)
@api_view(['GET',])
def instruction_file_download(request,instruction_file_id):
    instruction_file = Instructionfiles.objects.get(id=instruction_file_id).instruction_file
    if instruction_file:
        return download_file(instruction_file.path)
        # fl_path = instruction_file.path
        # filename = os.path.basename(fl_path)
        # # print(os.path.dirname(fl_path))
        # fl = open(fl_path, 'rb')
        # mime_type, _ = mimetypes.guess_type(fl_path)
        # response = HttpResponse(fl, content_type=mime_type)
        # response['Content-Disposition'] = "attachment; filename=%s" % filename
        # return response
    else:
        return JsonResponse({"msg":"no file associated with it"})

#
# @api_view(['GET',])
# def instruction_file_list_download(request):
#     file_ids = request.GET.get('file_ids')
#     file_list = file_ids.split(',')
#     file_objs = Instructionfiles.objects.get(id__in=file_list)
#     zipObj = ZipFile('sample.zip', 'w')
#     for i in file_objs:
#         print(i.instruction_file)
#         zipObj.write(i.instruction_file)
#     zipObj.close()
#     # if instruction_file:
#     #     fl_path = instruction_file.path
#     #     filename = os.path.basename(fl_path)
#     #     # print(os.path.dirname(fl_path))
#     fl = open('sample.zip', 'rb')
#     mime_type, _ = mimetypes.guess_type(fl_path)
#     response = HttpResponse(fl, content_type=mime_type)
#     response['Content-Disposition'] = "attachment; filename=%s" % filename
#     return response
#     else:
#         return JsonResponse({"msg":"no file associated with it"})

class AssignToListView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    def list(self, request, *args, **kwargs):
        project = self.request.GET.get('project')
        job = self.request.GET.getlist('job')
        reassign = self.request.GET.get('reassign',None)
        pro = Project.objects.get(id = project)
        try:
            job_obj = Job.objects.filter(id__in = job).first() #need to work
            #authorize(request, resource=job_obj, actor=request.user, action="read")
        except Job.DoesNotExist:
            pass
        #authorize(request, resource=pro, actor=request.user, action="read")
        if reassign:
            user = self.request.user.team.owner if self.request.user.team else self.request.user
            serializer = GetAssignToSerializer(user,context={'request':request,'pro_user':pro.ai_user})
        else:
            user =pro.ai_user   
            serializer = GetAssignToSerializer(user,context={'request':request})
        print("User----------->",user) 
        #serializer = GetAssignToSerializer(user,context={'request':request})
        return Response(serializer.data, status=201)

# class IntegerationProject(viewsets.ViewSet):

#     def list(self, request, *args, **kwargs):
#         project_id = self.kwargs.get("pk", None)
#         #  ownership
#         project = get_object_or_404(Project.objects.all(),
#             id=project_id)
#         #  ownership
#         download_project = project.project_download.\
#             get_download

#         serlzr_class = serializer_map.get(
#             download_project.serializer_class_str)

#         serlzr = serlzr_class(download_project.branch.branch_contentfiles_set
#             .all(), many=True)

#         return Response(serlzr.data)












class InstructionFilesView(viewsets.ModelViewSet):

    serializer_class = InstructionfilesSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_object(self, many=False):
        objs = []
        obj = None
        if not many:
            try:
                obj = get_object_or_404(Instructionfiles.objects.all(),\
                    id=self.kwargs.get("pk"))
            except:
                raise Http404
            return  obj

        objs_ids_list =  self.kwargs.get("ids").split(",")

        for obj_id in objs_ids_list:
            print("obj id--->", obj_id)
            try:
                objs.append(get_object_or_404(Instructionfiles.objects.all(),\
                    id=obj_id))
            except:
                raise Http404
        return objs

    def destroy(self, request, *args, **kwargs):
        if kwargs.get("many")=="true":
            objs = self.get_object(many=True)
            for obj in objs:
                obj.delete()
            return Response(status=204)
        return super().destroy(request, *args, **kwargs)


class StepsView(viewsets.ViewSet):
    permission_classes = [AllowAny,]
    def list(self,request):
        queryset = Steps.objects.all()
        serializer = StepsSerializer(queryset,many=True)
        return Response(serializer.data)


class CustomWorkflowCreateView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def list(self,request):
        queryset = Workflows.objects.all()
        serializer = WorkflowsSerializer(queryset,many=True)
        return Response(serializer.data)

    def create(self,request):
        steps = request.POST.getlist('steps')
        serializer = WorkflowsStepsSerializer(data={**request.POST.dict(),"user":self.request.user.id,"steps":steps})
        if serializer.is_valid():
            serializer.save()
            return Response({"msg":"workflow created"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self,request,pk):
        queryset = Workflows.objects.all()
        steps = request.POST.getlist('steps')
        step_delete_ids = request.POST.getlist('step_delete_ids')
        workflow = get_object_or_404(queryset, pk=pk)
        if step_delete_ids:
            [WorkflowSteps.objects.filter(workflow=workflow,steps=i).delete() for i in step_delete_ids]
        serializer= WorkflowsStepsSerializer(workflow,data={**request.POST.dict(),"steps":steps},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    def delete(self,request,pk):
        queryset = Workflows.objects.all()
        obj = get_object_or_404(queryset, pk=pk)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
def previously_created_steps(request):
    used_steps = []
    pr = Project.objects.filter(Q(created_by = request.user)\
         & Q(proj_steps__isnull=False) & ~Q(project_type=1)).distinct()
    for obj in pr:
        if obj.get_steps_name not in [step for step in used_steps]:
            used_steps.append(obj.get_steps_name)
    return Response({'used_steps':used_steps})

# @api_view(["GET"])
# def project_download(request,project_id):
#     pr = Project.objects.get(id=project_id)
#     if os.path.exists(os.path.join(pr.project_dir_path,'source')):
#         shutil.make_archive(pr.project_name, 'zip', pr.project_dir_path + '/source')
#         res = download_file(pr.project_name+'.zip')
#         os.remove(pr.project_name+'.zip')
#         return res
#     else:
#         return Response({'msg':'something went wrong'})


def file_write(pr):
    for i in pr.get_tasks:
        express_obj = ExpressProjectDetail.objects.filter(task=i).first()
        file_name,ext = os.path.splitext(i.file.filename)
        target_filename = file_name + "_out" +  "(" + i.job.source_language_code + "-" + i.job.target_language_code + ")" + ext
        target_filepath = os.path.join(pr.project_dir_path,'source',target_filename)
        source_filename = file_name + "_source" +  "(" + i.job.source_language_code + "-" + i.job.target_language_code + ")" + ext
        source_filepath = os.path.join(pr.project_dir_path,'source',source_filename)
        print("SRC--------->",express_obj.source_text)
        if express_obj.source_text:
            with open(source_filepath,'w') as f:
                f.write(express_obj.source_text)
        if express_obj.target_text:
            #print("File Path--------------->",target_filepath)
            with open(target_filepath,'w') as f:
                f.write("Source:" + "\n")
                f.write(express_obj.source_text) 
                f.write('\n')
                f.write("---------" + "\n")
                f.write("Target:" + "\n\n")
                f.write("Standard:" + "\n")
                target = express_obj.target_text if express_obj.target_text else ''
                f.write(target)
                f.write('\n')
                f.write("---------" + "\n")
                shorten_obj =express_obj.express_src_text.filter(customize__customize='Shorten')
                if shorten_obj.exists():
                    f.write("Shortened:" + "\n")
                    f.write(shorten_obj.last().final_result)
                    f.write("\n")
                    f.write("---------" + "\n")
                simplified_obj = express_obj.express_src_text.filter(customize__customize='Simplify')
                if simplified_obj.exists():
                    f.write("Simplified:" + "\n")
                    f.write(simplified_obj.last().final_result)
                    f.write("\n")
                    f.write("---------" + "\n")


@api_view(["GET"])
#@permission_classes([AllowAny])
def project_download(request,project_id):
    pr = Project.objects.get(id=project_id)
    if pr.project_type_id == 5:
        file_write(pr)

    elif pr.project_type_id not in [3,5]:
        print("Tasks--------->",pr.get_mtpe_tasks)
        for i in pr.get_mtpe_tasks:
            if i.document:
                print("DOC---------->",i.document.id)
                from ai_workspace_okapi.api_views import DocumentToFile
                res_1 = DocumentToFile.document_data_to_file(request,i.document.id)
                print("Res----------->",res_1)
    if os.path.exists(os.path.join(pr.project_dir_path,'source')):
        print("path Exists--------->",os.path.join(pr.project_dir_path,'source'))
        shutil.make_archive(pr.project_name, 'zip', pr.project_dir_path + '/source')
        if os.path.exists(os.path.join(pr.project_dir_path,'Audio')):
            shutil.make_archive(pr.project_name, 'zip', pr.project_dir_path + '/Audio')
        res = download_file(pr.project_name+'.zip')
        os.remove(pr.project_name+'.zip')
        return res
    else:
        return Response({'msg':'something went wrong'},status=400)
    # else:
    #     return Response({'msg':'project download not available'},status=400)


class ShowMTChoices(APIView):
    permission_classes = [AllowAny]

    @staticmethod
    def get_lang_code(lang_id):
        return LanguagesLocale.objects.filter(language_id = lang_id).first().locale_code

    @staticmethod
    def reduce_text(text,lang_code):
        punctuation='''!"#$%&'``()*+,-./:;<=>?@[\]^`{|}~_'''
        info =''
        lang_list = ['hi','bn','or','ne','pa']
        if lang_code in lang_list:
            sents = sentence_split(text, lang_code, delim_pat='auto')
            # sents = regex.split(u"([.।?!])?[\n]+|[.।?!] ", text)
        else:
            sents = nltk.sent_tokenize(text)
        for i in sents:
            info =info +' '+ i
            nltk_tokens = nltk.word_tokenize(info)
            count = len([word for word in nltk_tokens if word not in punctuation])
            #print("Count------------>",count)
            if count in range(90,100) or count>100:
                return info.lstrip()
            else:
                continue
        return info.lstrip()


    def post(self, request):
        user = None if request.user.is_anonymous == True else request.user
        data = request.POST.dict()
        text = data.get("text", "")
        target_languages = json.loads(data["target_language"])
        sl_code = json.loads(data["source_language"])
        text_1 = self.reduce_text(text,self.get_lang_code(sl_code))
        # print("###",text_1)
        res = {}
        for tl in target_languages:
            mt_responses = {}
            for mt_engine in AilaysaSupportedMtpeEngines.objects.all():
                if user:
                    initial_credit = user.credit_balance.get("total_left")
                    consumable_credits =  get_consumable_credits_for_text(text_1,source_lang=self.get_lang_code(sl_code),target_lang=self.get_lang_code(tl))
                    #print("Before Deduction","Initial--->",initial_credit,"Consumable---->",consumable_credits)
                    if initial_credit > consumable_credits:
                        try:
                            mt_responses[mt_engine.name] = get_translation(mt_engine.id, text_1, ShowMTChoices.get_lang_code(sl_code), ShowMTChoices.get_lang_code(tl),user_id=user.id)
                        except:
                            mt_responses[mt_engine.name] = None
                        #debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)
                    else:
                        mt_responses[mt_engine.name] = 'Insufficient Credits'
                    #print("After Deduction","Initial--->",initial_credit)
                    res[tl] = mt_responses
                else:
                    try:
                        mt_responses[mt_engine.name] = get_translation(mt_engine.id, text_1, ShowMTChoices.get_lang_code(sl_code), ShowMTChoices.get_lang_code(tl))
                    except:
                        mt_responses[mt_engine.name] = None
                    res[tl] = mt_responses
                    
        return Response(res, status=status.HTTP_200_OK)


###########################Transcribe Short File############################## #######

def transcribe_short_file(speech_file,source_code,obj,length,user,hertz):
    client = speech.SpeechClient()

    with io.open(speech_file, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)

    sample_hertz = hertz if hertz >= 48000 else 8000

    config = speech.RecognitionConfig(encoding=speech.RecognitionConfig.AudioEncoding.MP3,sample_rate_hertz=sample_hertz,language_code=source_code, enable_automatic_punctuation=True,)
    try:
        response = client.recognize(config=config, audio=audio)
        transcript=''
        for result in response.results:
            print(u"Transcript: {}".format(result.alternatives[0].transcript))
            transcript += result.alternatives[0].transcript
        file_length = int(response.total_billed_time.seconds)
        print("Length return from api--------->",file_length)
        ser = TaskTranscriptDetailSerializer(data={"transcripted_text":transcript,"task":obj.id,"audio_file_length":file_length,"user":user.id})
        if ser.is_valid():
            ser.save()
            return (ser.data)
        return (ser.errors)
    except:
        return ({'msg':'Something  went wrong in Google Cloud Api'})

###########################Transcribe Long File##############################

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)


def delete_blob(bucket_name, blob_name):
    """Deletes a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)

    blob.delete()



def transcribe_long_file(speech_file,source_code,filename,obj,length,user,hertz):
    print("User Long-------->",user.id)
    bucket_name = os.getenv("BUCKET")
    source_file_name = speech_file
    destination_blob_name = filename

    upload_blob(bucket_name, source_file_name, destination_blob_name)

    gcs_uri = os.getenv("BUCKET_URL") + filename
    transcript = ''
    sample_hertz = hertz if hertz >= 48000 else 8000
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(uri=gcs_uri)

    config =  speech.RecognitionConfig(encoding=speech.RecognitionConfig.AudioEncoding.MP3,sample_rate_hertz=sample_hertz,language_code=source_code, enable_automatic_punctuation=True,)


    # Detects speech in the audio file
    operation = client.long_running_recognize(config=config, audio=audio)
    response = operation.result(timeout=10000)
    for result in response.results:
        transcript += result.alternatives[0].transcript
    file_length = int(response.total_billed_time.seconds)
    print("Len------->",file_length)
    print("Transcript--------->",transcript)

    delete_blob(bucket_name, destination_blob_name)

    ser = TaskTranscriptDetailSerializer(data={"transcripted_text":transcript,"task":obj.id,"audio_file_length":length,"user":user.id})
    if ser.is_valid():
        ser.save()
        return (ser.data)
    return (ser.errors)



################################speech-to-text############# working#############################3
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def transcribe_file(request):
    from ai_workspace.models import MTonlytaskCeleryStatus
    task_id = request.POST.get('task')
    user = request.user
    print("User---------->",user)
    target_language = request.POST.getlist('target_languages')
    queryset = TaskTranscriptDetails.objects.filter(task_id = task_id)
    print("QS--->",queryset)
    if queryset:#or state == 'SUCCESS':
        ser = TaskTranscriptDetailSerializer(queryset,many=True)
        return Response(ser.data)
    ins = MTonlytaskCeleryStatus.objects.filter(Q(task_id=task_id) & Q(task_name = 'transcribe_long_file_cel')).last()
    state = transcribe_long_file_cel.AsyncResult(ins.celery_task_id).state if ins else None
    print("State----------------------->",state)
    if state == 'PENDING' or state == 'STARTED':
        return Response({'msg':'Transcription is ongoing. Pls Wait','celery_id':ins.celery_task_id},status=400)
    else:
        obj = Task.objects.get(id = task_id)
        project = obj.job.project
        account_debit_user = project.team.owner if project.team else project.ai_user
        source = [obj.job.source_language.id]
        source_code = obj.job.source_language_code
        filename = obj.file.filename
        speech_file = obj.file.file.path
        try:
            audio = AudioSegment.from_file(speech_file)
            length = int(audio.duration_seconds)###seconds####
            hertz = audio.frame_rate
        except:
            length=None
        print("Length in main----->",length)
        if length==None:
            return Response({'msg':'something wrong in input file'},status=400)
        initial_credit = account_debit_user.credit_balance.get("total_left")
        consumable_credits = get_consumable_credits_for_speech_to_text(length)
        print("Initial----------------->",initial_credit)
        print("Consumable------------------>",consumable_credits)
        if initial_credit > consumable_credits:
            if length and length<60:
                res = transcribe_short_file(speech_file,source_code,obj,length,user,hertz)
                if res.get('msg') == None:
                    consumable_credits = get_consumable_credits_for_speech_to_text(res.get('audio_file_length'))
                    debit_status, status_code = UpdateTaskCreditStatus.update_credits(account_debit_user, consumable_credits)
            else:
                ins = MTonlytaskCeleryStatus.objects.filter(Q(task_id=obj.id) & Q(task_name = 'transcribe_long_file_cel')).last()
                state = transcribe_long_file_cel.AsyncResult(ins.celery_task_id).state if ins else None
                print("State----------------------->",state)
                if state == 'PENDING' or state == 'STARTED':
                    return Response({'msg':'Transcription is ongoing. Pls Wait','celery_id':ins.celery_task_id},status=400)
                elif (not ins) or state == 'FAILURE':#need to revert credits
                    res = transcribe_long_file_cel.apply_async((speech_file,source_code,filename,obj.id,length,user.id,hertz),)
                    debit_status, status_code = UpdateTaskCreditStatus.update_credits(account_debit_user, consumable_credits)
                    return Response({'msg':'Transcription is ongoing. Pls Wait','celery_id':res.id},status=400)
                elif state == 'SUCCESS':
                    ser = TaskTranscriptDetailSerializer(queryset,many=True)
                    return Response(ser.data)
            #debit_status, status_code = UpdateTaskCreditStatus.update_credits(account_debit_user, consumable_credits)
            print("RES----->",res)
            return JsonResponse(res,safe=False,json_dumps_params={'ensure_ascii':False})
        else:
            return Response({'msg':'Insufficient Credits'},status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def transcribe_file_get(request):
    task_id = request.GET.get('task')
    queryset = TaskTranscriptDetails.objects.filter(task_id = task_id)
    ser = TaskTranscriptDetailSerializer(queryset,many=True)
    return Response(ser.data)

def google_long_text_file_process(file,obj,language,gender,voice_name):
    print("Main func Voice Name---------->",voice_name)
    final_name,ext =  os.path.splitext(file)
    size_limit = 4000 #if obj.job.target_language_code in ['ta','ja'] else 3500
    #final_audio = final_name + '.mp3'
    #final_audio = final_name + "_" + obj.ai_taskid + "[" + obj.job.source_language_code + "-" + obj.job.target_language_code + "]" + ".mp3"
    final_audio = final_name  + "_" + obj.job.source_language_code + "-" + obj.job.target_language_code  + ".mp3"
    dir_1 = os.path.join('/ai_home/',"output")
    if not os.path.exists(dir_1):
        os.mkdir(dir_1)
    split = Split(file,dir_1)
    split.bysize(size_limit,True)
    for file in os.listdir(dir_1):
        filepath = os.path.join(dir_1, file)
        if file.endswith('.txt'):
            name,ext = os.path.splitext(file)
            dir = os.path.join('/ai_home/',"OutputAudio")
            if not os.path.exists(dir):
                os.mkdir(dir)
            audio_ = name + '.mp3'
            audiofile = os.path.join(dir,audio_)
            text_to_speech_long(filepath,language if language else obj.job.target_language_code ,audiofile,gender if gender else 'FEMALE',voice_name)
    list_of_audio_files = [AudioSegment.from_mp3(mp3_file) for mp3_file in sorted(glob('*/*.mp3'),key=lambda x: int(os.path.splitext(os.path.basename(x))[0].split('_')[-1]))]
    print("ListOfAudioFiles---------------------->",list_of_audio_files)
    combined = AudioSegment.empty()
    for aud in list_of_audio_files:
        combined += aud
    combined.export(final_audio, format="mp3")
    f2 = open(final_audio, 'rb')
    file_obj = DJFile(f2,name=os.path.basename(final_audio))
    shutil.rmtree(dir)
    shutil.rmtree(dir_1)
    #os.remove(final_audio)
    return file_obj,f2


def long_text_source_process(consumable_credits,user,file_path,task,language,voice_gender,voice_name):

    res1,f2 = google_long_text_source_file_process(file_path,task,language,voice_gender,voice_name)
    print("Consumable------------>",consumable_credits)
    #debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)
    ser = TaskTranscriptDetailSerializer(data={"source_audio_file":res1,"task":task.id,"user":user.id})
    if ser.is_valid():
        ser.save()
    print(ser.errors)
    f2.close()

#####################Need to work###########################################

def google_long_text_source_file_process(file,obj,language,gender,voice_name):
    print("Lang-------------->",obj.job.source_language_code)
    project_id  = obj.job.project.id
    final_name,ext =  os.path.splitext(file)
    lang_list = ['hi','bn','or','ne','pa']
    final_audio = final_name + "_" + obj.job.source_language_code  + ".mp3"#+ "_" + obj.ai_taskid
    dir_1 = os.path.join('/ai_home/',"Output_"+str(obj.id))
    if not os.path.exists(dir_1):
        os.mkdir(dir_1)
    count=0
    out_filename = final_name + '_out.txt'
    size_limit = 4000 #if obj.job.source_language_code in ['ta','ja'] else 3500
    with open(file) as infile, open(out_filename, 'w') as outfile:
        lines = infile.readlines()
        for line in lines:
            if obj.job.source_language_code in lang_list:sents = sentence_split(line, obj.job.source_language_code, delim_pat='auto')
            else:sents = nltk.sent_tokenize(line)
            for i in sents:
                outfile.write(i)
                count = count+len(i.encode("utf8"))
                if count > size_limit:
                    outfile.write('\n')
                    count=0
    split = Split(out_filename,dir_1)
    split.bysize(size_limit,True)
    for file in os.listdir(dir_1):
        filepath = os.path.join(dir_1, file)
        if file.endswith('.txt') :
            name,ext = os.path.splitext(file)
            dir = os.path.join('/ai_home/',"OutputAudio_"+str(obj.id))
            if not os.path.exists(dir):
                os.mkdir(dir)
            audio_ = name + '.mp3'
            audiofile = os.path.join(dir,audio_)
            print("ARGS--------->",filepath,language,obj.job.source_language_code,audiofile,gender,voice_name)
            rr = text_to_speech_long(filepath,language if language else obj.job.source_language_code ,audiofile,gender if gender else 'FEMALE',voice_name)
            #print("RR------------------------>",rr.status_code)
    list_of_audio_files = [AudioSegment.from_mp3(mp3_file) for mp3_file in sorted(glob('*/*.mp3'),key=lambda x: int(os.path.splitext(os.path.basename(x))[0].split('_')[-1])) if len(mp3_file)!=0]
    print("ListOfAudioFiles---------------------->",list_of_audio_files)
    combined = AudioSegment.empty()
    for aud in list_of_audio_files:
        combined += aud
    combined.export(final_audio, format="mp3")
    f2 = open(final_audio, 'rb')
    file_obj = DJFile(f2,name=os.path.basename(final_audio))
    shutil.rmtree(dir)
    shutil.rmtree(dir_1)
    os.remove(final_audio)
    os.remove(out_filename)
    return file_obj,f2



@api_view(["GET"])
#@permission_classes([IsAuthenticated])
def convert_and_download_text_to_speech_source(request):#########working############Transcribe and Download
    tasks =[]
    user = request.user
    project = request.GET.get('project',None)
    language = request.GET.get('language_locale',None)
    gender = request.GET.get('gender',None)
    pr = Project.objects.get(id=project)
    for _task in pr.get_source_only_tasks:
        if _task.task_transcript_details.first() == None:
            tasks.append(_task)
    for obj in tasks:
        text_to_speech_task(obj,language,gender,user,None)
    shutil.make_archive(pr.project_name, 'zip', pr.project_dir_path + '/source/Audio')
    res = download_file(pr.project_name+'.zip')
    os.remove(pr.project_name+'.zip')
    return res


def text_to_speech_task(obj,language,gender,user,voice_name):
    
    from ai_workspace.models import MTonlytaskCeleryStatus
    project = obj.job.project
    account_debit_user = project.team.owner if project.team else project.ai_user
    file,ext = os.path.splitext(obj.file.file.path)
    dir,name_ = os.path.split(os.path.abspath(file))
    if ext == '.docx':
        name = file + '.txt'
        data = docx2txt.process(obj.file.file.path)
        with open(name, "w") as out:
            out.write(data)
    else:
        name = obj.file.file.path
        text_file = open(name, "r")
        data = text_file.read()
        text_file.close()
    consumable_credits = get_consumable_credits_for_text_to_speech(len(data))
    initial_credit = account_debit_user.credit_balance.get("total_left")
    seg_data = {"segment_source":data, "source_language":obj.job.source_language_code, "target_language":obj.job.source_language_code,\
                 "processor_name":"plain-text-processor", "extension":".txt"}
    res1 = requests.post(url=f"http://{spring_host}:8080/segment/word_count", data={"segmentWordCountdata":json.dumps(seg_data)})
    wc = res1.json() if res1.status_code == 200 else None
    TaskDetails.objects.get_or_create(task = obj,project = obj.job.project,defaults = {"task_word_count": wc,"task_char_count":len(data)})
    print("Consumable Credits--------------->",consumable_credits)
    print("Initial Credits---------------->",initial_credit)
    if initial_credit > consumable_credits:
        if len(data.encode("utf8"))>4500:
            ins = MTonlytaskCeleryStatus.objects.filter(Q(task_id=obj.id) & Q(task_name='text_to_speech_long_celery')).last()
            state = text_to_speech_long_celery.AsyncResult(ins.celery_task_id).state if ins else None
            print("State--------------->",state)
            if state == 'PENDING' or state == 'STARTED':
                return Response({'msg':'Text to Speech conversion ongoing. Please wait','celery_id':ins.celery_task_id},status=400)
            elif (obj.task_transcript_details.exists()==False) or (not ins) or state == "FAILURE":
                if state == "FAILURE":
                    user_credit = UserCredits.objects.get(Q(user=user) & Q(credit_pack_type__icontains="Subscription") & Q(ended_at=None))
                    user_credit.credits_left = user_credit.credits_left + consumable_credits
                    user_credit.save()
                celery_task = text_to_speech_long_celery.apply_async((consumable_credits,account_debit_user.id,name,obj.id,language,gender,voice_name), )
                debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)
                return Response({'msg':'Text to Speech conversion ongoing. Please wait','celery_id':celery_task.id},status=400)
        else:
            audio_file = name_ + "_source" + "_" + obj.job.source_language_code + ".mp3"#+ "_" + obj.ai_taskid
            print("Args short------->",name,language,obj.job.source_language_code,audio_file,gender,voice_name)
            res2,f2 = text_to_speech(name,language if language else obj.job.source_language_code ,audio_file,gender if gender else 'FEMALE',voice_name)
            debit_status, status_code = UpdateTaskCreditStatus.update_credits(account_debit_user, consumable_credits)
            os.remove(audio_file)
            ser = TaskTranscriptDetailSerializer(data={"source_audio_file":res2,"task":obj.id,"user":user.id})
            if ext == '.docx':
                os.remove(name)
            if ser.is_valid():
                ser.save()
                f2.close()
                return Response(ser.data)
            f2.close()
            #os.remove(name)
            return Response(ser.errors)
    else:
        return Response({'msg':'Insufficient Credits'},status=400)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_media_link(request,task_id):
    obj = Task.objects.get(id = task_id)
    try:
        task_transcript_obj = TaskTranscriptDetails.objects.filter(task = obj).first()
        return Response({'url':task_transcript_obj.source_audio_file.url})
    except:
        return Response({'msg':'something went wrong'})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def convert_text_to_speech_source(request):
    task = request.GET.get('task')
    project  = request.GET.get('project')
    language = request.GET.get('language_locale',None)
    gender = request.GET.get('gender')
    voice_name = request.GET.get('voice_name')
    user = request.user
    if task:
        obj = Task.objects.get(id = task)
        tt = text_to_speech_task(obj,language,gender,user,voice_name)
        if tt!=None and tt.status_code == 400:
            return tt
        else:
            ser = TaskTranscriptDetailSerializer(obj.task_transcript_details.first())
            return Response(ser.data)
    if project:
        tasks =[]
        task_list = []
        pr = Project.objects.get(id=project)
        for _task in pr.get_source_only_tasks:
            if _task.task_transcript_details.first() == None:
                tasks.append(_task)
        if tasks:
            for obj in tasks:
                print("Obj-------------->",obj)
                conversion = text_to_speech_task(obj,language,gender,user,voice_name)
                print("Conv----------->",conversion)
                if conversion.status_code == 200:
                    task_list.append(obj.id)
                elif conversion.status_code == 400:
                    return conversion#Response({'msg':'Insufficient Credits'},status=400)
        queryset = TaskTranscriptDetails.objects.filter(task__in = pr.get_source_only_tasks)
        ser = TaskTranscriptDetailSerializer(queryset,many=True)
        return Response(ser.data)
    else:
        return Response({'msg':'task_id or project_id must'})
    # file = obj.task_transcript_details.first().source_audio_file
    # return download_file(file.path)

@api_view(["GET"])
#@permission_classes([IsAuthenticated])
def download_text_to_speech_source(request):
    task = request.GET.get('task')
    language = request.GET.get('language_locale',None)
    gender = request.GET.get('gender')
    user = request.user
    obj = Task.objects.get(id = task)
    # if obj.task_transcript_details.exists()==False:
    #     tt = text_to_speech_task(obj,language,gender,user)
    file = obj.task_transcript_details.first().source_audio_file
    return download_file(file.path)




@api_view(["GET"])
#@permission_classes([IsAuthenticated])
def download_speech_to_text_source(request):
    task = request.GET.get('task')
    obj = Task.objects.get(id = task)
    try:
        output_from_writer =  obj.task_transcript_details.first().transcripted_file_writer
        return download_file(output_from_writer.path)
        # text = obj.task_transcript_details.first().transcripted_text
        # with open('out.txt', "w") as out:
        #     out.write(text)
        # res = download_file('out.txt')
        # os.remove('out.txt')
        # return res
    except BaseException as e:
        print(f"Error : {str(e)}")
        return Response({'msg':'something went wrong'})


# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def project_download(request,project_id):
#     # projects = request.GET.getlist('project')
#     pr = Project.objects.get(id=project_id)
#     shutil.make_archive(pr.project_name, 'zip', pr.project_dir_path + '/source')
#     tt = download_file(pr.project_name+'.zip')
#     os.remove(pr.project_name+'.zip')
#     return tt



def zipit(folders, zip_filename):
    zip_file = zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED)

    for folder in folders:
        for dirpath, dirnames, filenames in os.walk(folder):
            for filename in filenames:
                zip_file.write(
                    os.path.join(dirpath, filename),
                    os.path.relpath(os.path.join(dirpath, filename), os.path.join(folders[0], '../..')))

    zip_file.close()

@api_view(['GET',])
@permission_classes([IsAuthenticated])
def project_list_download(request):
    projects = request.GET.getlist('project')
    dest = []
    for obj in projects:
        pr = Project.objects.get(id=obj)
        path = pr.project_dir_path + '/source'
        dest.append(path)
    zip_file_name = "Project-"+projects[0]+"-"+projects[-1]+'.zip' if len(projects) > 1 else "Project-"+projects[0]+'.zip'
    zipit(dest,zip_file_name)
    tt = download_file(zip_file_name)
    os.remove(zip_file_name)
    return tt


############################Deprecated###########################################
@permission_classes([IsAuthenticated])
def task_unassign(request):
    task = request.GET.getlist('task')
    assigns = TaskAssignInfo.objects.filter(Q(task_id__in=task))
    for obj in assigns:
        user = obj.task.job.project.ai_user
        team_members = [i.internal_member for i in user.team.internal_member_team_info.filter(role=1)] if user.team else []
        if request.user == user or request.user in team_members:
            segment_count=0 if obj.task.document == None else obj.task.get_progress.get('confirmed_segments')
            task_history = TaskAssignHistory.objects.create(task =obj.task,previous_assign_id=obj.task.assign_to_id,task_segment_confirmed=segment_count,unassigned_by=request.user)
            obj.task.assign_to = user
            obj.task.save()
            obj.delete()
        else:
            return Response({'msg':'Permission Denied'})
    return Response({"msg":"Tasks Unassigned Successfully"},status=200)


def docx_save(name,data):
    from docx import Document
    document = Document()
    new_parser = HtmlToDocx()
    quill_data = data.get('ops')
    print("quilldata------------>",quill_data)
    docx = html.render(quill_data)
    new_parser.add_html_to_document(docx, document)
    document.save(name)
    f2 = open(name, 'rb')
    file_obj = DJFile(f2)
    return file_obj,name,f2


def target_exists(project):
    for i in project.project_jobs_set.all():
        print(i.target_language)
        if i.target_language != None:
            return True
    return False



def update_project_from_writer(task_id):
    obj = TaskTranscriptDetails.objects.filter(task_id = task_id).first()
    writer_project_updated_count = 1 if obj.writer_project_updated_count==None else obj.writer_project_updated_count+1
    print("project_update_count----------->",writer_project_updated_count)
    obj.writer_project_updated_count = writer_project_updated_count
    obj.save()
    writer_filename = obj.writer_filename + '_edited_'+ str(obj.writer_project_updated_count)+'.docx'
    file_obj = ContentFile(obj.transcripted_file_writer.file.read(),name=writer_filename)
    print("FileObj------------>",file_obj)
    return file_obj




@api_view(['GET',])
@permission_classes([IsAuthenticated])
def get_quill_data(request):
    task_id = request.GET.get('task_id')
    obj = TaskTranscriptDetails.objects.filter(task_id = task_id).first()
    try:
        data = json.loads(obj.quill_data)
        res = data.get('ops')
    except:res = None
    return Response({'data':res})


def update_task_assign(task_obj,user):
    try:
        obj = TaskAssignInfo.objects.filter(task_assign__task = task_obj).filter(task_assign__assign_to = user).first().task_assign
        if obj.status != 2:
            obj.status = 2
            obj.save()
            print("Changed to Inprogress")
    except:pass



@api_view(['POST',])
@permission_classes([IsAuthenticated])
def writer_save(request):
    task_id = request.POST.get('task_id')
    transcripted_file_writer = request.FILES.get('file',None)
    task_obj = Task.objects.get(id=task_id)
    edited_text = request.POST.get('edited_text')
    obj = TaskTranscriptDetails.objects.filter(task_id = task_id).first()
    filename,ext = os.path.splitext(task_obj.file.filename)
    data1 = {"writer_filename":filename,"task":task_id,"html_data":edited_text,'user':request.user.id}
    if transcripted_file_writer:
        data1.update({"transcripted_file_writer":transcripted_file_writer})
    if obj:
        ser1 = TaskTranscriptDetailSerializer(obj,data=data1,partial=True)#"transcripted_file_writer":file_obj,
    else:
        ser1 = TaskTranscriptDetailSerializer(data=data1,partial=True)#"transcripted_file_writer":file_obj,
    if ser1.is_valid():
        ser1.save()
        update_task_assign(task_obj,request.user)
        return Response(ser1.data)
    return Response(ser1.errors)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_voice_task_status(request):
    from ai_workspace.models import MTonlytaskCeleryStatus
    from ai_auth.tasks import transcribe_long_file_cel,google_long_text_file_process_cel
    project_id = request.GET.get('project')
    sub_category = request.GET.get('sub_category')
    pr = Project.objects.get(id=project_id)
    res= []
    if pr.project_type_id == 4:
        tasks = pr.get_source_only_tasks
        for i in tasks:
            obj = MTonlytaskCeleryStatus.objects.filter(task=i).filter(Q(task_name = 'transcribe_long_file_cel') | Q(task_name = 'google_long_text_file_process_cel')).last()
            if obj:
                if obj.task_name == 'transcribe_long_file_cel':
                    state = transcribe_long_file_cel.AsyncResult(obj.celery_task_id).state if obj and obj.celery_task_id else None
                elif obj.task_name == 'google_long_text_file_process_cel':
                    state = google_long_text_file_process_cel.AsyncResult(obj.celery_task_id).state if obj and obj.celery_task_id else None
                if state == 'STARTED':
                    status = 'False'
                else:
                    status = 'True'
            else:
                status = 'True'
            res.append({'task':i.id,'open':status})
        return Response({'res':res})
    else:
        return Response({'msg':'No Detail'})



def celery_check(obj):
    from ai_auth.tasks import pre_translate_update
    state = None
    if obj.task_name == 'mt_only':
        state = mt_only.AsyncResult(obj.celery_task_id).state if obj and obj.celery_task_id else None
    elif obj.task_name == 'pre_translate_update':
        state = pre_translate_update.AsyncResult(obj.celery_task_id).state if obj and obj.celery_task_id else None
    if state == 'STARTED':
        status = 'False'
    else:
        status = 'True'
    return status




@api_view(['GET',])
@permission_classes([IsAuthenticated])
def get_task_status(request):
    from ai_workspace_okapi.api_views import DocumentViewByTask
    from ai_workspace.models import MTonlytaskCeleryStatus
    from ai_tm.api_views import get_json_file_path
    project_id = request.GET.get('project')
    task_id = request.GET.get('task')
    if project_id:
        pr = Project.objects.get(id=project_id)
        pre_t = pr.pre_translate
        tasks = pr.get_mtpe_tasks
    elif task_id:
        pre_t = Task.objects.get(id=task_id).job.project.pre_translate
        tasks = Task.objects.filter(id=task_id)
    if pre_t == True:
        res = []
        for i in tasks:
            msg,progress = None,None
            document = i.document                    
            obj = MTonlytaskCeleryStatus.objects.filter(task=i).filter(Q(task_name = 'mt_only') | Q(task_name = 'pre_translate_update')).last()
            if document:
                if not obj or obj.status == 2:
                    status = 'True'
                elif obj.status == 1 and obj.error_type == "Insufficient Credits":
                    status = 'True'
                else:
                    status = celery_check(obj)
            else:
                if obj:
                    status = celery_check(obj)
                else:
                    status = 'True' 
            if status == 'True':
                progress = i.get_progress
            res.append({'task':i.id,'document':i.document_id,'open':status,'progress':progress,'msg':msg})
        return Response({'res':res})
    else:
        return Response({'msg':'No Detail'})

    
    
            # obj = MTonlytaskCeleryStatus.objects.filter(task=i).last()
            # if document:
            #     print("#####")
            #     status = 'True'
            # else:
            #     print("!!!!!!!!!!!")
            #     file_path = DocumentViewByTask.get_json_file_path(i)
            #     doc_data = json.load(open(file_path))
            #     if type(doc_data) == str:
            #         doc_data = json.loads(doc_data)

            #     if doc_data.get('total_word_count') == 0:
            #         status = 'True'
            #         msg = "Empty File"
            #     else:
            #         print("$$$$$$$$$")
            #         if obj:
            #             print("obj")
            #             if obj.task_name == 'mt_only':
            #                 state = mt_only.AsyncResult(obj.celery_task_id).state if obj and obj.celery_task_id else None
            #             elif obj.task_name == 'pre_translate_update':
            #                 state = pre_translate_update.AsyncResult(obj.celery_task_id).state if obj and obj.celery_task_id else None
            #             if state == 'STARTED':
            #                 status = 'False'
            #             else:
            #                 status = 'True' 
            #         else:
            #             print("no obj")
            #             status = 'True'



# @api_view(['POST',])
# @permission_classes([IsAuthenticated])
# def writer_save(request):
#     task_id = request.POST.get('task_id')
#     task_obj = Task.objects.get(id=task_id)
#     edited_text = request.POST.get('edited_text')
#     edited_data = json.loads(edited_text)
#     obj = TaskTranscriptDetails.objects.filter(task_id = task_id).first()
#     filename,ext = os.path.splitext(task_obj.file.filename)
#     print("Filename---------------->",filename)
#     name = filename + '.docx'
#     try:
#         file_obj,name,f2 = docx_save(name,edited_data)
#     except:
#         return Response({'msg':'something wrong with input file format'},status=400)
#     if obj:
#         ser1 = TaskTranscriptDetailSerializer(obj,data={"writer_filename":filename,"transcripted_file_writer":file_obj,"task":task_id,"quill_data":edited_text,'user':request.user.id},partial=True)
#     else:
#         ser1 = TaskTranscriptDetailSerializer(data={"writer_filename":filename,"transcripted_file_writer":file_obj,"task":task_id,"quill_data":edited_text,'user':request.user.id},partial=True)
#     if ser1.is_valid():
#         ser1.save()
#         os.remove(name)
#         return Response(ser1.data)
#     return Response(ser1.errors)


# class ExpressProjectSetupView(viewsets.ModelViewSet):
#     permission_classes = [IsAuthenticated]
#
#     def create(self, request):
#         punctuation='''!"#$%&'``()*+,-./:;<=>?@[\]^`{|}~_'''
#         text_data=request.POST.get('text_data')
#         name =  text_data.split()[0].strip(punctuation)+ ".txt" if len(text_data.split()[0])<=15 else text_data[:5].strip(punctuation)+ ".txt"
#         im_file= DjRestUtils.convert_content_to_inmemoryfile(filecontent = text_data.encode(),file_name=name)
#         serializer =ProjectQuickSetupSerializer(data={**request.data,"files":[im_file],"project_type":['2']},context={"request": request})
#         if serializer.is_valid(raise_exception=True):
#             serializer.save()
#             pr = Project.objects.get(id=serializer.data.get('id'))
#             mt_only.apply_async((serializer.data.get('id'), str(request.auth)), )
#             res=[{'task_id':i.id,'target_lang_name':i.job.target_language.language,"target_lang_id":i.job.target_language.id} for i in pr.get_mtpe_tasks]
#             return Response({'Res':res})
#         return Response(serializer.errors)



# @api_view(['GET',])
# @permission_classes([IsAuthenticated])
# def task_get_segments(request):
#     from ai_workspace_okapi.api_views import DocumentViewByTask
#     from ai_workspace.models import MTonlytaskCeleryStatus
#     from django_celery_results.models import TaskResult
#     user = request.user.team.owner  if request.user.team  else request.user
#     task_id = request.GET.get('task_id')
#     obj = Task.objects.get(id=task_id)
#     ins = MTonlytaskCeleryStatus.objects.filter(task_id=task_id).last()
#     if ins.status == 1:
#         obj = TaskResult.objects.filter(Q(task_id = ins.celery_task_id)).first()# & Q(task_name = 'ai_auth.tasks.mt_only').first()
#         if obj !=None and obj.status == "FAILURE":
#             Document.objects.filter(Q(file = task.file) &Q(job=task.job)).delete()
#             document = DocumentViewByTask.create_document_for_task_if_not_exists(task)
#             MTonlytaskCeleryStatus.objects.create(task_id=task.id,status=2)
#         else:
#             return Response({"msg": "File under process. Please wait a little while. \
#                     Hit refresh and try again"}, status=401)
#     else:
#         document = DocumentViewByTask.create_document_for_task_if_not_exists(obj)
#     seg_out = ''
#     seg_status = None
#     for j in document.segments:
#         if j.target=='':
#             if UserCredits.objects.filter(user_id=user.id).filter(ended_at__isnull=True).last().credits_left < len(j.source):
#                 seg_status = 'some segments may not be translated due to insufficient credits.please subscribe and try again'
#                 break
#         seg_out+=j.target
#     out =[{'task_id':obj.id,"seg_status":seg_status,"target":seg_out,'project_id':obj.job.project.id,'target_lang_name':obj.job.target_language.language,'job_id':obj.job.id,"target_lang_id":obj.job.target_language.id}]
#     return Response({'Res':out})




class ExpressProjectSetupView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        punctuation='''!"#$%&'``()*+,-./:;<=>?@[\]^`{|}~_'''
        text_data=request.POST.get('text_data')
        text_data = text_data.replace('\r','')
        name =  text_data.split()[0].strip(punctuation)+ ".txt" if len(text_data.split()[0])<=15 else text_data[:5].strip(punctuation)+ ".txt"
        im_file= DjRestUtils.convert_content_to_inmemoryfile(filecontent = text_data.encode(),file_name=name)
        serializer =ProjectQuickSetupSerializer(data={**request.data,"files":[im_file],"project_type":['5']},context={"request": request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            pr = Project.objects.get(id=serializer.data.get('id'))
            source_lang = pr.project_jobs_set.first().source_language_id
            res=[{'task_id':i.id,'target_lang_name':i.job.target_language.language,"target_lang_id":i.job.target_language.id} for i in pr.get_mtpe_tasks]
            return Response({'project_id':pr.id,'source_lang_id':source_lang,'Res':res})
        return Response(serializer.errors)


def get_consumable_credits_for_text(source,target_lang,source_lang):
    seg_data = { "segment_source" : source,
                 "source_language" : source_lang,
                 "target_language" : target_lang,
                 "processor_name" : "plain-text-processor",
                 "extension":".txt"
                 }
    res = requests.post(url=f"http://{spring_host}:8080/segment/word_count", \
        data={"segmentWordCountdata":json.dumps(seg_data)},timeout=3)

    if res.status_code == 200:
        print("Word count of the segment--->", res.json())
        return res.json()
    else:
        logger.info(">>>>>>>> Error in segment word count calculation <<<<<<<<<")
        raise  ValueError("Sorry! Something went wrong with word count calculation.")

def exp_proj_save(task_id,mt_change):
    vers = ExpressProjectSrcSegment.objects.filter(task_id = task_id).last().version
    exp_obj = ExpressProjectSrcSegment.objects.filter(task_id = task_id,version=vers)
    obj = Task.objects.get(id=task_id)
    express_obj = ExpressProjectDetail.objects.get(task_id = task_id)
    #results = ExpressProjectSrcSegment.objects.filter(task_id = task_id,version=vers).distinct('src_text_unit')
    tar = ''
    for i in exp_obj.distinct('src_text_unit'):
        rr = exp_obj.filter(src_text_unit=i.src_text_unit)
        for i in rr:
            tar_1 = i.express_src_mt.filter(mt_engine_id=express_obj.mt_engine_id).first().mt_raw #ExpressProjectSrcMTRaw.objects.get(src_seg = i).mt_raw
            tar = tar +' '+tar_1 if tar_1 else ''
        tar = tar + '\n\n'
    express_obj.mt_raw = tar.strip().strip('\n')
    express_obj.target_text = tar.strip('\n')
    express_obj.save()
    try:wc = get_consumable_credits_for_text(express_obj.source_text,None,obj.job.source_language_code)
    except:wc = 0
    td = TaskDetails.objects.update_or_create(task = obj,project = obj.job.project,defaults = {"task_word_count": wc,"task_char_count":len(express_obj.source_text)})
    print("Td--------------->",td)
    #express_obj.total_word_count = get_consumable_credits_for_text(express_obj.source_text,None,express_obj.task.job.source_language_code)
    #express_obj.total_char_count = len(express_obj.source_text)
    if mt_change == None:
        ExpressProjectSrcSegment.objects.filter(task_id = task_id).exclude(version = vers).delete()
    return express_obj


def seg_create(task_id,content,from_mt_edit=None):
    from ai_workspace.models import ExpressProjectSrcSegment,ExpressProjectSrcMTRaw
    obj = Task.objects.get(id=task_id)
    lang_code = obj.job.source_language_code
    user = obj.job.project.ai_user
    express_obj = ExpressProjectDetail.objects.get(task_id = task_id)
    if from_mt_edit == None:
        express_obj.source_text = content
        express_obj.mt_engine = obj.job.project.mt_engine
        express_obj.save()
    print("exp----->",express_obj.mt_engine)
    NEWLINES_RE = re.compile(r"\n{1,}")
    no_newlines = content.strip("\n")  # remove leading and trailing "\n"
    split_text = NEWLINES_RE.split(no_newlines)
    lang_list = ['hi','bn','or','ne','pa']
    lang_list_2 = ['zh-Hans','zh-Hant','ja']
    for i,j  in enumerate(split_text):
        if lang_code in lang_list_2:
            sents = cust_split(j)

        elif lang_code in lang_list:
            sents = sentence_split(j, lang_code, delim_pat='auto')
        else:
            sents = nltk.sent_tokenize(j)
        #sents = nltk.sent_tokenize(j)
        print("Sents------->",len(sents))
        for l,k in enumerate(sents):
            ExpressProjectSrcSegment.objects.create(task_id=task_id,src_text_unit=i,src_segment=k.strip(),seq_id=l,version=1)

    for i in ExpressProjectSrcSegment.objects.filter(task_id=task_id,version=1):
        print(i.src_segment)
        tar = get_translation(mt_engine_id=express_obj.mt_engine_id,source_string = i.src_segment ,source_lang_code=i.task.job.source_language_code , target_lang_code=i.task.job.target_language_code,user_id=user.id)
        ExpressProjectSrcMTRaw.objects.create(src_seg = i,mt_raw = tar,mt_engine_id=express_obj.mt_engine_id)
    res = exp_proj_save(task_id,None)
    return res


def get_total_consumable_credits(source_lang,prompt_string_list):
    credit = 0
    for i in prompt_string_list:
        if i != None:
            consumable_credit = get_consumable_credits_for_text(i,None,source_lang)
            credit+=consumable_credit
    return credit

def cust_split(text):
    import re
    tt = []
    for sent in re.findall(u'[^!?。\.\!\?]+[!?。\.\!\?]?', text, flags=re.U):
        tt.append(sent)
    final = [i for i in tt if i.strip()]
    print("Final inside CustSplit-------->",final)
    return final


def seg_edit(express_obj,task_id,src_text,from_mt_edit=None):
    obj = Task.objects.get(id=task_id)
    user = obj.job.project.ai_user
    NEWLINES_RE = re.compile(r"\n{1,}")
    no_newlines = src_text.strip("\n")  # remove leading and trailing "\n"
    split_text = NEWLINES_RE.split(no_newlines)
    print("split_text-------------->",split_text)
    lang_code = obj.job.source_language_code
    lang_list = ['hi','bn','or','ne','pa']
    lang_list_2 = ['zh-Hans','zh-Hant','ja']
    exp_src_obj = ExpressProjectSrcSegment.objects.filter(task_id=task_id)
    if not exp_src_obj:
        initial_credit = user.credit_balance.get("total_left")
        consumable_credits = get_consumable_credits_for_text(src_text,source_lang=obj.job.source_language_code,target_lang=obj.job.target_language_code)
        print("Consumable in seg_edit Create-------->",consumable_credits)
        res = seg_create(task_id,src_text,from_mt_edit)
        #debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)
        print("Created")
        return None
    vers = exp_src_obj.last().version
    for i,j  in enumerate(split_text):
        if lang_code in lang_list_2:
            sents = cust_split(j)
        elif lang_code in lang_list:
            sents = sentence_split(j, lang_code, delim_pat='auto')
        else:
            sents = nltk.sent_tokenize(j)
        print("Sents------>",len(sents))
        for l,k in enumerate(sents):
            ExpressProjectSrcSegment.objects.create(task_id=task_id,src_text_unit=i,src_segment=k.strip(),seq_id=l,version=vers+1)
    latest =  ExpressProjectSrcSegment.objects.filter(task_id=task_id).last().version
    for i in ExpressProjectSrcSegment.objects.filter(task=task_id,version=latest):
        print(i.src_segment)
        tt = ExpressProjectSrcSegment.objects.filter(task=task_id,version=latest-1).filter(src_segment__iexact = i.src_segment)
        if tt:
            mt_obj = tt.first().express_src_mt.filter(mt_engine_id=express_obj.mt_engine_id).first()
            if mt_obj: 
                ExpressProjectSrcMTRaw.objects.create(src_seg = i,mt_raw = mt_obj.mt_raw,mt_engine_id=express_obj.mt_engine_id)
                # mt_obj.src_seg = i
                # mt_obj.save()
                # ex_obj = ExpressProjectSrcSegment.objects.get(id=tt.first().id)
                # ex_obj.src_segment =''
                # ex_obj.save()
            else:
                print("MT only Change")
                consumed = get_consumable_credits_for_text(i.src_segment,None,obj.job.source_language_code)
                tar = get_translation(mt_engine_id=express_obj.mt_engine_id,source_string = i.src_segment ,source_lang_code=i.task.job.source_language_code , target_lang_code=i.task.job.target_language_code,user_id=user.id)
                #debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumed)
                ExpressProjectSrcMTRaw.objects.create(src_seg = i,mt_raw = tar,mt_engine_id=express_obj.mt_engine_id)
        else:
            print("New MT")
            consumable = get_consumable_credits_for_text(i.src_segment,None,obj.job.source_language_code)
            tar = get_translation(mt_engine_id=express_obj.mt_engine_id,source_string = i.src_segment ,source_lang_code=i.task.job.source_language_code , target_lang_code=i.task.job.target_language_code,user_id=user.id)
            #debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable)
            tt = ExpressProjectSrcMTRaw.objects.create(src_seg = i,mt_raw = tar,mt_engine_id=express_obj.mt_engine_id)
    res = exp_proj_save(task_id,None)
    print("Done Editing")
    return None


@api_view(['GET',])
@permission_classes([IsAuthenticated])
def task_get_segments(request):
    from ai_workspace.models import ExpressProjectDetail
    user = request.user.team.owner  if request.user.team  else request.user
    task_id = request.GET.get('task_id')
    express_obj = ExpressProjectDetail.objects.filter(task_id=task_id).first()
    obj = Task.objects.get(id=task_id)
    if express_obj.source_text == None:
        with open(obj.file.file.path, "r") as file:
            content = file.read()
    else:content = express_obj.source_text
    print("Content--------------->",content)
    if express_obj.mt_raw == None and express_obj.target_text == None:
        initial_credit = user.credit_balance.get("total_left")
        consumable_credits = get_consumable_credits_for_text(content,source_lang=obj.job.source_language_code,target_lang=obj.job.target_language_code)
        print("InitialCredits---------------->",initial_credit)
        print("ConsumableCredits---------------->",consumable_credits)
        if initial_credit > consumable_credits:
            res = seg_create(task_id,content)
            #debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)
            express_obj = ExpressProjectDetail.objects.filter(task_id=task_id).first()
            ser = ExpressProjectDetailSerializer(express_obj)
            return Response({'Res':ser.data})
            # out =[{'task_id':obj.id,"source":content,"mt_raw":res.mt_raw,"target":res.target_text,'project_id':obj.job.project.id,'project_name':obj.job.project.project_name,'target_lang_name':obj.job.target_language.language,'job_id':obj.job.id,"target_lang_id":obj.job.target_language.id,"source_lang_id":obj.job.source_language.id,"mt_engine_id":res.mt_engine.id if res.mt_engine else obj.job.project.mt_engine.id}]
            # return Response({'Res':out})
        else:
            express_obj.source_text = content
            express_obj.mt_engine = obj.job.project.mt_engine
            express_obj.save()
            ser = ExpressProjectDetailSerializer(express_obj)
            out = ser.data
            #out =[{'task_id':obj.id,"source":content,"mt_raw":None,"target":'','project_id':obj.job.project.id,'project_name':obj.job.project.project_name,'target_lang_name':obj.job.target_language.language,'job_id':obj.job.id,"target_lang_id":obj.job.target_language.id,"source_lang_id":obj.job.source_language.id,"mt_engine_id":obj.job.project.mt_engine.id}]
            return Response({'msg':'Insufficient Credits','Res':out})
            #return Response({'msg':'Insufficient Credits'},status=400)
    else:
        ser = ExpressProjectDetailSerializer(express_obj)
        return Response({'Res':ser.data})



def seg_get_new_mt(task,mt_engine_id,user,express_obj):
    exp_src_obj = ExpressProjectSrcSegment.objects.filter(task_id=task.id).last()
    if not exp_src_obj:
        seg_create(task.id,express_obj.source_text,True)
        print("SEg Created and MTChangeDone")
        return None
    else:
        latest =  ExpressProjectSrcSegment.objects.filter(task=task).last().version
        for i in ExpressProjectSrcSegment.objects.filter(task=task,version=latest):
            mt_obj = i.express_src_mt.filter(mt_engine_id=express_obj.mt_engine_id).first() 
            if not mt_obj:
                print("Inside New")
                consumable_credit = get_consumable_credits_for_text(i.src_segment,None,task.job.source_language_code)
                print("Consum---------->",consumable_credit)
                tar = get_translation(express_obj.mt_engine.id,i.src_segment ,i.task.job.source_language_code,i.task.job.target_language_code,i.task.job.project.ai_user.id)
                #debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credit)
                ExpressProjectSrcMTRaw.objects.create(src_seg = i,mt_raw = tar,mt_engine_id=mt_engine_id)
        exp_proj_save(task.id,True)
        print("MtChangeDone")

def inst_create(obj,option):
    customize = AiCustomize.objects.get(customize = option)
    created_obj = ExpressProjectAIMT.objects.create(express_id=obj.id,source=obj.source_text,customize_id=customize.id,mt_engine_id=obj.mt_engine_id)
    return created_obj

# def get_credits(lang_code,text1,text2):
#     lang_lists = ['zh-Hans','zh-Hant','lo','km','my','th','ja']#lang_lists_without_spaces
#     if lang_code not in lang_lists:
#         output_list = [li for li in difflib.ndiff(text1.split(), text2.strip().split()) if li[0]=='+' if li[-1].strip()]
#         print("Ol--------->",output_list)
#         cc = len(output_list)
#     else:
#         output_list_1 = [li for li in difflib.ndiff(text1.replace('\n',''), text2.strip().replace('\n','')) if li[0]=='+' if li[-1].strip()]
#         output_list = [i.strip("+") for i in output_list_1 if i.strip("+").strip()]
#         print('oll------------->',output_list)
#         src = ''.join(output_list)
#         cc = get_consumable_credits_for_text(src,None,lang_code)
#     return cc

def sent_tokenize(text,lang_code):
    print("Text Inside Tokenise--------->",text)
    lang_list = ['hi','bn','or','ne','pa']
    lang_list_2 = ['zh-Hans','zh-Hant','ja']
    NEWLINES_RE = re.compile(r"\n{1,}")
    no_newlines = text.strip("\n")  # remove leading and trailing "\n"
    split_text = NEWLINES_RE.split(no_newlines)
    out = []
    for i,j  in enumerate(split_text):
        if lang_code in lang_list_2:
            sents = cust_split(j)
        elif lang_code in lang_list:
            sents = sentence_split(j, lang_code, delim_pat='auto')
        else:
            sents = nltk.sent_tokenize(j)
        print("Sents------>",len(sents))
        out.extend(sents)
    print("Out--------->",out)
    return out


import difflib
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def task_segments_save(request):
    task_id = request.POST.get('task_id')
    if not task_id:
        return Response({'msg':'task_id required'},status=400)
    from_history = request.POST.get('from_history',None)
    target_text = request.POST.get('target_text',None)
    simplified_text = request.POST.get('simplified_text')
    shortened_text = request.POST.get('shortened_text')
    mt_engine_id = request.POST.get('mt_engine',None)
    source_text = request.POST.get('source_text')
    apply_all = request.POST.get('apply_all',None)
    obj = Task.objects.get(id=task_id)
    user = obj.job.project.ai_user
    express_obj = ExpressProjectDetail.objects.filter(task_id=task_id).first()

    if from_history:
        task_hist_obj = ExpressTaskHistory.objects.get(id = from_history)
        express_obj.source_text = task_hist_obj.source_text
        express_obj.target_text = task_hist_obj.target_text
        express_obj.mt_raw = ''
        express_obj.save()
        ExpressProjectSrcSegment.objects.filter(task_id = task_id).delete()

    
    elif target_text:# or target_text!=None:
        express_obj.target_text = target_text.replace('\r','')
        express_obj.save()

    elif simplified_text:
        inst_cust_obj = express_obj.express_src_text.filter(customize__customize='Simplify').last()
        if not inst_cust_obj:
            inst_cust_obj = inst_create(express_obj,'Simplify')
        inst_cust_obj.final_result = simplified_text
        inst_cust_obj.save()

    elif shortened_text:
        inst_cust_obj = express_obj.express_src_text.filter(customize__customize='Shorten').last()
        if not inst_cust_obj:
            inst_cust_obj = inst_create(express_obj,'Shorten')
        inst_cust_obj.final_result = shortened_text
        inst_cust_obj.save()

    elif ((source_text) or (source_text and mt_engine_id)):
        source_text = source_text.replace('\r','')
        print("Content--------------->",source_text)
        if mt_engine_id:
            express_obj.mt_engine_id = mt_engine_id
            express_obj.save()
        if apply_all == 'True':tasks = obj.job.project.get_tasks
        else: tasks = Task.objects.filter(id=task_id)
        for i in tasks:
            express_obj = ExpressProjectDetail.objects.filter(task_id=i.id).first()
            exp_src_obj = ExpressProjectSrcSegment.objects.filter(task_id=task_id)
            previous_stored_source = express_obj.source_text.strip() if express_obj.source_text else ''
            text1 = sent_tokenize(previous_stored_source,i.job.source_language_code)
            text2 = sent_tokenize(source_text.strip(),i.job.source_language_code)
            print("previous---------->",text1)
            print("current---------->",text2)
            output_list = [li for li in difflib.ndiff(text1,text2) if li[0] == '+']
            print("OL----------->",output_list)
            initial_credit = user.credit_balance.get("total_left")
            if exp_src_obj:
                consumable_credits = get_total_consumable_credits(i.job.source_language_code,output_list)
            else:
                consumable_credits = get_consumable_credits_for_text(source_text,None,i.job.source_language_code)
            print("Inial---------->",initial_credit)
            print("Cons12212-------->",consumable_credits)
            if initial_credit < consumable_credits:
                return  Response({'msg':'Insufficient Credits'},status=400) 
            else:
                express_obj = i.express_task_detail.first()
                express_obj.source_text = source_text
                express_obj.save()
                if i.id == json.loads(task_id) and mt_engine_id:
                    seg_edit(express_obj,i.id,source_text,True)
                else:
                    seg_edit(express_obj,i.id,source_text)


    elif mt_engine_id:
        initial_credit = user.credit_balance.get("total_left")
        consumable_credits = get_consumable_credits_for_text(express_obj.source_text,target_lang=None,source_lang=obj.job.source_language_code)
        if initial_credit < consumable_credits:
            return  Response({'msg':'Insufficient Credits'},status=400) 
        else:
            express_obj.mt_engine_id = mt_engine_id
            express_obj.save()
            seg_get_new_mt(obj,mt_engine_id,user,express_obj)
    express_obj = ExpressProjectDetail.objects.filter(task_id=task_id).first()
    ser = ExpressProjectDetailSerializer(express_obj)
    return Response(ser.data)

@api_view(['GET'])
#@permission_classes([IsAuthenticated])
def express_task_download(request,task_id):###############permission need to be added and checked##########################
    obj = Task.objects.get(id = task_id)
    express_obj = ExpressProjectDetail.objects.filter(task_id=task_id).first()
    file_name,ext = os.path.splitext(obj.file.filename)
    target_filename = file_name + "_out" +  "(" + obj.job.source_language_code + "-" + obj.job.target_language_code + ")" + ext
    with open(target_filename,'w') as f:
        f.write("Source:" + "\n")
        f.write(express_obj.source_text) 
        f.write('\n')
        f.write("---------" + "\n")
        f.write("Target:" + "\n\n")
        f.write("Standard:" + "\n")
        target = express_obj.target_text if express_obj.target_text else ''
        f.write(target)
        f.write('\n')
        f.write("---------" + "\n")
        shorten_obj =express_obj.express_src_text.filter(customize__customize='Shorten')
        if shorten_obj.exists():
            f.write("Shortened:" + "\n")
            f.write(shorten_obj.last().final_result)
            f.write("\n")
            f.write("---------" + "\n")
        simplified_obj = express_obj.express_src_text.filter(customize__customize='Simplify')
        if simplified_obj.exists():
            f.write("Simplified:" + "\n")
            f.write(simplified_obj.last().final_result)
            f.write("\n")
            f.write("---------" + "\n")
    print("File Written--------------->",target_filename)
    res = download_file(target_filename)
    os.remove(target_filename)
    return res

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def express_project_detail(request,project_id):
    obj = Project.objects.get(id=project_id)
    jobs = obj.project_jobs_set.all()
    jobs_data = JobSerializer(jobs, many=True)
    #target_languages = [job.target_language_id for job in obj.project_jobs_set.all() if job.target_language_id != None]
    source_lang_id =  obj.project_jobs_set.first().source_language_id
    mt_engine_id = obj.mt_engine_id
    project_name = obj.project_name
    team = obj.get_team
    project_file = obj.project_files_set.all().first()
    with open(project_file.file.path, "r") as file:
        content = file.read()
    return JsonResponse({'jobs':jobs_data.data,'source_lang':source_lang_id,\
                        'mt_engine':mt_engine_id,'project_name':project_name,'team':team,\
                        'source_text':content})


def voice_project_progress(pr,tasks):
    from ai_workspace_okapi.models import Document, Segment
    count=0
    progress = 0
    source_tasks = [i for i in tasks if i.job.target_language==None]
    if source_tasks:
        if pr.voice_proj_detail.project_type_sub_category_id==1:
            for i in source_tasks:
                if TaskTranscriptDetails.objects.filter(task_id = i).exists():
                    if TaskTranscriptDetails.objects.filter(task_id = i).last().transcripted_text !=None:
                        count+=1
        elif pr.voice_proj_detail.project_type_sub_category_id==2:
            for i in source_tasks:
                if TaskTranscriptDetails.objects.filter(task_id = i).exists():
                    if TaskTranscriptDetails.objects.filter(task_id = i).last().source_audio_file !=None:
                        count+=1
    mtpe_tasks = [i for i in tasks if i.job.target_language != None]
    if mtpe_tasks:
        assigned_jobs = [i.job.id for i in mtpe_tasks]
        docs = Document.objects.filter(job__in=assigned_jobs).all()
        #docs = Document.objects.filter(job__project_id=pr.id).all()
        print(docs)
        if not docs:
            count+=0
        if docs.count() == len(mtpe_tasks):
            total_seg_count = 0
            confirm_count  = 0
            confirm_list = [102, 104, 106, 110, 107]

            segs = Segment.objects.filter(text_unit__document__job__project_id=pr.id)
            for seg in segs:
                if seg.is_merged == True and seg.is_merge_start is None:
                    continue
                else:
                     total_seg_count += 1

                     seg_new = seg.get_active_object()
                     if seg_new.status_id in confirm_list:
                        confirm_count += 1

            if total_seg_count == confirm_count:
                count+=len(mtpe_tasks)
            else:
                progress+=1
    #print("count------------>",count)
    if count == 0 and progress == 0:
        return "Yet to Start"
    elif count == len(tasks):
        return "Completed"
    elif count != len(tasks) or progress != 0:
        return "In Progress"


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def translate_from_pdf(request,task_id):
    from ai_exportpdf.models import Ai_PdfUpload
    from ai_exportpdf.views import get_docx_file_path
    task_obj = Task.objects.get(id = task_id)
    pdf_obj = Ai_PdfUpload.objects.filter(task_id = task_id).last()
    # updated_count = pdf_obj.updated_count+1 if pdf_obj.updated_count else 1
    # pdf_obj.updated_count = updated_count
    # pdf_obj.save()
    # docx_file_name = pdf_obj.docx_file_name + '_edited_'+ str(pdf_obj.updated_count)+'.docx'
    if pdf_obj.pdf_api_use == "convertio":
        docx_file_path = get_docx_file_path(pdf_obj.id)
        file = open(docx_file_path,'rb')
        file_obj = ContentFile(file.read(),name= os.path.basename(docx_file_path))#name=docx_file_name
    else:
        file_obj = ContentFile(pdf_obj.docx_file_from_writer.file.read(),name= os.path.basename(pdf_obj.docx_file_from_writer.path))
    ins = task_obj.job.project
    team = True if ins.team else False
    serlzr = ProjectQuickSetupSerializer(ins, data={"files":[file_obj],'team':[team]},context={"request": request}, partial=True)
    if serlzr.is_valid():
        serlzr.save()
        return Response(serlzr.data)
    return Response(serlzr.errors)



class MyDocFilter(django_filters.FilterSet):
    doc_name = django_filters.CharFilter(field_name='doc_name',lookup_expr='icontains')#related_docs__doc_name
    class Meta:
        model = MyDocuments
        fields = ['doc_name']#proj_name

from django.db.models import Value, CharField, IntegerField
from ai_openai.models import BlogCreation
from functools import reduce

class MyDocumentsView(viewsets.ModelViewSet):

    serializer_class = MyDocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend,SearchFilter,CaseInsensitiveOrderingFilter]
    ordering_fields = ['doc_name','id']#'proj_name',
    search_fields = ['doc_name']
    filterset_class = MyDocFilter
    paginator = PageNumberPagination()
    ordering = ('-created_at')
    paginator.page_size = 20
    # https://www.django-rest-framework.org/api-guide/filtering/


    def get_queryset_new(self):
        query = self.request.GET.get('doc_name')
        ordering = self.request.GET.get('ordering')
        user = self.request.user
        project_managers = user.team.get_project_manager if user.team else []
        owner = user.team.owner if (user.team and user in project_managers) else user
        #ai_user = user.team.owner if user.team and user in user.team.get_project_manager else user 
        queryset = MyDocuments.objects.filter(Q(ai_user=user)|Q(ai_user__in=project_managers)|Q(ai_user=owner)).distinct()
        q1 = queryset.annotate(open_as=Value('Document', output_field=CharField())).values('id','created_at','doc_name','word_count','open_as','document_type__type')
        q1 = q1.filter(doc_name__icontains =query) if query else q1
        q2 = BlogCreation.objects.filter(Q(user = user)|Q(created_by__in = project_managers)|Q(user=owner)).distinct().filter(blog_article_create__document=None).distinct().annotate(word_count=Value(0,output_field=IntegerField()),document_type__type=Value(None,output_field=CharField()),open_as=Value('BlogWizard', output_field=CharField())).values('id','created_at','user_title','word_count','open_as','document_type__type')
        q2 = q2.filter(user_title__icontains = query) if query else q2
        q3 = q1.union(q2)
        final_queryset = q3.order_by('-created_at')
        if ordering:
            field_name = ordering.lstrip('-')
            if ordering.startswith('-'):
                queryset = final_queryset.order_by(F(field_name).desc(nulls_last=True))
            else:
                queryset = final_queryset.order_by(F(field_name).asc(nulls_last=True))

            return queryset
        
        return final_queryset
        
    def get_queryset_for_combined(self):
        user = self.request.user
        project_managers = user.team.get_project_manager if user.team else []
        owner = user.team.owner if (user.team and user in project_managers) else user
        #ai_user = user.team.owner if user.team and user in user.team.get_project_manager else user 
        queryset = MyDocuments.objects.filter(Q(ai_user=user)|Q(ai_user__in=project_managers)|Q(ai_user=owner)).distinct()
        q1 = queryset.annotate(open_as=Value('Document', output_field=CharField())).values('id','created_at','doc_name','word_count','open_as','document_type__type')
        q2 = BlogCreation.objects.filter(Q(user = user)|Q(created_by__in = project_managers)|Q(user=owner)).distinct().filter(blog_article_create__document=None).distinct().annotate(word_count=Value(0,output_field=IntegerField()),document_type__type=Value(None,output_field=CharField()),open_as=Value('BlogWizard', output_field=CharField()),doc_name=F('user_title')).values('id','created_at','doc_name','word_count','open_as','document_type__type')
        q3 = list(chain(q1, q2))
        return q3



    def get_queryset(self):
        user = self.request.user
        project_managers = self.request.user.team.get_project_manager if self.request.user.team else []
        owner = self.request.user.team.owner if self.request.user.team  else self.request.user
        queryset = MyDocuments.objects.filter(Q(ai_user=user)|Q(ai_user__in=project_managers)|Q(ai_user=owner)).order_by('-id')
        return queryset

    def list(self, request, *args, **kwargs):
        paginate = request.GET.get('pagination',True)
        queryset = self.get_queryset_new() #self.filter_queryset(self.get_queryset())
        if paginate == 'False':
            serializer = MyDocumentSerializer(self.filter_queryset(self.get_queryset()), many=True)
            return Response(serializer.data)
        pagin_tc = self.paginator.paginate_queryset(queryset, request , view=self)
        serializer = MyDocumentSerializerNew(pagin_tc, many=True)
        response = self.get_paginated_response(serializer.data)
        return  response

    # def get_queryset(self):
    #     user = self.request.user
    #     ai_user = user.team.owner if user.team and user in user.team.get_project_manager else user 
    #     return WriterProject.objects.filter(ai_user=user)#.order_by('-id')
        

    # def list(self, request, *args, **kwargs):
    #     paginate = request.GET.get('pagination',True)
    #     queryset = self.filter_queryset(self.get_queryset())
    #     if paginate == 'False':
    #         serializer = WriterProjectSerializer(queryset, many=True)
    #         return Response(serializer.data)
    #     pagin_tc = self.paginator.paginate_queryset(queryset, request , view=self)
    #     serializer = WriterProjectSerializer(pagin_tc, many=True)
    #     response = self.get_paginated_response(serializer.data)
    #     return  response

    def retrieve(self, request, pk):
        queryset = self.get_queryset()
        ins = get_object_or_404(queryset, pk=pk)
        serializer = MyDocumentSerializer(ins)
        return Response(serializer.data)

    def create(self, request):
        file = request.FILES.get('file',None)
        ai_user = request.user.team.owner if request.user.team else request.user
        writer_proj = request.POST.get('project',None)
        if not writer_proj:
            writer_obj = WriterProject.objects.create(ai_user_id = ai_user.id)
            writer_proj = writer_obj.id
            print("Writer Proj-------->",writer_proj)
        ser = MyDocumentSerializer(data={**request.POST.dict(),'project':writer_proj,'file':file,'ai_user':ai_user.id,'created_by':request.user.id})
        if ser.is_valid(raise_exception=True):
            ser.save()
            return Response(ser.data, status=201)
        return Response(ser.errors)
        
    def update(self, request, pk, format=None):
        ins = MyDocuments.objects.get(id=pk)
        file = request.FILES.get('file')
        if file:
            ser = MyDocumentSerializer(ins,data={**request.POST.dict(),'file':file},partial=True)
        else:
             ser = MyDocumentSerializer(ins,data={**request.POST.dict()},partial=True)
        if ser.is_valid(raise_exception=True):
            ser.save()
            return Response(ser.data, status=200)
        return Response(ser.errors)

    def destroy(self, request, pk):
        ins = MyDocuments.objects.get(id=pk)
        ins.blog_doc.all().delete()
        ins.ai_doc_blog.all().delete()
        if ins.file:
            os.remove(ins.file.path)
        ins.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        
from django.db.models import Subquery
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def default_proj_detail(request):
    last_pr = Project.objects.filter(Q(ai_user=request.user)|Q(created_by=request.user)).last()
    if last_pr:
        query =  Project.objects.filter(Q(ai_user=request.user)|Q(created_by=request.user)).exclude(project_jobs_set__target_language=None).exclude(project_type_id=3).order_by('-id').annotate(target_count = Count('project_jobs_set__target_language')).filter(target_count__gte = 1)[:20]
        out = []
        for i in query:
            res={'src':i.project_jobs_set.first().source_language.id}
            res['tar']=[j.target_language.id for j in i.project_jobs_set.all()]
            if res not in out:
                out.append(res)
        # langs = query.filter(pk__in=Subquery(query.distinct('target_language').values("id"))).\
        #         values_list("source_language","target_language").order_by('-project__created_at')
        # langs = Job.objects.filter(project__ai_user_id = request.user).exclude(target_language=None).\
        #         values_list("source_language","target_language").distinct('target_language')
        #source_langs = [i[0] for i in langs]
        #target_langs = [i[1] for i in langs]
        #final_list = list(set().union(source_langs,target_langs))
        #source = last_pr.project_jobs_set.first().source_language_id
        mt_engine =last_pr.mt_engine_id
        out_1 = [a[0] for a in itertools.groupby(out)][:5]
        return JsonResponse({'recent_pairs':out_1,'mt_engine_id':mt_engine})
    else:
        return JsonResponse({'recent_pairs':[],'mt_engine_id':None})


def express_custom(request,exp_obj,option):
    from ai_openai.serializers import AiPromptSerializer
    from ai_openai.api_views import instant_customize_response
    user = exp_obj.task.job.project.ai_user
    instant_text = exp_obj.source_text
    tone=1
    txt_generated = None
    if not instant_text:
        with open(exp_obj.task.file.file.path, "r") as file:
            instant_text = file.read()
    target_lang_code = exp_obj.task.job.target_language_code
    source_lang_code = exp_obj.task.job.source_language_code
    customize = AiCustomize.objects.get(customize = option)
    total_tokens = 0
    if source_lang_code != 'en':
        initial_credit = user.credit_balance.get("total_left")
        print('InitialCredit---------->',initial_credit)
        consumable_credits_user_text =  get_consumable_credits_for_text(instant_text,source_lang=source_lang_code,target_lang='en')
        if initial_credit > consumable_credits_user_text:
            if target_lang_code!='en':
                user_insta_text_mt_en = get_translation(mt_engine_id=exp_obj.mt_engine_id , source_string = instant_text,
                                source_lang_code=source_lang_code , target_lang_code='en',user_id=user.id,from_open_ai=True)
                
                total_tokens += get_consumable_credits_for_text(user_insta_text_mt_en,source_lang=target_lang_code,target_lang='en')
            else:
                user_insta_text_mt_en = exp_obj.target_text
            result_txt,total_tokens = instant_customize_response(customize,user_insta_text_mt_en.replace('\r',''),total_tokens)
            #result_txt = response['choices'][0]['text']
            #print("Res from openai------------->",result_txt)
           
            if target_lang_code != 'en':
                txt_generated = get_translation(mt_engine_id=exp_obj.mt_engine_id , source_string = result_txt.strip(),
                            source_lang_code='en' , target_lang_code=target_lang_code,user_id=user.id,from_open_ai=True)
                total_tokens += get_consumable_credits_for_text(result_txt,source_lang='en',target_lang=target_lang_code)
            print("Tokens---------->",total_tokens)
        else:
            return ({'msg':'Insufficient Credits'})
    
    else:##english
        initial_credit = user.credit_balance.get("total_left")
        consumable_credits_user_text =  get_consumable_credits_for_text(instant_text,source_lang=source_lang_code,target_lang=target_lang_code)
        if initial_credit < consumable_credits_user_text:
            return ({'msg':'Insufficient Credits'})
        result_txt,total_tokens = instant_customize_response(customize,instant_text.replace('\r',''),total_tokens)
        #result_txt = response['choices'][0]['text']
        print("Tokens---------->",total_tokens)
        #print("Res from openai------------->",result_txt)
        if target_lang_code != 'en':
            txt_generated = get_translation(mt_engine_id=exp_obj.mt_engine_id , source_string = result_txt.strip(),
                        source_lang_code='en' , target_lang_code=target_lang_code,user_id=user.id,from_open_ai=True)
            total_tokens += get_consumable_credits_for_text(result_txt,source_lang='en',target_lang=target_lang_code)
    AiPromptSerializer().customize_token_deduction(instance = None,total_tokens= total_tokens,user=user)
    print("MT----->",exp_obj.mt_engine_id)
    inst_data = {'express':exp_obj.id,'source':instant_text, 'customize':customize.id,
                'api_result':result_txt.strip() if result_txt else None,'mt_engine':exp_obj.mt_engine_id,'final_result':txt_generated if txt_generated else result_txt.strip()}
    print("inst_data--->",inst_data)
    queryset = ExpressProjectAIMT.objects.filter(express=exp_obj,customize=customize).last()
    if queryset:
        serializer = ExpressProjectAIMTSerializer(queryset,data=inst_data,partial=True)
    else:
        serializer = ExpressProjectAIMTSerializer(data=inst_data)
    if serializer.is_valid():
        serializer.save()
        return (serializer.data)
    return (serializer.errors)



@api_view(['POST',])
@permission_classes([IsAuthenticated])
def instant_translation_custom(request):
    from ai_openai.serializers import AiPromptSerializer
    from ai_openai.api_views import customize_response
    task = request.POST.get('task')
    output_list = []
    option = request.POST.get('option')#Shorten#Simplify
    customize = AiCustomize.objects.get(customize = option)
    exp_obj = ExpressProjectDetail.objects.get(task_id = task)
    user = exp_obj.task.job.project.ai_user
    queryset = ExpressProjectAIMT.objects.filter(express=exp_obj,customize=customize).last()
    if queryset:
        text1 = exp_obj.source_text.strip()
        text2 = queryset.source.strip()
        print("Text1-------->",text1)
        print("Text2---------->",text2)
        output_list = [li for li in difflib.ndiff(text1.replace('\n',''), text2.replace('\n','')) if li[0]=='+' or li[0]=='-' if li[-1].strip()]
        #output_list_1 = [li for li in difflib.ndiff(text1.splitlines(keepends=False), text2.splitlines(keepends=False)) if li[0] == '+' or li[0] == '-']
        #output_list = [i.strip("+-") for i in output_list_1 if i.strip("+-").strip()]
        #print("OL------>",output_list)
        print("Mt------>",exp_obj.mt_engine_id) 
        print("Custom------>",queryset.mt_engine_id)
        if output_list == []:
            if exp_obj.mt_engine_id == queryset.mt_engine_id:
                serializer = ExpressProjectAIMTSerializer(queryset)
                return Response(serializer.data)
            elif queryset.api_result:
                input_src = queryset.api_result
                initial_credit = user.credit_balance.get("total_left")
                consumable_credit = get_consumable_credits_for_text(input_src,exp_obj.task.job.target_language_code,exp_obj.task.job.source_language_code)
                if initial_credit > consumable_credit:
                    txt_generated = get_translation(mt_engine_id=exp_obj.mt_engine_id , source_string = input_src,
                                    source_lang_code=exp_obj.task.job.source_language_code , target_lang_code=exp_obj.task.job.target_language_code,user_id=exp_obj.task.job.project.ai_user_id)
                    #debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credit)
                    serializer = ExpressProjectAIMTSerializer(queryset,data={'final_result':txt_generated,'mt_engine':exp_obj.mt_engine.id},partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return Response(serializer.data)
                    return Response(serializer.errors)
                else:
                    return Response({'msg':'Insufficient Credits'},status=400)
            else:
                res = express_custom(request,exp_obj,option)
                if res.get('msg'):return Response(res,status=400)
                else:return Response(res)
        else:
            res = express_custom(request,exp_obj,option)
            if res.get('msg'):return Response(res,status=400)
            else:return Response(res)
            
    elif not queryset:
        res = express_custom(request,exp_obj,option)
        if res.get('msg'):return Response(res,status=400)
        else:return Response(res)
        



# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def get_vendor_rates(request):
#     task_id = request.GET.get('task_id')
#     vendor_id = request.GET.get('vendor_id')
#     obj = Task.objects.get(id = task_id)
#     vendor = AiUser.objects.get(id=vendor_id)
#     query = VendorLanguagePair.objects.filter((Q(source_lang_id=obj.job.src_lang_id) & Q(target_lang_id=obj.job.tar_lang_id) & Q(user=vendor) & Q(deleted_at=None)))\
#              .select_related('service').values('currency','service__mtpe_rate','service__mtpe_hourly_rate','service__mtpe_count_unit')
#     if query:
#         return JsonResponse({'currency':query[0].get('currency'),'mtpe_rate':query[0].get('service__mtpe_rate'),\
#                         'hourly_rate':query[0].get('service__mtpe_hourly_rate'),'count_unit':query[0].get('service__mtpe_count_unit')})
#     else:
#         return JsonResponse({'msg':'Not available'})

# ##################################Need to revise#######################################
# # @api_view(['PUT',])
# # @permission_classes([IsAuthenticated])
# def update_project_from_writer(task_id):###########No  writer now...so simple text editor#############For Transcription projects
#     #task_id = request.POST.get('task_id')
#     obj = TaskTranscriptDetails.objects.filter(task_id = task_id).first()
#     writer_project_updated_count = 1 if obj.writer_project_updated_count==None else obj.writer_project_updated_count+1
#     print("project_update_count----------->",writer_project_updated_count)
#     obj.writer_project_updated_count = writer_project_updated_count
#     obj.save()
#     writer_filename = obj.writer_filename + '_edited_'+ str(obj.writer_project_updated_count)+'.docx'
#     file_obj = ContentFile(obj.transcripted_file_writer.file.read(),name=writer_filename)
#     print("FileObj------------>",file_obj)
#     return file_obj
#     # team = request.POST.get('team')
#     # target_languages = request.POST.getlist('target_languages')
#     # instance = Project.objects.get(id=id)
#     # target = target_exists(instance)
#     # if not target:
#     #     if not target_languages:
#     #         return Response({"msg":"Target languages are must to translate project"},status=400)
#     # source_language = [str(instance.project_jobs_set.first().source_language_id)]
#     # if target_languages:
#     #     serializer = ProjectQuickSetupSerializer(instance,data={\
#     #     'source_language':source_language,'target_languages':target_languages,'team':[team],'files':[file_obj]},\
#     #     context={"request": request}, partial=True)
#     # else:
#     #     serializer = ProjectQuickSetupSerializer(instance,data={'team':[team],'files':[file_obj]},\
#     #     context={"request": request}, partial=True)
#     # if serializer.is_valid():
#     #     serializer.save()
#     #     print("Data----------->",serializer.data)
#     #     return Response(serializer.data)
#     # return Response(serializer.errors)


    # client = speech.SpeechClient()
    #
    # with io.open(speech_file, "rb") as audio_file:
    #     content = audio_file.read()
    #
    # audio = speech.RecognitionAudio(content=content)
    #
    # config = speech.RecognitionConfig(encoding=speech.RecognitionConfig.AudioEncoding.MP3,sample_rate_hertz=16000,language_code=source_code,)
    #
    # # if os.path.splitext(file)[1] == '.mp3':
    # #     config = speech.RecognitionConfig(encoding=speech.RecognitionConfig.AudioEncoding.MP3,sample_rate_hertz=16000,language_code=source,)
    # # elif os.path.splitext(file)[1] == '.wav':
    # #     config = speech.RecognitionConfig(encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    # #         sample_rate_hertz=44100, #for .wav files
    # #         audio_channel_count=2,# for .wav files
    # #         language_code=source,
    # #     )
    # try:
    #     response = client.recognize(config=config, audio=audio)
    #     transcript=''
    #     for result in response.results:
    #         print(u"Transcript: {}".format(result.alternatives[0].transcript))
    #         transcript += result.alternatives[0].transcript
    #     # transcript = 'This is for sample check..'
    #     ser = TaskTranscriptDetailSerializer(data={"transcripted_text":transcript,"task":obj.id})
    #     if ser.is_valid():
    #         ser.save()
    #         return Response(ser.data)
    #     return Response(ser.errors)
    # except:
    #     return Response({'msg':'Audio File Size Too long Error'})
    # transcript = 'This is for sample check..'
    # return Response({'transcripted_msg':transcript})
    # name =  transcript.split()[0]+ ".txt" if len(transcript.split()[0])<=15 else transcript[:5]+ ".txt"
    # im_file= DjRestUtils.convert_content_to_inmemoryfile(filecontent = transcript.encode(),file_name=name)
    # team = True if obj.job.project.team else False
    # pr = obj.job.project
    # serializer = ProjectQuickSetupSerializer(pr,data={"files":[im_file],"team":[team],\
    #             "source_language":source,'target_languages':target_language},context={"request": request}, partial=True)
    # if serializer.is_valid():
    #     serializer.save()
    #     return Response(serializer.data)
    # return Response(serializer.errors)


        # obj = Task.objects.get(id = task)
        # file,ext = os.path.splitext(os.path.basename(obj.file.file.path))
        # name =file +'_source.mp3'
        # dir = os.path.dirname(obj.file.file.path)
        # loc = os.path.join(dir,"Audio",name)
        # return download_file(loc)
# query = VendorLanguagePair.objects.filter((Q(source_lang_id=i.src_lang_id) & Q(target_lang_id=i.tar_lang_id) & Q(user=vendor) & Q(deleted_at=None)))\
#         .select_related('service').values('currency','service__mtpe_rate','service__mtpe_hourly_rate','service__mtpe_count_unit')



#convert_text_to_speech_source
        # print("func----->",tt)
        # if tt.status_code == 400:
        #     return Response({'msg':'Insufficient Credits'},status=400)
        # ins = MTonlytaskCeleryStatus.objects.filter(task_id=obj.id).last()
        # state = text_to_speech_celery.AsyncResult(ins.celery_task_id).state if ins else None
        # if state == 'PENDING':
        #     return Response({'msg':'Text to Speech conversion ongoing. Please wait','celery_id':ins.celery_task_id})
        # elif (obj.task_transcript_details.exists()==False) or (not ins) or state == "FAILURE":
        #     tt = text_to_speech_celery.apply_async((obj.id,language,gender,user.id,voice_name), ) ###need to check####
        #     print("TT in viewss------------->",tt.get())
        #     if tt.get() == 400:
        #         return Response({'msg':'Insufficient Credits'},status=400)
        #     else:
        #         return Response({'msg':'Text to Speech conversion ongoing. Please wait','celery_id':tt.id})


            #     ins = MTonlytaskCeleryStatus.objects.filter(task_id=obj.id).last()
            #     state = text_to_speech_celery.AsyncResult(ins.celery_task_id).state if ins else None
            #     if state == 'PENDING':
            #         return Response({'msg':'Text to Speech conversion ongoing. Please wait','celery_id':ins.celery_task_id})
            #     elif (obj.task_transcript_details.exists()==False) or (not ins) or state == "FAILURE":
            #         conversion = text_to_speech_celery.apply_async((obj.id,language,gender,user.id,voice_name),)
            #         if conversion.get() == 200:
            #             task_list.append(obj.id)
            #         elif conversion.get() == 400:
            #             return Response({'msg':'Insufficient Credits'},status=400)
            # return Response({'msg':'Text to Speech conversion ongoing. Please wait','celery_id':conversion.id })
############project Download##################33
# path,filename = os.path.split(i.file.file.path)
                # name,ext =os.path.splitext(filename)
                # print('path----------->',path +'/'+ name +'_out' +"(" + i.job.source_language_code + "-" + i.job.target_language_code + ")" + ext)
                # if os.path.exists(path+'/'+name+'_out'+"(" + i.job.source_language_code + "-" + i.job.target_language_code + ")" + ext):
                #     print("True")
                # else:



            # if serializer.is_valid(raise_exception=True):
            #     serializer.save()
            #     pr = Project.objects.get(id=serializer.data.get('id'))
            #     if pr.pre_translate == True:
            #         mt_only.apply_async((serializer.data.get('id'), str(request.auth)), )
            #         # mt_only.delay((serializer.data.get('id'), str(request.auth)), )
            #     return Response(serializer.data, status=201)
            # return Response(serializer.errors, status=409)



class DocumentImageView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self,request):
        user = request.user
        image = DocumentImages.objects.filter(ai_user_id=user.id).all()
        serializer = DocumentImagesSerializer(image, many=True)
        return Response(serializer.data)

    def create(self, request):
        #glossaries = request.POST.getlist('glossary')
        doc = request.POST.get('document')
        image = request.FILES.get('image')
        serializer = DocumentImagesSerializer(data={**request.POST.dict(),'image':image,'ai_user':request.user.id})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self,request,pk):
        pass
        # doc = MyDocuments.objects.get(id=pk)
        # image = request.FILES.get('image')
        # print("Image--------->",image)
        # if image:
        #     print("******")
        #     serializer = DocumentImagesSerializer(doc,data={**request.POST.dict(),'image':image},partial=True)
        # else:
        #     print("&&&&&&&&&&")
        #     serializer= DocumentImagesSerializer(doc,data={**request.POST.dict()},partial=True)
        # if serializer.is_valid():
        #     serializer.save()
        #     return Response(serializer.data)
        # else:
        #     return Response(serializer.errors)


    def delete(self,request):
        image_url = request.GET.get('image_url')
        doc = request.GET.get('document')
        pdf = request.GET.get('pdf')
        task = request.GET.get('task')
        if doc:queryset = DocumentImages.objects.filter(document_id=doc).all()
        if pdf:queryset = DocumentImages.objects.filter(pdf_id=pdf).all()
        if task:queryset = DocumentImages.objects.filter(task_id=task).all()
        for i in queryset:
            if i.image.url == image_url:
                i.delete()
            else:
                print("No match")
        return Response(status=status.HTTP_204_NO_CONTENT)





class ExpressTaskHistoryView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    # def get_queryset(self):
    #     queryset=ExpressTaskHistory.objects.filter(id=self.id).all()
    #     return queryset

    def list(self,request):
        task_id = request.GET.get('task')
        queryset = ExpressTaskHistory.objects.filter(task_id=task_id).exclude(target_text=None).all().order_by('-id')
        print("QR----------->",queryset)
        serializer = ExpressTaskHistorySerializer(queryset,many=True)
        return Response(serializer.data)

    def create(self,request):
        source = request.POST.get('source_text')
        target = request.POST.get('target_text')
        task = request.POST.get('task')
        action = request.POST.get('action')
        serializer = ExpressTaskHistorySerializer(data={'source_text':source.replace('\r',''),'target_text':target.replace('\r',''),'action':action,'task':task})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self,request,pk):
        pass

    def delete(self,request,pk):
        obj = ExpressTaskHistory.objects.get(id=pk)
        obj.delete()
        return Response(status=204)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def docx_convertor(request):
    from docx import Document
    from ai_workspace.html2docx_custom import HtmlToDocx
    import re
    html = request.POST.get('html')
    name = request.POST.get('name')
    document = Document()
    new_parser = HtmlToDocx()
    new_parser.table_style = 'TableGrid'
    target_filename = name + '.docx'

    def replace_hex_color(match):
        hex_color = match.group(1)
        red, green, blue = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        rgb_color = f"rgb({red}, {green}, {blue})"
        return rgb_color

    def replace_hex_colors_with_rgb(html):
        hex_color_regex = re.compile("'#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})'")
        html = hex_color_regex.sub(replace_hex_color, html)
        return html

    updatedHtml = replace_hex_colors_with_rgb(html)  
    htmlupdates = updatedHtml.replace('<br />', '')
    #new_parser.add_html_to_document(htmlupdates, document)
    try:new_parser.add_html_to_document(htmlupdates, document)
    except:return Response({'msg':"Unsupported formatting"}, status=400)
    document.save(target_filename)
    res = download_file(target_filename)
    os.remove(target_filename)
    return res

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def project_word_char_count(request):
    from .api_views import ProjectAnalysisProperty
    from .models import MTonlytaskCeleryStatus
    prs = request.GET.getlist('project_id')
    final =[]
    for pr in prs:
        pr_obj = Project.objects.get(id=pr)
        print("Tasks--------->",pr_obj.get_tasks)
        obj = MTonlytaskCeleryStatus.objects.filter(project_id = pr).filter(task_name = 'project_analysis_property').last()
        state = project_analysis_property.AsyncResult(obj.celery_task_id).state if obj else None
        print("State-------->",state)
        if state == 'STARTED' or state == 'PENDING':
            res = {"proj":pr_obj.id,'msg':'project analysis ongoing. Please wait','celery_id':obj.celery_task_id}
        elif state =='None' or state == 'FAILURE':
            celery_task = project_analysis_property.apply_async((pr_obj.id,), )
            res = {"proj":pr_obj.id,'msg':'project analysis ongoing. Please wait','celery_id':celery_task.id}
        elif state == "SUCCESS" or pr_obj.is_proj_analysed == True:
            task_words = []
            tasks = pr_obj.get_tasks
            if pr_obj.is_all_doc_opened:

                [task_words.append({i.id:i.document.total_word_count}) for i in tasks]
                out=Document.objects.filter(id__in=[j.document_id for j in tasks]).aggregate(Sum('total_word_count'),\
                    Sum('total_char_count'),Sum('total_segment_count'))

                res = ({"proj": pr_obj.id, "proj_word_count": out.get('total_word_count__sum'), "proj_char_count":out.get('total_char_count__sum'), \
                    "proj_seg_count":out.get('total_segment_count__sum'),\
                                    "task_words" : task_words })
            else:
                out = TaskDetails.objects.filter(task_id__in=[j.id for j in tasks]).aggregate(Sum('task_word_count'),Sum('task_char_count'),Sum('task_seg_count'))
                task_words = []
                [task_words.append({i.id:i.task_details.first().task_word_count if i.task_details.first() else 0}) for i in tasks]

                res = ({"proj":pr_obj.id, "proj_word_count": out.get('task_word_count__sum'), "proj_char_count":out.get('task_char_count__sum'), \
                    "proj_seg_count":out.get('task_seg_count__sum'),
                                "task_words":task_words})
        else:
            #from .api_views import ProjectAnalysisProperty
            try:
                celery_task = project_analysis_property.apply_async((pr_obj_id,), )
                res = {"proj":pr_obj.id,'msg':'project analysis ongoing. Please wait','celery_id':celery_task.id}
                #return ProjectAnalysisProperty.get(pr_obj_id)

            except:
                res = ({"proj_word_count": 0, "proj_char_count": 0, \
                    "proj_seg_count": 0, "task_words":[]})
        final.append(res)
    return Response({'out':final})



# def task_download(task_id):
#     tt = Task.objects.get(id=task_id)
#     mt_only.apply_async((task.job.project.id, str(request.auth),task.id),)

from celery.result import AsyncResult
from django.http import HttpResponse
from celery import Celery

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stop_task(request):
    app = Celery('ai_tms')
    task_id = request.GET.get('task_id')
    task = AsyncResult(task_id)
    print("TT---------->",task.state)
    app.control.revoke(task_id,terminated=True, signal='SIGKILL')
    # if task.state == 'STARTED':
    #     app.control.revoke(task_id, terminated=True, signal='SIGKILL')
    #     return HttpResponse('Task has been stopped.') 
    # elif task.state == 'PROGRESS':
    #     app.control.revoke(task_id,terminated=True, signal='SIGKILL')
        # return HttpResponse('Task has been revoked.')
    # else:
    return HttpResponse('Task is already running or has completed.')

from django.template.loader import render_to_string
from django.core.mail import send_mail
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def msg_to_extend_deadline(request):
    from ai_marketplace.serializers import ThreadSerializer
    from ai_marketplace.models import ChatMessage
    task = request.POST.get('task')
    step = request.POST.get('step')
    reassigned = request.POST.get('reassigned')
    task_assign = TaskAssign.objects.get(task=task,step=step,reassigned=reassigned)
    sender = task_assign.assign_to
    receivers = []
    receiver =  task_assign.task_assign_info.assigned_by
    receivers =  receiver.team.get_project_manager if (receiver.team and receiver.team.owner.is_agency) or receiver.is_agency else []
    print("AssignedBy--------->",task_assign.task_assign_info.assigned_by)
    receivers.append(task_assign.task_assign_info.assigned_by)
    if receiver.team:
        receivers.append(task_assign.task_assign_info.assigned_by.team.owner)
    receivers = [*set(receivers)]
    print("Receivers----------->",receivers)
    for i in receivers:
        thread_ser = ThreadSerializer(data={'first_person':sender.id,'second_person':i.id})
        if thread_ser.is_valid():
            thread_ser.save()
            thread_id = thread_ser.data.get('id')
        else:
            thread_id = thread_ser.errors.get('thread_id')
		#print("Thread--->",thread_id)
        print("Details----------->",task_assign.task.ai_taskid,task_assign.assign_to.fullname,task_assign.task.job.project.project_name)
       
        message = "Task with task_id "+task_assign.task.ai_taskid+" assigned to "+ task_assign.assign_to.fullname +' for '+task_assign.step.name +" in "+task_assign.task.job.project.project_name+" has requested you to extend deadline."
        
    if thread_id:
        msg = ChatMessage.objects.create(message=message,user=sender,thread_id=thread_id)
        notify.send(sender, recipient=i, verb='Message', description=message,thread_id=int(thread_id))
        print("Msg Sent---------->",message)
    context = {'message':message}	
    Receiver_emails = [i.email for i in [*set(receivers)]]	
    print("Rece-------->",Receiver_emails)		
    msg_html = render_to_string("assign_notify_mail.html", context)
    send_mail(
        "Regarding Assigned Task Deadline Extension",None,
        settings.DEFAULT_FROM_EMAIL,
        Receiver_emails,
        #['thenmozhivijay20@gmail.com',],
        html_message=msg_html,
    )
    print("vendor requested expiry date extension  mailsent to vendor>>")	
    return Response({"msg":"Notification sent"})   
    # @integrity_error
    # def create(self,request):
    #     step = request.POST.get('step')
    #     task_assign_detail = request.POST.get('task_assign_detail')
    #     files=request.FILES.getlist('instruction_file')
    #     sender = self.request.user
    #     receiver = request.POST.get('assign_to')
    #     Receiver = AiUser.objects.get(id = receiver)
    #     ################################Need to change########################################
    #     user = request.user.team.owner  if request.user.team  else request.user
    #     if Receiver.email == 'ailaysateam@gmail.com':
    #         HiredEditors.objects.get_or_create(user_id=user.id,hired_editor_id=receiver,defaults = {"role_id":2,"status":2,"added_by_id":request.user.id})
    #     ##########################################################################################
    #     task = request.POST.getlist('task')
    #     hired_editors = sender.get_hired_editors if sender.get_hired_editors else []
    #     tasks= [json.loads(i) for i in task]
    #     tsks = Task.objects.filter(id__in=tasks)
    #     for tsk in tsks:
    #         authorize(request, resource=tsk, actor=request.user, action="read")
    #     job_id = Task.objects.get(id=tasks[0]).job.id
    #     assignment_id = create_assignment_id()
    #     for i in task_assign_detail:
            
    #         with transaction.atomic():
    #             try:
    #                 serializer = TaskAssignInfoSerializer(data={**request.POST.dict(),'assignment_id':assignment_id,'files':files,'task':request.POST.getlist('task')},context={'request':request})
    #                 if serializer.is_valid():
    #                     serializer.save()
    #                     weighted_count_update.apply_async((receiver,sender.id,assignment_id),)
    #                     msg_send(sender,Receiver,tasks[0])
    #                     print("Task Assigned")
    #                 print("Error--------->",serializer.errors)
    #             except:
    #                 pass
    #                 # if Receiver in hired_editors:
    #                 #     ws_forms.task_assign_detail_mail(Receiver,assignment_id)
    #                 # notify.send(sender, recipient=Receiver, verb='Task Assign', description='You are assigned to new task.check in your project list')
    #     return Response({"msg":"Task Assigned"})
    #     #return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
from itertools import chain
from .serializers import CombinedSerializer



class CombinedProjectListView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CombinedSerializer
    paginator = PageNumberPagination()
    paginator.page_size = 20

    def list(self,request):
        view_instance_1 = QuickProjectSetupView()

        view_instance_1.request = request
        view_instance_1.request.GET = request.GET

        queryset1 = view_instance_1.get_queryset()


        view_instance_2 = MyDocumentsView()

        view_instance_2.request = request
        view_instance_2.request.GET = request.GET

        queryset2 = view_instance_2.get_queryset_for_combined()
        print("Queryset@------------>",queryset2)

        project_managers = request.user.team.get_project_manager if request.user.team else []
        owner = request.user.team.owner if request.user.team  else request.user
        queryset3 = Ai_PdfUpload.objects.filter(Q(user = request.user) |Q(created_by=request.user)|Q(created_by__in=project_managers)|Q(user=owner))\
                            .filter(task_id=None).order_by('-id')
         
        search_query = request.GET.get('search')
        if search_query:
            queryset1 = queryset1.filter(project_name__icontains=search_query)
            queryset2 = [item for item in queryset2 if search_query.lower() in item.get('doc_name', '').lower()]
            queryset3 = queryset3.filter(pdf_file_name__icontains=search_query)
        print("Qu------->",queryset2)
        print("Q3--------->",queryset3)
        merged_queryset = list(chain(queryset1,queryset2,queryset3))
        ordering_param = request.GET.get('ordering', '-created_at')  

        if ordering_param.startswith('-'):
            field_name = ordering_param[1:]  
            reverse_order = True
        else:
            field_name = ordering_param
            reverse_order = False
        print("FieldName-------->",field_name)
        print("ReverseOrder---------->",reverse_order)
        ordered_queryset = sorted(merged_queryset, key=lambda obj: obj[field_name] if isinstance(obj, dict) else getattr(obj, field_name), reverse=reverse_order)

        # final_queryset = self.filter_queryset(merged_queryset)
        pagin_tc = self.paginator.paginate_queryset(ordered_queryset, request , view=self)
        ser = CombinedSerializer(pagin_tc,many=True,context={'request': request})
        response = self.get_paginated_response(ser.data)
        return response




# @api_view(['GET'])
# def combined_paginated_response(request):
#     view_instance_1 = QuickProjectSetupView()

#     view_instance_1.request = request
#     view_instance_1.request.GET = request.GET

#     queryset1 = view_instance_1.get_queryset()


#     view_instance_2 = MyDocumentsView()

#     view_instance_2.request = request
#     view_instance_2.request.GET = request.GET

#     queryset2 = view_instance_2.get_queryset_new()

#     search_query = request.GET.get('search')

#     if search_query:
#         queryset1 = queryset1.filter(project_name__icontains=search_query)
#         queryset2 = queryset2.filter(doc_name__icontains=search_query)

#     merged_queryset = list(chain(queryset1,queryset2))
#     ser = CombinedSerializer(merged_queryset,many=True,context={'request': request})
#     return Response(ser.data)
    


            # parent_queryset = queryset.annotate(
        #                     sorted_datetime=ExpressionWrapper(Coalesce(
        #                     # Use child_datetime if Child model is present, otherwise use parent_datetime
        #                     Case(
        #                         When(project_jobs_set__job_tasks_set__task_info__task_assign_info__isnull=False, then=F('project_jobs_set__job_tasks_set__task_info__task_assign_info__created_at')),
        #                         default=F('created_at'),
        #                         output_field=DateTimeField(),
        #                     ),
        #                     Value(datetime.min),),
        #                     output_field=DateTimeField(),)
        #                     )#.order_by('-sorted_datetime')

        #queryset = filter_authorize(self.request,queryset,'read',self.request.user)
               # print("User------------------>111----->",user)
        # user = self.request.user.team.owner if self.request.user.team else self.request.user
        # queryset = Project.objects.filter(Q(project_jobs_set__job_tasks_set__assign_to = self.request.user)|Q(ai_user = self.request.user)|Q(team__owner = self.request.user)).distinct()#.order_by("-id")



# from .serializers import ToolkitSerializer
# class ToolkitList(viewsets.ModelViewSet):

#     serializer_class = ToolkitSerializer
#     permission_classes = [IsAuthenticated]
#     filter_backends = [DjangoFilterBackend,SearchFilter,CaseInsensitiveOrderingFilter]
#     paginator = PageNumberPagination()
#     paginator.page_size = 20
#     # https://www.django-rest-framework.org/api-guide/filtering/


#     def list(self,request):
#         user = request.user
#         project_managers = user.team.get_project_manager if user.team else []
#         owner = user.team.owner if user.team  else user
#         query = request.GET.get('name')
#         ordering = request.GET.get('ordering')

#         view_instance_1 = QuickProjectSetupView()

#         view_instance_1.request = request
#         view_instance_1.request.GET = request.GET

#         queryset = view_instance_1.get_queryset()

#         queryset1 = queryset.filter(Q(glossary_project__isnull=True)&Q(voice_proj_detail__isnull=True)).filter(project_file_create_type__file_create_type="From insta text")
#         queryset2 = Ai_PdfUpload.objects.filter(Q(user = user) |Q(created_by=user)|Q(created_by__in=project_managers)|Q(user=owner))\
#                         .filter(task_id=None).order_by('-id')

#         search_query = request.GET.get('search')

#         if search_query:
#             queryset1 = queryset1.filter(project_name__icontains=search_query)
#             queryset2 = queryset2.filter(pdf_file_name__icontains=search_query)
#         merged_queryset = list(chain(queryset1,queryset2))
#         print("MQ-------------->",merged_queryset)
#         ordering_param = request.GET.get('ordering', '-created_at')  

#         if ordering_param.startswith('-'):
#             field_name = ordering_param[1:]  
#             reverse_order = True
#         else:
#             field_name = ordering_param
#             reverse_order = False
#         if field_name == 'created_at':
#             ordered_queryset = sorted(merged_queryset, key=lambda obj:getattr(obj, field_name), reverse=reverse_order)
#         else:
#             ordered_queryset = sorted(merged_queryset,key=lambda obj: (getattr(obj, 'project_name', None) or getattr(obj,'pdf_file_name',None)),reverse=reverse_order)
#         print("Or---------->",ordered_queryset)
#         pagin_tc = self.paginator.paginate_queryset(ordered_queryset, request , view=self)
#         ser = ToolkitSerializer(pagin_tc,many=True,context={'request': request})
#         response = self.get_paginated_response(ser.data)
#         return response


