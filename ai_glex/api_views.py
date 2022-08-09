from rest_framework import viewsets, status
import json
import mimetypes
import os
import xml.etree.ElementTree as ET
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from .models import Glossary, GlossaryFiles, TermsModel,GlossarySelected, MyGlossary
from .serializers import GlossarySerializer,GlossaryFileSerializer,TermsSerializer,\
                        GlossaryListSerializer,GlossarySelectedSerializer,\
                        MyGlossarySerializer
import json,mimetypes,os
from rest_framework.views import APIView
from ai_workspace.serializers import Job
from ai_workspace.models import TaskAssign, Task
from ai_workspace.excel_utils import WriteToExcel_lite,WriteToExcel
from django.http import JsonResponse,HttpResponse
import xml.etree.ElementTree as ET
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from ai_workspace.models import Task
from ai_workspace.api_views import UpdateTaskCreditStatus
from django.db.models import Q
from .serializers import TermsSerializer
from rest_framework.decorators import api_view,permission_classes
from nltk import word_tokenize
from ai_workspace.models import Task,Project,TaskAssign
from ai_workspace_okapi.models import Document
from ai_workspace_okapi.utils import get_translation
# from ai_workspace.serializers import ProjectListSerializer

# Create your views here.
############ GLOSSARY GET & CREATE VIEW #######################
# class GlossaryListCreateView(viewsets.ViewSet, PageNumberPagination):
#     filter_backends = (filters.SearchFilter,DjangoFilterBackend,)
#     search_fields = ('glossary_Name')
#     ordering_fields = ['modified_date']
#     ordering = ['-modified_date']
#     permission_classes = [IsAuthenticated]
#     page_size = settings.REST_FRAMEWORK["PAGE_SIZE"]
#
#     def get_custom_page_size(self, request, view):
#         try:
#             self.page_size = self.request.query_params.get('limit', 10)
#         except (ValueError, TypeError):
#             pass
#         return super().get_page_size(request)
#
#     def paginate_queryset(self, queryset, request, view=None):
#         self.page_size = self.get_custom_page_size(request, view)
#         return super().paginate_queryset(queryset, request, view)
#
#     def get_queryset(self):
#         queryset = queryset_all = Glossary.glossaryobjects.filter(user=self.request.user.id).all().order_by('-modified_date')
#         search_word =  self.request.query_params.get('search_word',0)
#         status = 200
#         if search_word:
#             queryset = queryset.filter(
#                         Q(glossary_Name__contains=search_word) | Q(subject_field__contains=search_word)
#                     )
#         if not queryset:
#             queryset = queryset_all
#             status = 422
#         return queryset, status
#
#     def list(self, request):
#         queryset, status = self.get_queryset()
#         pagin_tc = self.paginate_queryset( queryset, request , view=self )
#         serializer = GlossarySerializer(pagin_tc, many=True, context={'request': request})
#         # return  self.get_paginated_response (serializer.data)
#         response =self.get_paginated_response(serializer.data)
#         return  Response(response.data, status=status)
#
#     def create(self, request):
#         file = request.FILES.getlist("uploadfile")
#         print(file)
#         serializer = GlossarySerializer(data={**request.POST.dict(),"files":file},context={"request": request})
#         if serializer.is_valid():
#             serializer.save()
#             return Response(data={"Message":"Glossary created"}, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     def update(self, request, pk):
#         try:
#             queryset = Glossary.objects.get(Q(id=pk) & Q(user=request.user))
#         except Glossary.DoesNotExist:
#             return Response(status=204)
#         serializer =GlossarySerializer(queryset,data={**request.POST.dict()},partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#     def delete(self,request,pk):
#         queryset = Glossary.objects.filter(user=request.user)
#         glossary = get_object_or_404(queryset, pk=pk)
#         glossary.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)
#

######### Glossary FILE UPLOAD  #####################################

class GlossaryFileView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self,request):
        job = request.GET.get('job')
        queryset = GlossaryFiles.objects.filter(job_id = job)
        serializer = GlossaryFileSerializer(queryset,many=True)
        return  Response(serializer.data)

    def create(self, request):
        proj_id = request.POST.get('project')
        job_id = request.POST.get('job',None)
        files = request.FILES.getlist("glossary_file")
        if job_id:
            job = json.loads(request.POST.get('job'))
            obj = Job.objects.get(id=job)
            data = [{"project": obj.project.id, "file": file, "job":job, "usage_type":8} for file in files]
        else:
            proj = Project.objects.get(id=proj_id)
            jobs = proj.get_jobs
            data = [{"project": proj.id, "file": file, "job":job.id, "usage_type":8, "source_only":True} for file in files for job in jobs]
        serializer = GlossaryFileSerializer(data=data,many=True)
        if serializer.is_valid():
            print(serializer.is_valid())
            serializer.save()
            return Response(serializer.data, status=201)
        else:
            return Response (serializer.errors,status=400)

    def delete(self,request,pk=None):
        file_delete_ids = request.GET.get('file_delete_ids')
        print("FDI------->",file_delete_ids)
        delete_list = file_delete_ids.split(',')
        job = request.GET.get('job',None)
        project =request.GET.get('project')
        if job:
            [GlossaryFiles.objects.filter(job=job,id=i).delete() for i in delete_list]
        else:
            proj = Project.objects.get(id=project)
            jobs = proj.get_jobs
            [GlossaryFiles.objects.filter(job=job,id=i).delete() for i in delete_list for job in jobs]
        return Response({"Msg":"Files Deleted"})

