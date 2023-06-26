from .serializers import (DocumentSerializer, DocumentSerializerV3,
                          TranslationStatusSerializer, CommentSerializer,
                          TM_FetchSerializer, VerbSerializer,SegmentPageSizeSerializer)
from ai_workspace.serializers import TaskCreditStatusSerializer, TaskTranscriptDetailSerializer
from rest_framework import views
import json, logging,os,re,urllib.parse,xlsxwriter
from json import JSONDecodeError
from django.urls import reverse
import requests
from ai_auth.tasks import google_long_text_file_process_cel,pre_translate_update,mt_raw_update
from django.contrib.auth import settings
from django.http import HttpResponse, JsonResponse
import json
import logging
import os
import re
import requests
import urllib.parse
import urllib.parse
import xlsxwriter
import rapidfuzz
from json import JSONDecodeError
from os.path import exists
from ai_tm.utils import tm_fetch_extract,tmx_read_with_target
from django.contrib.auth import settings
from itertools import chain
from ai_auth.tasks import google_long_text_file_process_cel,pre_translate_update,mt_only
from django.db.models import Q
from django.http import HttpResponse
from django.http import JsonResponse
from django_celery_results.models import TaskResult
from django.shortcuts import get_object_or_404
from nltk.tokenize import TweetTokenizer
from rest_framework import permissions
from rest_framework import status
from rest_framework import views
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.exceptions import APIException
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from spellchecker import SpellChecker
from django.http import  FileResponse
from rest_framework.views import APIView
from django.db.models import Q
import urllib.parse
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from wiktionaryparser import WiktionaryParser
from ai_auth.models import AiUser, UserCredits
from ai_auth.tasks import google_long_text_file_process_cel, pre_translate_update, mt_only
from ai_auth.tasks import write_segments_to_db
from ai_auth.utils import get_plan_name
from ai_staff.models import SpellcheckerLanguages
from ai_workspace.api_views import UpdateTaskCreditStatus
# from controller.models import DownloadController
from ai_workspace.models import File
from ai_workspace.models import Project
from ai_workspace.models import Task, TaskAssign
from ai_workspace.serializers import TaskSerializer, TaskAssignSerializer
from ai_workspace.serializers import TaskTranscriptDetailSerializer
from ai_workspace.utils import get_consumable_credits_for_text_to_speech
from ai_workspace_okapi.models import SplitSegment,SegmentPageSize
from .models import Document, Segment, MT_RawTranslation, TextUnit, TranslationStatus, FontSize, Comment, MergeSegment, \
    MtRawSplitSegment
from .okapi_configs import CURRENT_SUPPORT_FILE_EXTENSIONS_LIST
from .serializers import PentmUpdateSerializer, SegmentHistorySerializer
from .serializers import (SegmentSerializer, DocumentSerializerV2,
                          SegmentSerializerV2, MT_RawSerializer, DocumentSerializerV3,
                          TranslationStatusSerializer, FontSizeSerializer, CommentSerializer,
                          TM_FetchSerializer, MergeSegmentSerializer, SplitSegmentSerializer)
from django.urls import reverse
from json import JSONDecodeError
from .utils import SpacesService
from google.cloud import translate_v2 as translate
import os, io, requests, time
from django.http import HttpResponse
from rest_framework.response import Response
# from controller.models import DownloadController
from ai_workspace.models import File
from .utils import SpacesService,text_to_speech
from django.contrib.auth import settings
from ai_auth.utils import get_plan_name
from .utils import download_file, bl_title_format, bl_cell_format,get_res_path, get_translation, split_check
from django.db import transaction
from rest_framework.decorators import permission_classes
from ai_auth.tasks import write_segments_to_db
from django.db import transaction
from os.path import exists
from .serializers import (VerbSerializer)
from .utils import SpacesService, text_to_speech
from .utils import download_file, bl_title_format, bl_cell_format, get_res_path, get_translation, split_check
from django_oso.auth import authorize
from ai_auth.utils import filter_authorize
from django.db import transaction
from ai_tm.models import TmxFileNew
from ai_tm.api_views import TAG_RE, remove_tags as remove_tm_tags
#from translate.storage.tmx import tmxfile
from ai_tm import match


# logging.basicConfig(filename="server.log", filemode="a", level=logging.DEBUG, )
logger = logging.getLogger('django')

spring_host = os.environ.get("SPRING_HOST")

END_POINT= settings.END_POINT

class IsUserCompletedInitialSetup(permissions.BasePermission):

    def has_permission(self, request, view):
        # user = (get_object_or_404(AiUser, pk=request.user.id))
        if request.user.user_permissions.filter(codename="user-attribute-exist").first():
            return True

class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = 'Service temporarily unavailable, try again later.'


def get_empty_segments(doc):
    segments_1 = doc.segments_for_find_and_replace.filter(target__exact='')
    merge_segments_1 =MergeSegment.objects.filter(text_unit__document=doc).filter(Q(target__exact=None)|Q(target__exact=''))
    split_segments_1 = SplitSegment.objects.filter(text_unit__document=doc).filter(Q(target__exact=None)|Q(target__exact=''))
    if (segments_1 or merge_segments_1 or split_segments_1):
        return True
    else:
        return False


class DocumentViewByTask(views.APIView, PageNumberPagination):
    permission_classes = [IsAuthenticated]
    PAGE_SIZE = page_size =  20

    def get_object(self, task_id):
        tasks = Task.objects.all()
        return get_object_or_404(tasks, id=task_id)

    @staticmethod
    def exact_required_fields_for_okapi_get_document():
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
        [data.pop(i) for i in remove_keys]
        if check_fields != []:
            raise ValueError("OKAPI request fields not setted correctly!!!")

    @staticmethod
    def trim_segments(doc_data):

        #doc_data = json.loads(doc_json_data)
        text = doc_data["text"]
        count = 0
        needed_keys = []

        for key, value in text.items():
            needed_keys.append(key)
            count += len(value)
            if count >= 100:
                break

        for key in text.copy():
            if key not in needed_keys:
                text.pop(key)

        doc_data["text"] = text
        return doc_data, needed_keys

    @staticmethod
    def correct_segment_for_task(doc_json_path, needed_keys):

        doc_data_str = json.load(open(doc_json_path))
        doc_data = json.loads(doc_data_str)
        text = doc_data["text"]
        for key in text.copy():
            if key in needed_keys:
                text.pop(key)
        doc_data["text"] = text
        return doc_data

    @staticmethod
    def get_json_file_path(task):
        source_file_path = TaskSerializer(task).data["source_file_path"]
        path_list = re.split("source/", source_file_path)
        return path_list[0] + "doc_json/" + path_list[1] + ".json"

    @staticmethod
    def write_from_json_file(task, json_file_path):

        # Writing first 100 segments in DB

        doc_data = json.load(open(json_file_path))

        if type(doc_data) == str:

            doc_data = json.loads(doc_data)

        if doc_data['total_word_count'] == 0:

            return {'msg':'Empty File'}

        if doc_data['total_word_count'] >= 50000:

            doc_data, needed_keys = DocumentViewByTask.trim_segments(doc_data)
            serializer = (DocumentSerializerV2(data={**doc_data, \
                                                     "file": task.file.id, "job": task.job.id,
                                                     }, ))
            if serializer.is_valid(raise_exception=True):
                document = serializer.save()
                task.document = document
                task.save()

            # Writing remaining segment using task
            doc_data_task = DocumentViewByTask.correct_segment_for_task(json_file_path, needed_keys)

            if doc_data_task["text"] != {}:

                # For celery task
                serializer_task = DocumentSerializerV2(data={**doc_data_task, \
                                                             "file": task.file.id, "job": task.job.id, }, )

                validated_data = serializer_task.to_internal_value(data={**doc_data_task, \
                                                                         "file": task.file.id, "job": task.job.id, })
                task_write_data = json.dumps(validated_data, default=str)
                write_segments_to_db.apply_async((task_write_data, document.id), )
        else:
            serializer = (DocumentSerializerV2(data={**doc_data, \
                                                     "file": task.file.id, "job": task.job.id,
                                                     }, ))
            if serializer.is_valid(raise_exception=True):
                document = serializer.save()
                task.document = document
                task.save()

        return document
    
    def authorize_doc(self,request,doc,action):
        if  dict == type(doc):
            try:
                doc =doc.get('doc')
                if doc ==None:
                    return False 
            except:
                return False 
        authorize(request, resource=doc, actor=request.user, action=action)

    @staticmethod
    def create_document_for_task_if_not_exists(task):

        from ai_workspace.models import MTonlytaskCeleryStatus
        print("create_document_for_task_if_not_exists")
        if task.document != None:
            print("<--------------------------Document Exists--------------------->")
            if task.job.project.pre_translate == True:
                mt_only_check =  MTonlytaskCeleryStatus.objects.filter(Q(task_id=task.id) & Q(task_name = 'mt_only')).last()
                if mt_only_check:
                    if get_empty_segments(task.document) == False:
                        return task.document
                ins = MTonlytaskCeleryStatus.objects.filter(Q(task_id=task.id) & Q(task_name = 'pre_translate_update')).last()
                state = pre_translate_update.AsyncResult(ins.celery_task_id).state if ins and ins.celery_task_id else None
                if state == 'STARTED' or state == 'PENDING':
                    try:
                        cel = TaskResult.objects.get(task_id=ins.celery_task_id)
                        return {'msg':'Pre Translation Ongoing. Please wait a little while.Hit refresh and try again','celery_id':ins.celery_task_id}
                    except TaskResult.DoesNotExist:
                        cel_task = pre_translate_update.apply_async((task.id,),)
                        return {'msg':'Pre Translation Ongoing. Please wait a little while.Hit refresh and try again','celery_id':ins.celery_task_id}
                elif (not ins) or state == 'FAILURE':
                    print("Inside Pre celery")
                    cel_task = pre_translate_update.apply_async((task.id,),)
                    return {"msg": "Pre Translation Ongoing. Please wait a little while.Hit refresh and try again",'celery_id':cel_task.id}
                elif state == "SUCCESS":
                    #empty = task.document.get_segments().filter(target='').first()
                    if ins.error_type == "Insufficient Credits" or get_empty_segments(task.document) == True:
                        initial_credit = task.document.doc_credit_debit_user.credit_balance.get("total_left")
                        seg = task.document.get_segments().filter(target='').first().source
                        consumable_credits = MT_RawAndTM_View.get_consumable_credits(task.document,None,seg)
                        if initial_credit > consumable_credits:
                            cel_task = pre_translate_update.apply_async((task.id,),)
                            return {"msg": "Pre Translation Ongoing. Please wait a little while.Hit refresh and try again",'celery_id':cel_task.id}
                        return {"doc":task.document,"msg":"Pre Translation may be incomplete due to insufficient credit"}
                    else:
                        return task.document

            else:return task.document

        # If file for the task is already processed
        elif Document.objects.filter(file_id=task.file_id).exists():
            print("-----------Already Processed--------------")
            json_file_path = DocumentViewByTask.get_json_file_path(task)

            if exists(json_file_path):
                document = DocumentViewByTask.write_from_json_file(task, json_file_path)

            ####  Copying segments from previous task   #######
            else:
                doc = Document.objects.filter(file_id=task.file_id).last()
                doc_data = DocumentSerializerV3(doc).data

                serializer = (DocumentSerializerV2(data={**doc_data, \
                                                         "file": task.file.id, "job": task.job.id,
                                                         }, ))
                if serializer.is_valid(raise_exception=True):
                    document = serializer.save()
                    task.document = document
                    print("********   Document written using existing file  ***********")
                    task.save()

        # Fresh task
        else:
            print("<--------------------------------Fresh Task-----------------------------------")
            data = TaskSerializer(task).data
            DocumentViewByTask.correct_fields(data)
            params_data = {**data, "output_type": None}

            res_paths = get_res_path(params_data["source_language"])
            json_file_path = DocumentViewByTask.get_json_file_path(task)

            print("doc_req_res_params",json.dumps(res_paths))

            # For large files, json file is already written during word count
            if exists(json_file_path):
                document = DocumentViewByTask.write_from_json_file(task, json_file_path)
                
            else:
                doc = requests.post(url=f"http://{spring_host}:8080/getDocument/", data={
                    "doc_req_params": json.dumps(params_data),
                    "doc_req_res_params": json.dumps(res_paths)
                })

                if doc.status_code == 200:
                    doc_data = doc.json()
                    if doc_data.get('total_word_count') == 0:
                        return {'msg':'Empty File'}
                    serializer = (DocumentSerializerV2(data={**doc_data, \
                                                             "file": task.file.id, "job": task.job.id, }, ))

                    if serializer.is_valid(raise_exception=True):
                        document = serializer.save()
                        task.document = document
                        task.save()
                else:
                    logger.info(">>>>>>>> Something went wrong with file reading <<<<<<<<<")
                    raise ValueError("Sorry! Something went wrong with file processing.")

        return document

    def get(self, request, task_id, format=None):

        from ai_workspace.models import MTonlytaskCeleryStatus

        task = self.get_object(task_id=task_id)
        if task.job.project.pre_translate == True and task.document == None:
            ins = MTonlytaskCeleryStatus.objects.filter(Q(task_id=task_id) & Q(task_name = 'mt_only')).last()
            state = mt_only.AsyncResult(ins.celery_task_id).state if ins and ins.celery_task_id else None

            if state == 'STARTED' or state == 'PENDING':
                if ins.status == 1:
                    return Response({'msg':'Mt only Ongoing. Pls Wait','celery_id':ins.celery_task_id},status=401)
                else:
                    document = self.create_document_for_task_if_not_exists(task)
                    self.authorize_doc(request,document,action="read") 
                    doc = DocumentSerializerV2(document).data
                    return Response(doc, status=201)
            elif (not ins) or state == 'FAILURE':
                # cel_task = pre_translate_update.apply_async((task.id,),)
                # return Response({'msg':'Pre Translation Ongoing. Please wait a little while.Hit refresh and try again','celery_id':cel_task.id},status=401)
                ##need to authorize
                cel_task = mt_only.apply_async((task.job.project.id, str(request.auth),task.id),)
                return Response({"msg": "Pre Translation Ongoing. Please wait a little while.Hit refresh and try again",'celery_id':cel_task.id},status=401)
            elif state == "SUCCESS":
                document = self.create_document_for_task_if_not_exists(task)
                self.authorize_doc(request,document,action="read") 
                try:
                    doc = DocumentSerializerV2(document).data
                    return Response(doc, status=201)
                except:
                    if document.get('doc')!= None:
                        doc = DocumentSerializerV2(document.get('doc')).data
                        return Response({'msg':document.get('msg'),'doc_data':doc}, status=201)
                    else:
                        return Response(document,status=400)
            else:
                document = self.create_document_for_task_if_not_exists(task)
                self.authorize_doc(request,document,action="read") 
                doc = DocumentSerializerV2(document).data
                return Response(doc, status=201)
        else:
            document = self.create_document_for_task_if_not_exists(task)   
            self.authorize_doc(request,document,action="read")        
            try:
                doc = DocumentSerializerV2(document).data
                return Response(doc, status=201)
            except:
                if document.get('doc')!= None:
                    doc = DocumentSerializerV2(document.get('doc')).data
                    return Response({'msg':document.get('msg'),'doc_data':doc}, status=201)
                else:
                    return Response(document,status=400)


