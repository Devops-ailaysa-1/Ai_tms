from rest_framework import viewsets, status
from rest_framework.pagination import PageNumberPagination
import json
import mimetypes
import os, urllib
from itertools import groupby
import xml.etree.ElementTree as ET
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from .models import Glossary, GlossaryFiles, TermsModel,GlossarySelected, MyGlossary, GlossaryMt
from .serializers import GlossarySerializer,GlossaryFileSerializer,TermsSerializer,\
                        GlossaryListSerializer,GlossarySelectedSerializer,\
                        MyGlossarySerializer,WholeGlossaryTermSerializer,GlossaryMtSerializer
import json,mimetypes,os
from rest_framework import filters,generics
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
import pandas as pd
from ai_staff.models import LanguageMetaDetails
from django.db.models import Value, IntegerField, CharField
from django_oso.auth import authorize
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
#from ai_auth.tasks import update_words_from_template_task
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
        for i in files:
            df = pd.read_excel(i)
            if 'Source language term' not in df.head():
                return Response({'msg':'file(s) not contained supported data'},status=400)
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
            # file_ids = [i.get('id') for i in serializer.data]
            # update_words_from_template_task.apply_async((file_ids,))
            return Response(serializer.data, status=201)
        else:
            return Response (serializer.errors,status=400)

    def delete(self,request,pk=None):
        file_delete_ids = request.GET.get('file_delete_ids')
        #print("FDI------->",file_delete_ids)
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
    ordering_fields = ['created_date','id','sl_term','tl_term']
    search_fields = ['sl_term','tl_term']
    ordering = ('-id')
    paginator = PageNumberPagination()
    paginator.page_size = 20


    def edit_allowed_check(self,job):
        from ai_workspace.models import Task,TaskAssignInfo
        user = self.request.user
        task_obj = Task.objects.get(job_id = job.id)
        task_assigned_info = TaskAssignInfo.objects.filter(task_assign__task = task_obj)
        assigners = [i.task_assign.assign_to for i in task_assigned_info]
        if user not in assigners:
            edit_allowed = True
        else:
            try:
                task_assign_status = task_assigned_info.filter(~Q(task_assign__assign_to = user)).first().task_assign.status
                edit_allowed = False if task_assign_status == 2 else True
            except:
                edit_allowed = True
        return edit_allowed

    def update_task_assign(self,job,user):
        from ai_workspace.models import Task,TaskAssignInfo
        task_obj = Task.objects.get(job_id = job.id)
        try:
            obj = TaskAssignInfo.objects.filter(task_assign__task = task_obj).filter(task_assign__assign_to = user).first().task_assign
            if obj.status != 2:
                obj.status = 2
                obj.save()
        except Exception as e:
            print("Exception1-->", e)

    def list(self, request):
        task = request.GET.get('task')
        job = Task.objects.get(id=task).job
        project_name = job.project.project_name
        queryset = self.filter_queryset(TermsModel.objects.filter(job = job)).select_related('job')
        source_language = str(job.source_language)
        try:target_language = LanguageMetaDetails.objects.get(language_id=job.target_language.id).lang_name_in_script
        except:target_language = None
        additional_info = [{'project_name':project_name,'source_language':source_language,'target_language':target_language}]
        pagin_tc = self.paginator.paginate_queryset(queryset, request , view=self)
        serializer = TermsSerializer(pagin_tc, many=True, context={'request': request})
        response = self.get_paginated_response(serializer.data)
        response.data['additional_info'] = additional_info
        return response
        # serializer = TermsSerializer(queryset, many=True, context={'request': request})
        #additional_info.extend(serializer.data)
        #return  Response(additional_info)

    def create(self, request):
        user = self.request.user
        task = request.POST.get('task')
        job = Task.objects.get(id=task).job
        if not task:
            return Response({'msg':'Task id required'},status=status.HTTP_400_BAD_REQUEST)
        glossary = job.project.glossary_project.id
        edit_allow = self.edit_allowed_check(job)
        if edit_allow == False:
            return Response({"msg":"Already someone is working"},status = 400)
        serializer = TermsSerializer(data={**request.POST.dict(),"job":job.id,"glossary":glossary})
        if serializer.is_valid():
            serializer.save()
            self.update_task_assign(job,user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk):
        user = self.request.user
        queryset = TermsModel.objects.get(id=pk)
        edit_allow = self.edit_allowed_check(queryset.job)
        if edit_allow == False:
            return Response({"msg":"Already someone is working"},status = 400)
        serializer =TermsSerializer(queryset,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            self.update_task_assign(queryset.job,user)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        term_delete_ids =request.GET.get('term_delete_ids')
        print("TDI------->",term_delete_ids)
        delete_list = term_delete_ids.split(',')
        TermsModel.objects.filter(id__in=delete_list).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


########################GlossaryTemplateDownload###################################
@api_view(['GET',])
#@permission_classes([IsAuthenticated])
def glossary_template_lite(request):
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Glossary_template_lite.xlsx'
    xlsx_data = WriteToExcel_lite()
    response.write(xlsx_data)
    response['Access-Control-Expose-Headers'] = 'Content-Disposition'
    return response


@api_view(['GET',])
#@permission_classes([IsAuthenticated])
def glossary_template(request):
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Glossary_template.xlsx'
    xlsx_data = WriteToExcel()
    response.write(xlsx_data)
    response['Access-Control-Expose-Headers'] = 'Content-Disposition'
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
            return Response({'msg':'There are no terms in glossary'},status=400)
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
        encoded_filename = urllib.parse.quote(filename, encoding='utf-8')
        response['Content-Disposition'] = 'attachment;filename*=UTF-8\'\'{}' \
            .format(encoded_filename)
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
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
    user = request.user.team.owner if request.user.team else request.user
    queryset = Project.objects.filter(ai_user=user).filter(glossary_project__isnull=False)\
                .filter(project_jobs_set__source_language_id = project.project_jobs_set.first().source_language.id)\
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

    def delete(self,request):
        glossary_selected_delete_ids = request.query_params.get('to_remove_ids')
        ids = glossary_selected_delete_ids.split(',')
        GlossarySelected.objects.filter(id__in = ids).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST',])
@permission_classes([IsAuthenticated])
def glossary_search(request):
    user_input = request.POST.get("user_input")
    doc_id = request.POST.get("doc_id")
    doc = Document.objects.get(id=doc_id)
    authorize(request, resource=doc, actor=request.user, action="read")
    user = request.user.team.owner if request.user.team else request.user
    glossary_selected = GlossarySelected.objects.filter(project = doc.job.project).values('glossary_id')
    target_language = doc.job.target_language
    source_language = doc.job.source_language
    queryset1 = MyGlossary.objects.filter(Q(tl_language__language=target_language)& Q(user=user)& Q(sl_language__language=source_language))\
                .extra(where={"%s ilike ('%%' || sl_term  || '%%')"},
                      params=[user_input]).distinct().values('sl_term','tl_term').annotate(glossary__project__project_name=Value("MyGlossary", CharField()))
    queryset = TermsModel.objects.filter(glossary__in=glossary_selected)\
                .filter(job__target_language__language=target_language)\
                .extra(where={"%s ilike ('%%' || sl_term  || '%%')"},
                      params=[user_input]).distinct().values('sl_term','tl_term','glossary__project__project_name')
    queryset_final = queryset1.union(queryset)
    if queryset_final:
        res=[]
        for data in queryset_final:
           out = [{'source':data.get('sl_term'),'target':data.get('tl_term'),'name':data.get('glossary__project__project_name')}]
           res.extend(out)
    else:
        res=None
    res_1 = [{"glossary": key, "data": [g  for g in group]} for key, group in groupby(res, lambda x: x['name'])] if res else None
    return JsonResponse({'res':res_1},safe=False)

class GetTranslation(APIView):#############Mt update need to work###################
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
        mt_engine_id = task_obj.task_info.get(step_id = 1).mt_engine_id
        target_mt = GlossaryMt.objects.filter(Q(task_id = task_id) & Q(source = source) & Q(mt_engine_id = mt_engine_id)).first()
        if target_mt:
            return Response(GlossaryMtSerializer(target_mt).data,status=200)

        # Finding the debit user
        project = task_obj.job.project
        user = project.team.owner if project.team else project.ai_user

        credit_balance = user.credit_balance.get("total_left")
        #print("SOURCE---------->",source)
        word_count = GetTranslation.word_count(self,source)

        if credit_balance > word_count:

            # get translation
            translation = get_translation(mt_engine_id, source, sl_code, tl_code,user_id=user.id,cc=word_count)
            #debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, word_count)
            tt = GlossaryMt.objects.create(task_id = task_id,source = source,target_mt = translation,mt_engine_id=mt_engine_id)
            return Response(GlossaryMtSerializer(tt).data,status=201)
            #return Response({"res": translation}, status=200)

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
def clone_source_terms_from_multiple_to_single_task(request):
    current_task = request.GET.get('task_id')
    existing_task = request.GET.getlist('copy_from_task_id')
    current_job = Task.objects.get(id=current_task).job
    #current_job_id = Task.objects.get(id=current_task).job_id
    existing_job = [i.job_id for i in Task.objects.filter(id__in=existing_task)]
    print("Existing Job---->",existing_job)
    queryset = TermsModel.objects.filter(job_id__in = existing_job)
    with transaction.atomic():
        for i in queryset:
            i.pk = None
            i.job_id = current_job.id
            i.tl_term = None
            i.tl_source = None
            i.tl_definition = None
            i.file_id = None
            i.glossary_id = current_job.project.glossary_project.id
            #i.save()
        TermsModel.objects.bulk_create(queryset)
    return JsonResponse({'msg':'SourceTerms Cloned'})

@api_view(['GET',])
@permission_classes([IsAuthenticated])
def clone_source_terms_from_single_to_multiple_task(request):
    existing_task = request.GET.get('copy_from_task_id')
    to_task = request.GET.getlist('copy_to_ids')
    existing_job = Task.objects.get(id=existing_task).job_id
    to_job_ids = [i.job_id for i in Task.objects.filter(id__in=to_task)]
    queryset = TermsModel.objects.filter(job_id = existing_job)
    obj =[
            TermsModel(pk = None,
            job_id = j,
            sl_term = i.sl_term,
            sl_source = i.sl_source,
            sl_definition = i.sl_definition,
            pos = i.pos,
            context = i.context,
            note = i.note,
            gender=i.gender,
            termtype=i.termtype,
            geographical_usage=i.geographical_usage,
            term_location=i.term_location,
            glossary_id=Job.objects.get(id=j).project.glossary_project.id,#glossary_id,file_id clone need to revise
            )for j in to_job_ids for i in queryset ]
    print(obj)
    TermsModel.objects.bulk_create(obj)
    return JsonResponse({'msg':'SourceTerms Cloned'})


#########################Not used, Need to test#################################
class NoPagination(PageNumberPagination):
      page_size = None


class WholeGlossaryTermSearchView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WholeGlossaryTermSerializer
    filter_backends = [DjangoFilterBackend ,filters.SearchFilter,filters.OrderingFilter]
    ordering_fields = ['sl_term','tl_term','id']
    ordering = ('-id')
    search_fields = ['sl_term','tl_term']
    pagination_class = NoPagination
    # page_size = None

    def get_queryset(self):
        user = self.request.user.team.owner if self.request.user.team else self.request.user
        queryset = Project.objects.filter(ai_user=user).filter(glossary_project__isnull=False)\
                    .filter(glossary_project__term__isnull=False).distinct()
        glossary_ids = [glossary_id] if glossary_id else [i.glossary_project.id for i in queryset]
        query = TermsModel.objects.filter(glossary_id__in=glossary_ids)
        return query


@api_view(['GET',])
@permission_classes([IsAuthenticated])
def whole_glossary_term_search(request):
    search_term = request.GET.get('term')
    glossary_id = request.GET.get('glossary_id',None)
    if not search_term:
        return Response({'msg':'term required'},status=400)
    search_in = request.GET.get('search_in',None)
    user = request.user.team.owner if request.user.team else request.user
    queryset = Project.objects.filter(ai_user=user).filter(glossary_project__isnull=False)\
                .filter(glossary_project__term__isnull=False).distinct()
    glossary_ids = [glossary_id] if glossary_id else [i.glossary_project.id for i in queryset]
    query = TermsModel.objects.filter(glossary_id__in=glossary_ids)
    if search_in == 'source':
        res =  query.filter(Q(sl_term__icontains=search_term)).distinct('tl_term')
    elif search_in == 'target':
        res = query.filter(Q(tl_term__icontains=search_term)).distinct('tl_term')
    else:
        res = query.filter(Q(sl_term__icontains=search_term)|Q(tl_term__icontains=search_term)).distinct('tl_term')
    #ser = TermsSerializer(res,many=True)
    out = [{'term_id':i.id,'sl_term':i.sl_term,'tl_term':i.tl_term,'pos':i.pos,'glossary_name':i.glossary.project.project_name,'job':i.job.source_target_pair_names,'task_id':Task.objects.get(job_id=i.job_id).id} for i in res]
    return JsonResponse({'results':out})#'data':ser.data})


class GlossaryListView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self,request):
        user = request.user.team.owner if request.user.team else request.user
        queryset = Project.objects.filter(ai_user=user).filter(glossary_project__isnull=False)\
                    .filter(glossary_project__term__isnull=False).distinct().order_by('-id')
        serializer = GlossaryListSerializer(queryset, many=True)
        return Response(serializer.data)



import io
import xlsxwriter
import pandas as pd
from ai_glex.models import TermsModel
@api_view(['GET',])
def glossary_task_simple_download(request):
    gloss_id = request.GET.get('gloss_id')
    task_id  = request.GET.get('task')
    task_obj = Task.objects.get(id=task_id)
    term_model = TermsModel.objects.filter(glossary=gloss_id).filter(job_id = task_obj.job.id).values("sl_term","tl_term")
    if term_model:
        df = pd.DataFrame.from_records(term_model)
        df.columns=['source_term','target_term']
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        writer.save()
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=Glossary_simple.xlsx'
        output.seek(0)
        response.write(output.read())
        return response
    else:
        return Response({'msg':'No terms'},status=400)