import django_filters, mutagen
import shutil,docx2txt,regex,zipfile
from ai_workspace import forms as ws_forms
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from urllib.parse import urlparse
from ai_workspace.utils import create_assignment_id
from ai_workspace_okapi.models import Document
from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from ai_vendor.models import VendorLanguagePair
from ai_workspace_okapi.utils import download_file, get_translation
from ai_auth.authentication import IsCustomer
from ai_workspace.excel_utils import WriteToExcel_lite
from ai_glex.serializers import GlossarySetupSerializer,GlossaryFileSerializer,GlossarySerializer
from ai_auth.models import AiUser, UserCredits, Team, InternalMember
from rest_framework import viewsets, status
from integerations.base.utils import DjRestUtils
from rest_framework.response import Response
from indicnlp.tokenize.sentence_tokenize import sentence_split
from indicnlp.tokenize.indic_tokenize import trivial_tokenize
from ai_workspace_okapi.utils import download_file,text_to_speech
from .serializers import (ProjectContentTypeSerializer, ProjectCreationSerializer,\
    ProjectSerializer, JobSerializer,FileSerializer,FileSerializer,FileSerializer,\
    ProjectSetupSerializer, ProjectSubjectSerializer, TempProjectSetupSerializer,\
    TaskSerializer, FileSerializerv2, FileSerializerv3, TmxFileSerializer,\
    PentmWriteSerializer, TbxUploadSerializer, ProjectQuickSetupSerializer, TbxFileSerializer,\
    VendorDashBoardSerializer, ProjectSerializerV2, ReferenceFileSerializer, TbxTemplateSerializer,\
    TaskCreditStatusSerializer,TaskAssignInfoSerializer,TaskDetailSerializer,ProjectListSerializer,\
    GetAssignToSerializer,TaskTranscriptDetailSerializer, InstructionfilesSerializer, StepsSerializer, WorkflowsSerializer, \
                          WorkflowsStepsSerializer, TaskAssignUpdateSerializer, ProjectStepsSerializer)
import copy, os, mimetypes, logging
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Project, Job, File, ProjectContentType, ProjectSubjectField, TaskCreditStatus,\
    TempProject, TmxFile, ReferenceFiles,Templangpair,TempFiles,TemplateTermsModel, TaskDetails,\
    TaskAssignInfo,TaskTranscriptDetails, TaskAssign, Workflows, Steps, WorkflowSteps, TaskAssignHistory
from rest_framework import permissions
from django.shortcuts import get_object_or_404, get_list_or_404
from django.db import IntegrityError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Task, TbxFile, Instructionfiles
from django.http import JsonResponse
from .models import Task,Tbxfiles
from lxml import etree as ET
from django.db import transaction
from ai_marketplace.models import ChatMessage
from django.http import JsonResponse,HttpResponse
import requests, json, os,mimetypes
from ai_workspace_okapi.models import Document
from rest_framework.decorators import api_view
from django.http import JsonResponse, Http404, HttpResponse
from ai_workspace.excel_utils import WriteToExcel_lite
from ai_workspace.tbx_read import upload_template_data_to_db, user_tbx_write
from django.core.files import File as DJFile
from django.http import JsonResponse
from tablib import Dataset
import shutil,nltk
from datetime import datetime
from django.db.models import Q, Sum
from rest_framework.decorators import permission_classes
from notifications.signals import notify
from ai_marketplace.serializers import ThreadSerializer
from controller.serializer_mapper import serializer_map
# from ai_workspace_okapi.api_views import DocumentViewByTask
from ai_staff.models import LanguagesLocale, AilaysaSupportedMtpeEngines
from mutagen.mp3 import MP3
from google.cloud import speech
from google.cloud import speech_v1p1beta1 as speech
import io
from google.cloud import storage
from ai_auth.tasks import mt_only

spring_host = os.environ.get("SPRING_HOST")

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
        if kwargs.get("many")=="true":
            objs = self.get_object(many=True)
            for obj in objs:
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
        jobs = project.project_jobs_set.all()
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
                         "team_edit":team_edit,"project_type_id":project.project_type.id,\
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

