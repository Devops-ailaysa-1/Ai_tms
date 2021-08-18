from ai_workspace_okapi.models import Document
from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from ai_auth.authentication import IsCustomer
from ai_auth.models import AiUser
from rest_framework import viewsets
from rest_framework.response import Response
from .serializers import (ProjectContentTypeSerializer, ProjectCreationSerializer, \
    ProjectSerializer, JobSerializer,FileSerializer,FileSerializer,FileSerializer,\
    ProjectSetupSerializer, ProjectSubjectSerializer, TempProjectSetupSerializer, \
    TaskSerializer, FileSerializerv2, FileSerializerv3, TmxFileSerializer,\
    PentmWriteSerializer, TbxUploadSerializer, ProjectQuickSetupSerializer,\
    VendorDashBoardSerializer)
                        
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Project, Job, File, ProjectContentType, ProjectSubjectField, TempProject, TmxFile
from rest_framework import permissions
from django.shortcuts import get_object_or_404, get_list_or_404
from django.db import IntegrityError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Task
from django.http import JsonResponse
import requests, json, os
from ai_workspace import serializers
from ai_workspace_okapi.models import Document
from ai_staff.models import LanguagesLocale, Languages
from rest_framework.decorators import api_view
from django.http import JsonResponse

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

    def get_queryset(self):
        return Job.objects.filter(project__ai_user=self.request.user)

    def create(self, request):
        serializer = self.serializer_class(data = request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)


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
    def get_queryset(self):
        return File.objects.filter(project__ai_user=self.request.user)

    def create(self, request):
        print(request.data)
        serializer = FileSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=201)

def integrity_error(func):
    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IntegrityError as e:
            print("error---->", e)
            return Response({'message': "integrirty error"}, 409)
        
    return decorator

class ProjectSetupView(viewsets.ViewSet):
    serializer_class = ProjectSetupSerializer
    parser_classes = [MultiPartParser, JSONParser]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(ai_user=self.request.user)

    @integrity_error
    def create(self, request):
        # print("metaaa>>",request.META)
        serializer = ProjectSetupSerializer(data={**request.POST.dict(),
            "files":request.FILES.getlist('files')},context={"request":request})
        if serializer.is_valid(raise_exception=True):
            #try:
            serializer.save()
            return Response(serializer.data, status=201)

        else:
            return Response(serializer.errors, status=409)

    def list(self,request):
        queryset = self.get_queryset()
        # pagin_tc = self.paginate_queryset( queryset, request , view=self )
        serializer = ProjectSetupSerializer(queryset, many=True, context={'request': request})
        # response =self.get_paginated_response(serializer.data)
        return  Response(serializer.data)

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

class AnonymousProjectSetupView(viewsets.ViewSet):
    serializer_class = TempProjectSetupSerializer
    parser_classes = [MultiPartParser, JSONParser]
    permission_classes = [AllowAny,]

    def get_queryset(self):
        return TempProject.objects.filter(ai_user=self.request.user)

    @integrity_error
    def create(self, request):
        # print("metaaa>>",request.META)
        serializer = TempProjectSetupSerializer(data={**request.POST.dict(),
            "tempfiles":request.FILES.getlist('tempfiles')})
        if serializer.is_valid(raise_exception=True):
            #try:
            serializer.save()
            #except IntegrityError:
              #  return Response(serializer.data, status=409)

            return Response(serializer.data, status=201)

        else:
            return Response(serializer.errors, status=409)


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
        tasks_serlzr = TaskSerializer(tasks, many=True)
        return Response(tasks_serlzr.data, status=200)

    @staticmethod
    def get_object(data):
        obj = Task.objects.filter(**data).first()
        return obj

    def post(self, request):
        obj = self.get_object({**request.POST.dict(), "assign_to": self.request.user.id})
        if obj:
            task_ser = TaskSerializer(obj)
            return Response(task_ser.data, status=200)

        task_serlzr = TaskSerializer(data=request.POST.dict(), context={# Self assign
            "assign_to": self.request.user.id})
        if task_serlzr.is_valid(raise_exception=True):
            task_serlzr.save()
            return Response({"msg": task_serlzr.data}, status=200)

        else:
            return Response({"msg": task_serlzr.errors}, status=400)