###############################Terms CRUD########################################

class TermUploadView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TermsSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    ordering_fields = ['created_date','id']
    search_fields = ['sl_term','tl_term']
    ordering = ('-id')

    def list(self, request):
        task = request.GET.get('task')
        job = Task.objects.get(id=task).job
        queryset = self.filter_queryset(TermsModel.objects.filter(job = job))
        serializer = TermsSerializer(queryset, many=True, context={'request': request})
        return  Response(serializer.data)

    def create(self, request):
        task = request.POST.get('task')
        job = Task.objects.get(id=task).job
        if not task:
            return Response({'msg':'Task id required'},status=status.HTTP_400_BAD_REQUEST)
        # job_obj = Job.objects.get(id=job)
        glossary = job.project.glossary_project.id
        serializer = TermsSerializer(data={**request.POST.dict(),"job":job.id,"glossary":glossary})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk):
        queryset = TermsModel.objects.get(id=pk)
        serializer =TermsSerializer(queryset,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        term = TermsModel.objects.get(id=self.kwargs.get("pk"))
        term.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


########################GlossaryTemplateDownload###################################
@api_view(['GET',])
@permission_classes([IsAuthenticated])
def glossary_template_lite(request):
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Glossary_template_lite.xlsx'
    xlsx_data = WriteToExcel_lite()
    response.write(xlsx_data)
    return response


@api_view(['GET',])
@permission_classes([IsAuthenticated])
def glossary_template(request):
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Glossary_template.xlsx'
    xlsx_data = WriteToExcel()
    response.write(xlsx_data)
    return response

######################################TBXWrite####################################

@api_view(['GET',])
def tbx_write(request,task_id):
    try:
        job = Task.objects.get(id = task_id).job
        sl_code = job.source_language_code
        tl_code = job.target_language_code if (job.target_language != job.source_language) and (job.target_language != None) else None
        objs = TermsModel.objects.filter(job = job)
        if not objs:
            return JsonResponse({'msg':'There are no terms in glossary'})
        root = ET.Element("tbx",type='TBX-Core',style='dca',**{"{http://www.w3.org/XML/1998/namespace}lang": sl_code},xmlns="urn:iso:std:iso:30042:ed-2",
                                nsmap={"xml":"http://www.w3.org/XML/1998/namespace"})
        tbxHeader = ET.Element("tbxHeader")
        root.append (tbxHeader)
        Filedesc=ET.SubElement(tbxHeader,"fileDesc")
        TitleStmt=ET.SubElement(Filedesc,"titleStmt")
        Title=ET.SubElement(TitleStmt,"title")
        Title.text=job.project.project_name
        SourceDesc=ET.SubElement(Filedesc,"sourceDesc")
        Info=ET.SubElement(SourceDesc,"p")
        Info.text="TBX created from " + job.term_job.last().file.filename if job.term_job.last().file else "TBX created from " +  job.project.project_name
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
            if tl_code:
                langSec1 = ET.SubElement(conceptEntry,"langSec",**{"{http://www.w3.org/XML/1998/namespace}lang": tl_code})
                termSec1 = ET.SubElement(langSec1,"termSec")
                Term1 = ET.SubElement(termSec1,"term")
                Term1.text = obj.tl_term.strip() if obj.tl_term else obj.tl_term
        if tl_code:
            out_fileName = job.project.project_name+"(" + sl_code + "-" + tl_code + ")"+ ".tbx"
        else:out_fileName= job.project.project_name+"(" + sl_code + ")" +".tbx"
        ET.ElementTree(root).write(out_fileName, encoding="utf-8",xml_declaration=True)
        #print("TBX FILE----------------->",out_fileName)
        fl_path=os.getcwd()+"/"+out_fileName
        filename = out_fileName
        fl = open(fl_path, 'rb')
        mime_type, _ = mimetypes.guess_type(fl_path)
        response = HttpResponse(fl, content_type=mime_type)
        response['Content-Disposition'] = "attachment; filename=%s" % filename
        os.remove(os.getcwd()+"/"+out_fileName)
        return response

    except Exception as e:
        print("Exception1-->", e)
        return Response(data={"Message":"Something wrong in TBX conversion"})



@api_view(['GET',])
@permission_classes([IsAuthenticated])
def glossaries_list(request,project_id):
    project = Project.objects.get(id=project_id)
    target_languages = project.get_target_languages
    queryset = Project.objects.filter(glossary_project__isnull=False)\
                .filter(project_jobs_set__target_language__language__in = target_languages)\
                .filter(glossary_project__term__isnull=False)\
                .exclude(id=project.id).distinct()

    serializer = GlossaryListSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)


