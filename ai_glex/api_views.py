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
from rest_framework import filters,generics
from rest_framework.views import APIView
from ai_workspace.serializers import Job
from ai_workspace.models import TaskAssign, Task
from ai_workspace.excel_utils import WriteToExcel_lite,WriteToExcel,WriteToExcel_wordchoice
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
from ai_workspace.models import Task,Project,TaskAssign,File
from ai_workspace_okapi.models import Document 
from ai_workspace_okapi.utils import get_translation
import pandas as pd
from ai_staff.models import LanguageMetaDetails
from django.db.models import Value, IntegerField, CharField
from django_oso.auth import authorize
from ai_workspace.signals import invalidate_cache_on_save
from django.shortcuts import get_object_or_404
from celery.decorators import task
import requests


def job_lang_pair_check(gloss_job_list, src, tar):
    for gloss_pair in gloss_job_list:
        if gloss_pair.source_language_id == src and gloss_pair.target_language_id == tar:
            print(gloss_pair)
            return gloss_pair
    return None

######### Glossary FILE UPLOAD  #####################################

class GlossaryFileView(viewsets.ViewSet):
    '''
    This viewset is to add, delete template files. 
    when the file is added, signal is connected with GlossaryFiles model to save terms from template to TermsModel.
    when the file is deleted, signal is connected with GlossaryFiles model to delete all the terms from TermsModel related to that file.
    '''
    permission_classes = [IsAuthenticated]

    def list(self,request):
        job = request.GET.get('job')
        queryset=GlossaryFiles.objects.filter(job_id=job)
        serializer=GlossaryFileSerializer(queryset,many=True)
        return  Response(serializer.data)

    def create(self, request):

        proj_id = request.POST.get('project')
        job_id = request.POST.get('job',None)
        files = request.FILES.getlist("glossary_file")
        glossary_id = request.POST.get('glossary_id',None)
        task_id  = request.POST.get('task_id',None)
        for i in files:
            df = pd.read_excel(i)
            if 'Source language term' not in df.head():
                return Response({'msg':'file(s) not contained supported data'},status=400)
    
        if job_id: ## from gloss page with gloss project 
            job = json.loads(request.POST.get('job'))
            obj = Job.objects.get(id=job)
            data = [{"project": obj.project.id, "file": file, "job":job, "usage_type":8} for file in files]

        if task_id: ### from transeditor with translation project which is project's task id 
            task_inst = Task.objects.get(id=task_id)
            job_inst = task_inst.job #### project's job
            gloss_project = job_inst.project.individual_gloss_project
            gloss_job_list = gloss_project.project.project_jobs_set.all()  
            gloss_job = job_lang_pair_check(gloss_job_list,job_inst.source_language.id ,job_inst.target_language.id )

            data = [{"project": gloss_project.project.id , "file": file, "job":gloss_job.id, "usage_type":8} for file in files]

        else:
            proj = Project.objects.get(id=proj_id)
            jobs = proj.get_jobs
            data = [{"project": proj.id,"file":file,"job":job.id,"usage_type":8,"source_only":True} for file in files for job in jobs]
        
        serializer = GlossaryFileSerializer(data=data,many=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        else:
            return Response (serializer.errors,status=400)

    def delete(self,request,pk=None):
        file_delete_ids = request.GET.get('file_delete_ids')
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


from rest_framework.decorators import action

@api_view(['GET',])
def check_gloss_task_id_for_project_task_id(request):
    trans_project_id = request.GET.get('trans_project_id',None) ### Need translation project id
    task = request.GET.get('task',None) 
    trans_project_ins = Project.objects.get(id=trans_project_id)
    job_ins = Task.objects.get(id=task).job
    source_language = job_ins.source_language
    target_language = job_ins.target_language

    gloss_job_list = trans_project_ins.individual_gloss_project.project.project_jobs_set.all()
    gloss_job_ins = job_lang_pair_check(gloss_job_list,source_language.id,target_language.id)
    
    if not gloss_job_ins:
        
        return Response({"msg":"not gloss job"},status = 400)
    else:
        gloss_task_id = gloss_job_ins.job_tasks_set.last().id
        
        return Response({'gloss_project_id':gloss_job_ins.project_id , 
                         'gloss_id': trans_project_ins.individual_gloss_project.id,
                         'gloss_task_id':gloss_task_id, 'gloss_job_id':gloss_job_ins.id})


class TermUploadView(viewsets.ModelViewSet):
    '''
    This view is to add, list, update and delete the terms in glossary.
    '''
    permission_classes = [IsAuthenticated]
    serializer_class = TermsSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    ordering_fields = ['created_date','id','sl_term','tl_term']
    search_fields = ['sl_term','tl_term']
    ordering = ('-id')
    paginator = PageNumberPagination()
    paginator.page_size = 20


    def edit_allowed(self,obj):
        #Not using now
        request_obj = self.request
        from ai_workspace_okapi.api_views import DocumentViewByDocumentId
        doc_view_instance = DocumentViewByDocumentId(request_obj)
        edit_allowed = doc_view_instance.edit_allow_check(task_obj=obj.job_tasks_set.first(),given_step=1) #default_step = 1 need to change in future
        return edit_allowed


    def edit_allowed_check(self,job):
        #Not using now. not working correctly.
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
        task = request.GET.get('task',None)
        
        if task:
            job = Task.objects.get(id=task).job
            project_name = job.project.project_name
            queryset = self.filter_queryset(TermsModel.objects.filter(job = job)).select_related('job')
            source_language = str(job.source_language)
            try:
                target_language = LanguageMetaDetails.objects.get(language_id=job.target_language.id).lang_name_in_script
            except:
                target_language = None
        
            edit_allow = self.edit_allowed(job)
        else:
            return Response({'msg':'No task'})
        
        
        additional_info = [{'project_name':project_name,'source_language':str(source_language),
                                'target_language':str(target_language),'edit_allowed':edit_allow}]
        
        pagin_tc = self.paginator.paginate_queryset(queryset, request , view=self)
 
        serializer = TermsSerializer(pagin_tc, many=True, context={'request': request})
        response = self.get_paginated_response(serializer.data)
        response.data['additional_info'] = additional_info
        return response


    def create(self, request):
        user = self.request.user
        task = request.POST.get('task')
        if not task:
            return Response({'msg':'Task id required'},status=status.HTTP_400_BAD_REQUEST)
        job = Task.objects.get(id=task).job
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
    

    # @action(detail=False, methods=['POST'])
    # def bulk_upload(self, request):
    #     # Check if the file is provided
    #     files = request.FILES.getlist("glossary_file")
    #     task_id = request.POST.get('task',None)
    #     job_id =  request.POST.get('job',None)
        
    #     # Read the Excel file into a DataFrame
    #     for i in files:
    #         df = pd.read_excel(i)
    #         if 'Source language term' not in df.head():
    #             return Response({'msg':'file(s) not contained supported data'},status=400)
        
    def destroy(self, request, *args, **kwargs):
        term_delete_ids =request.GET.get('term_delete_ids')
        delete_list = term_delete_ids.split(',')
        TermsModel.objects.filter(id__in=delete_list).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


########################GlossaryTemplateDownload###################################
@api_view(['GET',])
#@permission_classes([IsAuthenticated])
def glossary_template_lite(request):
    '''
    This function is to download glossary simple template
    '''
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Glossary_template_lite.xlsx'
    xlsx_data = WriteToExcel_lite()
    response.write(xlsx_data)
    response['Access-Control-Expose-Headers'] = 'Content-Disposition'
    return response

########################WordChoiceTemplateDownload###################################
@api_view(['GET',])
#@permission_classes([IsAuthenticated])
def word_choice_template(request):
    '''
    This function is to download Word choices template
    '''
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=glossary_template.xlsx'
    xlsx_data = WriteToExcel_wordchoice()
    response.write(xlsx_data)
    response['Access-Control-Expose-Headers'] = 'Content-Disposition'
    return response



@api_view(['GET',])
#@permission_classes([IsAuthenticated])
def glossary_template(request):
    '''
    This function is to download glossary full template
    '''
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Glossary_template.xlsx'
    xlsx_data = WriteToExcel()
    response.write(xlsx_data)
    response['Access-Control-Expose-Headers'] = 'Content-Disposition'
    return response

######################################TBXWrite####################################

@api_view(['GET',])
def tbx_write(request,task_id):
    '''
    This function is to write tbx file for the given task_id with the help of ET(Element Tree) library
    and downloads tbx file.
    '''
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



# @api_view(['GET',])
# @permission_classes([IsAuthenticated])
# def glossaries_list(request,project_id):
#     '''
#     This function is to list the glossaries(exclude the empty one) which matches the given project's source and target
#     languages and returns GlossaryListSerializer data.
#     '''
#     project = Project.objects.get(id=project_id)
#     target_languages = project.get_target_languages
#     user = request.user.team.owner if request.user.team else request.user
#     queryset = Project.objects.filter(ai_user=user).filter(glossary_project__isnull=False)\
#                 .filter(project_jobs_set__source_language_id = project.project_jobs_set.first().source_language.id)\
#                 .filter(project_jobs_set__target_language__language__in = target_languages)\
#                 .filter(glossary_project__term__isnull=False)\
#                 .exclude(id=project.id).distinct().order_by('-id')
#     serializer = GlossaryListSerializer(queryset, many=True, context={'request': request})
#     return Response(serializer.data)
def has_glossary_project(project):
    try:
        return project.individual_gloss_project is not None
    except:
        return None

@api_view(['GET',])
@permission_classes([IsAuthenticated])
def glossaries_list(request,project_id):   ###### this function is for wordchoise option list select
    project = Project.objects.get(id=project_id)
    option = request.GET.get('option')
    #print("option-->",option)
    #print("project--->",project)
    user = request.user.team.owner if request.user.team else request.user
    #print("user--->",user)
    if option == 'glossary':
        queryset = Project.objects.filter(ai_user=user).filter(project_type=3)
    else:
        queryset = Project.objects.filter(ai_user=user).filter(project_type=10)
    #print("queryset",queryset)
    target_languages = project.get_target_languages
    queryset = queryset.filter(ai_user=user).filter(glossary_project__isnull=False)\
                .filter(project_jobs_set__source_language_id = project.project_jobs_set.first().source_language.id)\
                .filter(project_jobs_set__target_language__language__in = target_languages)\
                .filter(glossary_project__term__isnull=False)\
                .exclude(id=project.id).distinct().order_by('-id')   #### project's task's job gloss list
    
    #print("queryset",queryset)
    #print("queryset",len(queryset))

    serializer = GlossaryListSerializer(queryset, many=True, context={'request': request })
    data = serializer.data


 
    return Response(data)

class GlossarySelectedCreateView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    '''
    This view is to add and list glossaries selected for the particular project by the users.
    delete is to unselect the glossary for that project.
    '''

    def list(self,request):
        project = request.GET.get('project')
        option = request.GET.get('option',None)
        if not project:
            return Response({"msg":"project_id required"})
        
        if option == 'glossary':
            glossary_selected = GlossarySelected.objects.filter(glossary__project__project_type_id=3).filter(project_id=project).all()
        else:
            glossary_selected = GlossarySelected.objects.filter(glossary__project__project_type_id=10).filter(project_id=project).all()

        # glossary_selected = GlossarySelected.objects.filter(project_id=project).all()
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

    '''
    This function is to search user_input(segment source) against MYGlossary and TermsModel 
    and returns the match if any.
    '''

    user_input = request.POST.get("user_input")
    doc_id = request.POST.get("doc_id")
    task_id = request.POST.get("task_id")
    if doc_id:
        doc = Document.objects.get(id=doc_id)
        target_language = doc.job.target_language
        source_language = doc.job.source_language
        pr = doc.job.project
        authorize(request, resource=doc, actor=request.user, action="read")
    if task_id:
        task = Task.objects.get(id=task_id)
        target_language = task.job.target_language
        source_language = task.job.source_language
        pr = task.job.project
        authorize(request, resource=task, actor=request.user, action="read")
    user = request.user.team.owner if request.user.team else request.user
    glossary_selected = GlossarySelected.objects.filter(project = pr,glossary__project__project_type__id=3).values('glossary_id') ### only for gloss list
    
    queryset1 = MyGlossary.objects.filter(Q(tl_language__language=target_language)& Q(user=user)& Q(sl_language__language=source_language))\
                .extra(where={"%s ilike ('%%' || sl_term  || '%%')"},
                      params=[user_input]).distinct().values('sl_term','tl_term').annotate(glossary__project__project_name=Value("MyGlossary", CharField()))
    
    queryset = TermsModel.objects.filter(glossary__in=glossary_selected)\
                .filter(job__target_language__language=target_language)\
                .extra(where={"%s ilike ('%%' || sl_term  || '%%')"},
                      params=[user_input]).distinct().values('sl_term','tl_term','glossary__project__project_name')
    
    queryset_final = queryset1.union(queryset)
    #queryset_final = queryset
    if queryset_final:
        res=[]
        for data in queryset_final:
           out = [{'source':data.get('sl_term'),'target':data.get('tl_term'),'name':data.get('glossary__project__project_name')}]
           res.extend(out)
    else:
        res=None
    res_1 = [{"glossary": key, "data": [g  for g in group]} for key, group in groupby(res, lambda x: x['name'])] if res else None
    return JsonResponse({'res':res_1},safe=False)    ### commad for word choice for mygloss list

class GetTranslation(APIView):#############Mt update need to work###################
    permission_classes = [IsAuthenticated]
    
    '''
    This view is to get_mt for source term inside glossary workspace for MT Button. 
    This is similar to get_term_mt, try to merge it.
    '''

    @staticmethod
    def word_count(string):
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

        
        project = task_obj.job.project
        user = project.team.owner if project.team else project.ai_user

        credit_balance = user.credit_balance.get("total_left")
        
        word_count = GetTranslation.word_count(source)

        if credit_balance > word_count:

            # get translation
            translation = get_translation(mt_engine_id, source, sl_code, tl_code,user_id=user.id,cc=word_count)
            tt = GlossaryMt.objects.create(task_id = task_id,source = source,target_mt = translation,mt_engine_id=mt_engine_id)
            return Response(GlossaryMtSerializer(tt).data,status=201)
        else:
            return Response({"res": "Insufficient credits"}, status=424)

################ Not using now ###########################################
@api_view(['POST',])
@permission_classes([IsAuthenticated])
def adding_term_to_glossary_from_workspace(request):
    '''
    This function is to add terms from workspace to glossary if glossary id is given, else it will save it in default glossary.
    Now it is changed to MyGlossaryView Post method.


    Note for word choice:
    
    need to check project_id and gloss id id while adding terms in termmodel 
    for wordchoise if not created for this case please create , ignore if already selected 
    
    '''

    sl_term = request.POST.get('source')
    tl_term = request.POST.get('target',"")
    doc_id = request.POST.get("doc_id")
    doc = Document.objects.get(id=doc_id)
    glossary_id = request.POST.get('glossary',None)
    project_id = doc.project
    if glossary_id:
        glossary = Glossary.objects.get(id = glossary_id)
        job = glossary.project.project_jobs_set.filter(target_language = doc.job.target_language).first()
        serializer = TermsSerializer(data={"sl_term":sl_term,"tl_term":tl_term,"job":job.id,"glossary":glossary.id})
        if serializer.is_valid():
            serializer.save()
            gloss_selected_check = GlossarySelected.objects.filter(project__id=project_id,glossary=glossary)
            if not gloss_selected_check:
                GlossarySelected.objects.create(project_id=project_id,glossary=glossary)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    
    else:
        from ai_glex.serializers import GlossarySetupSerializer
        from ai_workspace.api_views import AddStoriesView
        user = request.user
        din = AddStoriesView.check_user_dinamalar(user)

        if not din:
            user_1 = user.team.owner if user.team and user.team.owner.is_agency and (user in user.team.get_project_manager) else user
            project_ins_create = {'source_language':[doc.job.source_language.id],'target_languages':[doc.job.target_language.id]}
            serializer = GlossarySetupSerializer(data={**project_ins_create,"project_type":['10']},context={"request": request,'user_1':user_1})
            
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                data = serializer.data
                project_id = data.get('id')
                glossary_id = data.get('glossary_id')
                term_instance = TermsModel.objects.create(sl_term=sl_term,tl_term=tl_term,glossary_id=glossary_id,job=doc.job)
                GlossarySelected.objects.create(project_id=project_id,glossary_id=glossary_id)
                serializer = TermsSerializer(term_instance)
                return Response(serializer.data)

        else:
            print("din user")
            data = {"sl_term":sl_term,"tl_term":tl_term,"sl_language":doc.job.source_language.id,\
                    "tl_language":doc.job.target_language.id,"project":project_id,"user":user.id,\
                    "created_by":user.id}
    
            serializer = MyGlossarySerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# @api_view(['POST',])
# @permission_classes([IsAuthenticated])
# def adding_term_to_glossary_from_workspace(request):
#     sl_term = request.POST.get('source')
#     tl_term = request.POST.get('target',"")
#     doc_id = request.POST.get("doc_id")
#     doc = Document.objects.get(id=doc_id)
#     glossary_id = request.POST.get('glossary',None)
#     user = request.user.team.owner if request.user.team else request.user
#     if glossary_id:
#         glossary = Glossary.objects.get(id = glossary_id)
#         glss,created = GlossarySelected.objects.get_or_create(project=doc.job.project,glossary=glossary)
#         print("RRR------------->",glss, created)


#     glossary = Glossary.objects.get(id = glossary_id)
#     job = glossary.project.project_jobs_set.filter(target_language = doc.job.target_language).first()
#     serializer = TermsSerializer(data={"sl_term":sl_term,"tl_term":tl_term,"pos":pos,"job":job.id,"glossary":glossary.id,"created_by":request.user.id})
#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 

######################################## Not using now ########################################################
from ai_glex.models import Terminologyextract
from ai_nlp.utils import ner_terminology_finder
from ai_staff.models import Languages

@api_view(['POST',])
@permission_classes([IsAuthenticated])
def get_ner_terminology_extract(request):
    '''
    This function is to extract keywords and ner from uploaded file. it is now for only english language.
    '''
    proj_id = request.POST.get('proj_id',None)
    files = request.FILES.getlist('file',None)
    language_ids = request.POST.getlist('language_id',None)
    if not proj_id:
        return Response({'msg':'need proj_id and file'},status=400)
    proj = Project.objects.get(id=proj_id)

    if language_ids:
        for language_id in language_ids:
            lang_instance = Languages.objects.get(id=language_id)
            
            job_instance = proj.project_jobs_set.get(target_language=lang_instance)
            existing_job = proj.project_jobs_set.first()
            term_list = TermsModel.objects.filter(job=existing_job)
            objs = []
            for  term in term_list:
                objs.append(TermsModel(pk = None,sl_term=term.sl_term,job_id=job_instance.id,
                                       pos=term.pos,glossary_id=proj.glossary_project.id))
            print(objs,language_id)
            if objs:
                TermsModel.objects.bulk_create(objs)
                choice_instance = TermsModel.objects.filter(job=job_instance)
                ser = TermsSerializer(choice_instance,many=True)
        
    file_paths = []
    if files:
        for file in files:
            terminology_instance = Terminologyextract.objects.create(file=file,project = proj)
            file_paths.append(terminology_instance.file.path)
        print("FP----------->",file_paths)
        ner_terminology= ner_terminology_finder(file_paths)
        print("NER TERM--------------->",ner_terminology)
        if ner_terminology:
            obj =[
                TermsModel(pk = None,
                job_id = lang.id,
                sl_term = i['term'],
                pos = i['pos'],
                glossary_id=proj.glossary_project.id,
                )for i in ner_terminology['terminology'] for lang in proj.project_jobs_set.all()]
    
            TermsModel.objects.bulk_create(obj)    

            choice_instance = TermsModel.objects.filter(glossary__project=proj)
            
            ser = TermsSerializer(choice_instance,many=True)
            return Response(ser.data)
        else:
            return Response({'msg':'no terminology'})
    return Response({'msg':"updated"})
    
            
#################### Not using now ##########################################################################################
from ai_workspace.api_views import  get_consumable_credits_for_text
from ai_workspace_okapi.utils import get_translation
def get_terms_mt(task_id,terms):
    task = Task.objects.get(id=task_id)
    job = task.job
    user  = job.project.ai_user
    initial_credit = user.credit_balance.get("total_left")

    term_instance = TermsModel.objects.filter(job=job)
    tar_code = job.target_language_code
    for term in terms:
        if not term.tl_term:

            consumed_credit = get_consumable_credits_for_text(term.sl_term,
                                                                job.source_language_code,tar_code)

            if initial_credit < consumed_credit:
                return Response({'msg':'Insufficient credit'})

            term.tl_term = get_translation(1,term.sl_term,source_lang_code=job.source_language_code,
                                                                target_lang_code=tar_code,user_id=user.id) 
            term.save()

    print("Completed")

###########################################################################################################################
@api_view(['GET',])
@permission_classes([IsAuthenticated])
def clone_source_terms_from_multiple_to_single_task(request):
    '''
    This function is to clone the source terms from multiple tasks to single task.
    '''
    current_task = request.GET.get('task_id')
    existing_task = request.GET.getlist('copy_from_task_id')
    current_job = Task.objects.get(id=current_task).job
    existing_job = [i.job_id for i in Task.objects.filter(id__in=existing_task)]
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
        TermsModel.objects.bulk_create(queryset)
        invalidate_cache_on_save(sender=TermsModel, instance=queryset.last())
    return JsonResponse({'msg':'SourceTerms Cloned'})

@api_view(['GET',])
@permission_classes([IsAuthenticated])
def clone_source_terms_from_single_to_multiple_task(request):
    '''
    This function is to clone all the source terms from single task to multiple tasks.
    '''
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
            glossary_id=Job.objects.get(id=j).project.glossary_project.id
            )for j in to_job_ids for i in queryset ]
    
    TermsModel.objects.bulk_create(obj)
    invalidate_cache_on_save(sender=TermsModel, instance=queryset.last())
    return JsonResponse({'msg':'SourceTerms Cloned'})