class ProjectReportAnalysis(APIView):
    def get_queryset(self, project_id):
        project_qs = Project.objects.all()
        project = get_object_or_404(project_qs, id=project_id, ai_user=self.request.user)
        files = project.project_files_set.all()
        return files

    def post(self, request, project_id):
        data = dict(
            pentm_path = "/home/langscape/Documents/ailaysa_github/Ai_TMS/media/u343460/u343460p1/.pentm/",
            report_output_path = "/home/langscape/Documents/ailaysa_github/Ai_TMS/media/u343460/u343460p1/tt/report.html",
            srx_file_path = "/home/langscape/Documents/ailaysa_github/Ai_TMS/okapi_resources/okapi_default_icu4j.srx"
        )
        files = self.get_queryset(project_id)
        batches_data =  FileSerializerv3(files, many=True).data
        data = {
            **data,
            **dict(batches=batches_data)
        }
        print("data---->", data)
        res = requests.post(
            f"http://{spring_host}:8080/project/report-analysis",
            data = {"report_params": json.dumps(data)}
        )
        if res.status_code in [200, 201]:
            return JsonResponse({"msg": res.text}, safe=False)
        else:
            return JsonResponse({"msg": "something went to wrong"}, safe=False)

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
        if value == "glossary":
            queryset = queryset.filter(Q(glossary_project__isnull=False))
            return queryset
        if value == "voice":
            queryset = queryset.filter(Q(voice_proj_detail__isnull=False))
            return queryset
        # if value == "glossary":
        #     lookup = '__'.join([name, 'isnull'])
        #     return queryset.filter(**{lookup: False})
        # if value == "voice":
        #     lookup = '__'.join([name, 'isnull'])
        #     return queryset.filter(**{lookup: False})

class QuickProjectSetupView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    paginator = PageNumberPagination()
    serializer_class = ProjectQuickSetupSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    ordering_fields = ['project_name','team__name','id']
    filterset_class = ProjectFilter
    search_fields = ['project_name','project_files_set__filename','project_jobs_set__source_language__language',\
                    'project_jobs_set__target_language__language']
    ordering = ('-id')
    paginator.page_size = 20

    def get_serializer_class(self):
        project_type = json.loads(self.request.POST.get('project_type','1'))
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
        print(self.request.user)
        # queryset = Project.objects.filter(Q(project_jobs_set__job_tasks_set__assign_to = self.request.user)|Q(ai_user = self.request.user)|Q(team__owner = self.request.user)).distinct()#.order_by("-id")
        queryset = Project.objects.filter(Q(project_jobs_set__job_tasks_set__task_info__assign_to = self.request.user)\
                    |Q(ai_user = self.request.user)|Q(team__owner = self.request.user)\
                    |Q(team__internal_member_team_info__in = self.request.user.internal_member.filter(role=1))).distinct()
        return queryset

        # return Project.objects.filter(ai_user=self.request.user).order_by("-id").all()
        # return Project.objects.filter(Q(project_jobs_set__job_tasks_set__assign_to = self.request.user)|Q(ai_user = self.request.user)).distinct().order_by("-id")

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        pagin_tc = self.paginator.paginate_queryset(queryset, request , view=self)
        serializer = ProjectQuickSetupSerializer(pagin_tc, many=True, context={'request': request})
        response = self.get_paginated_response(serializer.data)
        return  response


    def create(self, request):
        # print("Project Creation request data----->", request.data)
        text_data=request.POST.get('text_data')
        ser = self.get_serializer_class()
        audio_file = request.FILES.getlist('audio_file',None)
        if text_data:
            if urlparse(text_data).scheme:
                return Response({"msg":"Url not Accepted"},status = 406)
            name =  text_data.split()[0]+ ".txt" if len(text_data.split()[0])<=15 else text_data[:5]+ ".txt"
            im_file= DjRestUtils.convert_content_to_inmemoryfile(filecontent = text_data.encode(),file_name=name)
            serializer = ser(data={**request.data,"files":[im_file]},context={"request": request})
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=409)
        else:
            #serlzr = ser(data={**request.data, "files": request.FILES.getlist("files")}, context={"request": request})
            serlzr = ser(data=\
            {**request.data, "files": request.FILES.getlist("files"),"audio_file":audio_file},context={"request": request})
            if serlzr.is_valid(raise_exception=True):
                serlzr.save()
                print("tt======>",serlzr.data.get('id'), str(request.auth))
                pr = Project.objects.get(id=serlzr.data.get('id'))
                print("TASks--------->",pr.get_tasks)
                mt_only.apply_async((serlzr.data.get('id'), str(request.auth)), )
                #check_dict.apply_async(serlzr.data,)
                return Response(serlzr.data, status=201)
            return Response(serlzr.errors, status=409)

    def update(self, request, pk, format=None):
        instance = self.get_object()
        ser = self.get_serializer_class()
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

        serlzr = ser(instance, data=\
            {**request.data, "files": request.FILES.getlist("files")},
            context={"request": request}, partial=True)

        if serlzr.is_valid(raise_exception=True):
            serlzr.save()
            return Response(serlzr.data)
        return Response(serlzr.errors, status=409)
    # def delete(self, request, pk):
    #     project = self.get_object()
    #     project.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)