class GlossarySelectedCreateView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self,request):
        project = request.GET.get('project')
        if not project:
            return Response({"msg":"project_id required"})
        glossary_selected = GlossarySelected.objects.filter(project_id=project).all()
        serializer = GlossarySelectedSerializer(glossary_selected, many=True)
        return Response(serializer.data)

    def create(self, request):
        glossaries = request.POST.getlist('glossary')
        project = request.POST.get('project')
        data = [{"project":project, "glossary": glossary} for glossary in glossaries]
        serializer = GlossarySelectedSerializer(data=data,many=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(data={"Message":"successfully added"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self,request,pk):
        pass

    def delete(self,request,pk):
        obj = GlossarySelected.objects.get(id = pk)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST',])
@permission_classes([IsAuthenticated])
def glossary_search(request):
    user_input = request.POST.get("user_input")
    doc_id = request.POST.get("doc_id")
    doc = Document.objects.get(id=doc_id)
    glossary_selected = GlossarySelected.objects.filter(project = doc.job.project).values('glossary_id')
    target_language = doc.job.target_language
    source_language = doc.job.source_language
    queryset1 = MyGlossary.objects.filter(Q(tl_language__language=target_language)& Q(user=request.user)& Q(sl_language__language=source_language))\
                .extra(where={"%s ilike ('%%' || sl_term  || '%%')"},
                      params=[user_input]).distinct().values('sl_term','tl_term')
    queryset = TermsModel.objects.filter(glossary__in=glossary_selected)\
                .filter(job__target_language__language=target_language)\
                .extra(where={"%s ilike ('%%' || sl_term  || '%%')"},
                      params=[user_input]).distinct().values('sl_term','tl_term')
    queryset_final = queryset1.union(queryset)
    if queryset_final:
        res=[]
        for data in queryset_final:
           out = [{'source':data.get('sl_term'),'target':data.get('tl_term')}]
           res.extend(out)
    else:
        res=None
    return JsonResponse({'res':res},safe=False)

class GetTranslation(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def word_count(self, string):
        punctuations = '''!"#$%&'()*+,./:;<=>?@[\]^`{|}~'''
        tokens = word_tokenize(string)
        tokens_new = [word for word in tokens if word not in punctuations]
        return len(tokens_new)

    def post(self, request, task_id):

        # input data
        task_obj = Task.objects.get(id=task_id)
        source = request.POST.get("source", "")
        sl_code = task_obj.job.source_language_code
        if task_obj.job.target_language:
            tl_code = task_obj.job.target_language_code
        else:
            return Response({'msg':'Monolingual dictionary'})
        mt_engine_id = task_obj.task_info.get(step__name="PostEditing").mt_engine_id

        # Finding the debit user
        project = task_obj.job.project
        user = project.team.owner if project.team else project.ai_user

        credit_balance = user.credit_balance.get("total_left")
        print("SOURCE---------->",source)
        word_count = GetTranslation.word_count(self,source)

        if credit_balance > word_count:

            # get translation
            translation = get_translation(mt_engine_id, source, sl_code, tl_code)
            debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, word_count)
            return Response({"res": translation}, status=200)

        else:
            return Response({"res": "Insufficient credits"}, status=424)


@api_view(['POST',])
@permission_classes([IsAuthenticated])
def adding_term_to_glossary_from_workspace(request):
    sl_term = request.POST.get('source')
    tl_term = request.POST.get('target',"")
    doc_id = request.POST.get("doc_id")
    doc = Document.objects.get(id=doc_id)
    glossary_id = request.POST.get('glossary',None)
    if glossary_id:
        glossary = Glossary.objects.get(id = glossary_id)
        job = glossary.project.project_jobs_set.filter(target_language = doc.job.target_language).first()
        serializer = TermsSerializer(data={"sl_term":sl_term,"tl_term":tl_term,"job":job.id,"glossary":glossary.id})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        data = {"sl_term":sl_term,"tl_term":tl_term,"sl_language":doc.job.source_language.id,\
                "tl_language":doc.job.target_language.id,"project":doc.project,"user":request.user.id}
        serializer = MyGlossarySerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET',])
@permission_classes([IsAuthenticated])
def clone_source_terms(request):
    current_job = request.GET.get('job_id')
    existing_job = request.GET.getlist('copy_from_job_id')
    queryset = TermsModel.objects.filter(job_id__in = existing_job)
    with transaction.atomic():
        for i in queryset:
            i.pk = None
            i.job_id = current_job
            i.tl_term = None
            i.tl_source = None
            i.tl_definition = None
            #i.save()
        TermsModel.objects.bulk_create(queryset)
    return JsonResponse({'msg':'SourceTerms Cloned'})
