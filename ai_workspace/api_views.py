from ai_workspace_okapi.models import Document
from django.conf import settings
from django.core.files import File as DJFile
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from ai_auth.authentication import IsCustomer
from ai_workspace.excel_utils import WriteToExcel_lite
from ai_auth.models import AiUser
from rest_framework import viewsets
from rest_framework.response import Response
from .serializers import (ProjectContentTypeSerializer, ProjectCreationSerializer, ProjectSerializer, JobSerializer,FileSerializer,FileSerializer,FileSerializer,
                            ProjectSetupSerializer, ProjectSubjectSerializer, TempProjectSetupSerializer, TaskSerializer,
                          FileSerializerv2, FileSerializerv3, TmxFileSerializer, PentmWriteSerializer, TbxUploadSerializer,TbxTemplateUploadSerializer)

from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Project, Job, File, ProjectContentType, ProjectSubjectField, TempProject, TmxFile,TbxTemplateUploadFiles,TermsModel
from rest_framework import permissions
from django.shortcuts import get_object_or_404, get_list_or_404
from django.db import IntegrityError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Task,Tbxfiles
from lxml import etree as ET
from ai_marketplace.models import AvailableVendors
from django.http import JsonResponse,HttpResponse
import requests, json, os,mimetypes
from ai_workspace import serializers
from ai_workspace_okapi.models import Document
from ai_staff.models import LanguagesLocale, Languages
from rest_framework.decorators import api_view
from django.http import JsonResponse
from tablib import Dataset
import shutil

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
    parser_classes = [MultiPartParser, JSONParser]
    permission_classes = []

    def get_queryset(self):
        return Project.objects.filter(ai_user=self.request.user)

   #@integrity_error
    def create(self, request):
        # print("metaaa>>",request.META)
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

# class TaskView(viewsets.ModelViewSet):
#     permission_classes = [IsAuthenticated]
#     serializer_class = TaskSerializer
#
#     def get_queryset(self):
#         task_queryset = Task.objects.all()
#         tasks = get_list_or_404(task_queryset, file__project__ai_user_id=self.request.user.id)
#         return  tasks
#
#     def list(self, request):
#         tasks = self.get_queryset()
#         tasks_serlzr = TaskSerializer(tasks, many=True)
#         return Response(tasks_serlzr.data, status=200)
#
#     def create(self, request, project_id):
#         task_serlzr = TaskSerializer(data=request.data)
#         print("initial data---->", task_serlzr.initial_data)
#         if task_serlzr.is_valid(raise_exception=True):
#             task_serlzr.save()
#             return Response({"msg": task_serlzr.data}, status=200)
#
#         else:
#             return Response({"msg": task_serlzr.errors}, status=400)


# class TaskView(APIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = TaskSerializer
#
#     def get_queryset(self,):
#         tasks = [ task for project in get_list_or_404(Project.objects.all(), ai_user=self.request.user)
#                     for task in project.get_tasks
#                   ]
#         return  tasks
#
#     def get(self, request):
#         tasks = self.get_queryset()
#         print(tasks)
#         tasks_serlzr = TaskSerializer(tasks, many=True)
#         return Response(tasks_serlzr.data, status=200)
#
#     @staticmethod
#     def get_object(data):
#         obj = Task.objects.filter(**data).first()
#         return obj
#
#     def post(self, request):
#         obj = self.get_object({**request.POST.dict(), "assign_to": self.request.user.id})
#         if obj:
#             task_ser = TaskSerializer(obj)
#             return Response(task_ser.data, status=200)
#
#         task_serlzr = TaskSerializer(data=request.POST.dict(), context={# Self assign
#             "assign_to": self.request.user.id})
#         if task_serlzr.is_valid(raise_exception=True):
#             task_serlzr.save()
#             return Response({"msg": task_serlzr.data}, status=200)
#
#         else:
#             return Response({"msg": task_serlzr.errors}, status=400)

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
      src_id=Job.objects.get(id=job_id).source_language_id
      src_name=Languages.objects.get(id=src_id).language
      tar_id=Job.objects.get(id=job_id).target_language_id
      tar_name=Languages.objects.get(id=tar_id).language
      src_lang_code=LanguagesLocale.objects.get(language_locale_name=src_name).locale_code
      tar_lang_code=LanguagesLocale.objects.get(language_locale_name=tar_name).locale_code
      return JsonResponse({"source_lang":src_name,"target_lang":tar_name,"src_code":src_lang_code,"tar_code":tar_lang_code})



@api_view(['GET',])
def glossary_template_lite(request):
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Glossary_Lite.xlsx'
    xlsx_data = WriteToExcel_lite()
    response.write(xlsx_data)
    return response


class TbxTemplateUploadView(APIView):
    def post(self, request,id):
        project_id =id
        tbx_template_file=request.FILES.get('tbx_template_file')
        job_id=request.POST.get('job_id',0)
        print(job_id)
        serializer = TbxTemplateUploadSerializer(data={'tbx_template_file':tbx_template_file,'project':project_id,'job':job_id})
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            saved_data=serializer.data
            file_id = saved_data.get("id")
            upload_template_data_to_db(file_id,job_id)
            tbx_file= user_tbx_write(job_id,project_id)
            fl = open(tbx_file, 'rb')
            file_obj1 = DJFile(fl)#,name=os.path.basename(tbx_file))
            serializer2 = TbxUploadSerializer(data={'tbx_files':file_obj1,'project':project_id,'job':job_id})
            if serializer2.is_valid():
                serializer2.save()
            else:
                print(serializer2.errors)
            fl.close()
            os.remove(os.path.abspath(tbx_file))
            return Response({'msg':"Template File uploaded and TBX created and uploaded","data":serializer.data})#,"tbx_file":tbx_file})
        else:
            return Response(serializer.errors)