class Files_Jobs_List(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, project_id):
        project = get_object_or_404(Project.objects.all(), id=project_id,
                        ai_user=self.request.user)
        jobs = project.project_jobs_set.all()
        files = project.project_files_set.filter(usage_type__use_type="source").all()
        return jobs, files

    def get(self, request, project_id):
        jobs, files = self.get_queryset(project_id)
        jobs = JobSerializer(jobs, many=True)
        files = FileSerializer(files, many=True)
        return Response({"files":files.data, "jobs": jobs.data}, status=200)

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
            return JsonResponse({"msg": "Something went to wrong in tmx to pentm processing"}, status=res.status_code)

    def create(self, request):
        data = {**request.POST.dict(), "tmx_files": request.FILES.getlist("tmx_files")}
        ser_data = TmxFileSerializer.prepare_data(data)
        ser = TmxFileSerializer(data=ser_data, many=True)
        if ser.is_valid(raise_exception=True):
            ser.save()
            return self.TmxToPenseiveWrite(ser.data)




class TbxUploadView(APIView):
    def post(self, request):
        tbx_file = request.FILES.get('tbx_file')
        project_id = request.POST.get('project_id', 0)
        doc_id = request.POST.get('doc_id', 0)
        if doc_id != 0:
            job_id = Document.objects.get(id=doc_id).job_id
            project_id = Job.objects.get(id=job_id).project_id
        serializer = TbxUploadSerializer(data={'tbx_files':tbx_file,'project':project_id})
        # print("SER VALIDITY-->", serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)


# class AssignTaskView(viewsets.ModelViewSet):
#     permission_classes = [IsAuthenticated]
#     serializer_class =

    # def

#  /////////////////  References  \\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# from django.contrib.auth.models import Permission, User
# from django.contrib.contenttypes.models import ContentType
# content_type = ContentType.objects.get_for_model( UserAttribute
# permission = Permission.objects.get( content_type = content_type , codename='user-attribute-exist')


# class ProjectSetupView2(APIView):

#     parser_classes = [MultiPartParser, FormParser, JSONParser]


#     def post(self, request, format=None):
#         print("request DATa >>",request.data)
#         # print(request.data.get('logo'))
#         # print("files",request.FILES.get('logo'))
#         print(request.POST.dict())
#         serializer = ProjectSetupSerializer(data=request.data, context={'request':request})
#         if serializer.is_valid():
#             try:
#                 serializer.save()
#             except IntegrityError:
#                 return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET',])
def getLanguageName(request,id):
      job_id=Document.objects.get(id=id).job_id
      print("JOB ID--->", job_id)
      src_id=Job.objects.get(id=job_id).source_language_id
      src_name=Languages.objects.get(id=src_id).language
      tar_id=Job.objects.get(id=job_id).target_language_id
      tar_name=Languages.objects.get(id=tar_id).language
      src_lang_code=LanguagesLocale.objects.get(language_locale_name=src_name)\
          .locale_code
      tar_lang_code=LanguagesLocale.objects.get(language_locale_name=tar_name)\
          .locale_code
      return JsonResponse({"source_lang":src_name,"target_lang":tar_name,\
            "src_code":src_lang_code,"tar_code":tar_lang_code})

class QuickProjectSetupView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    def create(self, request):
        print("data---->", request.data, request.POST.dict(), request.FILES) 
        serlzr = ProjectQuickSetupSerializer(data=\
            {**request.data, "files": request.FILES.getlist("files")},
            context={"request": request})
        if serlzr.is_valid(raise_exception=True):
            serlzr.save()
            return Response(serlzr.data, status=201)

class VendorDashBoardView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    paginator = PageNumberPagination()
    paginator.page_size = 20

    def get_object(self):
        tasks = Task.objects.order_by("-id").all()
        tasks = get_list_or_404(tasks, file__project__ai_user=self.request.user)
        return tasks

    def list(self, request, *args, **kwargs):
        tasks = self.get_object()
        pagin_queryset = self.paginator.paginate_queryset(tasks, request, view=self)
        serlzr = VendorDashBoardSerializer(pagin_queryset, many=True)
        return self.get_paginated_response(serlzr.data)



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
        # pagin_queryset = self.paginator.paginate_queryset(tasks, request, view=self)
        serlzr = VendorDashBoardSerializer(tasks, many=True)
        return Response(serlzr.data, status=200)