class VendorDashBoardView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    paginator = PageNumberPagination()
    paginator.page_size = 20

    def get_tasks_by_projectid(self, pk):
        project = get_object_or_404(Project.objects.all(),
                    id=pk)
        if project.ai_user == self.request.user:
            return project.get_tasks
        if project.team:
            print(project.team.get_project_manager)
            if ((project.team.owner == self.request.user)|(self.request.user in project.team.get_project_manager)):
                return project.get_tasks
            # elif self.request.user in project.team.get_project_manager:
            #     return project.get_tasks
            else:
                return [task for job in project.project_jobs_set.all() for task \
                        in job.job_tasks_set.all() for task_assign in task.task_info.filter(assign_to_id = self.request.user)]
        else:
            return [task for job in project.project_jobs_set.all() for task \
                    in job.job_tasks_set.all() for task_assign in task.task_info.filter(assign_to_id = self.request.user)]


    def get_object(self):
        tasks = Task.objects.order_by("-id").all()
        tasks = get_list_or_404(tasks, file__project__ai_user=self.request.user)
        return tasks

    def list(self, request, *args, **kwargs):
        tasks = self.get_object()
        pagin_queryset = self.paginator.paginate_queryset(tasks, request, view=self)
        serlzr = VendorDashBoardSerializer(pagin_queryset, many=True,context={'request':request})
        return self.get_paginated_response(serlzr.data)

    def retrieve(self, request, pk, format=None):
        print("%%%%")
        tasks = self.get_tasks_by_projectid(pk=pk)
        print(tasks)
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
        data = {**request.POST.dict(), "tbx_file" : request.FILES.get('tbx_file')}
        # data["project_id"] = project_id
        data.update({'project_id': project_id})
        #print("########", data)
        ser_data = TbxFileSerializer.prepare_data(data)
        #print("$$$$$$", ser_data)
        serializer = TbxFileSerializer(data=ser_data)
        #print("%%%%%%%%%%", serializer.is_valid())
        if serializer.is_valid(raise_exception=True):
            #print("***VALID***")
            serializer.save()
            #print("AFTER SAVE", serializer.data)
        return Response(serializer.data, status=201)

class TbxFileDetail(APIView):

    def get_object(self, id):
        try:
            return TbxFile.objects.get(id=id)
        except TbxFile.DoesNotExist:
            return HttpResponse(status=404)

    def put(self, request, id):
        tbx_asset = self.get_object(id)
        tbx_file = request.FILES.get('tbx_file')
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
                return Response({'msg':"Something wrong in TBX conversion. Use glossary template to upload terms", "data":{}},
                        status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors)