class NoPagination(PageNumberPagination):
      page_size = None

########## Not using now ###############################################################
class WholeGlossaryTermSearchView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WholeGlossaryTermSerializer
    filter_backends = [DjangoFilterBackend ,filters.SearchFilter,filters.OrderingFilter]
    ordering_fields = ['sl_term','tl_term','id']
    ordering = ('-id')
    search_fields = ['sl_term','tl_term']
    pagination_class = NoPagination
   

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
    '''
    Not using now
    This function is to search term across all glossaries of user. 
    '''
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

    out = [{'term_id':i.id,'sl_term':i.sl_term,'tl_term':i.tl_term,'pos':i.pos,'glossary_name':i.glossary.project.project_name,'job':i.job.source_target_pair_names,'task_id':Task.objects.get(job_id=i.job_id).id} for i in res]
    return JsonResponse({'results':out})


class GlossaryListView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    '''
    This view is for to list glossaries based on user.
    '''

    def list(self,request):
        task = request.GET.get('task_id')
        user = request.user.team.owner if request.user.team else request.user
        queryset = Project.objects.filter(ai_user=user).filter(glossary_project__isnull=False)\
                    .filter(glossary_project__term__isnull=False).distinct().order_by('-id')
        if task:
            task_obj = Task.objects.get(id=task)
            queryset = queryset.filter(Q(project_jobs_set__source_language=task_obj.job.source_language) & Q(project_jobs_set__target_language=task_obj.job.target_language)).order_by('-id')
        serializer = GlossaryListSerializer(queryset, many=True)
        return Response(serializer.data)