class DocumentViewByDocumentId(views.APIView):
    @staticmethod
    def get_object(document_id):
        docs = Document.objects.all()
        document = get_object_or_404(docs, id=document_id)
        return  document


    def edit_allow_check(self, task_obj, given_step):
        given_step = int(given_step) if given_step else None
        print("GivenStep------>",given_step, type(given_step))
        from ai_workspace.models import Task, TaskAssignInfo
        pr_managers = self.request.user.team.get_project_manager if self.request.user.team and self.request.user.team.owner.is_agency else [] 
        user = self.request.user.team.owner if (self.request.user.team and self.request.user.team.owner.is_agency and self.request.user in pr_managers) else self.request.user
        #task_obj = Task.objects.get(document_id=instance.id)
        task_assigned_info = TaskAssignInfo.objects.filter(task_assign__task=task_obj)
        print("TaskassignedInfo------->",task_assigned_info)
        if not task_assigned_info:return True
        assigners = [i.task_assign.assign_to for i in task_assigned_info]
        print("Assigners----------->",assigners)
        if user not in assigners:
            print("Not in assigners")
            query = task_assigned_info.filter(task_assign__reassigned=False)
            reassigns = task_assigned_info.filter(task_assign__reassigned=True)
            print("QR--------->",query.count(),query.first().task_assign.step_id,query.first().task_assign.status)
            if query.count() == 1 and query.first().task_assign.step_id == 2:
                editor = TaskAssign.objects.get(task=task_obj,step_id=1,reassigned=False)
                if editor.status == 3 and query.first().task_assign.status in [1,2]:edit_allowed = False
                else:edit_allowed = True
            else:
                print("Inside else")
                if query.count() == 1 and query.get(task_assign__step_id = 1).task_assign.status in [3,4] and not reassigns:
                    print("Inside else if")
                    edit_allowed =True
                else:
                    print("Inside else Else")
                    status = [i.task_assign.status for i in query]
                    print("st------>",status)
                    if all(i == 3 or i == 4 for i in status):edit_allowed =True
                    else:edit_allowed = False
            print("ED-------->",edit_allowed)
            return edit_allowed
        else:
            print("In assigners")
            if user.is_agency:
                task_assign_query = task_assigned_info.filter(Q(task_assign__assign_to=user)).filter(task_assign__reassigned=False)
                tsq = task_assign_query.distinct('task_assign__step').count()
                print("Tsq---------->",tsq)
                if tsq == 2:
                    task_assign_ins = task_assign_query.filter(task_assign__step_id = given_step).first().task_assign
                    task_assign_another_assign = task_assign_query.filter(~Q(task_assign__step_id = given_step)).first().task_assign if given_step != 1 else None
                    reassigns = TaskAssignInfo.objects.filter(task_assign__task = task_obj,task_assign__step_id = given_step,task_assign__reassigned=True)
                    task_assign_reassigns = reassigns.first().task_assign if reassigns else None
                else:
                    task_assign_ins = task_assign_query.first().task_assign
                    if task_assign_ins.step_id == 2:    
                        task_assign_another_assign = TaskAssign.objects.get(task=task_obj,step_id=1,reassigned=False)
                    else:
                        task_assign_another_assign = None
                    reassigns = TaskAssignInfo.objects.filter(task_assign__task = task_obj,task_assign__step = task_assign_ins.step,task_assign__reassigned=True)
                    task_assign_reassigns = reassigns.first().task_assign if reassigns else None
            else:
                task_assign_query = task_assigned_info.filter(Q(task_assign__assign_to=user))
                task_assign_ins = task_assign_query.first().task_assign
                task_assign_another_assign_query = task_assigned_info.filter(task_assign__reassigned=task_assign_ins.reassigned)\
                                            .filter(~Q(task_assign__assign_to=user))
                print("TASQ--------->",task_assign_another_assign_query)
                if task_assign_another_assign_query:
                    task_assign_another_assign = task_assign_another_assign_query.first().task_assign
                    print("TAS------------>",task_assign_another_assign)
                else:
                    if task_assign_ins.step_id == 2:
                        task_assign_another_assign = TaskAssign.objects.get(task=task_obj,step_id=1,reassigned=False)
                    else:task_assign_another_assign = None
                task_assign_reassigns = None 
        task_assign_reassigns_status = task_assign_reassigns.status if task_assign_reassigns else 0
        task_assign_another_assign_status = task_assign_another_assign.status if task_assign_another_assign else 0
        print("TaskAssignIns------------->",task_assign_ins)
        print("TaskAssignInsStep----------->",task_assign_ins.step)
        print("TaskAssignInsStatus----------->",task_assign_ins.status)
        print("TaskAssignAnotherAssignStatus--------->",task_assign_another_assign_status)
        print("TaskReassignStatus------------>",task_assign_reassigns_status)
        if task_assign_ins.step_id == 1 and task_assign_ins.status in [1,2]:
            if (task_assign_reassigns and task_assign_reassigns_status in [1,2]) or (user.is_agency and task_assign_another_assign_status in [1,2]):#and (task_assign_ins.status in [3,4] or task_assign_reassigns_status in [1,2] or task_assign_another_assign_status in[1,2]):
                edit_allowed = False
            else:edit_allowed = True
        elif task_assign_ins.step_id == 1 and task_assign_ins.status in [3,4]:
            edit_allowed =False
        elif task_assign_ins.step_id == 2 and ((task_assign_ins.status in [3,4]) or task_assign_another_assign_status in [2,1,4]):
            edit_allowed = False
        elif task_assign_ins.step_id == 2 and task_assign_ins.status in [1,2]:
            if task_assign_reassigns and task_assign_reassigns_status in [1,2]:
                edit_allowed = False
            else:edit_allowed = True
        else:edit_allowed = True
        print("EditAllowed---------->",edit_allowed)
        return edit_allowed  
            

    def get(self, request, document_id):
        if request.GET:
            given_step = request.GET.get('step_id',None) 
        else:
            given_step = None
        document = self.get_object(document_id)
        mt_enable = document.job.project.mt_enable
        task = Task.objects.get(document=document)
        edit_allowed = self.edit_allow_check(task,given_step)
        #doc_user = AiUser.objects.get(project__project_jobs_set__file_job_set=document_id).id
        doc_user = AiUser.objects.filter(project__project_jobs_set__file_job_set=document_id).first()
        assigned_users = [i.assign_to for i in Task.objects.get(document=document).task_info.all() if i.assign_to.is_agency]
        assigned_users = [*set(assigned_users)]
        assigned_users.extend([j.team.get_project_manager for j in assigned_users if j.team and j.team.get_project_manager]) 
        print("Assigned---------->",assigned_users)
        team_members = doc_user.get_team_members if doc_user.get_team_members else []
        hired_editors = doc_user.get_hired_editors if doc_user.get_hired_editors else []
        try :managers = doc_user.team.get_project_manager if doc_user.team.get_project_manager else []
        except:managers =[]
        assign_enable = True if (request.user == doc_user) or (request.user in managers) else False
        # if (request.user == doc_user) or (request.user in team_members) or (request.user in hired_editors):
        dict = {'download':'enable'} if (request.user == doc_user) else {'download':'disable'}
        dict_1 = {'updated_download':'enable'} if (request.user == doc_user) or (request.user in managers) or (request.user in assigned_users) else {'updated_download':'disable'}
        dict_2 = {'mt_enable':mt_enable,'task_id':task.id,'assign_enable':assign_enable,'edit_allowed':edit_allowed}
        authorize(request, resource=document, actor=request.user, action="read")
        data = DocumentSerializerV2(document).data
        data.update(dict)
        data.update(dict_1)
        data.update(dict_2)
        return Response(data, status=200)
        # else:
        #     return Response({"msg" : "Unauthorised"}, status=401)

# @api_view(['GET',])
# @permission_classes([IsAuthenticated])
# def get_mt_raw(request,task_id):
#     from ai_auth.tasks import mt_raw_update
#     print("TT--------->",task_id)
#     data={}
#     task = Task.objects.get(id=task_id)
#     if task.document == None:
#         print("Document process first")
#         document_view_by_task = DocumentViewByTask()
#         response = document_view_by_task.get(request,task_id)
#         print("RR------->",response.data)
#     else:
#         result = mt_raw_update.apply((task_id,))
#         if result.successful():
#             print('Task completed successfully')
#             print('Result:', result.result)
#             data = {'msg':'completed call download','doc_id':task.document.id}
#         else:
#             print('Task failed')
#             print('Exception:', result.result)
        
#     return Response(data,status=200)


# from rest_framework import pagination

# class CustomPageNumberPagination(pagination.PageNumberPagination):
#     """Custom page number pagination."""

#     page_size = 20
#     max_page_size = 50
#     page_size_query_param = 'page_size'

#     def get_page_size(self, request):
#         """Get page size."""
#         # On certain pages, force custom/max page size.
#         try:
#             user = request.user
#             Print("User-------->",user)
#             size = SegmentPageSize.objects.get(user=user).page_size
#             return size
#         except:
#             return self.page_size

#         return super(CustomPageNumberPagination, self).get_page_size(request)



class SegmentsView(views.APIView, PageNumberPagination):
    PAGE_SIZE = page_size =  20
    max_page_size = 50
    page_size_query_param = 'page_size'#self.get_page_size()
    #pagination_class = CustomPageNumberPagination

    def get_object(self, document_id):
        document = get_object_or_404(\
            Document.objects.all(), id=document_id)
        authorize(self.request, resource=document, actor=self.request.user, action="read")
        return document

    # def get_page_size(self):
    #     page_size = SegmentPageSize.objects.filter(ai_user_id = self.request.user.id).last().page_size
    #     return page_size

    def get(self, request, document_id):
        document = self.get_object(document_id=document_id)
        segments = document.segments_for_find_and_replace
        merge_segments = MergeSegment.objects.filter(text_unit__document=document_id)
        split_segments = SplitSegment.objects.filter(text_unit__document=document_id)
        final_segments = list(chain(segments, merge_segments, split_segments))
        sorted_final_segments = sorted(final_segments, key=lambda pu:pu.id if ((type(pu) is Segment) or (type(pu) is MergeSegment)) else pu.segment_id)
        page_len = self.paginate_queryset(range(1, len(final_segments) + 1), request)
        page_segments = self.paginate_queryset(sorted_final_segments, request, view=self)
        segments_ser = SegmentSerializer(page_segments, many=True)
        [i.update({"segment_count": j}) for i, j in zip(segments_ser.data, page_len)]
        res = self.get_paginated_response(segments_ser.data)
        return res

class MergeSegmentView(viewsets.ModelViewSet):
    serializer_class = MergeSegmentSerializer
    @staticmethod
    def is_regular_segments(segments):

        is_regular = []

        for seg in segments:
            if split_check(int(seg)):
                is_regular.append(True)
            else:
                is_regular.append(False)

        if all(is_regular): return True
        elif True in is_regular:
            return "Mixed"
        else: return False

    def create(self, request, *args, **kwargs):

        segments = request.POST.getlist("segments")

        status = MergeSegmentView.is_regular_segments(segments)

        if status == "Mixed":
            return Response({"msg" : "Cannot be merged. One of the segment is already split"}, status=400)
            # raise Exception("Only one of the selected segments is a split segment")

        # For normal segment merge
        if status == True:
            serlzr = self.serializer_class(data=request.data)
            if serlzr.is_valid(raise_exception=True):
                serlzr.save(id=serlzr.validated_data.get("segments")[0].id)
                obj =  serlzr.instance
                obj.update_segments(serlzr.validated_data.get("segments"))
                return Response(MergeSegmentSerializer(obj).data)

        # For split segment merge
        else:

            # Checking if split segments are of the same parent segment or not
            segment_ids = [SplitSegment.objects.get(id=int(seg)).segment_id for seg in segments]
            if (len(set(segment_ids)) > 1):
                return Response({"msg": "Split segments should be of the same parent segment"}, status = 400)

            # Setting the is_split flag to False
            segment_id = SplitSegment.objects.filter(id=int(segments[0])).first().segment_id
            segment = Segment.objects.filter(id=segment_id).first()
            segment.is_split = False
            segment.save()

            # Deleting the split segment objects
            for seg in segments:
                SplitSegment.objects.filter(id=int(seg)).first().delete()
            return Response(SegmentSerializer(segment).data, status=204)

class SplitSegmentView(viewsets.ModelViewSet):
    serializer_class = SplitSegmentSerializer
    @staticmethod
    def is_only_tags(string):
        tags = re.findall(r"</?\d+>", string)
        tag_string = ""
        for tag in tags:
            tag_string += tag
        if tag_string == string:
            return True
        else: False
    @staticmethod
    def empty_or_tags(seg1, seg2):
        if seg1 == "" or seg2 == "":
            return True
        if SplitSegmentView.is_only_tags(seg1) or SplitSegmentView.is_only_tags(seg2):
            return True
        return False
    def create(self, request, *args, **kwargs):

        seg_first = request.data["seg_first"]
        seg_second = request.data["seg_second"]

        if SplitSegmentView.empty_or_tags(seg_first.strip(), seg_second.strip()):
            return Response({"msg": "No text content found. Segment cannot be split"}, status = 400)

        segment = request.data["segment"]

        segment_id = int(request.POST.get("segment"))

        # Checking for a already split or merged segment
        split_seg = SplitSegment.objects.filter(id=segment_id)

        if split_seg:
            return Response({"msg": "Segment is already split"}, status = 400)
        elif Segment.objects.filter(id=segment_id).first().is_merged == True:
            return Response({"msg": "Segment is already merged. You can only restore the segment"}, \
                            status=400)

        serializer_first = self.serializer_class(data = request.data)
        serializer_second = self.serializer_class(data = request.data)

        if serializer_first.is_valid(raise_exception=True) & \
                serializer_second.is_valid(raise_exception=True):

            serializer_first.save()
            serializer_second.save()

            first_seg = serializer_first.instance
            second_seg = serializer_second.instance

            first_seg.update_segments(seg_first, is_first=True)
            second_seg.update_segments(seg_second)

            # Setting the original segment as split
            seg = Segment.objects.filter(id=segment).first()
            seg.is_split = True
            seg.save()

            return Response(SegmentSerializer(first_seg).data)