@api_view(['GET',])
def tbx_download(request,tbx_file_id):
    tbx_asset = TbxFile.objects.get(id=tbx_file_id).tbx_file
    fl_path = tbx_asset.path
    filename = os.path.basename(fl_path)
    print(os.path.dirname(fl_path))
    fl = open(fl_path, 'rb')
    mime_type, _ = mimetypes.guess_type(fl_path)
    response = HttpResponse(fl, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response

class UpdateTaskCreditStatus(APIView):

    permission_classes = [IsAuthenticated]

    @staticmethod
    def update_addon_credit(user, actual_used_credits=None, credit_diff=None):
        add_ons = UserCredits.objects.filter(Q(user=user) & Q(credit_pack_type="Addon"))
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
        # doc = Document.objects.get(id = doc_id)
        # user = doc.doc_credit_debit_user
        print("Credit User",type(user))
        present = datetime.now()
        try:
            # carry_on_credits = UserCredits.objects.filter(Q(user=user) & Q(credit_pack_type__icontains="Subscription") & \
            #     Q(ended_at__isnull=False)).last()

            user_credit = UserCredits.objects.get(Q(user=user) & Q(credit_pack_type__icontains="Subscription") & Q(ended_at=None))

            # Check whether to debit from carry-on-credit or current subscription credit record
            # if (carry_on_credits) and \
            #     (user_credit.created_at.strftime('%Y-%m-%d %H:%M:%S') <= carry_on_credits.expiry.strftime('%Y-%m-%d %H:%M:%S')):
            #     credit_record = carry_on_credits
            # else:
            #     credit_record = user_credit

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
        # print("CREDIT STATUS----->", credit_status)

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
    # if (request.user.is_internal_member) and (InternalMember.objects.get(internal_member=request.user.id).role.id == 1):
    #     return Response({"credits_left" : request.user.internal_team_manager.credit_balance,
    #                         "total_available" : request.user.internal_team_manager.buyed_credits}, status=200)
    # return Response({"credits_left" : request.user.credit_balance,
    #                         "total_available" : request.user.buyed_credits}, status=200)
    return Response({"credits_left": request.user.credit_balance,}, status=200)

#############Tasks Assign to vendor#################
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


@api_view(['POST',])
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

    @staticmethod
    def correct_fields(data):
        check_fields = ProjectAnalysisProperty.erfogd()
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
        tasks = []
        for _task in project_tasks:
            if _task.task_details.first() == None:
                tasks.append(_task)
        task_words = []
        file_ids = []

        for task in tasks:
            if task.file_id not in file_ids:

                ser = TaskSerializer(task)
                data = ser.data
                ProjectAnalysisProperty.correct_fields(data)
                params_data = {**data, "output_type": None}
                res_paths = {"srx_file_path":"okapi_resources/okapi_default_icu4j.srx",
                         "fprm_file_path": None,
                         "use_spaces" : settings.USE_SPACES
                         }
                doc = requests.post(url=f"http://{spring_host}:8080/getDocument/", data={
                    "doc_req_params":json.dumps(params_data),
                    "doc_req_res_params": json.dumps(res_paths)
                })
                print("Status@@@@@@@@@@@@@@@@@@@@@@@@",doc.status_code)
                try:
                    if doc.status_code == 200 :
                        doc_data = doc.json()
                        # task_words.append({task.id : doc_data.get('total_word_count')})

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
                        logging.debug(msg=f"error raised while process the document, the task id is {task.id}")
                        raise  ValueError("Sorry! Something went wrong with file processing.")
                except:
                    print("No entry")
                file_ids.append(task.file_id)

            else:
                print("*************  File taken only once  **************")
                tasks = [i for i in Task.objects.filter(file_id=task.file_id)]
                print("####",tasks)
                task_details = TaskDetails.objects.filter(task__in = tasks).first()
                task_details.pk = None
                task_details.task_id = task.id
                task_details.save()
                # task_words.append({task.id : task_details.task_word_count})

        [task_words.append({task.id : task.task_details.first().task_word_count})for task in project.get_mtpe_tasks]
        out = TaskDetails.objects.filter(project_id=project_id).aggregate(Sum('task_word_count'),Sum('task_char_count'),Sum('task_seg_count'))
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

def msg_send(sender,receiver,task):
    obj = Task.objects.get(id=task)
    proj = obj.job.project.project_name
    thread_ser = ThreadSerializer(data={'first_person':sender.id,'second_person':receiver.id})
    if thread_ser.is_valid():
        thread_ser.save()
        thread_id = thread_ser.data.get('id')
    else:
        thread_id = thread_ser.errors.get('thread_id')
    # print("Thread--->",thread_id)
    message = "You have been assigned a new task in "+proj+"."
    msg = ChatMessage.objects.create(message=message,user=sender,thread_id=thread_id)
    notify.send(sender, recipient=receiver, verb='Message', description=message,thread_id=int(thread_id))

class TaskAssignUpdateView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def update(self, request,pk=None):
        task = request.POST.get('task')
        step = request.POST.get('step')
        file = request.FILES.getlist('instruction_file')
        req_copy = copy.copy( request._request)
        req_copy.method = "DELETE"

        file_delete_ids = self.request.query_params.get(\
            "file_delete_ids", [])

        if file_delete_ids:
            file_res = InstructionFilesView.as_view({"delete": "destroy"})(request=req_copy,\
                        pk='0', many="true", ids=file_delete_ids)
        if not task:
            return Response({'msg':'Task Id required'},status=status.HTTP_400_BAD_REQUEST)
        # try:
        task_assign = TaskAssign.objects.get(Q(task_id = task) & Q(step_id = step))
        if file:
            serializer =TaskAssignUpdateSerializer(task_assign,data={**request.POST.dict(),'files':file},context={'request':request},partial=True)
        else:
            serializer =TaskAssignUpdateSerializer(task_assign,data={**request.POST.dict()},context={'request':request},partial=True)
        if serializer.is_valid():
            serializer.save()
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # except:
            # return Response({'msg':'Task Assign details not found'},status=status.HTTP_400_BAD_REQUEST)
        return Response(task, status=status.HTTP_200_OK)




class TaskAssignInfoCreateView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self,request):
        tasks = request.GET.getlist('tasks')
        step = request.GET.get('step')
        try:
            task_assign_info = TaskAssignInfo.objects.filter(task_assign__task_id__in = tasks)
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


    @integrity_error
    def create(self,request):
        step = request.POST.get('step')
        task_assign_detail = request.POST.get('task_assign_detail')
        files=request.FILES.getlist('instruction_file')
        sender = self.request.user
        receiver = request.POST.get('assign_to')
        Receiver = AiUser.objects.get(id = receiver)
        ################################Need to change########################################
        user = request.user.team.owner  if request.user.team  else request.user
        if Receiver.email == 'ailaysateam@gmail.com':
            HiredEditors.objects.get_or_create(user_id=user.id,hired_editor_id=receiver,defaults = {"role_id":2,"status":2,"added_by_id":request.user.id})
        ##########################################################################################
        task = request.POST.getlist('task')
        hired_editors = sender.get_hired_editors if sender.get_hired_editors else []
        tasks= [json.loads(i) for i in task]
        assignment_id = create_assignment_id()
        with transaction.atomic():
            serializer = TaskAssignInfoSerializer(data={**request.POST.dict(),'assignment_id':assignment_id,'files':files,'task':request.POST.getlist('task')},context={'request':request})
            # assignment_id = create_assignment_id()
            # serializer = TaskAssignInfoSerializer(data={**request.POST.dict(),'assignment_id':assignment_id,'instruction_file':file,'task':request.POST.getlist('task')},context={'request':request})
            if serializer.is_valid():
                serializer.save()
                msg_send(sender,Receiver,tasks[0])
                if Receiver in hired_editors:
                    ws_forms.task_assign_detail_mail(Receiver,assignment_id)
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
    def update(self, request,pk=None):
        task = request.POST.getlist('task')
        file = request.FILES.get('instruction_file')
        assign_to = request.POST.get('assign_to',None)
        if not task:
            return Response({'msg':'Task Id required'},status=status.HTTP_400_BAD_REQUEST)
        ###############################Need to change############################################
        if assign_to:
            Receiver = AiUser.objects.get(id = assign_to)
            user = request.user.team.owner  if request.user.team  else request.user
            if Receiver.email == 'ailaysateam@gmail.com':
                HiredEditors.objects.get_or_create(user_id=user.id,hired_editor_id=assign_to,defaults = {"role_id":2,"status":2,"added_by_id":request.user.id})
        ###########################################################################################
        for i in task:
            try:
                task_assign_info = TaskAssignInfo.objects.get(task_id = i)
                if file:
                    serializer =TaskAssignInfoSerializer(task_assign_info,data={**request.POST.dict(),'instruction_file':file},context={'request':request},partial=True)
                else:
                    serializer =TaskAssignInfoSerializer(task_assign_info,data={**request.POST.dict()},context={'request':request},partial=True)
                if serializer.is_valid():
                    serializer.save()
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except TaskAssignInfo.DoesNotExist:
                print('not exist')
        return Response(task, status=status.HTTP_200_OK)

    def delete(self,request):
        task = request.GET.getlist('task')
        steps = request.GET.getlist('step')
        task_assign_info_ids = request.GET.getlist('task_assign_info')
        if task and steps:
            assigns = TaskAssignInfo.objects.filter(Q(task_assign__task_id__in=task) & Q(task_assign__step_id__in=steps))
        if task_assign_info_ids:
            assigns = TaskAssignInfo.objects.filter(id__in = task_assign_info_ids )
        for obj in assigns:
            self.history(obj)
            user = obj.task_assign.task.job.project.ai_user
            obj.task_assign.assign_to = user
            obj.task_assign.save()
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