import io
import xlsxwriter
import pandas as pd
from ai_glex.models import TermsModel
@api_view(['GET',])
def glossary_task_simple_download(request):
    '''
    This function is to download the simple excel file of glossary terms (sl_term, tl_term)
    '''
    gloss_id = request.GET.get('gloss_id')
    task_id  = request.GET.get('task')
    task_obj = Task.objects.get(id=task_id)
    # gloss_id = task_obj.job.project.glossary.id
    term_model = TermsModel.objects.filter(job_id = task_obj.job.id).values("sl_term","tl_term","pos")

    if term_model:
        df = pd.DataFrame.from_records(term_model)
        df.columns=['source_term','target_term','pos']
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        writer.save()
        response = HttpResponse(content_type='application/vnd.ms-excel')
        encoded_filename = 'word_choice.xlsx'
        response['Content-Disposition'] = 'attachment;filename*=UTF-8\'\'{}' \
        .format(encoded_filename)
        response['X-Suggested-Filename'] = encoded_filename
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        output.seek(0)
        response.write(output.read())
        return response
    else:
        return Response({'msg':'No terms'},status=400)



class MyGlossaryView(viewsets.ModelViewSet):
    '''
    This view is to list, add, update and delete the terms in default glossary for each user. currently it is used for dinamalar flow.
    '''
    permission_classes = [IsAuthenticated]
    serializer_class = MyGlossarySerializer
    filter_backends = [DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    ordering_fields = ['created_date','id','sl_term','tl_term']
    search_fields = ['sl_term','tl_term']
    ordering = ('sl_term')
    paginator = PageNumberPagination()
    paginator.page_size = 20


    def get_queryset(self):
        user = self.request.user.team.owner if self.request.user.team else self.request.user 
        query = MyGlossary.objects.filter(user=user).all()
        return query

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        pagin_tc = self.paginator.paginate_queryset(queryset, request , view=self)
        serializer = MyGlossarySerializer(pagin_tc, many=True)
        response = self.get_paginated_response(serializer.data)
        return  response


    def create(self, request):
        sl_term = request.POST.get('sl_term',None)
        tl_term = request.POST.get('tl_term',"")
        doc_id = request.POST.get("doc_id")
        glossary_id = request.POST.get('glossary',None)
        user = request.user.team.owner if request.user.team else request.user 
        doc = None
        if doc_id:
            doc = Document.objects.get(id=doc_id)
            target_lang = doc.job.target_language.id
            source_lang = doc.job.source_language.id
        else:
            #Default lang-pair for dinamalar
            target_lang = 77 
            source_lang = 17 
        if glossary_id:
            glossary = Glossary.objects.get(id = glossary_id)
            job = glossary.project.project_jobs_set.filter(target_language = doc.job.target_language).first()
            serializer = TermsSerializer(data={"sl_term":sl_term,"tl_term":tl_term,"job":job.id,"glossary":glossary.id})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            if not sl_term:
                return Response({'msg':'need source term and target term'})
            data = {"sl_term":sl_term,"tl_term":tl_term,"sl_language":source_lang,\
                    "tl_language":target_lang,"project":doc.project if doc else None,\
                    "user":user.id,"created_by":request.user.id}
            serializer = MyGlossarySerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self,request,pk):
        user = request.user.team.owner if request.user.team else request.user 
        instance = MyGlossary.objects.get(id=pk,user=user)
        data = request.POST.dict()
        serializer = MyGlossarySerializer(instance,data=data,partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self,request,pk):
        user = request.user.team.owner if request.user.team else request.user 
        obj = MyGlossary.objects.get(Q(user=user) & Q(id=pk))
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST',])
def get_word_mt(request):
    '''
    This function is to check for the mt of given word in that language. 
    if it exists, it will return the target_term else it will MT the source term and store 
    and then return GlossaryMtSerializer data
    '''
    user = request.user.team.owner if request.user.team else request.user
    task_id = request.POST.get("task_id",None)
    source = request.POST.get("source", "")
    target = request.POST.get("target", "")
    task_obj = get_object_or_404(Task.objects.all(),id=task_id)
    #mt_engine_id = task_obj.task_info.get(step_id = 1).mt_engine_id
    mt_engine_id = 1 ### by default the gloss to google_mt
    if source:
        sl_code = task_obj.job.source_language_code
        tl_code = task_obj.job.target_language_code
        text = source
        target_mt = GlossaryMt.objects.filter(Q(source = source) & Q(mt_engine_id = mt_engine_id) & Q(task__job__target_language = task_obj.job.target_language)).last()
        if target_mt:
            return Response(GlossaryMtSerializer(target_mt).data,status=200)
    elif target:
        sl_code = task_obj.job.target_language_code
        tl_code = task_obj.job.source_language_code
        text = target
        source_mt = GlossaryMt.objects.filter(Q(target_mt = target) & Q(mt_engine_id = mt_engine_id) & Q(task__job__target_language = task_obj.job.target_language)).last()
        if source_mt:
            return Response(GlossaryMtSerializer(source_mt).data,status=200)
    

    credit_balance = user.credit_balance.get("total_left")
    
    word_count = GetTranslation.word_count(source)

    if credit_balance > word_count:

        translation = get_translation(mt_engine_id, text, sl_code, tl_code,user_id=user.id,cc=word_count)
        source_new = translation if target else source
        target_new = translation if source else target
        tt = GlossaryMt.objects.create(source = source_new,task=None,target_mt = target_new,mt_engine_id=mt_engine_id)
        return Response(GlossaryMtSerializer(tt).data,status=201)

    else:
        return Response({"res": "Insufficient credits"}, status=400)