@permission_classes([AllowAny,])
def get_supported_file_extensions(request):
    return JsonResponse(CURRENT_SUPPORT_FILE_EXTENSIONS_LIST, safe=False)

class SourceTMXFilesCreate(views.APIView):
    def get_queryset(self, project_id):
        project_qs = Project.objects.all()
        project = get_object_or_404(project_qs, id=project_id)
        return  project.files_and_jobs_set

    def post(self, request, project_id):
        jobs, files = self.get_queryset(project_id=project_id)


from rest_framework import serializers
class SegmentsUpdateView(viewsets.ViewSet):
    def get_object(self, segment_id):
        qs = Segment.objects.all()
        #qs = filter_authorize(self.request, qs,self.request.user,"read")

        if split_check(segment_id):
            segment = get_object_or_404(qs, id=segment_id)
            return segment.get_active_object()
        else:
            return SplitSegment.objects.filter(id=segment_id).first()

    @staticmethod
    def get_update(segment, data, request):
        segment_serlzr = SegmentSerializerV2(segment, data=data, partial=True, \
                                             context={"request": request})
        if segment_serlzr.is_valid(raise_exception=True):
            segment_serlzr.save()
            return segment_serlzr
        else:
            logger.info(">>>>>>>> Error in Segment update <<<<<<<<<")
            return segment_serlzr.errors

    # def edit_allowed_check(self, instance):
    #     from ai_workspace.models import Task, TaskAssignInfo
    #     user = self.request.user
    #     task_obj = Task.objects.get(document_id=instance.text_unit.document.id)
    #     task_assigned_info = TaskAssignInfo.objects.filter(task_assign__task=task_obj)
    #     assigners = [i.task_assign.assign_to for i in task_assigned_info]
    #     if user not in assigners:
    #         edit_allowed = True
    #     else:
    #         try:
    #             task_reassign = TaskAssignInfo.objects.filter(task_assign__reassigned=True).filter(task_assign__task=task_obj)
    #             if task_reassign:
    #                 task_assign = task_assigned_info.filter(task_assign__reassigned=True).filter(
    #                 ~Q(task_assign__assign_to=user)).first().task_assign
    #             else:
    #                 task_assign = task_assigned_info.filter(task_assign__reassigned=False).filter(
    #                 ~Q(task_assign__assign_to=user)).first().task_assign
    #             edit_allowed = True if task_assign.step_id == 2 and task_assign.status == 2 else False
    #         except:
    #             edit_allowed = True
    #     return edit_allowed

    def update_pentm(self, segment):
        data = PentmUpdateSerializer(segment).data
        res = requests.post(f"http://{spring_host}:8080/project/pentm/update", data=data)
        if res.status_code == 200:
            print("res text--->", res.json())
        else:
            print("not successfully update")

    def split_update(self, request_data, segment):
        print("Seg---------->",segment)
        org_segment = SplitSegment.objects.get(id=segment.id).segment_id
        status = request_data.get("status",None)
        if status:
            status_obj = TranslationStatus.objects.filter(status_id=status).first()
            segment.status = status_obj
            if status not in [109,110]:step = 1
            else:step=2
        else: 
            step = None
            status_obj = segment.status
        content = request_data['target'] if "target" in request_data else request_data['temp_target']
        existing_step = 1 if segment.status_id not in [109,110] else 2 
        seg_his_create = True if segment.temp_target!=content or existing_step != step else False
        if request_data.get("target", None) != None:
            segment.target = request_data["target"]
            segment.temp_target = request_data["target"]
        else:segment.temp_target = request_data["temp_target"]
        segment.save()
        print("Seg His Create--------------->",seg_his_create)
        if seg_his_create:
            SegmentHistory.objects.create(segment_id=org_segment, split_segment_id = segment.id, user = self.request.user, target= content, status= status_obj )
        return Response(SegmentSerializerV2(segment).data, status=201)

    def partial_update(self, request, *args, **kwargs):
        # Get a list of PKs to update
        data={}
        confirm_list = request.data.get('confirm_list', [])
        confirm_list = json.loads(confirm_list)
        print("RTR---------->",confirm_list)
        msg=None
        success_list=[]
        
        for item in confirm_list:
            try:
                msg = None
                segment_id = item.get('pk')
                status = item.get('status')
                segment = self.get_object(segment_id)
                if segment.temp_target != '':
                    data['target'] = segment.temp_target
                    data['status'] = status
                else:
                    data={}
                authorize(request, resource=segment, actor=request.user, action="read")
                # edit_allow = self.edit_allowed_check(segment)
                # if edit_allow == False:
                #     return Response({"msg": "Someone is working already.."}, status=400)

                # Segment update for a Split segment
                if segment.is_split == True:
                    self.split_update(data, segment)
                segment_serlzr = self.get_update(segment, data, request)
                if data!={}:
                    success_list.append(item.get('pk'))
            except serializers.ValidationError as e:
                print("Exception=======>",e)
                msg = 'confirm all may not work properly due to insufficient credits'
        message = msg if msg else 'Objects updated successfully'
        return Response({'message': message,'confirmed_list':success_list})
        # self.update_pentm(segment)  # temporarily commented to solve update pentm issue
        # return Response(segment_serlzr.data, status=201)
        
        # # Get the objects to update
        # queryset = Segment.objects.filter(pk__in=pks)
        
        # # Update each object with the request data
        # for obj in queryset:
        #     serializer = self.serializer_class(obj, data=request.data, partial=True)
        #     serializer.is_valid(raise_exception=True)
        #     serializer.save()
    def update(self, request, pk=None):
        segment_id  = request.POST.get('segment')
        segment = self.get_object(segment_id)
        authorize(request, resource=segment, actor=request.user, action="read")
        # edit_allow = self.edit_allowed_check(segment)
        # if edit_allow == False:
        #     return Response({"msg": "Someone is working already.."}, status=400)

        # Segment update for a Split segment
        if segment.is_split == True:
            return self.split_update(request.data, segment)
        segment_serlzr = self.get_update(segment, request.data, request)
        # self.update_pentm(segment)  # temporarily commented to solve update pentm issue
        return Response(segment_serlzr.data, status=201)

class MergeSegmentDeleteView(viewsets.ModelViewSet):
    def get_queryset(self):
        return  MergeSegment.objects.all()

class MT_RawAndTM_View(views.APIView):

    @staticmethod
    def can_translate(request, debit_user):

        hired_editors = debit_user.get_hired_editors if debit_user.get_hired_editors else []

        # Check if the debit_user (account holder) has plan other than Business like Pro, None etc
        if get_plan_name(debit_user) not in settings.TEAM_PLANS:
            return {}, 424, "cannot_translate"

        elif (request.user.is_internal_member or request.user.id in hired_editors) and \
            (get_plan_name(debit_user) in settings.TEAM_PLANS) and \
            (UserCredits.objects.filter(Q(user_id=debit_user.id)  \
                                     & Q(credit_pack_type__icontains="Subscription")).last().ended_at != None):
            return {}, 424, "cannot_translate"

        else:
            return None

    @staticmethod
    def get_word_count(segment_source, doc):

        seg_data = {"segment_source": segment_source,
                    "source_language": doc.source_language_code,
                    "target_language": doc.target_language_code,
                    "processor_name": "plain-text-processor",
                    "extension": ".txt"
                    }
        res = requests.post(url=f"http://{spring_host}:8080/segment/word_count", \
                            data={"segmentWordCountdata": json.dumps(seg_data)},timeout=3)
        if res.status_code == 200:
            return res.json()
        else:
            logger.info(">>>>>>>> Error in segment word count calculation <<<<<<<<<")
            raise ValueError("Sorry! Something went wrong with word count calculation.")

    @staticmethod
    def get_consumable_credits(doc, segment_id, seg):

        if seg:
            return MT_RawAndTM_View.get_word_count(seg, doc)

        elif segment_id:
            if split_check(segment_id):
                segment = Segment.objects.filter(id=segment_id).first().get_active_object() #if segment_id else None
                segment_source = segment.source #if segment!= None else seg
                return MT_RawAndTM_View.get_word_count(segment_source, doc)

            # For split segment
            else:
                split_seg_source = SplitSegment.objects.filter(id=segment_id).first().source
                return MT_RawAndTM_View.get_word_count(split_seg_source, doc)

    @staticmethod
    def get_task_assign_mt_engine(segment_id):
        task_assign_mt_engine = TaskAssign.objects.filter(
            Q(task__document__document_text_unit_set__text_unit_segment_set=segment_id) &
            Q(step_id=1)
        ).first().mt_engine
        return task_assign_mt_engine

    @staticmethod
    def get_user_and_doc(segment_id):
        text_unit_id = Segment.objects.get(id=segment_id).text_unit_id
        doc = TextUnit.objects.get(id=text_unit_id).document
        user = doc.doc_credit_debit_user
        return user, doc

    @staticmethod
    def is_account_holder(request, doc, user):

        if (doc.job.project.team) and (request.user != AiUser.objects.get(project__project_jobs_set__file_job_set=doc)):
            can_translate = MT_RawAndTM_View.can_translate(request, user)
            if can_translate == None:
                pass
            else:
                return MT_RawAndTM_View.can_translate(request, user)
    @staticmethod
    def get_data(request, segment_id, mt_params):

        mt_raw = MT_RawTranslation.objects.filter(segment_id=segment_id).first()
        task_assign_mt_engine = MT_RawAndTM_View.get_task_assign_mt_engine(segment_id)

        # If raw translation is already available and Proj & Task MT engines are same
        if mt_raw:
            # authorize(request, resource=mt_raw, actor=request.user, action="read")
            if mt_raw.mt_engine == task_assign_mt_engine:
                return MT_RawSerializer(mt_raw).data, 200, "available"


        # If MT disabled for the task
        if mt_params.get("mt_enable", True) != True:
            return {}, 200, "MT disabled"

        user, doc = MT_RawAndTM_View.get_user_and_doc(segment_id)

        MT_RawAndTM_View.is_account_holder(request, doc, user)

        initial_credit = user.credit_balance.get("total_left")

        consumable_credits = MT_RawAndTM_View.get_consumable_credits(doc, segment_id, None)

        print("Consumable_credits---------------->",consumable_credits)
        
        if initial_credit > consumable_credits :
            if mt_raw:
                #############   Update   ############
                translation = get_translation(task_assign_mt_engine.id, mt_raw.segment.source, \
                                              doc.source_language_code, doc.target_language_code,user_id=doc.owner_pk,cc=consumable_credits)
                #debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)

                MT_RawTranslation.objects.filter(segment_id=segment_id).update(mt_raw = translation, \
                                       mt_engine = task_assign_mt_engine, task_mt_engine=task_assign_mt_engine)
                obj = MT_RawTranslation.objects.filter(segment_id=segment_id).first()
                return MT_RawSerializer(obj).data, 200, "available"
            else:

                #########   Create   #######
                print("#########   Create   #######")
                mt_raw_serlzr = MT_RawSerializer(data = {"segment": segment_id},\
                                context={"request": request})
                if mt_raw_serlzr.is_valid(raise_exception=True):
                    mt_raw_serlzr.save()
                    #debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)
                    return mt_raw_serlzr.data, 201, "available"
        else:
            return {}, 424, "unavailable"
        
    

    @staticmethod
    def get_split_data(request, segment_id, mt_params):

        mt_raw_split = MtRawSplitSegment.objects.filter(split_segment_id=segment_id).first()

        split_seg = SplitSegment.objects.filter(id=segment_id).first()

        # Getting the task MT engine
        task_assign_mt_engine = MT_RawAndTM_View.get_task_assign_mt_engine(split_seg.segment_id)

        # If raw translation is already available and Proj & Task MT engines are same
        if mt_raw_split:

            # Getting the project MT engine
            proj_mt_engine = Project.objects.filter(\
                project_jobs_set__job_tasks_set__document__document_text_unit_set__text_unit_segment_set\
                    =split_seg.segment_id).first().mt_engine

            if proj_mt_engine == task_assign_mt_engine:
                return {"mt_raw": mt_raw_split.mt_raw, "segment": split_seg.id}, 200, "available"

        # If MT disabled for the task
        if mt_params.get("mt_enable", True) != True:
            return {}, 200, "MT disabled"

        user, doc = MT_RawAndTM_View.get_user_and_doc(split_seg.segment_id)

        MT_RawAndTM_View.is_account_holder(request, doc, user)

        initial_credit = user.credit_balance.get("total_left")

        consumable_credits = MT_RawAndTM_View.get_consumable_credits(doc, segment_id, None)

        # initial_credit = 10000

        if initial_credit > consumable_credits:

            # Updating raw translation of split segments
            if mt_raw_split:
                translation = get_translation(task_assign_mt_engine.id, split_seg.source, doc.source_language_code,
                                              doc.target_language_code,user_id=doc.owner_pk,cc=consumable_credits)
                
                print(translation)
                # translation=MT_RawAndTM_View.asset_replace(translation)

                #debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)
                MtRawSplitSegment.objects.filter(split_segment_id=segment_id).update(mt_raw=translation,)
                return {"mt_raw": mt_raw_split.mt_raw, "segment": split_seg.id}, 200, "available"

            # Creating new MT raw for split segment
            else:
                print("Creating new MT raw for split segment")
                translation = get_translation(task_assign_mt_engine.id, split_seg.source, doc.source_language_code,
                                              doc.target_language_code,user_id=doc.owner_pk,cc=consumable_credits)
                
                # translation=MT_RawAndTM_View.asset_replace(translation)

                MtRawSplitSegment.objects.create(**{"mt_raw" : translation, "split_segment_id" : segment_id})
                #debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)

                return {"mt_raw": translation, "segment": split_seg.id}, 200, "available"

        else:
            return {}, 424, "unavailable"

    @staticmethod
    def find_tm_matches(seg_source, user, doc):

        proj = doc.job.project
        tmx_files = TmxFileNew.objects.filter(job=doc.job_id)

        tm_lists = []

        if tmx_files:
            tm_lists = tmx_read_with_target(tmx_files,doc.job)
            #print("TmLists--------------->",tm_lists)
        match_results = tm_fetch_extract(seg_source,
                                        tm_lists,
                                        scorer=rapidfuzz.distance.Levenshtein.normalized_similarity,
                                        score_cutoff=round(proj.threshold / 100, 2),
                                        limit=proj.max_hits)
        response_data = [{'source':mr[0].get('source'),'target':mr[0].get('target'),'percentage':round(mr[1]*100,2)} for mr in match_results] if match_results else []
        return response_data

    @staticmethod
    def get_tm_data(request, segment_id):

        # For normal segment
        if split_check(segment_id):
            seg_source = Segment.objects.filter(id=segment_id).first().get_active_object().source
            user, doc = MT_RawAndTM_View.get_user_and_doc(segment_id)
            return MT_RawAndTM_View.find_tm_matches(seg_source, user, doc)

            # Old PenTM search logic

            # if segment:
            #     tm_ser = TM_FetchSerializer(segment)
            #     res = requests.post( f'http://{spring_host}:8080/pentm/source/search',\
            #             data = {'pentmsearchparams': json.dumps(tm_ser.data)})
            #     if res.status_code == 200:
            #         return res.json()
            #     else:
            #         return []
            # return []


        # TMX fetch for split segment
        else:
            split_seg = SplitSegment.objects.filter(id=segment_id).first()
            seg_source = split_seg.source
            user, doc = MT_RawAndTM_View.get_user_and_doc(split_seg.segment_id)
            return MT_RawAndTM_View.find_tm_matches(seg_source, user, doc)

    def get_alert_msg(self, status_code, can_team):

        if (status_code == 424 and can_team == "unavailable"):
            return "MT doesn't work as the credits are insufficient. Please buy more or upgrade"
        elif (status_code == 200 and can_team == "MT disabled"):
            return "MT Disabled"
        elif (status_code == 200 and can_team == "available"):
            return None
        elif (status_code == 201 and can_team == "available"):
            return None
        else:
            return "Team subscription inactive"

    def get_task_assign_data(self, segment_id):
        task_assign_obj = TaskAssign.objects.filter(
            Q(task__document__document_text_unit_set__text_unit_segment_set=segment_id) &
            Q(step_id=1)
        ).first()
        return TaskAssignSerializer(task_assign_obj).data

    def get_segment_MT_params(self, segment_id):

        if split_check(segment_id):
            return self.get_task_assign_data(segment_id)

        else:
            split_seg = SplitSegment.objects.filter(id=segment_id).first()
            if split_seg:
                return self.get_task_assign_data(split_seg.segment_id)

    @staticmethod   
    def asset_replace(request,translation,segment_id):
        seg=get_object_or_404(Segment,id=segment_id)
        tar_lang=seg.text_unit.document.job.target_language_id
        # tar_lang=doc
        # tar_lang=77
        word=word_tokenize(translation)
        result={}
        for word in word:
            assets=SelflearningAsset.objects.filter(Q(target_language_id = tar_lang) & Q(user=request.user) & Q(source_word__iexact = word)).order_by('-occurance')
            if assets:
                coun=[i.occurance for i in assets if i.occurance>4]
                print(coun)
                rep=[i.edited_word for i in assets if i.occurance>4]
                print(rep)
                if rep:
                    translation=translation.replace(word,rep[0]) 
                    result[rep[0]]=[i.edited_word for i in assets if i.occurance>2 and i.edited_word != rep[0]]
                    result[rep[0]].insert(0,word)
             
                else:
                    result[word]=[i.edited_word for i in assets if i.occurance>2]         
                                 
        print(translation)
        return translation,result


    def get(self, request, segment_id):
            tm_only = {
                        "segment": segment_id,
                        "mt_raw": "",
                        "mt_alert": False,
                        "alert_msg": None
                       }

            mt_uc = request.GET.get("mt_uc", 'false')

            # Getting MT params
            mt_params = self.get_segment_MT_params(segment_id)
            
            if split_check(segment_id):
                seg = Segment.objects.get(id=segment_id)
                authorize(request, resource=seg, actor=request.user, action="read")
            else:
                seg_id = SplitSegment.objects.get(id=segment_id).get_parent_seg_id
                seg = Segment.objects.get(id=seg_id)
                print("entered split check")
                authorize(request, resource=seg, actor=request.user, action="read")
                print("pass")


            # For normal and merged segments
            if split_check(segment_id):

                tm_data = self.get_tm_data(request, segment_id)

                if tm_data and (mt_uc == 'false'):
                    return Response({**tm_only, "tm":tm_data}, status = 200 )
                data, status_code, can_team = self.get_data(request, segment_id, mt_params)
                mt_alert = True if status_code == 424 else False
                alert_msg = self.get_alert_msg(status_code, can_team)

                # print('data normal=-----------',data['mt_raw'])
                rep=data['mt_raw']
                #list option assets
                # replace asset auto
                asset_rep,asset_list=MT_RawAndTM_View.asset_replace(request,rep,segment_id)
                data['mt_raw']=asset_rep
                data['options']=asset_list

        
                # print('rep----------',asset_rep)

                return Response({**data, "tm":tm_data, "mt_alert": mt_alert,
                    "alert_msg":alert_msg}, status=status_code)

            # For split segment
            else:

                tm_data = self.get_tm_data(request, segment_id)

                if tm_data and (mt_uc == False):
                    return Response({**tm_only, "tm": tm_data}, status=200)

                data, status_code, can_team = self.get_split_data(request, segment_id, mt_params)
                mt_alert = True if status_code == 424 else False
                alert_msg = self.get_alert_msg(status_code, can_team)
                
                rep=data['mt_raw']

                #list option assets
                # replace asset auto
                asset_rep,asset_list=MT_RawAndTM_View.asset_replace(request,rep,segment_id)
                data['mt_raw']=asset_rep
                data['options']=asset_list
                # print('rep----------',asset_rep)



                return Response({**data, "tm": tm_data, "mt_alert": mt_alert,
                                 "alert_msg": alert_msg}, status=status_code)
            
