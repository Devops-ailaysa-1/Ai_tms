from rest_framework.exceptions import ValidationError
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from urllib.parse import urlparse
from ai_workspace_okapi.models import Document
from django.conf import settings
from django.core.files import File as DJFile
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from ai_vendor.models import VendorLanguagePair
from ai_auth.authentication import IsCustomer
from ai_workspace.excel_utils import WriteToExcel_lite
from ai_auth.models import AiUser, UserCredits, Team, InternalMember, HiredEditors
from rest_framework import viewsets, status
from rest_framework.response import Response
from .serializers import (ProjectContentTypeSerializer, ProjectCreationSerializer,\
    ProjectSerializer, JobSerializer,FileSerializer,FileSerializer,FileSerializer,\
    ProjectSetupSerializer, ProjectSubjectSerializer, TempProjectSetupSerializer,\
    TaskSerializer, FileSerializerv2, FileSerializerv3, TmxFileSerializer,\
    PentmWriteSerializer, TbxUploadSerializer, ProjectQuickSetupSerializer, TbxFileSerializer,\
    VendorDashBoardSerializer, ProjectSerializerV2, ReferenceFileSerializer, TbxTemplateSerializer,\
    TaskCreditStatusSerializer,TaskAssignInfoSerializer,TaskDetailSerializer,ProjectListSerializer)
import copy, os, mimetypes, logging
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Project, Job, File, ProjectContentType, ProjectSubjectField, TaskCreditStatus,\
    TempProject, TmxFile, ReferenceFiles,Templangpair,TempFiles,TemplateTermsModel, TaskDetails, TaskAssignInfo
from rest_framework import permissions
from django.shortcuts import get_object_or_404, get_list_or_404
from django.db import IntegrityError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Task, TbxFile
from django.http import JsonResponse
import requests, json, os, time
from .models import Task,Tbxfiles
from lxml import etree as ET
from ai_marketplace.models import AvailableVendors
from django.http import JsonResponse,HttpResponse
import requests, json, os,mimetypes
from ai_workspace import serializers
from ai_workspace_okapi.models import Document
from ai_staff.models import LanguagesLocale, Languages
from rest_framework.decorators import api_view
from django.http import JsonResponse, Http404, HttpResponse
from ai_workspace.excel_utils import WriteToExcel_lite
from ai_workspace.tbx_read import upload_template_data_to_db, user_tbx_write
from django.core.files import File as DJFile
from django.http import JsonResponse
from tablib import Dataset
import shutil
from datetime import datetime
from django.db.models import Q, Sum
from rest_framework.decorators import permission_classes
from notifications.signals import notify
from notifications.models import Notification
# from ai_workspace_okapi.api_views import DocumentViewByTask

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

class ProjectContentTypeView(viewsets.ModelViewSet):
    serializer_class = ProjectContentTypeSerializer

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
        project = get_object_or_404(Project.objects.all(), id=project_id,
                        ai_user=self.request.user)
        project_name = project.project_name
        jobs = project.project_jobs_set.all()
        files = project.project_files_set.filter(usage_type__use_type="source").all()
        return jobs, files, project_name

    def get(self, request, project_id):
        jobs, files, project_name = self.get_queryset(project_id)
        jobs = JobSerializer(jobs, many=True)
        files = FileSerializer(files, many=True)
        return Response({"files":files.data, "jobs": jobs.data, "project_name": project_name}, status=200)

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
    # team = django_filters.CharFilter(field_name='team__name',lookup_expr='icontains')
    team = django_filters.CharFilter(field_name='team__name',method='filter_team')#lookup_expr='isnull')
    class Meta:
        model = Project
        fields = ('project', 'team')

    def filter_team(self, queryset, name, value):
        if value=="None":
            lookup = '__'.join([name, 'isnull'])
            return queryset.filter(**{lookup: True})
        else:
            lookup = '__'.join([name, 'icontains'])
            return queryset.filter(**{lookup: value})