class WordChoiceListView(viewsets.ViewSet):
    '''
    This view is to list the wordchoices 
    '''
    permission_classes = [IsAuthenticated]

    def list(self,request):
        task = request.GET.get('task_id')
        user = request.user.team.owner if request.user.team else request.user
        queryset = Project.objects.filter(ai_user=user).filter(project_type = 10).filter(glossary_project__isnull=False).distinct().order_by('-id')
        if task:
            task_obj = Task.objects.get(id=task)
            queryset = queryset.filter(Q(project_jobs_set__source_language=task_obj.job.source_language) & Q(project_jobs_set__target_language=task_obj.job.target_language)).order_by('-id')
        serializer = GlossaryListSerializer(queryset, many=True)
        return Response(serializer.data)
    


@api_view(['GET',])
def download_gloss_dinamalar(request):
    from ai_workspace.api_views import AddStoriesView
    user = request.user.team.owner if request.user.team else request.user 
    # din = AddStoriesView.check_user_dinamalar(user)
 
    gloss_list = list(MyGlossary.objects.filter(user=user).values_list('sl_term','tl_term'))
    if gloss_list:
        gloss_data_frame = pd.DataFrame(gloss_list).dropna()
        gloss_data_frame.columns=['Source term','Target term']
        gloss_data_frame = gloss_data_frame.sort_values(by='Source term', key=lambda x: x.str.lower())
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        gloss_data_frame.to_excel(writer, index=False, sheet_name='Sheet1')
        writer.save()
        response = HttpResponse(content_type='application/vnd.ms-excel')
        encoded_filename = 'glossary_terms.xlsx'
        response['Content-Disposition'] = 'attachment;filename*=UTF-8\'\'{}' \
        .format(encoded_filename)
        response['X-Suggested-Filename'] = encoded_filename
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        output.seek(0)
        response.write(output.read())
        return response
    else:
        return Response({'msg':'no gloss term'},status=400)
    # else:
    #     return Response({'msg':'dont have permission to access'},status=401)