"""



def word_change():
    # segment=request.POST.get('segment',None)
    # tar_lang=request.POST.get('target_language',None)
    segment="This apple size is small so he provide multiple apples"
    tar_lang=17
    word=word_tokenize(segment)
    for word in word:
        assets=SelflearningAsset.objects.filter(Q(target_language_id = tar_lang) & Q(user_id =946) & Q(source_word__iexact = word))
        if assets:
            edited_word=assets.last().edited_word
            # print(edited_word)
            segment=segment.replace(word,edited_word)         
    print(segment)
"""
        # return JsonResponse(result,status=status.HTTP_200_OK)


    # def get(self, request, segment_id):
    #
    #     # Getting MT params
    #     mt_params = self.get_segment_MT_params(segment_id)
    #
    #     # For normal and merged segments
    #     if split_check(segment_id):
    #         data, status_code, can_team = self.get_data(request, segment_id, mt_params)
    #         mt_alert = True if status_code == 424 else False
    #         alert_msg = self.get_alert_msg(status_code, can_team)
    #         tm_data = self.get_tm_data(request, segment_id)
    #         return Response({**data, "tm":tm_data, "mt_alert": mt_alert,
    #             "alert_msg":alert_msg}, status=status_code)
    #
    #     # For split segment
    #     else:
    #         data, status_code, can_team = self.get_split_data(request, segment_id, mt_params)
    #         mt_alert = True if status_code == 424 else False
    #         alert_msg = self.get_alert_msg(status_code, can_team)
    #         tm_data = self.get_tm_data(request, segment_id)
    #         return Response({**data, "tm": tm_data, "mt_alert": mt_alert,
    #                          "alert_msg": alert_msg}, status=status_code)


# class ConcordanceSearchView(views.APIView):
#
#     @staticmethod
#     def get_concordance_data(request, segment_id, search_string):
#         segment = Segment.objects.filter(id=segment_id).first()
#         if segment:
#             tm_ser_data = TM_FetchSerializer(segment).data
#             tm_ser_data.update({'search_source_string':search_string, "max_hits":20,\
#                     "threshold": 10})
#             res = requests.post( f'http://{spring_host}:8080/pentm/source/search',\
#                     data = {'pentmsearchparams': json.dumps( tm_ser_data), "isCncrdSrch":"true" })
#             if res.status_code == 200:
#                 return res.json()
#             else:
#                 return []
#         return []
#
#     def get(self, request, segment_id):
#         search_string = request.GET.get("string", None).strip('0123456789')
#         concordance = []
#         if search_string:
#             concordance = self.get_concordance_data(request, segment_id, search_string)
#         return Response(concordance, status=200)


class ConcordanceSearchView(views.APIView):

    @staticmethod
    def get_concordance_data(request, segment_id, search_string):

        seg = Segment.objects.filter(id=segment_id).first()
        job = seg.text_unit.document.job

        if seg:
            tm_lists = []
            tmx_files = TmxFileNew.objects.filter(job=job)
            if tmx_files:
                tm_lists = tmx_read_with_target(tmx_files,job)

            match_results = tm_fetch_extract(search_string,
                                        tm_lists,
                                        scorer=rapidfuzz.distance.Levenshtein.normalized_similarity,
                                        score_cutoff=0.85,
                                        limit=10)
            response_data = [{'source':mr[0].get('source'),'target':mr[0].get('target'),'percentage':round(mr[1]*100,2)} for mr in match_results] if match_results else []
            return response_data
        return []
        # if segment:
        #     tm_ser_data = TM_FetchSerializer(segment).data
        #     tm_ser_data.update({'search_source_string':search_string, "max_hits":20,\
        #             "threshold": 10})
        #     res = requests.post( f'http://{spring_host}:8080/pentm/source/search',\
        #             data = {'pentmsearchparams': json.dumps( tm_ser_data), "isCncrdSrch":"true" })
        #     if res.status_code == 200:
        #         return res.json()
        #     else:
        #         return []
        # return []

    def get(self, request, segment_id):
        search_string = request.GET.get("string", None).strip('0123456789')
        concordance = []
        if search_string:
            concordance = self.get_concordance_data(request, segment_id, search_string)
        #print("Concordance------------->",concordance)
        return Response(concordance, status=200)





def long_text_process(consumable_credits,document_user,file_path,task,target_language,voice_gender,voice_name):
    from ai_workspace.api_views import google_long_text_file_process
    res1,f2 = google_long_text_file_process(file_path,task,target_language,voice_gender,voice_name)
    #debit_status, status_code = UpdateTaskCreditStatus.update_credits(document_user, consumable_credits)
    if task.task_transcript_details.first()==None:
        ser = TaskTranscriptDetailSerializer(data={"translated_audio_file":res1,"task":task.id})
    else:
        t = task.task_transcript_details.first()
        ser = TaskTranscriptDetailSerializer(t,data={"translated_audio_file":res1,"task":task.id},partial=True)
    if ser.is_valid():
        ser.save()
    print(ser.errors)
    f2.close()


def pre_process(data):
    for key in data['text'].keys():
        for d in data['text'][key]:
            #del d['mt_raw_target']
            d.pop('mt_raw_target',None)
    return data

def mt_raw_pre_process(data):
    for key in data['text'].keys():
        for d in data['text'][key]:
            if d.get('mt_raw_target') != None:
                d['target'] = d.get('mt_raw_target')
            else:
                d['target'] = ''
            #del d['mt_raw_target']
            d.pop('mt_raw_target',None)
    return data

    