class ProjectListView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectListSerializer

    def get_queryset(self):
        print(self.request.user)
        queryset = Project.objects.filter(Q(project_jobs_set__job_tasks_set__task_info__assign_to = self.request.user)\
                    |Q(ai_user = self.request.user)|Q(team__owner = self.request.user)\
                    |Q(team__internal_member_team_info__in = self.request.user.internal_member.filter(role=1))).distinct().order_by('-id')
        # queryset = Project.objects.filter(Q(project_jobs_set__job_tasks_set__assign_to = self.request.user)\
        #             |Q(ai_user = self.request.user)|Q(team__owner = self.request.user)\
        #             |Q(team__internal_member_team_info__in = self.request.user.internal_member.filter(role=1))).distinct().order_by('-id')
        return queryset

    def list(self,request):
        proj_list=[]
        queryset = self.get_queryset()
        serializer = ProjectListSerializer(queryset, many=True, context={'request': request})
        data = serializer.data
        for i in data:
            if i.get('assign_enable')==True:
                proj_list.append(i)
        return Response(proj_list)
        # return  Response(serializer.data)



@permission_classes([IsAuthenticated])
@api_view(['GET',])
def tasks_list(request):
    job_id = request.GET.get("job")
    try:
        job = Job.objects.get(id = job_id)
        tasks = job.job_tasks_set.all()
        ser = VendorDashBoardSerializer(tasks,many=True,context={'request':request})
        return Response(ser.data)
    except:
        return JsonResponse({"msg":"No job exists"})


    # for i in tasks:
    #     task_list.append({'id':i.id,'task':i.job,'file':i.file})
    # return Response(task_list)