def upload_template_data_to_db(file_id,job_id):
    uploadfile =TbxTemplateUploadFiles.objects.get(id=file_id).tbx_template_file
    dataset = Dataset()
    imported_data = dataset.load(uploadfile.read(), format='xlsx')
    for data in imported_data:
        value = TermsModel(
                # data[0],          #Blank column
                data[1],            #Autoincremented in the model
                sl_term = data[2].strip(),    #SL term column
                tl_term = data[3].strip()    #TL term column
        )
        value.job_id = job_id
        value.file_id = file_id
        value.save()

# def tbx_file_upload_path(project):
#     file_path = os.path.join(project.ai_user.uid,project.ai_project_id,"tbx")
#     return file_path
################Tbx write####################

def user_tbx_write(job_id,project_id):
    try:
        project = Project.objects.get(id = project_id)
        sl_lang=Job.objects.select_related('locale').filter(id=job_id).values('source_language__locale__locale_code')
        ta_lang=Job.objects.select_related('locale').filter(id=job_id).values('target_language__locale__locale_code')
        sl_code = sl_lang[0].get('source_language__locale__locale_code')
        tl_code = ta_lang[0].get('target_language__locale__locale_code')
        objs = TermsModel.objects.filter(job_id = job_id)
        # objs = UserTerms.objects.filter(user_id=id)
        root = ET.Element("tbx",type='TBX-Core',style='dca',**{"{http://www.w3.org/XML/1998/namespace}lang": sl_code},xmlns="urn:iso:std:iso:30042:ed-2",
                                nsmap={"xml":"http://www.w3.org/XML/1998/namespace"})
        tbxHeader = ET.Element("tbxHeader")
        root.append (tbxHeader)
        Filedesc=ET.SubElement(tbxHeader,"fileDesc")
        TitleStmt=ET.SubElement(Filedesc,"titleStmt")
        Title=ET.SubElement(TitleStmt,"title")
        Title.text=Project.objects.get(id=project_id).project_name
        SourceDesc=ET.SubElement(Filedesc,"sourceDesc")
        Info=ET.SubElement(SourceDesc,"p")
        Info.text="TBX created from " + Project.objects.get(id=project_id).project_name
        EncodingDesc=ET.SubElement(tbxHeader,"encodingDesc")
        EncodingInfo=ET.SubElement(EncodingDesc,"p",type="XCSURI")
        EncodingInfo.text="TBXXCSV02.xcs"
        Text= ET.Element("text")
        root.append(Text)
        Body=ET.SubElement(Text,"body")
        for i,obj in enumerate(objs):
            i=i+1
            conceptEntry    = ET.SubElement(Body,"conceptEntry",id="c"+str(i))
            langSec         = ET.SubElement(conceptEntry,"langSec",**{"{http://www.w3.org/XML/1998/namespace}lang": sl_code})
            Termsec         = ET.SubElement(langSec,"termSec")
            Term = ET.SubElement(Termsec,"term")
            Term.text = obj.sl_term.strip()
            langSec1 = ET.SubElement(conceptEntry,"langSec",**{"{http://www.w3.org/XML/1998/namespace}lang": tl_code})
            termSec1 = ET.SubElement(langSec1,"termSec")
            Term1 = ET.SubElement(termSec1,"term")
            Term1.text = obj.tl_term.strip()
        out_file=Project.objects.get(id=project_id).project_name+"j"+str(Job.objects.filter(project=1).count()+ 1)
        out_fileName=out_file+"_out.tbx"
        ET.ElementTree(root).write(out_fileName, encoding="utf-8",xml_declaration=True, pretty_print=True)
        return out_fileName

    except Exception as e:
        print("Exception1-->", e)
        return Response(data={"Message":"TBX file Not ready"})


@api_view(['GET',])
def tbx_write(request,file_id):
    out_fileName = Tbxfiles.objects.get(id=file_id).tbx_files
    print(out_fileName.path)
    fl_path = out_fileName.path
    print(fl_path)
    filename=os.path.basename(fl_path)
    print(os.path.dirname(fl_path))
    fl = open(fl_path, 'rb')
    mime_type, _ = mimetypes.guess_type(fl_path)
    response = HttpResponse(fl, content_type=mime_type)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response

@api_view(['GET',])
def get_tbx_files(request,project_id):
    queryset = Tbxfiles.objects.filter(project_id=project_id)
    serializer = TbxUploadSerializer(queryset,many=True)
    return Response(serializer.data)

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
            "assign_to": self.request.POST.get('assign_to'),"customer":self.request.user.id})
        if task_serlzr.is_valid(raise_exception=True):
            task_serlzr.save()
            return Response({"msg": task_serlzr.data}, status=200)

        else:
            return Response({"msg": task_serlzr.errors}, status=400)