class DocumentToFile(views.APIView):
   
    @staticmethod
    def get_object(document_id):
        qs = Document.objects.all()
        document = get_object_or_404(qs, id=document_id)
        return  document

    def get_file_response(self, file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type= \
                "application/vnd.ms-excel")
            encoded_filename = urllib.parse.quote(os.path.basename(file_path), \
                                                  encoding='utf-8')
            response['Content-Disposition'] = 'attachment;filename*=UTF-8\'\'{}' \
                .format(encoded_filename)
            # filename = os.path.basename(file_path)
            # response['Content-Disposition'] = "attachment; filename=%s" % filename
            response['X-Suggested-Filename'] = encoded_filename
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Headers"] = "*"
            response['Access-Control-Expose-Headers'] = 'Content-Disposition'
            # print("cont-disp--->", response.get("Content-Disposition"))
            return response

    def get_source_file_path(self, document_id):
        doc = DocumentToFile.get_object(document_id)
        return File.objects.get(file_document_set=doc).get_source_file_path
        # return File.objects.get(file_document_set=doc).file.path

    # FOR DOWNLOADING SOURCE FILE
    def download_source_file(self, document_id):
        source_file_path = self.get_source_file_path(document_id)
        return download_file(source_file_path)


    def mt_pre_process(self,document_id):
        doc = DocumentToFile.get_object(document_id)
        task = doc.task_set.first()
        segments = doc.segments_for_workspace.filter(seg_mt_raw__isnull=True)
        split_segments = SplitSegment.objects.filter(text_unit__document=doc).filter(mt_raw_split_segment__isnull=True)
        final_segments = list(chain(segments, split_segments))
        print("Fs---------->",final_segments)
        if final_segments:
            cel = mt_raw_update.apply_async((task.id,))
            if cel:
                return {'status':False,'celery_id':cel.id}
        else:
            return {'status':True}

    #For Downloading Audio File################only for voice project###########Need to work
    def download_audio_file(self,document_user,document_id,voice_gender,language_locale,voice_name):
        res_1 = process_audio_file(document_user,document_id,voice_gender,language_locale,voice_name)
        if res_1:
            return Response(res_1,status=401)
        else:
            doc = DocumentToFile.get_object(document_id)
            task = doc.task_set.first()
            return download_file(task.task_transcript_details.last().translated_audio_file.path)

    # FOR DOWNLOADING BILINGUAL FILE
    def remove_tags(self, string):
        if string!=None:
            return re.sub(rf'</?\d+>', "", string)
        else:return string
        # return string

    def get_bilingual_filename(self, document_id):
        doc = DocumentToFile.get_object(document_id)
        task = doc.task_set.first()
        ser = TaskSerializer(task)
        task_data = ser.data

        pre, ext = os.path.splitext(self.get_source_file_path(document_id).split('source/')[1])

        return task_data['source_language'], task_data['target_language'], pre

    def download_bilingual_file(self, document_id):

        source_lang, target_lang, filename = self.get_bilingual_filename(document_id)

        bilingual_file_path = self.get_source_file_path(document_id).split('source/')[0] + 'source/' + filename + "_bl_" + \
                                "(" + source_lang + "-" + target_lang + ")" + ".xlsx"

        workbook = xlsxwriter.Workbook(bilingual_file_path)
        worksheet = workbook.add_worksheet(source_lang + '-' + target_lang)

        title_format = workbook.add_format(bl_title_format)
        cell_format = workbook.add_format(bl_cell_format)
        worksheet.set_column('A:B', 100, cell_format)

        worksheet.write('A1', 'Source language' + '(' + source_lang + ')', title_format)
        worksheet.write('B1', 'Target language' + '(' + target_lang + ')', title_format)

        row = 1

        text_units = TextUnit.objects.filter(document_id=document_id)

        for text_unit in text_units:
            segments = Segment.objects.filter(text_unit_id=text_unit.id)
            for segment in segments:
                # If the segment is merged
                if segment.is_merged:
                    if not segment.is_merge_start:
                        continue
                    else:
                        segment_new = segment.get_active_object()
                        worksheet.write(row, 0, segment_new.source.strip(), cell_format)
                        worksheet.write(row, 1, self.remove_tags(segment_new.target), cell_format)
                        row += 1
                # If the segment is split
                elif segment.is_split:
                    split_segs = SplitSegment.objects.filter(segment_id=segment.id)
                    target = ""
                    for split_seg in split_segs:
                        if split_seg.target:
                            target += self.remove_tags(split_seg.target)
                    worksheet.write(row, 0, segment.source.strip(), cell_format)
                    worksheet.write(row, 1, target, cell_format)
                    row += 1
                # For normal segments
                else:
                    worksheet.write(row, 0, segment.source.strip(), cell_format)
                    worksheet.write(row, 1, self.remove_tags(segment.target), cell_format)
                    row += 1
        workbook.close()

        return download_file(bilingual_file_path)


    def get(self, request, document_id):
        doc = DocumentToFile.get_object(document_id)
        authorize(request, resource=doc, actor=request.user, action="download")
        # Incomplete segments in db
        segment_count = Segment.objects.filter(text_unit__document=document_id).count()
        if Document.objects.get(id=document_id).total_segment_count != segment_count:
            return JsonResponse({"msg": "File under process. Please wait a little while. \
                    Hit refresh and try again"}, status=400)

        output_type = request.GET.get("output_type", "")
        voice_gender = request.GET.get("voice_gender", "FEMALE")
        voice_name = request.GET.get("voice_name",None)
        language_locale = request.GET.get("locale", None)

        document_user = AiUser.objects.get(project__project_jobs_set__file_job_set=document_id)
        try:managers = document_user.team.get_project_manager if document_user.team.get_project_manager else []
        except:managers = []

        if (request.user ==  document_user) or (request.user in managers):


            # FOR DOWNLOADING SOURCE FILE
            if output_type == "SOURCE":
                return self.download_source_file(document_id)

            # FOR DOWNLOADING BILINGUAL FILE
            if output_type == "BILINGUAL":
                return self.download_bilingual_file(document_id)


            # For Downloading Audio File
            if output_type == "AUDIO":
                #res = self.document_data_to_file(request, document_id)
                return self.download_audio_file(document_user,document_id,voice_gender,language_locale,voice_name)

            if output_type == "MTRAW":
                mt_process = self.mt_pre_process(document_id)
                print("In write--------->",mt_process.get('status'))
                if mt_process.get('status') == True:
                    res = self.document_data_to_file(request,document_id,True)
                else:
                    return Response({'msg':'Conversion is going on.Please wait',"celery_id":mt_process.get('celery_id')},status=400)
            else:
                res = self.document_data_to_file(request, document_id)
            if res.status_code in [200, 201]:
                file_path = res.text
                try:
                    if os.path.isfile(res.text):
                        if os.path.exists(file_path):
                            return self.get_file_response(file_path)
                except Exception as e:
                    print("Exception during file output------> ", e)
            else:
                logger.info(f">>>>>>>> Error in output for document_id -> {document_id}<<<<<<<<<")
                return JsonResponse({"msg": "Sorry! Something went wrong with file processing."},\
                            status=409)
        else:
            return JsonResponse({"msg": "Unauthorised"}, status=401)

    @staticmethod
    def document_data_to_file(request, document_id,mt_raw=None):
        output_type = request.GET.get("output_type", "")
        document = DocumentToFile.get_object(document_id)
        doc_serlzr = DocumentSerializerV3(document)
        data = doc_serlzr.data
        if mt_raw == True:
            data = mt_raw_pre_process(data)
        else:
            data = pre_process(data)
        print("Data--------------->",data)
        if 'fileProcessed' not in data:
            data['fileProcessed'] = True
        if 'numberOfWords' not in data: # we can remove this duplicate field in future
            data['numberOfWords'] = 0
        task = document.task_set.first()
        ser = TaskSerializer(task)
        task_data = ser.data
        print("TT------------->",task_data)
        DocumentViewByTask.correct_fields(task_data)
        output_type = output_type if output_type in OUTPUT_TYPES else "ORIGINAL"

        pre, ext = os.path.splitext(task_data["output_file_path"])
        ext = ".xliff" if output_type == "XLIFF" else \
            (".tmx" if output_type == "TMX" else ext)

        task_data["output_file_path"] = pre + "(" + task_data["source_language"] + \
                "-" + task_data["target_language"] + ")" + ext

        params_data = {**task_data, "output_type": output_type}

        res_paths = get_res_path(task_data["source_language"])

        print("data---------->",json.dumps(data))
        with open("sample.json", "w") as outfile:
            outfile.write(json.dumps(data))
        print("req_res_params--------->",json.dumps(res_paths))
        print('req_params------>',json.dumps(params_data))

        res = requests.post(
            f'http://{spring_host}:8080/getTranslatedAsFile/',
            data={
                'document-json-dump': json.dumps(data),
                "doc_req_res_params": json.dumps(res_paths),
                "doc_req_params": json.dumps(params_data),})

        if settings.USE_SPACES:

            with open(task_data["output_file_path"], "rb") as f:
                SpacesService.put_object(output_file_path=File
                                        .get_aws_file_path(task_data["output_file_path"]), f_stream=f)
        return res

OUTPUT_TYPES = dict(
    ORIGINAL = "ORIGINAL",
    XLIFF = "XLIFF",
    TMX = "TMX",
    SOURCE = "SOURCE",
    BILINGUAL = "BILINGUAL",
    AUDIO = "AUDIO",
)

def output_types(request):
    return JsonResponse(OUTPUT_TYPES, safe=False)

class TranslationStatusList(views.APIView):
    def get(self, request):
        qs = TranslationStatus.objects.all()
        ser = TranslationStatusSerializer(qs, many=True)
        return Response(ser.data, status=200)

class SourceSegmentsListView(viewsets.ViewSet, PageNumberPagination):
    PAGE_SIZE = page_size = 20
    lookup_field = "source"
    page_size_query_param = 'page_size'

    @staticmethod
    def prepare_data(data):
        for i in data:
            try: data[i] = json.loads(data[i])
            except: pass
        return data

    @staticmethod
    def do_search(data, segments, lookup_field):

        status_list = status_list = data.get("status_list", [])

        if status_list:
            if 0 in status_list:
                segments = segments.filter(Q(status=None) | \
                        Q(status__status_id__in=status_list)).all()
            else:
                segments = segments.filter(status__status_id__in=status_list).all()

        search_word = data.get("search_word", None)

        if search_word not in [None, '']:

            match_case = data.get("match_case", False)
            exact_word = data.get("exact_word", False)

            if match_case and exact_word:
                segments = segments.filter(**{f'{lookup_field}'
                    f'__regex':f'(?<!\w){search_word}(?!\w)'})
            elif not(match_case or exact_word):
                segments = segments.filter(**{f'{lookup_field}'
                    f'__icontains':f'{search_word}'})
            elif match_case:
                segments = segments.filter(**{f'{lookup_field}'
                    f'__regex':f'{search_word}'})
            elif exact_word:
                # segments = segments.filter(**{f'{lookup_field}__regex':f'(?<!\w)(?i){search_word}(?!\w)'})
                segments = segments.filter(**{f'{lookup_field}'
                    f'__regex':f'(?i)[^\w]{search_word}[^\w]'})  # temp regex

        return segments

    @staticmethod
    def get_queryset(request, data, document_id, lookup_field):
        qs = Document.objects.all()
        document = get_object_or_404(qs, id=document_id)

        # Getting different segment type querysets
        segments = document.segments_for_find_and_replace
        merge_segments = MergeSegment.objects.filter(text_unit__document=document_id)
        split_segments = SplitSegment.objects.filter(text_unit__document=document_id)
        # Getting the search querysets for each type of segment
        segments = SourceSegmentsListView.do_search(data, segments, lookup_field)
        merge_segments = SourceSegmentsListView.do_search(data, merge_segments, lookup_field)
        split_segments = SourceSegmentsListView.do_search(data, split_segments, lookup_field)
        final_segments = list(chain(segments, merge_segments, split_segments))
        return final_segments, 200

    def post(self, request, document_id):
        data = self.prepare_data(request.POST.dict())
        segments, status = self.get_queryset(request, data, document_id, self.lookup_field)
        page_len = self.paginate_queryset(range(1, len(segments) + 1), request)
        page_segments = self.paginate_queryset(segments, request, view=self)
        segments_ser = SegmentSerializer(page_segments, many=True)

        # data = [SegmentSerializer(MergeSegment.objects.get(id=i.get("segment_id"))).data
        #         if (i.get("is_merged") == True and i.get("is_merge_start")) else i for i in segments_ser.data]
        #
    
        [i.update({"segment_count": j}) for i, j in zip(segments_ser.data, page_len)]

        res = self.get_paginated_response(segments_ser.data)
        #res = segments_ser.data
        res.status_code = status
        return res

class TargetSegmentsListAndUpdateView(SourceSegmentsListView):
    lookup_field = "temp_target"

    @staticmethod
    def unconfirm_status(segment):
        segment.status_id = {102:101, 104:103, 106:105, 110:109}.get(
            segment.status_id, segment.status_id)

    @staticmethod
    def confirm_status(segment):
        segment.status_id = {101:102, 103:104, 105:106, 109:110}.get(
            segment.status_id, segment.status_id)

    def paginate_response(self, segments, request, status):
        page_len = self.paginate_queryset(range(1, len(segments) + 1), request)
        page_segments = self.paginate_queryset(segments, request, view=self)
        segments_ser = SegmentSerializer(page_segments, many=True)

        # data = [SegmentSerializer(MergeSegment.objects.get(id=i.get("segment_id"))).data
        #         if (i.get("is_merged") == True and i.get("is_merge_start")) else i for i in segments_ser.data]
        #
        [i.update({"segment_count": j}) for i, j in zip(segments_ser.data, page_len)]

        res = self.get_paginated_response(segments_ser.data)

        res.status_code = status
        return res

    def post(self, request, document_id):
        data = self.prepare_data(request.POST.dict())
        segments, status = self.get_queryset(request, data, document_id, self.lookup_field)
        return self.paginate_response(segments, request, status)

    @staticmethod
    def update_segments(request, data, segments, self):
        search_word = data.get('search_word', '')
        replace_word = data.get('replace_word', '')
        match_case = data.get('match_case', False)
        exact_word = data.get('exact_word', False)
        do_confirm = data.get("do_confirm", False)

        if exact_word:
            if match_case:
                regex = re.compile(f'(?<!\w){search_word}(?!\w)')
            else:
                regex = re.compile(f'(?i)(?<!\w){search_word}(?!\w)')
                #regex = re.compile(f'(?i)[^\w]{search_word}[^\w]')  # temp regex
        else:
            if match_case:
                regex = re.compile(search_word)
            else:
                regex = re.compile(r'((?i)' + search_word + r')')

        for instance in segments:
            # if type(instance) is MergeSegment:
            #     instance = instance
            # elif type(instance) is SplitSegment:
            #     instance = instance
            # else:
            #     instance = instance.get_active_object()
            self.unconfirm_status(instance)
            if do_confirm:
                self.confirm_status(instance)
                segment_serlzr = SegmentSerializerV2(instance, data={"target":\
                    re.sub(regex, replace_word, instance.temp_target), "status_id": instance.status_id},\
                    partial=True, context={"request": request})
            else:
                self.unconfirm_status(instance)
                segment_serlzr = SegmentSerializerV2(instance, data={"temp_target":\
                    re.sub(regex, replace_word, instance.temp_target), "status_id": instance.status_id},\
                    partial=True, context={"request": request})

            if segment_serlzr.is_valid(raise_exception=True):
                segment_serlzr.save()

        return segments, 200

    def update(self, request, document_id):
        data = self.prepare_data(request.POST.dict())
        segments, status = self.get_queryset(request, data, document_id, self.lookup_field)
        segments, status = self.update_segments(request, data, segments, self=self)
        return self.paginate_response(segments, request, status)

# class FindAndReplaceTargetBySegment(TargetSegmentsListAndUpdateView):
#
#     @staticmethod
#     def get_object(segment_id):
#         segments = Segment.objects.all()
#         obj = get_object_or_404(segments, id=segment_id)
#         return  obj
#
#     def put(self, request, segment_id):
#         segment = self.get_object(segment_id)
#         data = self.prepare_data(request.POST.dict())
#         search_word = data.get('search_word', '')
#         replace_word = data.get('replace_word', '')
#         match_case = data.get('match_case', False)
#         exact_word = data.get('exact_word', False)
#         do_confirm = data.get("do_confirm", False)
#
#         if exact_word:
#             if match_case:
#                 regex = re.compile(f'(?<!\w){search_word}(?!\w)')
#             else:
#                 # regex = re.compile(f'(?<!\w)(?i){search_word}(?!\w)')
#                 regex = re.compile(f'(?i)[^\w]{search_word}[^\w]')  # temp regex
#
#         else:
#             if match_case:
#                 regex = re.compile(search_word)
#             else:
#                 regex = re.compile(r'((?i)' + search_word + r')')
#
#         segment.temp_target = re.sub(regex, replace_word, segment.temp_target)
#         self.unconfirm_status(segment)
#         if do_confirm:
#             segment.target = segment.temp_target
#             self.confirm_status(segment)
#         segment.save()
#         return  Response(SegmentSerializer(segment).data, status=200)

class ProgressView(views.APIView):
    @staticmethod
    def get_object(document_id):
        document = get_object_or_404(
            Document.objects.all(), id=document_id
        )
        return document

    @staticmethod
    def get_progress(document):

        confirm_list = [102, 104, 106, 110, 107]
        total_seg_count = 0
        confirm_count = 0

        segs = Segment.objects.filter(text_unit__document=document)
        for seg in segs:

            if (seg.is_merged == True and seg.is_merge_start != True):
                continue

            elif seg.is_split == True:
                total_seg_count += 2

            else:
                total_seg_count += 1

            seg_new = seg.get_active_object()

            if seg_new.is_split == True:
                for split_seg in SplitSegment.objects.filter(segment_id=seg_new.id):
                    if split_seg.status_id in confirm_list:
                        confirm_count += 1

            elif seg_new.status_id in confirm_list:
                confirm_count += 1

        return total_seg_count, confirm_count

    def get(self, request, document_id):
        document = self.get_object(document_id)
        authorize(request, resource=document, actor=request.user, action="read")
        total_segment_count, segments_confirmed_count = self.get_progress(document)
        return JsonResponse(
            dict(total_segment_count=total_segment_count,
                 segments_confirmed_count=segments_confirmed_count), safe=False
        )