@api_view(['GET',])
def instruction_file_download(request,task_assign_info_id):
    instruction_file = TaskAssignInfo.objects.get(id=task_assign_info_id).instruction_file
    if instruction_file:
        fl_path = instruction_file.path
        filename = os.path.basename(fl_path)
        # print(os.path.dirname(fl_path))
        fl = open(fl_path, 'rb')
        mime_type, _ = mimetypes.guess_type(fl_path)
        response = HttpResponse(fl, content_type=mime_type)
        response['Content-Disposition'] = "attachment; filename=%s" % filename
        return response
    else:
        return JsonResponse({"msg":"no file associated with it"})


class AssignToListView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    def list(self, request, *args, **kwargs):
        project = self.request.GET.get('project')
        user = Project.objects.get(id = project).ai_user
        serializer = GetAssignToSerializer(user,context={'request':request})
        return Response(serializer.data, status=201)

class IntegerationProject(viewsets.ViewSet):

    def list(self, request, *args, **kwargs):
        project_id = self.kwargs.get("pk", None)
        #  ownership
        project = get_object_or_404(Project.objects.all(),
            id=project_id)
        #  ownership
        download_project = project.project_download.\
            get_download

        serlzr_class = serializer_map.get(
            download_project.serializer_class_str)

        serlzr = serlzr_class(download_project.branch.branch_contentfiles_set
            .all(), many=True)

        return Response(serlzr.data)












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