class QuickProjectSetupView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    paginator = PageNumberPagination()
    serializer_class = ProjectQuickSetupSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    ordering_fields = ['project_name','team__name','id']
    filterset_class = ProjectFilter
    search_fields = ['project_name']
    ordering = ('-id')
    paginator.page_size = 20

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
        queryset = Project.objects.filter(Q(project_jobs_set__job_tasks_set__assign_to = self.request.user)\
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
        text_data=request.POST.get('text_data')
        if text_data:
            if urlparse(text_data).scheme:
                return Response({"msg":"Url not Accepted"},status = 406)
            file_obj2,f2,name = text_file_processing(text_data)
            serializer = ProjectQuickSetupSerializer(data={**request.data,"files":[file_obj2]},context={"request": request})
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                f2.close()
                os.remove(os.path.abspath(name))
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=409)
        else:
            serlzr = ProjectQuickSetupSerializer(data=\
            {**request.data, "files": request.FILES.getlist("files")},context={"request": request})
            if serlzr.is_valid(raise_exception=True):
                serlzr.save()
                return Response(serlzr.data, status=201)
            return Response(serlzr.errors, status=409)

    def update(self, request, pk, format=None):
        instance = self.get_object()
        req_copy = copy.copy( request._request)
        req_copy.method = "DELETE"

        file_delete_ids = self.request.query_params.get(\
            "file_delete_ids", [])
        job_delete_ids = self.request.query_params.get(\
            "job_delete_ids", [])
        if file_delete_ids:
            file_res = FileView.as_view({"delete": "destroy"})(request=req_copy,\
                        pk='0', many="true", ids=file_delete_ids)

        if job_delete_ids:
            job_res = JobView.as_view({"delete": "destroy"})(request=req_copy,\
                        pk='0', many="true", ids=job_delete_ids)

        serlzr = ProjectQuickSetupSerializer(instance, data=\
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
            if ((project.team.owner == self.request.user)|(self.request.user in project.team.get_project_manager)):
                return project.get_tasks
            # elif self.request.user in project.team.get_project_manager:
            #     return project.get_tasks
            else:
                return [task for job in project.project_jobs_set.all() for task \
                        in job.job_tasks_set.all().filter(assign_to_id = self.request.user)]
        else:
            return [task for job in project.project_jobs_set.all() for task \
                    in job.job_tasks_set.all().filter(assign_to_id = self.request.user)]


    def get_object(self):
        tasks = Task.objects.order_by("-id").all()
        tasks = get_list_or_404(tasks, file__project__ai_user=self.request.user)
        return tasks

    def list(self, request, *args, **kwargs):
        tasks = self.get_object()
        pagin_queryset = self.paginator.paginate_queryset(tasks, request, view=self)
        serlzr = VendorDashBoardSerializer(pagin_queryset, many=True)
        return self.get_paginated_response(serlzr.data)

    def retrieve(self, request, pk, format=None):
        print("%%%%")
        tasks = self.get_tasks_by_projectid(pk=pk)
        print(tasks)
        serlzr = VendorDashBoardSerializer(tasks, many=True)
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
        serlzr = VendorDashBoardSerializer(tasks, many=True)
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

    # @staticmethod
    # def get_object(doc_id):
    #     try:
    #         return TaskCreditStatus.objects.get(task__document=doc_id)
    #     except TaskCreditStatus.DoesNotExist:
    #         return HttpResponse(status=404)

    @staticmethod
    def update_addon_credit(request,user, actual_used_credits=None, credit_diff=None):
        add_ons = UserCredits.objects.filter(Q(user_id=user.id) & Q(credit_pack_type="Addon"))
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
    def update_usercredit(request,doc_id, actual_used_credits):
        doc = Document.objects.get(id = doc_id)
        user = doc.doc_credit_debit_user
        print("Credit User",user)
        present = datetime.now()
        try:
            user_credit = UserCredits.objects.get(Q(user_id=user.id) & Q(credit_pack_type__icontains="Subscription") & Q(ended_at=None))
            if present.strftime('%Y-%m-%d %H:%M:%S') <= user_credit.expiry.strftime('%Y-%m-%d %H:%M:%S'):
                if not actual_used_credits > user_credit.credits_left:
                    user_credit.credits_left -= actual_used_credits
                    user_credit.save()
                    return True
                else:
                    credit_diff = actual_used_credits - user_credit.credits_left
                    user_credit.credits_left = 0
                    user_credit.save()
                    from_addon = UpdateTaskCreditStatus.update_addon_credit(request,user,credit_diff)
                    return from_addon
            else:
                raise Exception

        except Exception as e:
            from_addon = UpdateTaskCreditStatus.update_addon_credit(request, actual_used_credits)
            return from_addon

    @staticmethod
    def update_credits(request, doc_id, actual_used_credits):
        # task_cred_status = UpdateTaskCreditStatus.get_object(doc_id)
        credit_status = UpdateTaskCreditStatus.update_usercredit(request,doc_id, actual_used_credits)
        # print("CREDIT STATUS----->", credit_status)
        if credit_status:
            msg = "Successfully debited MT credits"
            status = 200
        else:
            msg = "Insufficient credits to apply MT"
            status = 424
        # serializer = TaskCreditStatusSerializer(task_cred_status,
        #              data={"actual_used_credits" : actual_used_credits }, partial=True)
        # if serializer.is_valid(raise_exception=True):
        #     serializer.save()
        #     return {"msg" : msg}, status
        return {"msg" : msg}, status

################Incomplete project list for Marketplace###########3
# class IncompleteProjectListView(viewsets.ViewSet) :
#     serializer_class = ProjectSetupSerializer
#
#     def get_queryset(self):
#         objects_id = [x.id for x in Project.objects.all() if x.progress != "completed" ]
#         return Project.objects.filter(Q(ai_user=self.request.user) & Q(id__in=objects_id))
#
#     def list(self,request):
#         queryset = self.get_queryset()
#         print(queryset)
#         # pagin_tc = self.paginate_queryset(queryset, request , view=self)
#         serializer = ProjectSetupSerializer(queryset, many=True, context={'request': request})
#         # response = self.get_paginated_response(serializer.data)
#         return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_credit_status(request):
    return Response({"credits_left" : request.user.credit_balance,
                            "total_available" : request.user.buyed_credits}, status=200)



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
    source_language = [str(jobs_list[0].source_language_id)]
    target_languages = [str(i.target_language_id) for i in jobs_list]
    files = [DJFile(i.files,name=i.filename) for i in files_list]
    filename,extension = os.path.splitext((files_list[0].filename))
    serializer = ProjectQuickSetupSerializer(data={'project_name':[filename +'-tmp'+ str(temp_proj.id)],\
    'source_language':source_language,'target_languages':target_languages,'files':files},\
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

        for task in project.get_tasks:
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
        for task in project.get_tasks:
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
        project_tasks = Project.objects.get(id=project_id).get_tasks
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
                         "fprm_file_path": None
                         }
                doc = requests.post(url=f"http://{spring_host}:8080/getDocument/", data={
                    "doc_req_params":json.dumps(params_data),
                    "doc_req_res_params": json.dumps(res_paths)
                })
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
                task_details = TaskDetails.objects.filter(task__in = tasks).first()
                task_details.pk = None
                task_details.task_id = task.id
                task_details.save()
                # task_words.append({task.id : task_details.task_word_count})

        [task_words.append({task.id : task.task_details.first().task_word_count})for task in project.get_tasks]
        out = TaskDetails.objects.filter(project_id=project_id).aggregate(Sum('task_word_count'),Sum('task_char_count'),Sum('task_seg_count'))
        return {"proj_word_count": out.get('task_word_count__sum'), "proj_char_count":out.get('task_char_count__sum'), \
                        "proj_seg_count":out.get('task_seg_count__sum'),
                        "task_words":task_words}

    # def get(self, request, project_id):

    #     if bool(Project.objects.get(id=project_id).is_proj_analysed):
    #         return ProjectAnalysis.get_analysed_data(project_id)
    #     else:
    #         return ProjectAnalysis.analyse_project(project_id)

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

class TaskAssignInfoCreateView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self,request):
        tasks = request.GET.getlist('tasks')
        print(tasks)
        try:
            task_assign_info = TaskAssignInfo.objects.filter(task_id__in = tasks)
        except TaskAssignInfo.DoesNotExist:
            return HttpResponse(status=404)
        ser = TaskAssignInfoSerializer(task_assign_info,many=True)
        return Response(ser.data)


    @integrity_error
    def create(self,request):
        file=request.FILES.get('instruction_file')
        sender = self.request.user
        receiver = request.POST.get('assign_to')
        Receiver = AiUser.objects.get(id = receiver)
        serializer = TaskAssignInfoSerializer(data={**request.POST.dict(),'instruction_file':file,'task':request.POST.getlist('task')},context={'request':request})
        if serializer.is_valid():
            serializer.save()
            notify.send(sender, recipient=Receiver, verb='Task Assign', description='You are assigned to new task')
            return Response({"msg":"Task Assigned and Notification Sent"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request,pk=None):
        task = request.POST.getlist('task')
        file = request.FILES.get('instruction_file')
        if not task:
            return Response({'msg':'Task Id required'},status=status.HTTP_400_BAD_REQUEST)
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
        internal_team = proj.ai_user.team.internal_member_team_info.filter(role = 2)
        for i in internal_team:
            try:profile = i.internal_member.professional_identity_info.avatar_url
            except:profile = None
            internalmembers.append({'name':i.internal_member.fullname,'id':i.internal_member_id,\
                                    'status':i.get_status_display(),'avatar': profile})
    except:
        print("No team")
    external_team = proj.ai_user.team.owner.user_info.filter(role=2) if proj.ai_user.team else proj.ai_user.user_info.filter(role=2)
    hirededitors = find_vendor(external_team,jobs)
    return JsonResponse({'internal_members':internalmembers,'Hired_Editors':hirededitors})

def find_vendor(team,jobs):
    externalmembers=[]
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
    serializer_class = ProjectListSerializer

    def get_queryset(self):
        print(self.request.user)
        queryset = Project.objects.filter(Q(project_jobs_set__job_tasks_set__assign_to = self.request.user)\
                    |Q(ai_user = self.request.user)|Q(team__owner = self.request.user)\
                    |Q(team__internal_member_team_info__in = self.request.user.internal_member.filter(role=1))).distinct()
        return queryset

    def list(self,request):
        queryset = self.get_queryset()
        serializer = ProjectListSerializer(queryset, many=True, context={'request': request})
        return  Response(serializer.data)



@permission_classes([IsAuthenticated])
@api_view(['GET',])
def tasks_list(request):
    job_id = request.GET.get("job")
    try:
        job = Job.objects.get(id = job_id)
        tasks = job.job_tasks_set.all()
        ser = VendorDashBoardSerializer(tasks,many=True)
        return Response(ser.data)
    except:
        return JsonResponse({"msg":"No job exists"})


    # for i in tasks:
    #     task_list.append({'id':i.id,'task':i.job,'file':i.file})
    # return Response(task_list)