# class SegmentSizeView(viewsets.ViewSet):
#     permission_classes = [IsAuthenticated]
    
#     def list(self, request):
#         print("$$$$")
#         obj = SegmentPageSize.objects.filter(ai_user_id = request.user.id)
#         ser = FontSizeSerializer(obj, many=True)
#         return Response(ser.data, status=200)

#     def create(self,request):
        # obj = SegmentPageSize.objects.filter(ai_user_id = request.user.id)
        # if obj is not None:
        #     obj.update({'page_size':request.POST.get('page_size')})
        # else:
        #     ser = SegmentPageSizeSerializer(data={**request.POST.dict(), "ai_user": request.user.id})
        #     if ser.is_valid(raise_exception=True):
        #         ser.save()
        #         return Response(ser.data)
        #     return Response(ser.errors)
        # return Response({'page_size':obj.page_size})

class SegmentSizeView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def list(self,request):
        try:
            queryset = SegmentPageSize.objects.get(ai_user_id = request.user.id)
            serializer = SegmentPageSizeSerializer(queryset)
            return Response(serializer.data)
        except:
            return Response({'page_size':None})

    def create(self,request):
        obj = SegmentPageSize.objects.filter(ai_user_id = request.user.id)
        if obj:
            obj.update(page_size = request.POST.get('size'))
        else:
            ser = SegmentPageSizeSerializer(data={'page_size':request.POST.get('size'), "ai_user": request.user.id})
            if ser.is_valid(raise_exception=True):
                ser.save()
                return Response(ser.data)
            return Response(ser.errors)
        return Response({'page_size':obj.last().page_size})

    def update(self,request,pk):
        pass

    def delete(self,request,pk):
        pass