#extract term

def term_extraction_ner_and_terms(text):
    TERM_EXTRACTION_URL = settings.TERM_EXTRACTION
    payload = {'text': text}
    response = requests.request("POST", TERM_EXTRACTION_URL, headers={}, data=payload, files=[])
    return response.json()


def requesting_ner(joined_term_unit):
    if joined_term_unit:
        response_result = term_extraction_ner_and_terms(joined_term_unit)
        terms_from_request = []
        for i in response_result['named_entities']:
            if i['text']:
                terms_from_request.append(i['text'])   
        if response_result['terms']:
            terms_from_request.extend(response_result['terms'])

        return terms_from_request
    else:
        return None
 
import re
from ai_glex.serializers import CeleryStatusForTermExtractionSerializer
@task(queue='default')
def get_ner_with_textunit_merge(file_id,gloss_model_inst):
    try:    
        file_instance = File.objects.get(id=file_id)
        print("file_instance-->",file_instance)
        print("file_id-->",file_id)
        file_path = file_instance.get_source_file_path
        path_list = re.split("source/", file_path)

        doc_json_path = path_list[0] + "doc_json/" + path_list[1] + ".json"

        print("file_path--->",doc_json_path)
        with open(doc_json_path,'rb') as fp:
            file_json = json.load(fp)
        file_json = json.loads(file_json)
        terms = []
        text_unit = []
        for i in  file_json['text']:
            for j in file_json['text'][i]:
                if j['source']:
                    text_unit.append(j['source'])
            full_text_unit_merge = "".join(text_unit)
            terms.extend(requesting_ner(full_text_unit_merge))
            text_unit = []

        file_instance.status = "FINISHED"
        #file_instance.file_document_set.done_extraction = True
        file_instance.done_extraction = True
        file_instance.save()
        terms =  list(set(terms))
        gloss_job_inst = file_instance.gloss_job
        #gloss_model_inst = gloss_job_inst.project.glossary
        termsmodel_instances = [TermsModel(sl_term=term,job=gloss_job_inst,glossary=gloss_model_inst) for term in terms]
        TermsModel.objects.bulk_create(termsmodel_instances)
        print("terms_created")
        file_instance.save()

    except:
        file_instance.term_extraction_done = False
        file_instance.status = "ERROR"
        file_instance.done_extraction = False
        file_instance.save()
        print("terms_error")
 