@api_view(["GET"])
def project_download(request,project_id):
    pr = Project.objects.get(id=project_id)
    if os.path.exists(os.path.join(pr.project_dir_path,'source')):
        shutil.make_archive(pr.project_name, 'zip', pr.project_dir_path + '/source')
        res = download_file(pr.project_name+'.zip')
        os.remove(pr.project_name+'.zip')
        return res
    else:
        return Response({'msg':'something went wrong'})

class ShowMTChoices(APIView):
    # permission_classes = [IsAuthenticated]

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
                try:
                    mt_responses[mt_engine.name] = get_translation(mt_engine.id, text_1, ShowMTChoices.get_lang_code(sl_code), ShowMTChoices.get_lang_code(tl))
                except:
                    mt_responses[mt_engine.name] = None
                res[tl] = mt_responses

        return Response(res, status=status.HTTP_200_OK)


###########################Transcribe Short File############################## #######

def transcribe_short_file(speech_file,source_code,obj):
    client = speech.SpeechClient()

    with io.open(speech_file, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)

    config = speech.RecognitionConfig(encoding=speech.RecognitionConfig.AudioEncoding.MP3,sample_rate_hertz=16000,language_code=source_code,)
    try:
        response = client.recognize(config=config, audio=audio)
        transcript=''
        for result in response.results:
            print(u"Transcript: {}".format(result.alternatives[0].transcript))
            transcript += result.alternatives[0].transcript
        ser = TaskTranscriptDetailSerializer(data={"transcripted_text":transcript,"task":obj.id})
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



def transcribe_long_file(speech_file,source_code,filename,obj):

    bucket_name = os.getenv("BUCKET")
    source_file_name = speech_file
    destination_blob_name = filename

    upload_blob(bucket_name, source_file_name, destination_blob_name)

    gcs_uri = os.getenv("BUCKET_URL") + filename
    transcript = ''

    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(uri=gcs_uri)

    config =  speech.RecognitionConfig(encoding=speech.RecognitionConfig.AudioEncoding.MP3,sample_rate_hertz=16000,language_code=source_code,)


    # Detects speech in the audio file
    operation = client.long_running_recognize(config=config, audio=audio)
    response = operation.result(timeout=10000)

    for result in response.results:
        transcript += result.alternatives[0].transcript
    print("Transcript--------->",transcript)

    delete_blob(bucket_name, destination_blob_name)

    ser = TaskTranscriptDetailSerializer(data={"transcripted_text":transcript,"task":obj.id})
    if ser.is_valid():
        ser.save()
        return (ser.data)
    return (ser.errors)