class FontSizeView(views.APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get_object(data, request):
        obj = FontSize.objects.filter(ai_user_id=request.user.id, language_id=data.get("language", None)).first()
        ## need to add authorize if non owner user use this  
        return  obj

    def post(self, request):
        obj = self.get_object(request.POST.dict(), request)
        if obj is not None:
            ser = FontSizeSerializer(instance=obj, data={**request.POST.dict(), "ai_user": request.user.id})
            status = 202

        else:
            ser = FontSizeSerializer(data={**request.POST.dict(), "ai_user": request.user.id})
            status = 201

        if ser.is_valid(raise_exception=True):
            ser.save()
            return Response(ser.data, status=status)

    def get(self, request):
        try:
            source_id = int(request.GET.get('source', '0'))
            target_id = int(request.GET.get('target', '0'))
        except:
            return JsonResponse({"msg": "input data is wrong"}, status=422)
        objs = FontSize.objects.filter(ai_user=request.user).filter(
            language_id__in=[source_id, target_id]
        ).all()
        ser = FontSizeSerializer(objs, many=True)
        return Response(ser.data, status=200)


class CommentView(viewsets.ViewSet):
    @staticmethod
    def get_object(comment_id):
        qs = Comment.objects.all()
        obj = get_object_or_404(qs, id=comment_id)
        return obj

    @staticmethod
    def get_list_of_objects(request):
        by = request.GET.get("by", "")
        id = request.GET.get("id", 0)

        try:id=int(id)
        except:id=0

        if by=="segment":
            if split_check(id):
                print("normal")
                segment = get_object_or_404(Segment.objects.all(), id=id)                
                return segment.segment_comments_set.order_by('id')
            else:
                print("split")
                split_segment = SplitSegment.objects.get(id=id)
                return split_segment.split_segment_comments_set.order_by('id')


        if by=="document":
            document = get_object_or_404(Document.objects.all(), id=id)
            comments_list=[]
            for segment in document.segments.all():
                if segment.is_split!=True:
                    comments_list.extend(segment.segment_comments_set.order_by('id'))
                else:
                    split_seg = SplitSegment.objects.filter(segment_id=segment.id)
                    for i in  split_seg:
                        comments_list.extend(i.split_segment_comments_set.order_by('id'))
            return comments_list

            # return [ comment
            #     for segment in document.segments.all()
            #     for comment in segment.segment_comments_set.all()
            # ]
        return Comment.objects.none()

    def list(self, request):
        objs = self.get_list_of_objects(request)
        print("user",request.user)
        objs = filter_authorize(request, objs, user=request.user, action="read")
        print("objs",objs)
        ser = CommentSerializer(objs, many=True)
        return Response(ser.data, status=200)

    def create(self, request):
        seg = request.POST.get('segment')
        comment = request.POST.get('comment')
        if split_check(seg):
            ser = CommentSerializer(data={**request.POST.dict(), "commented_by": request.user.id} )
        else:
            segment = SplitSegment.objects.filter(id=seg).first().segment_id
            ser = CommentSerializer(data={'segment':segment,'comment':comment,'split_segment':seg,'commented_by':request.user.id})
        if ser.is_valid(raise_exception=True):
            with transaction.atomic():
                ser.save()
                authorize(request, resource=ser.instance, actor=request.user, action="create")
            return Response(ser.data, status=201)

    def retrieve(self, request, pk=None):
        obj = self.get_object(comment_id=pk)
        return Response(CommentSerializer(obj).data, status=200)

    def update(self, request, pk=None):
        obj = self.get_object(comment_id=pk)
        authorize(request, resource=obj, actor=request.user, action="update")
        if obj.commented_by:
            if obj.commented_by == request.user:
                ser = CommentSerializer(obj, data=request.POST.dict(), partial=True)
                if ser.is_valid(raise_exception=True):
                    ser.save()    
                    return Response(ser.data, status=202)
                return Response(ser.errors)
            else:
                return Response({'msg':'You do not have permission to edit'},status=403)
        else:
            ser = CommentSerializer(obj, data=request.POST.dict(), partial=True)
            if ser.is_valid(raise_exception=True):
                ser.save()    
                return Response(ser.data, status=202)
            return Response(ser.errors)

    def destroy(self, request, pk=None):
        obj = self.get_object(comment_id=pk)
        authorize(request, resource=obj, actor=request.user, action="delete")
        if obj.commented_by:
            if obj.commented_by == request.user:
                obj.delete()
                return  Response({},204)
            else:
                return Response({'msg':'You do not have permission to edit'},status=403)
        else:
            obj.delete()
            return  Response({},204)

class GetPageIndexWithFilterApplied(views.APIView):

    def get_queryset(self, seg, status_list):
        if '0' in status_list:
            segments = seg.filter(Q(status=None)|\
                        Q(status__status_id__in=status_list)).all()
        else:
            segments = seg.filter(status__status_id__in=status_list).all()
        return  segments

    def post(self, request, document_id, segment_id):
        status_list = request.data.get("status_list", [])
        page_size = SegmentPageSize.objects.filter(ai_user_id = self.request.user.id).last().page_size
        page_size = page_size if page_size else 20
        doc = get_object_or_404(Document.objects.all(), id=document_id)
        segs = doc.segments_for_find_and_replace
        merge_segments = MergeSegment.objects.filter(text_unit__document=document_id)
        split_segments = SplitSegment.objects.filter(text_unit__document=document_id)
        seg =  self.get_queryset(segs, status_list)
        merge_seg = self.get_queryset(merge_segments, status_list)
        split_seg = self.get_queryset(split_segments, status_list)
        segments = list(chain(seg, merge_seg, split_seg))
        if not segments:
            return Response( {"detail": "No segment found"}, 404 )
        ids = [
            segment.id for segment in segments
        ]
        try:
            res = ({"page_id": (ids.index(segment_id)//page_size)+1}, 200)
        except:
            res = ({"page_id": None}, 404)
        return  Response(*res)

############ wiktionary quick lookup ##################
@api_view(['GET', 'POST',])
def WiktionaryParse(request):
    user_input=request.POST.get("term")
    term_type=request.POST.get("term_type")
    doc_id=request.POST.get("doc_id")
    user_input=user_input.strip()
    user_input=user_input.strip('0123456789')
    doc = Document.objects.get(id=doc_id)
    sourceLanguage=doc.source_language
    targetLanguage=doc.target_language
    if term_type=="source":
        src_lang=sourceLanguage
        tar_lang=targetLanguage
    elif term_type=="target":
        src_lang=targetLanguage
        tar_lang=sourceLanguage
    parser = WiktionaryParser()
    parser.set_default_language(src_lang)
    parser.include_relation('Translations')
    word = parser.fetch(user_input)
    if word:
        if word[0].get('definitions')==[]:
            word=parser.fetch(user_input.lower())
    res=[]
    tar=""
    for i in word:
        defin=i.get("definitions")
        for j,k in enumerate(defin):
            out=[]
            pos=k.get("partOfSpeech")
            text=k.get("text")
            rel=k.get('relatedWords')
            # for n in rel:
            #     if n.get('relationshipType')=='translations':
            #         for l in n.get('words'):
            #             if tar_lang in l:
            #                 tar=l
            out=[{'pos':pos,'definitions':text,'target':tar}]
            res.extend(out)

    return JsonResponse({"Output":res},safe=False)


def wikipedia_ws(code,codesrc,user_input):
    S = requests.Session()
    URL = f"https://{codesrc}.wikipedia.org/w/api.php"
    PARAMS = {
        "action": "query",
        "format": "json",
        "prop": "langlinks",
        "llinlanguagecode":codesrc,
        "titles": user_input,
        "redirects": 1,
        "llprop": "url",
        "lllang": code,
    }
    R = S.get(url=URL, params=PARAMS)
    DATA = R.json()
    res=DATA["query"]["pages"]
    srcURL=f"https://{codesrc}.wikipedia.org/wiki/{user_input}"
    for i in res:
        lang=DATA["query"]["pages"][i]
        if 'missing' in lang:
            return {"source":'',"target":'',"targeturl":'',"srcURL":''}
    if (lang.get("langlinks"))!=None:
        for j in lang.get("langlinks"):
            output=j.get("*")
            url=j.get("url")
        return {"source":user_input,"target":output,"targeturl":url,"srcURL":srcURL}
    else:
        output=""
    return {"source":user_input,"target":output,"targeturl":"","srcURL":srcURL}




########  Workspace WIKI OPTIONS  ##########################
#WIKIPEDIA
@api_view(['GET',])
# @permission_classes((HasToken,))
def WikipediaWorkspace(request):
    doc_id =request.GET.get('doc_id')
    task_id = request.GET.get('task_id')
    data=request.GET.dict()
    lang_list = ["zh-Hans","zh-Hant"]
    user_input=data.get("term")
    term_type=data.get("term_type","source")
    user_input=user_input.strip()
    user_input=user_input.strip('0123456789')
    if doc_id:
        doc = Document.objects.get(id=doc_id)
        src = doc.source_language_code if doc.source_language_code not in lang_list else "zh"
        tar = doc.target_language_code if doc.target_language_code not in lang_list else "zh"
    if task_id:
        task = Task.objects.get(id=task_id)
        src = task.job.source_language_code if task.job.source_language_code not in lang_list else "zh"
        tar = task.job.target_language_code if task.job.target_language_code not in lang_list else "zh"
    if term_type=="source":
        codesrc = src
        code = tar
    elif term_type=="target":
        codesrc = tar
        code = src
    res=wikipedia_ws(code,codesrc,user_input)
    return JsonResponse({"out":res}, safe = False,json_dumps_params={'ensure_ascii':False})



def wiktionary_ws(code,codesrc,user_input):
    S = requests.Session()
    URL =f" https://{codesrc}.wiktionary.org/w/api.php?"
    PARAMS={
        "action": "query",
        "format": "json",
        "prop": "iwlinks",
        "iwprop": "url",
        "iwprefix":code,
        "titles": user_input,
        "iwlocal":codesrc,
    }
    response = S.get(url=URL, params=PARAMS)
    try:
        data = response.json()
    except JSONDecodeError:
        return {"source":'',"source-url":''}
    srcURL=f"https://{codesrc}.wiktionary.org/wiki/{user_input}"
    res=data["query"]["pages"]
    if "-1" in res:
        PARAMS.update({'titles':user_input.lower()})
        data = S.get(url=URL, params=PARAMS).json()
        srcURL=f"https://{codesrc}.wiktionary.org/wiki/{user_input.lower()}"
        res =data['query']['pages']
    for i in res:
       lang=data["query"]["pages"][i]
       if 'missing' in lang:
           return {"source":'',"source-url":''}
    output=[]
    out=[]
    if (lang.get("iwlinks"))!=None:
         for j in lang.get("iwlinks"):
                out=[{'target':j.get("*"),'target-url':j.get("url")}]
                output.extend(out)
         return {"source":user_input,"source-url":srcURL,"targets":output}
    return {"source":user_input,"source-url":srcURL}

#WIKTIONARY
@api_view(['GET',])
# @permission_classes((HasToken,))
def WiktionaryWorkSpace(request):
    data=request.GET.dict()
    doc_id =request.GET.get('doc_id')
    task_id = request.GET.get('task_id')
    lang_list = ["zh-Hans","zh-Hant"]
    user_input=data.get("term")
    term_type=data.get("term_type")
    user_input=user_input.strip()
    user_input=user_input.strip('0123456789')
    if doc_id:
        doc = Document.objects.get(id=doc_id)
        src = doc.source_language_code if doc.source_language_code not in lang_list else "zh"
        tar = doc.target_language_code if doc.target_language_code not in lang_list else "zh"
    if task_id:
        task = Task.objects.get(id=task_id)
        src = task.job.source_language_code if task.job.source_language_code not in lang_list else "zh"
        tar = task.job.target_language_code if task.job.target_language_code not in lang_list else "zh"
    if term_type=="source":
        codesrc =src
        code = tar
    elif term_type=="target":
        codesrc = tar
        code = src
    res=wiktionary_ws(code,codesrc,user_input)
    return JsonResponse({"out":res}, safe = False, json_dumps_params={'ensure_ascii':False})


######  USING PY SPELLCHECKER  AND HunSpell######
@api_view(['GET', 'POST',])
def spellcheck(request):
    import hunspell
    tar = request.POST.get('target')
    doc_id = request.POST.get('doc_id')
    task_id = request.POST.get('task_id')
    if doc_id:
        doc = Document.objects.get(id=doc_id)
        lang_code = doc.target_language_code
        lang_id = doc.target_language_id
    if task_id:
        task = Task.objects.get(id=task_id)
        lang_code = task.job.target_language_code
        lang_id = task.job.target_language_id
    out,res = [],[]
    try:
        if lang_code == 'en':
            lang = lang_code
            dic = r'/ai_home/dictionaries/{lang}.dic'.format(lang = lang)
            aff = r'/ai_home/dictionaries/{lang}.aff'.format(lang = lang)
            hobj = hunspell.HunSpell(dic,aff )
            punctuation='''!"#$%&'``()*+,-./:;<=>?@[\]^`{|}~_'''
            tknzr = TweetTokenizer()
            nltk_tokens = tknzr.tokenize(tar)
            tokens_new = [word for word in nltk_tokens if word not in punctuation]
            print(tokens_new)
            for word in tokens_new:
                suggestions=[]
                if hobj.spell(word)==False:
                     suggestions.extend(hobj.suggest(word))
                     out=[{"word":word,"Suggested Words":suggestions}]
                     res.extend(out)
            return JsonResponse({"result":res},safe=False)
        else:
            spellchecker=SpellcheckerLanguages.objects.get(language_id=lang_id).spellchecker.spellchecker_name
            if spellchecker=="pyspellchecker":
                code = lang_code
                spell = SpellChecker(code)
                words=spell.split_words(tar)#list
                misspelled=spell.unknown(words)#set
                for word in misspelled:
                    suggestion=list(spell.candidates(word))
                    for k in words:
                        if k==word.capitalize():
                            out=[{"word":k,"Suggested Words":suggestion}]
                            break
                        else:
                            out=[{"word":word,"Suggested Words":suggestion}]
                    res.extend(out)
                return JsonResponse({"result":res},safe=False)
    except:
        return JsonResponse({"message":"Spellcheck not available"},safe=False)


# class MergeSegmentView(viewsets.ModelViewSet):
#     serializer_class = MergeSegmentSerializer
#
#     def create(self, request, *args, **kwargs):
#         print("Request data ---> ", request.data)
#         serlzr = self.serializer_class(data=request.data)
#         if serlzr.is_valid(raise_exception=True):
#             print("Serializer validated data ---> ", serlzr.validated_data)
#             serlzr.save(id=serlzr.validated_data.get("segments")[0].id)
#             obj =  serlzr.instance
#             print("Object ---> ", obj)
#             obj.update_segments(serlzr.validated_data.get("segments"))
#             return Response(MergeSegmentSerializer(obj).data)

# class ProjectDownload(viewsets.ModelViewSet):
#     def get_queryset(self):
#         # limiting queryset for current user
#         qs = Project.objects.filter(ai_user=self.request.user).all()
#         return  qs

#     def get_files_info(self):
#         self.project = project = self.get_object()
#         documents = Document.objects.filter(file__project=project).all()

#         files_info = []
#         for document in documents:
#             res = DocumentToFile.document_data_to_file("", document_id=document.id)
#             if res.status_code == 200:
#                 files_info.append({"file_path":res.text, "file_id": document.file.id,
#                                    "job_id": document.job.id})
#         return files_info

#     def zip(self, request, *args, **kwargs): #get

#         file_paths = [info.get("file_path") for info in self.get_files_info()]
#         response = HttpResponse(content_type='application/zip')
#         # zf = zipfile.ZipFile(response, 'w')
#         with zipfile.ZipFile(response, 'w') as zf:
#             for file_path in file_paths:
#                 with open(file_path, "rb") as f:
#                     zf.writestr(file_path.split("/")[-1], f.read())

#         response['Content-Disposition'] = f'attachment; filename={self.project.project_name}.zip'

#         return response

#     def push_to_repo(self, request, *args, **kwargs):#post
#         files_info = self.get_files_info()
#         dc = DownloadController.objects.filter(project=self.project).first()
#         if dc :
#             try:
#                 dc.get_download .download(project=self.project, files_info=files_info)
#                 return Response({"message": "Successfully pushed to repository!!!"}, status=200)
#             except Exception as e:
#                 print("errror--->", e)
#                 return Response({"message": "Something went to wrong!!!"},status=500)
#         return Response({"message": "There is no documnent to push!!!"}, status=204)

############################segment history#############################################
@api_view(['GET',])
def get_segment_history(request):
    seg_id = request.GET.get('segment')
    try:
        if split_check(seg_id):
            obj = Segment.objects.get(id=seg_id)
            history = obj.segment_history.all().order_by('-id') 
        else:
            obj = SplitSegment.objects.filter(id=seg_id).first()
            history = obj.split_segment_history.all().order_by('-id') 
        #obj = Segment.objects.get(id=seg_id)
        #history = obj.segment_history.all().order_by('-id') 
        ser = SegmentHistorySerializer(history,many=True)
        data_ser=ser.data
        data=[i for i in data_ser if dict(i)['segment_difference']]
        return Response(data)
    except Segment.DoesNotExist:
        return Response({'msg':'Not found'}, status=404)






def get_src_tags(sent):
    opening_tags = re.findall(r"<(\d+)>", sent)
    closing_tags = re.findall(r"</(\d+)>", sent)

    opening_result = ''.join([f"<{tag}>" for tag in opening_tags])
    closing_result = ''.join([f"</{tag}>" for tag in closing_tags])

    result = opening_result + closing_result

    print("Combined result:", result)

    return result

from ai_workspace.api_views import get_consumable_credits_for_text
from ai_openai.utils import get_prompt_chatgpt_turbo
from .utils import get_prompt
from ai_openai.serializers import openai_token_usage ,get_consumable_credits_for_openai_text_generator

@api_view(['POST',])############### only available for english ###################
def paraphrasing_for_non_english(request):
    from ai_staff.models import Languages
    from ai_workspace.api_views import get_consumable_credits_for_text
    from ai_openai.utils import get_prompt_chatgpt_turbo,get_consumable_credits_for_openai_text_generator
    sentence = request.POST.get('source_sent')
    target_lang_id = request.POST.get('target_lang_id')
    doc_id = request.POST.get('doc_id')
    option = request.POST.get('option')
    doc_obj = Document.objects.get(id=doc_id)
    project = doc_obj.job.project
    user = doc_obj.doc_credit_debit_user
    #subj_fields =  [i.subject.name for i in project.proj_subject.all()]
    #content_fields = [i.content_type.name for i in project.proj_content_type.all()]
    target_lang = Languages.objects.get(id=target_lang_id).locale.first().locale_code
    
    initial_credit = user.credit_balance.get("total_left")
    if initial_credit == 0:
        return  Response({'msg':'Insufficient Credits'},status=400)
    
    tags = get_src_tags(sentence) 
    clean_sentence = re.sub('<[^<]+?>', '', sentence)
    consumable_credits_user_text =  get_consumable_credits_for_text(clean_sentence,source_lang='en',target_lang=None)
    if initial_credit >= consumable_credits_user_text:
        prompt = get_prompt(option,clean_sentence)#,subj_fields,content_fields) 
        print("Pr--------------->",prompt)
        result_prompt = get_prompt_chatgpt_turbo(prompt,n=1)
        print("Resp--------->",result_prompt)
        para_sentence = result_prompt["choices"][0]["message"]["content"]
        #para_sentence = re.search(r'(?:.*:\s*)?(.*)$', result).group(1).strip()
        consumable_credits_to_translate = get_consumable_credits_for_text(para_sentence,source_lang='en',target_lang=target_lang)
        if initial_credit >= consumable_credits_to_translate:
            rewrited =  get_translation(1, para_sentence, 'en',target_lang,user_id=user.id,cc=consumable_credits_to_translate)
        else:
            return  Response({'msg':'Insufficient Credits'},status=400)
        prompt_usage = result_prompt['usage']
        total_token = prompt_usage['total_tokens']
        consumed_credits = get_consumable_credits_for_openai_text_generator(total_token)
        debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumed_credits)
        print("Tsg------->",tags)
        return Response({'result':rewrited ,'tag':tags})
    else:
        return  Response({'msg':'Insufficient Credits'},status=400)




####################################################### Hemanth #########################################################

# @api_view(['POST',])############### only available for english ###################
# def paraphrasing(request):

from ai_workspace.api_views import get_consumable_credits_for_text
from ai_openai.utils import get_prompt_chatgpt_turbo
from ai_openai.serializers import openai_token_usage ,get_consumable_credits_for_openai_text_generator
from .utils import get_general_prompt

@api_view(['POST',])############### only available for english ###################
def paraphrasing(request):
    from ai_workspace.api_views import get_consumable_credits_for_text
    from ai_openai.utils import get_prompt_chatgpt_turbo,get_consumable_credits_for_openai_text_generator
    sentence = request.POST.get('sentence')
    doc_id = request.POST.get('doc_id')
    option = request.POST.get('option')
    doc_obj = Document.objects.get(id=doc_id)
    user = doc_obj.doc_credit_debit_user
    #user = request.user.team.owner if request.user.team else request.user ##Need to revise this and this must be changed to doc_debit user
    initial_credit = user.credit_balance.get("total_left")
    if initial_credit == 0:
        return  Response({'msg':'Insufficient Credits'},status=400)
    
    tags = get_src_tags(sentence)
    clean_sentence = re.sub('<[^<]+?>', '', sentence)
    consumable_credits_user_text =  get_consumable_credits_for_text(clean_sentence,source_lang='en',target_lang=None)
    if initial_credit >= consumable_credits_user_text:
        prompt = get_general_prompt(option,clean_sentence)
        print("Prompt------------->",prompt)
        result_prompt = get_prompt_chatgpt_turbo(prompt,n=1)
        para_sentence = result_prompt["choices"][0]["message"]["content"]#.split('\n')
        prompt_usage = result_prompt['usage']
        total_token = prompt_usage['completion_tokens']
        consumed_credits = get_consumable_credits_for_openai_text_generator(total_token)
        debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumed_credits)
        print("tag-->",tags)
        return Response({'result':para_sentence ,'tag':tags})
    else:
        return  Response({'msg':'Insufficient Credits'},status=400)

# @api_view(['POST',])############### only available for english ###################
# def paraphrasing(request):
#     sentence = request.POST.get('sentence')
#     try:
#         text = {}
#         text['sentence'] = sentence
#         end_pts = settings.END_POINT +"paraphrase/"
#         data = requests.post(end_pts , text)
#         return JsonResponse(data.json())
#     except:
#         return JsonResponse({"message":"error in paraphrasing connect"},safe=False)



@api_view(['POST',])############### only available for english ###################
def synonmys_lookup(request):
    if request.method == "POST":
        try:
            data = {}
            txt = request.POST["text"]
            end_pts = settings.END_POINT +"synonyms/"
            data['text'] = txt
            result = requests.post(end_pts , data )
            serialize = VerbSerializer(result.json())
            return JsonResponse(serialize.data)
        except:
            return JsonResponse({"message":"error in synonmys"},safe=False)



@api_view(['POST',])############### only available for english ###################
def grammar_check_model(request):
    text = request.POST.get('target')
    data = {}
    data['text'] = text
    end_pts = settings.END_POINT +"grammar-checker/"
    result = requests.post(end_pts , data )
    try:return JsonResponse(result.json())
    except:return JsonResponse({'msg':'something went wrong'})


@api_view(['POST',])############### only available for english ###################
def get_word_api(request):
    text = request.POST.get('word')
    sentence = request.POST.get('sentence')
    second_word = request.POST.get('second_word')
    data = {}
    data['word'] = text
    data['sentence'] = sentence
    data['second_word'] =second_word
    end_pts = settings.END_POINT +"wordsapi_synonyms/"
    result = requests.post(end_pts , data )
    try:return JsonResponse(result.json())
    except:return JsonResponse({'msg':'something went wrong'})

from ai_workspace_okapi.models import SelflearningAsset,SegmentHistory,SegmentDiff



# headers = {
#     "X-RapidAPI-Key": os.getenv("X-RapidAPI-Key"),
#     "X-RapidAPI-Host":  os.getenv("X-RapidAPI-Host")
# }
#
# class WordApiView(viewsets.ViewSet):
#     def lemma_word(self,text):
#         import spacy
#         nlp = spacy.load("en_core_web_sm")
#         text  = nlp(text)
#         return [i.lemma_ for i in text][0]
#
#
#     def wordsapi_request(self,text):
#         url = "https://wordsapiv1.p.rapidapi.com/words/{synonyms_request}".format(synonyms_request = text)
#         response = requests.request("GET", url, headers=headers)
#         return response
#
#
#     def create_syn_list(self,data):
#         data =data.json()
#         syn = []
#         if 'success' in data.keys():
#             data =  "no synonmys"
#             return data
#         if data.get('results'):
#             for i in data.get('results'):
#                 if 'synonyms' in i.keys():
#                     syn.extend(i['synonyms'])
#                     syn = syn[:10]
#         return syn
#
#
#     def create(self,request):
#         word = request.POST.get('word')
#         context = {}
#         context['word'] = word
#         response =self.wordsapi_request(word)
#         data = self.create_syn_list(response)
#         if len(data)==0:
#             word = self.lemma_word(word)
#             response =self.wordsapi_request(word)
#             data = self.create_syn_list(response)
#             if len(data) == 0:
#                 data = "Not Available"
#                 context['synonyms'] = data
#                 return JsonResponse({'context':context})
#         context['synonyms'] = data
#         return JsonResponse({'context':context})

# def mt_only(project,request):
#     token = str(request.auth)
#     print(token)
#     if project.pre_translate == True:
#         headers = {'Authorization':'Bearer '+token}
#         print(headers)
#         tasks = project.get_mtpe_tasks
#         for i in project.get_mtpe_tasks:
#             url = f"http://localhost:8089/workspace_okapi/document/{i.id}"
#             res = requests.request("GET", url, headers=headers)
#     print("doc--->",res.text)

#################################################################################################################################

@api_view(['GET',])
@permission_classes([IsAuthenticated])
def download_audio_output_file(request):
    from ai_workspace.models import MTonlytaskCeleryStatus
    celery_id = request.GET.get('celery_id')
    document_id = request.GET.get('document_id')
    doc = Document.objects.get(id=document_id)
    task = doc.task_set.first()
    user_credit = UserCredits.objects.get(Q(user=doc.doc_credit_debit_user) & Q(credit_pack_type__icontains="Subscription") & Q(ended_at=None))
    cel_task = MTonlytaskCeleryStatus.objects.filter(task = doc.task_set.first()).last()
    state = google_long_text_file_process_cel.AsyncResult(cel_task.celery_task_id).state
    if state == 'SUCCESS':
        return download_file(task.task_transcript_details.last().translated_audio_file.path)
    elif state == 'FAILURE':
        source_file_path = File.objects.get(file_document_set=doc).get_source_file_path
        filename, ext = os.path.splitext(source_file_path.split('source/')[1])
        temp_name = filename + '.txt'
        text_file = open(temp_name, "r")
        data = text_file.read()
        consumable_credits = get_consumable_credits_for_text_to_speech(len(data))
        user_credit.credits_left = user_credit.credits_left + consumable_credits
        user_credit.save()
        return Response({'msg':'Failure'},status=400)
    else:
        return Response({'msg':'Pending'},status=400)

@api_view(['GET',])
@permission_classes([IsAuthenticated])
def download_mt_file(request):
    from ai_workspace.models import MTonlytaskCeleryStatus
    celery_id = request.GET.get('celery_id')
    document_id = request.GET.get('document_id')
    doc = Document.objects.get(id=document_id)
    task = doc.task_set.first()
    #user_credit = UserCredits.objects.get(Q(user=doc.doc_credit_debit_user) & Q(credit_pack_type__icontains="Subscription") & Q(ended_at=None))
    cel_task = MTonlytaskCeleryStatus.objects.filter(task = doc.task_set.first(),task_name='mt_raw_update').last()
    print("YY----->",cel_task)
    state = mt_raw_update.AsyncResult(cel_task.celery_task_id).state
    print("st------>",state)
    if state == 'SUCCESS':
        #if cel_task.error_type == 'Insufficient Credits':
        #    return Response({'msg':'Insufficient Credits'},status=400)
        doc_to_file = DocumentToFile()
        res = doc_to_file.document_data_to_file(request,document_id,True)
        if res.status_code in [200, 201]:
            file_path = res.text
            try:
                if os.path.isfile(res.text):
                    if os.path.exists(file_path):
                        return doc_to_file.get_file_response(file_path)
            except Exception as e:
                print("Exception during file output------> ", e)
        else:
            logger.info(f">>>>>>>> Error in output for document_id -> {document_id}<<<<<<<<<")
            return JsonResponse({"msg": "Sorry! Something went wrong with file processing."},\
                        status=409)
    elif state == 'FAILURE':
        return Response({'msg':'Failure','task':task.id},status=400)
    else:
        return Response({'msg':'Pending','task':task.id},status=400)


@api_view(['GET',])
@permission_classes([IsAuthenticated])
def download_converted_audio_file(request):
    document_id = request.GET.get('document_id')
    doc = Document.objects.get(id=document_id)
    task = doc.task_set.first()
    return download_file(task.task_transcript_details.last().translated_audio_file.path)



def process_audio_file(document_user,document_id,voice_gender,language_locale,voice_name):
    from ai_workspace.models import MTonlytaskCeleryStatus
    temp_name = segments_with_target(document_id)
    doc = Document.objects.get(id = document_id)
    source_file_path = File.objects.get(file_document_set=doc).get_source_file_path
    filename, ext = os.path.splitext(source_file_path.split('source/')[1])
    file_path = temp_name
    task = doc.task_set.first()
    ser = TaskSerializer(task)
    task_data = ser.data
    target_language = language_locale if language_locale else task_data["target_language"]
    source_lang = task_data['source_language']
    text_file = open(temp_name, "r")
    data = text_file.read()
    text_file.close()
    print(len(data))
    consumable_credits = get_consumable_credits_for_text_to_speech(len(data))
    initial_credit = document_user.credit_balance.get("total_left")#########need to update owner account######
    print("Init------>",initial_credit)
    print("Cons----->",consumable_credits)
    if initial_credit > consumable_credits:
        if len(data.encode("utf8"))>4500:
            celery_task = google_long_text_file_process_cel.apply_async((consumable_credits,document_user.id,file_path,task.id,target_language,voice_gender,voice_name), )
            MTonlytaskCeleryStatus.objects.create(task_id=task.id,task_name='google_long_text_file_process_cel',celery_task_id=celery_task.id)
            debit_status, status_code = UpdateTaskCreditStatus.update_credits(document_user, consumable_credits)
            return {'msg':'Conversion is going on.Please wait',"celery_id":celery_task.id}
            #celery_task = google_long_text_file_process_cel(file_path,task.id,target_language,voice_gender,voice_name)
            #res1,f2 = google_long_text_file_process(file_path,task,target_language,voice_gender,voice_name)
        else:
            filename_ = filename + "_"+ task.ai_taskid+ "_out" + "_" + source_lang + "-" + target_language + ".mp3"
            res1,f2 = text_to_speech(file_path,target_language,filename_,voice_gender,voice_name)
            debit_status, status_code = UpdateTaskCreditStatus.update_credits(document_user, consumable_credits)
            os.remove(filename_)
            os.remove(temp_name)
        
        if task.task_transcript_details.first()==None:
            ser = TaskTranscriptDetailSerializer(data={"translated_audio_file":res1,"task":task.id})
        else:
            t = task.task_transcript_details.first()
            ser = TaskTranscriptDetailSerializer(t,data={"translated_audio_file":res1,"task":task.id},partial=True)
        if ser.is_valid():
            ser.save()
        print(ser.errors)
        f2.close()
        print("Done")
    else:
        return {"msg":"Insufficient credits to convert text file to audio file"}


def remove_tags(string):
    return re.sub(rf'</?\d+>', "", string)

def segments_with_target(document_id):

    document = Document.objects.get(id=document_id)
    segments = document.segments_for_workspace
    segments_ser = SegmentSerializer(segments, many=True)
    source_file_path = File.objects.get(file_document_set=document).get_source_file_path
    filename, ext = os.path.splitext(source_file_path.split('source/')[1])
    temp_name = filename + '.txt'
    counter = 0
    data = []
    limit = 4000 #if document.target_language_code in ['ta','ja'] else 3500

    for i in segments_ser.data:
        # If the segment is merged
        if (i.get("is_merged") == True and i.get("is_merge_start")):
            merge_obj = MergeSegment.objects.get(id=i.get("segment_id"))
            if merge_obj.target!=None:
                data.append(remove_tags(merge_obj.target))

        # If the segment is split
        elif i.get("is_split") == True:
            split_segs = SplitSegment.objects.filter(segment_id=i.get("segment_id")).order_by("id")
            for split_seg in split_segs:
                if split_seg.target!=None:
                    data.append(remove_tags(split_seg.target))

        # Normal segment
        else:
            if i.get('target')!=None:
                data.append(remove_tags(i.get('target')))

    #print("############",data)

    with open(temp_name, "w") as out:
        for i in data:
            counter = counter + len(i.encode("utf8"))
            out.write(' '+i)
            if counter>limit:
                out.write('\n')
                counter = 0

    return temp_name


def remove_random_tags(string, random_tag_list):
    if not random_tag_list:
        return string
    for id in random_tag_list:
        string = re.sub(fr'</?{id}>', "", string)
    return string


def get_tags(seg):
    random_tags = json.loads(seg.random_tag_ids)
    if random_tags == []:
        tags = seg.target_tags
    else:
        tags = remove_random_tags(seg.target_tags,random_tags)
    return tags


from ai_workspace_okapi.serializers import SegmentDiffSerializer,SelflearningAssetSerializer
from django.http import Http404
from ai_staff.models import Languages
from ai_workspace_okapi.models import SelflearningAsset,SegmentHistory,SegmentDiff
from ai_workspace_okapi.utils import do_compare_sentence
from django.db.models.signals import post_save 

# class SelflearningAssetViewset(viewsets.ViewSet):
#     permission_classes = [IsAuthenticated,]
#     def get_object(self, pk):
#         try:
#             return SelflearningAsset.objects.get(id=pk)
#         except SelflearningAsset.DoesNotExist:
#             raise Http404

#     def create(self,request):
#         serializer = SelflearningAssetSerializer(data=request.data,context={'request':request})
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors)
    
#     def list(self, request):
#         target_language=request.query_params.get('target_language', None)
#         if target_language:
#             target_language=Languages.objects.get(id=target_language)
#             queryset = SelflearningAsset.objects.filter(user=request.user.id,target_language=target_language)
#         else:
#             queryset = SelflearningAsset.objects.filter(user=request.user.id)
#         serializer=SelflearningAssetSerializer(queryset,many=True)
#         return Response(serializer.data)

#     def retrieve(self,request,pk):
#         obj =self.get_object(pk)
#         serializer=SelflearningAssetSerializer(obj)
#         return Response(serializer.data)
    
#     def update(self,request,pk):
#         obj =self.get_object(pk)
#         serializer=SelflearningAssetSerializer(obj,data=request.data,partial=True,context={'request':request})
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors,status=400)