from ai_workspace.models import File
@api_view(['POST',])
def extraction_text(request):
    file_ids = request.POST.getlist('file_id',None)
    gloss_task_id = request.POST.get('gloss_task_id',None)

    if not gloss_task_id:
        return Response({'msg':'Need gloss_task_id'})
    
    gloss_task_inst = Task.objects.get(id = gloss_task_id)
    gloss_job  = gloss_task_inst.job #### to save on job in gloss 
    glossary_project = gloss_task_inst.proj_obj.glossary_project
     
    if not file_ids:
        return Response({'msg': 'Need file ids'})

    celery_instance_ids = []
    for file_id in file_ids:
        file_instance = File.objects.get(id=file_id)
        file_instance.is_extract = True #### saving for listing the file which is used to extract the text
 
        
        #file_instance.gloss_model = glossary_project
        file_instance.gloss_job = gloss_job
        file_instance.save()  # Save term_model
        
        celery_instance_ids.append(file_instance.id)
        celery_id = get_ner_with_textunit_merge.apply_async(args=(file_id,glossary_project))
        file_instance.celery_id = celery_id
        file_instance.status = "PENDING"
        file_instance.save()  # Save celery status

    if celery_instance_ids:
        gloss_term_extraction_instances = File.objects.filter(id__in=celery_instance_ids)
        serializer = CeleryStatusForTermExtractionSerializer(gloss_term_extraction_instances, many=True)
        return Response(serializer.data, status=200)
    else:
        return Response({'msg': 'No files to extract the terms or already extracted'}, status=200)
    
@api_view(['GET'])
def term_extraction_celery_status(request):
    project_id = request.GET.get('project_id')
    if not project_id:
        return Response({'msg': 'Project ID not provided'}, status=400)

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response({'msg': 'Project not found'}, status=404)
    
    term_extract_status = []

    for file_ins in project.files_and_jobs_set[1]:
        if file_ins.is_extract:
            term_extract_status.append(file_ins)


    if term_extract_status:
        serializer = CeleryStatusForTermExtractionSerializer(term_extract_status, many=True)
        return Response(serializer.data, status=200)
    else:
        return Response({'msg': 'No files to extract the terms or already extracted'}, status=200)
    
@api_view(['GET',])
def get_pos(request):
    pass