################################speech-to-text############# working#############################3
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def transcribe_file(request):
    task_id = request.POST.get('task')
    target_language = request.POST.getlist('target_languages')
    queryset = TaskTranscriptDetails.objects.filter(task_id = task_id)
    print("QS--->",queryset)
    if queryset:
        ser = TaskTranscriptDetailSerializer(queryset,many=True)
        return Response(ser.data)
    else:
        obj = Task.objects.get(id = task_id)
        source = [obj.job.source_language.id]
        source_code = obj.job.source_language_code
        filename = obj.file.filename
        speech_file = obj.file.file.path
        try:
            audio = MP3(speech_file)
            length = int(audio.info.length)
        except:
            length=None
        print("Length----->",length)
        if length and length<60:
            res = transcribe_short_file(speech_file,source_code,obj)
        else:
            res = transcribe_long_file(speech_file,source_code,filename,obj)
        print("RES----->",res)
        return JsonResponse(res,safe=False)



@api_view(["GET"])
#@permission_classes([IsAuthenticated])
def convert_and_download_text_to_speech_source(request):#########working############Transcribe and Download
    tasks =[]
    project = request.GET.get('project',None)
    # task = request.GET.get('task',None)
    pr = Project.objects.get(id=project)
    for _task in pr.get_tasks:
        if _task.task_transcript_details.first() == None:
            tasks.append(_task)
    for obj in tasks:
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
        seg_data = {"segment_source":data, "source_language":obj.job.source_language_code, "target_language":obj.job.source_language_code,\
                     "processor_name":"plain-text-processor", "extension":".txt"}
        res1 = requests.post(url=f"http://{spring_host}:8080/segment/word_count", data={"segmentWordCountdata":json.dumps(seg_data)})
        wc = res1.json() if res1.status_code == 200 else None
        TaskDetails.objects.create(task = obj,task_word_count = wc,project = obj.job.project)
        audio_file = name_ + '_source'+'.mp3'
        res2,f2 = text_to_speech(name,obj.job.source_language_code,audio_file,'FEMALE')
        ser = TaskTranscriptDetailSerializer(data={"source_audio_file":res2,"task":obj.id})
        if ser.is_valid():
            ser.save()
        f2.close()
        os.remove(audio_file)
        print(ser.errors)
    shutil.make_archive(pr.project_name, 'zip', pr.project_dir_path + '/source/Audio')
    res = download_file(pr.project_name+'.zip')
    os.remove(pr.project_name+'.zip')
    return res



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_text_to_speech_source(request):
    task = request.GET.get('task')
    obj = Task.objects.get(id = task)
    try:
        file = obj.task_transcript_details.first().source_audio_file
        return download_file(file.path)
    except:
        return Response({'msg':'something went wrong'})



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_speech_to_text_source(request):
    task = request.GET.get('task')
    obj = Task.objects.get(id = task)
    try:
        # output_from_writer =  obj.task_transcript_details.first().transcripted_file_writer
        # return download_file(output_from_writer.path)
        text = obj.task_transcript_details.first().transcripted_text
        with open('out.txt', "w") as out:
            out.write(text)
        res = download_file('out.txt')
        os.remove('out.txt')
        return res
    except:
        return Response({'msg':'something went wrong'})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def project_download(request,project_id):
    # projects = request.GET.getlist('project')
    pr = Project.objects.get(id=project_id)
    shutil.make_archive(pr.project_name, 'zip', pr.project_dir_path + '/source')
    tt = download_file(pr.project_name+'.zip')
    os.remove(pr.project_name+'.zip')
    return tt



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

##################################Need to revise#######################################
@api_view(['PUT',])
@permission_classes([IsAuthenticated])
def update_project_from_writer(request,id):
    project = Project.objects.get(id=id)
    ser = ProjectQuickSetupSerializer(project, data=\
        {**request.data, "files": request.FILES.get("files")},
        context={"request": request}, partial=True)
    if ser.is_valid():
        ser.save()
    ser1 = TaskTranscriptDetailSerializer(data={"transcripted_file_writer":request.FILES.get('files'),"task":task.id})
    if ser1.is_valid():
        ser1.save()




































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