class SegmentDiffViewset(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,]
    def get_object(self, pk):
        try:
            return SegmentDiff.objects.get(id=pk)
        except SegmentDiff.DoesNotExist:
            raise Http404


def update_self_learning(sender, instance, *args, **kwargs):
    user=instance.user
    language=instance.segment.text_unit.document.job.target_language
    seg_his=SegmentHistory.objects.filter(segment=instance.segment)
    if hasattr(instance.segment,'seg_mt_raw'):
        target_segment =instance.segment.seg_mt_raw.mt_raw  
    else:target_segment=''
    
    edited_segment=instance.target

    # if instance.status.status_id==104:
    if edited_segment and target_segment:
        diff_words=do_compare_sentence(target_segment,edited_segment,sentense_diff=False)
        if diff_words:
            for diff_word in diff_words:
                self_learn_filter=SelflearningAsset.objects.filter(user=user,source_word=diff_word[0])
                if not self_learn_filter:
                    SelflearningAsset.objects.create(user=user,source_word=diff_word[0],edited_word=diff_word[1],
                                                    target_language=language)
                if self_learn_filter:
                    self_learn_filter.update(source_word=diff_word[0],edited_word=diff_word[1])
            print("diff_words--->",diff_words)
        else:
            print("no_diff")
    else:
        print("no_seg and no_tar")


# post_save.connect(update_self_learning, sender=SegmentHistory)



def segment_difference(sender, instance, *args, **kwargs):
    seg_his=SegmentHistory.objects.filter(segment=instance.segment)
    #from current segment
    edited_segment=''
    target_segment=''
    if len(seg_his)>=2:
        edited_segment=seg_his.last().target
        target_segment=seg_his[len(seg_his)-2].target
    elif len(seg_his)==1:
        if hasattr(instance.segment,'seg_mt_raw'):
            target_segment =instance.segment.seg_mt_raw.mt_raw  
        elif instance.segment.temp_target:
            target_segment=instance.segment.temp_target
        else:target_segment = None
        # target_segment=instance.segment.seg_mt_raw.mt_raw
        edited_segment=instance.target
 
    print('edited_segment',edited_segment , 'target_segment',target_segment )
    if edited_segment and target_segment:
        print('edited_segment',edited_segment , 'target_segment',target_segment )
        edited_segment=remove_tags(edited_segment)
        target_segment=remove_tags(target_segment)
        if edited_segment != target_segment:
            diff_sentense=do_compare_sentence(target_segment,edited_segment,sentense_diff=True)
            if diff_sentense:
                result_sen,save_type=diff_sentense
                if result_sen.strip()!=edited_segment.strip():
                    SegmentDiff.objects.create(seg_history=instance,sentense_diff_result=result_sen,save_type=save_type)
                    print("seg_diff_created")

post_save.connect(segment_difference, sender=SegmentHistory)



from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import SelflearningAssetSerializer
from rest_framework.response import Response
from ai_workspace_okapi.models import SelflearningAsset,Document,BaseSegment
from ai_staff.models import Languages
from rest_framework import status
from nltk import word_tokenize
from django_filters.rest_framework import DjangoFilterBackend
import difflib

class SelflearningView(viewsets.ViewSet, PageNumberPagination):
    permission_classes = [IsAuthenticated,]
    page_size = 20
    search_fields = ['source_word','edited_word']
    ordering_fields = ['id','source_word','edited_word']
    page_size = 20

    def filter_queryset(self, queryset):
        from rest_framework.filters import SearchFilter, OrderingFilter
        filter_backends = (DjangoFilterBackend,SearchFilter,OrderingFilter )
        for backend in list(filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        return queryset
    
    def list(self,request):
        segment_id=request.GET.get('segment_id',None)
        if segment_id:
            seg = get_object_or_404(Segment,id=segment_id)

            if split_check(segment_id):
                raw_mt=MT_RawTranslation.objects.get(segment=seg).mt_raw
                mt_edited=seg.target
                print("raw_mt normal>>>>>>",raw_mt)
            else:
                split_seg = SplitSegment.objects.get(segment=seg)
                raw_mt=MtRawSplitSegment.objects.get(split_segment=split_seg).mt_raw
                mt_edited=seg.target
                print("raw_mt split>>>>>>>",raw_mt)

            asset=seq_match_seg_diff(raw_mt,mt_edited)
            print(asset,'<<<<<<<<<<<<<<<<<<<<<<<<<<<')
            if asset:
                return Response(asset,status=status.HTTP_200_OK)
            return Response({},status=status.HTTP_200_OK)
        else:
            assets = SelflearningAsset.objects.filter(user=request.user).order_by('-id')
            queryset = self.filter_queryset(assets)
            pagin_tc = self.paginate_queryset(queryset, request , view=self)
            serializer = SelflearningAssetSerializer(pagin_tc, many=True)
            response = self.get_paginated_response(serializer.data)
            print(response)
            return  response

    def retrieve(self,request,pk):
        obj =self.get_object(pk)
        serializer=SelflearningAssetSerializer(obj)
        return Response(serializer.data)


    def create(self,request): 
        doc_id=request.POST.get('document_id',None)
        source=request.POST.get('source_word',None)
        edited=request.POST.get('edited_word',None)

        doc=get_object_or_404(Document,id=doc_id)
        lang=get_object_or_404(Languages,id=doc.target_language_id)
        
        user=self.request.user
        ser = SelflearningAssetSerializer(data={'source_word':source,'edited_word':edited,'user':user.id,'target_language':lang.id})
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors)

    def update(self,request,pk):
        ins = SelflearningAsset.objects.get(user=self.request.user,id=pk)
        ser = SelflearningAssetSerializer(ins,data=request.POST.dict(), partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors)

    def delete(self,request,pk):
        ins = SelflearningAsset.objects.get(user=self.request.user,id=pk)
        ins.delete()
        return Response(status=204)

def seq_match_seg_diff(words1,words2):
    s1=words1.split()
    s2=words2.split()
    assets={}
    matcher=difflib.SequenceMatcher(None,s1,s2 )
    print(matcher.get_opcodes())
    for tag,i1,i2,j1,j2 in matcher.get_opcodes():
        if tag=='replace':
            assets[" ".join(s1[i1:i2])]=" ".join(s2[j1:j2])
    print("------------------",assets)  
    for i in assets:
        if len(assets[i].split())>3:
            assets[i]=" ".join(assets[i].split()[0:3])
    return assets

