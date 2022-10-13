from datetime import datetime
from .serializers import (DocumentSerializer, SegmentSerializer, DocumentSerializerV2,
                          SegmentSerializerV2, MT_RawSerializer, DocumentSerializerV3,
                          TranslationStatusSerializer, FontSizeSerializer, CommentSerializer,
                          TM_FetchSerializer,VerbSerializer)
from ai_workspace.serializers import TaskCreditStatusSerializer, TaskSerializer,TaskTranscriptDetailSerializer
from .models import Document, Segment, MT_RawTranslation, TextUnit, TranslationStatus, FontSize, Comment
from rest_framework import viewsets, authentication
from rest_framework import views
import json,jwt,logging,os,re,urllib.parse,xlsxwriter
from json import JSONDecodeError
from django.urls import reverse
import requests
from ai_auth.tasks import write_segments_to_db,google_long_text_file_process_cel,pre_translate_update
from django.contrib.auth import settings
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework import views
from nltk.tokenize import TweetTokenizer
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.exceptions import APIException
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from django.http import  FileResponse
from rest_framework.views import APIView
from django.db.models import Q
import urllib.parse
import nltk,docx2txt
from .serializers import PentmUpdateSerializer
from wiktionaryparser import WiktionaryParser
from ai_workspace.utils import get_consumable_credits_for_text_to_speech
from ai_auth.models import AiUser, UserCredits
from ai_auth.utils import get_plan_name
from ai_staff.models import SpellcheckerLanguages
from ai_workspace.api_views import UpdateTaskCreditStatus
from ai_workspace.models import File,Project
from ai_workspace.models import Task, TaskAssign
from ai_workspace.serializers import TaskSerializer, TaskAssignSerializer
from .models import Document, Segment, MT_RawTranslation, TextUnit, TranslationStatus, FontSize, Comment, MergeSegment
from .okapi_configs import CURRENT_SUPPORT_FILE_EXTENSIONS_LIST
from .serializers import PentmUpdateSerializer,SegmentHistorySerializer
from .serializers import (SegmentSerializer, DocumentSerializerV2,
                          SegmentSerializerV2, MT_RawSerializer, DocumentSerializerV3,
                          TranslationStatusSerializer, FontSizeSerializer, CommentSerializer,
                          TM_FetchSerializer, MergeSegmentSerializer)
from django.urls import reverse
from json import JSONDecodeError
from .utils import SpacesService
from .utils import download_file, bl_title_format, bl_cell_format
from google.cloud import translate_v2 as translate
from rest_framework import serializers
import os, io, zipfile, requests, time
from django.http import HttpResponse
from rest_framework.response import Response
# from controller.models import DownloadController
from ai_workspace.models import File
from .utils import SpacesService,text_to_speech
from django.contrib.auth import settings
from ai_auth.utils import get_plan_name
from .utils import download_file, bl_title_format, bl_cell_format,get_res_path
from os.path import exists
from ai_auth.tasks import write_segments_to_db
from django.db import transaction
from rest_framework.decorators import permission_classes
from ai_auth.tasks import write_segments_to_db
from django.db import transaction
from os.path import exists


# logging.basicConfig(filename="server.log", filemode="a", level=logging.DEBUG, )
logger = logging.getLogger('django')

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
    def trim_segments(doc_json_data):

        doc_data = json.loads(doc_json_data)
        text = doc_data["text"]
        count = 0
        needed_keys = []

        for key, value in text.items():
            needed_keys.append(key)
            count += len(value)
            if count >= 40:
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

        # Writing first 20 segments in DB

        doc_data = json.load(open(json_file_path))
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

        return document

    @staticmethod
    def create_document_for_task_if_not_exists(task):
        from .utils import get_translation
        from ai_workspace.models import MTonlytaskCeleryStatus
        if task.document != None:
            print("<--------------------------Document Exists--------------------->")
            if task.job.project.pre_translate == True:
                ins = MTonlytaskCeleryStatus.objects.filter(task_id=task.id).last()
                print("Ins------------>",ins)
                state = pre_translate_update.AsyncResult(ins.celery_task_id).state if ins and ins.celery_task_id else None
                print("State----------------------->",state)
                if state == 'PENDING':
                    return {'msg':'Pre Translation Ongoing. Pls Wait','celery_id':ins.celery_task_id}
                elif (not ins) or state == 'FAILURE':
                    cel_task = pre_translate_update.apply_async((task.id,),)
                    return {"msg": "Pre Translation Ongoing. Please wait a little while.Hit refresh and try again",'celery_id':cel_task.id}
                elif state == "SUCCESS":
                    if ins.error_type == "Insufficient Credits":
                        cel_task = pre_translate_update.apply_async((task.id,),)
                        return {"doc":task.document,"msg":"Pre Translation may be incomplete due to insufficient credit"}
                    else:return task.document
        # If document already exists for a task
        # if task.document != None:
        #     print("<--------------------------Document Exists--------------------->")
        #     if task.job.project.pre_translate == True:
        #         #pre_translate_update.apply_async((task.id,),)
        #         #return Response({"msg": "File under process. Please wait a little while.Hit refresh and try again"}, status=401)
        #         user = task.job.project.ai_user
        #         mt_engine = task.job.project.mt_engine_id
        #         task_mt_engine_id = TaskAssign.objects.get(Q(task=task) & Q(step_id=1)).mt_engine.id
        #         segments = Segment.objects.filter(text_unit__document=task.document)
        #         update_list = []
        #         mt_segments = []
        #
        #         for seg in segments:###############Need to revise####################
        #             i = seg.get_active_object()
        #             if i.target == '':
        #                 initial_credit = user.credit_balance.get("total_left")
        #                 consumable_credits = MT_RawAndTM_View.get_consumable_credits(task.document, i.id, i)
        #                 if initial_credit > consumable_credits:
        #                     i.target = get_translation(mt_engine, i.source, task.document.source_language_code, task.document.target_language_code)
        #                     i.temp_target = i.target
        #                     i.status_id = TranslationStatus.objects.get(status_id=104).id
        #                     debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)
        #                     mt_segments.append(i)
        #                 else:
        #                     break
        #         #             i.target= ""
        #         #             i.temp_target = ''
        #         #             i.status_id = None
        #                 update_list.append(i)
        #         #
        #         Segment.objects.bulk_update(update_list,['target','temp_target','status_id'])
        #
        #
        #         instances = [
        #                 MT_RawTranslation(
        #                     mt_raw= i.target,
        #                     mt_engine_id = mt_engine,
        #                     task_mt_engine_id = task_mt_engine_id,
        #                     segment_id= i.id,
        #                 )
        #                 for i in mt_segments
        #             ]
        #
        #         MT_RawTranslation.objects.bulk_create(instances)

            return task.document

        # If file for the task is already processed
        elif Document.objects.filter(file_id=task.file_id).exists():
            print("-------------------------Document Already Processed-------------------------")
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
        # task = self.get_object(task_id=task_id)
        # document = self.create_document_for_task_if_not_exists(task)
        # doc = DocumentSerializerV2(document).data
        # return Response(doc, status=201)
        from ai_workspace.models import MTonlytaskCeleryStatus
        from django_celery_results.models import TaskResult
        task = self.get_object(task_id=task_id)
        if task.job.project.pre_translate == True and task.document == None:
            ins = MTonlytaskCeleryStatus.objects.filter(task_id=task_id).last()
            if not ins:
                Document.objects.filter(Q(file = task.file) &Q(job=task.job)).delete()
                document = self.create_document_for_task_if_not_exists(task)
                doc = DocumentSerializerV2(document).data
                MTonlytaskCeleryStatus.objects.create(task_id=task.id,status=2)
                return Response(doc, status=201)
            if ins.status == 1:
                obj = TaskResult.objects.filter(Q(task_id = ins.celery_task_id)).first()# & Q(task_name = 'ai_auth.tasks.mt_only').first()
                if obj !=None and obj.status == "FAILURE":
                    Document.objects.filter(Q(file = task.file) &Q(job=task.job)).delete()
                    document = self.create_document_for_task_if_not_exists(task)
                    doc = DocumentSerializerV2(document).data
                    MTonlytaskCeleryStatus.objects.create(task_id=task.id,status=2)
                    return Response(doc, status=201)
                else:
                    return Response({"msg": "File under process. Please wait a little while.Hit refresh and try again"}, status=401)
            else:
                document = self.create_document_for_task_if_not_exists(task)
                doc = DocumentSerializerV2(document).data
                return Response(doc, status=201)
        else:
            document = self.create_document_for_task_if_not_exists(task)
            print("Doc--------->",document)
            try:
                doc = DocumentSerializerV2(document).data
                return Response(doc, status=201)
            except:
                if document.get('doc')!=None:
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

    def get(self, request, document_id):
        #doc_user = AiUser.objects.get(project__project_jobs_set__file_job_set=document_id).id
        doc_user = AiUser.objects.filter(project__project_jobs_set__file_job_set=document_id).first()
        team_members = doc_user.get_team_members if doc_user.get_team_members else []
        hired_editors = doc_user.get_hired_editors if doc_user.get_hired_editors else []
        try :managers = doc_user.team.get_project_manager if doc_user.team.get_project_manager else []
        except:managers =[]
        if (request.user == doc_user) or (request.user in team_members) or (request.user in hired_editors):
            dict = {'download':'enable'} if (request.user == doc_user) else {'download':'disable'}
            dict_1 = {'updated_download':'enable'} if (request.user == doc_user) or (request.user in managers) else {'updated_download':'disable'}
            document = self.get_object(document_id)
            data = DocumentSerializerV2(document).data
            data.update(dict)
            data.update(dict_1)
            return Response(data, status=200)
        else:
            return Response({"msg" : "Unauthorised"}, status=401)

class SegmentsView(views.APIView, PageNumberPagination):
    PAGE_SIZE = page_size =  20

    def get_object(self, document_id):
        document = get_object_or_404(\
            Document.objects.all(), id=document_id)
        return document

    def get(self, request, document_id):
        document = self.get_object(document_id=document_id)
        segments = document.segments_for_workspace
        len_segments = segments.count()
        page_len = self.paginate_queryset(range(1, len_segments + 1), request)
        page_segments = self.paginate_queryset(segments, request, view=self)
        segments_ser = SegmentSerializer(page_segments, many=True)

        data = [SegmentSerializer(MergeSegment.objects.get(id=i.get("segment_id"))).data
                if (i.get("is_merged") == True and i.get("is_merge_start")) else i for i in segments_ser.data]

        [i.update({"segment_count": j}) for i, j in zip(data, page_len)]

        res = self.get_paginated_response(data)
        return res

class MergeSegmentView(viewsets.ModelViewSet):
    serializer_class = MergeSegmentSerializer
    def create(self, request, *args, **kwargs):
        serlzr = self.serializer_class(data=request.data)
        if serlzr.is_valid(raise_exception=True):
            serlzr.save(id=serlzr.validated_data.get("segments")[0].id)
            obj =  serlzr.instance
            obj.update_segments(serlzr.validated_data.get("segments"))
            return Response(MergeSegmentSerializer(obj).data)

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
    def get_object(self, segment_id):
        # segment_id = self.kwargs["pk"]
        qs = Segment.objects.all()
        segment = get_object_or_404(qs, id = segment_id)
        return segment.get_active_object()

    @staticmethod
    def get_update(segment, data, request):
        segment_serlzr = SegmentSerializerV2(segment, data=data, partial=True,\
            context={"request": request})
        if segment_serlzr.is_valid(raise_exception=True):
            segment_serlzr.save()
            return segment_serlzr
        else:
            logger.info(">>>>>>>> Error in Segment update <<<<<<<<<")
            return segment_serlzr.errors

    def edit_allowed_check(self,instance):
        from ai_workspace.models import Task,TaskAssignInfo
        user = self.request.user
        task_obj = Task.objects.get(document_id = instance.text_unit.document.id)
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

    def update_pentm(self, segment):
        data = PentmUpdateSerializer(segment).data
        res = requests.post(f"http://{spring_host}:8080/project/pentm/update", data=data)
        if res.status_code == 200:
            print("res text--->", res.json())
        else:
            print("not successfully update")

    def update(self, request, segment_id):
        segment = self.get_object(segment_id)
        # segment = self.get_object()
        edit_allow = self.edit_allowed_check(segment)
        if edit_allow == False:
            return Response({"msg":"Someone is working already.."},status = 400)
        segment_serlzr = self.get_update(segment, request.data, request)
        # self.update_pentm(segment)  # temporarily commented to solve update pentm issue
        return Response(segment_serlzr.data, status=201)

# class SegmentsUpdateView(viewsets.ModelViewSet):
#
#     serializer_class = SegmentSerializerV2
#
#     # def get_object(self):
#     #     segment_id = self.kwargs["pk"]
#     #     qs = Segment.objects.all()
#     #     segment = get_object_or_404(qs, id = segment_id)
#     #     if segment.is_merged == True:
#     #         return MergeSegment.objects.get(id=segment_id)
#     #     return segment
#
#     def get_object(self):
#         segment_id = self.kwargs["pk"]
#         qs = Segment.objects.all()
#         segment = get_object_or_404(qs, id = segment_id)
#         return segment.get_active_object()


class MergeSegmentDeleteView(viewsets.ModelViewSet):
    def get_queryset(self):
        return  MergeSegment.objects.all()
class MT_RawAndTM_View(views.APIView):

    @staticmethod
    def can_translate(request, debit_user):
        hired_editors = debit_user.get_hired_editors if debit_user.get_hired_editors else []

        # Check if the debit_user (account holder) has plan other than Business like Pro, None etc
        if get_plan_name(debit_user) != "Business":
            return {}, 424, "cannot_translate"

        elif (request.user.is_internal_member or request.user.id in hired_editors) and \
            (get_plan_name(debit_user)=="Business") and \
            (UserCredits.objects.filter(Q(user_id=debit_user.id)  \
                                     & Q(credit_pack_type__icontains="Subscription")).last().ended_at != None):
            print("For internal & hired editors only")
            return {}, 424, "cannot_translate"
        else:
            return None


    @staticmethod
    def get_consumable_credits(doc, segment_id, seg):
        segment = Segment.objects.filter(id=segment_id).first().get_active_object() if segment_id else None
        segment_source = segment.source if segment!= None else seg
        seg_data = { "segment_source" : segment_source,
                     "source_language" : doc.source_language_code,
                     "target_language" : doc.target_language_code,
                     "processor_name" : "plain-text-processor",
                     "extension":".txt"
                     }
        res = requests.post(url=f"http://{spring_host}:8080/segment/word_count", \
            data={"segmentWordCountdata":json.dumps(seg_data)})

        if res.status_code == 200:
            print("Word count of the segment--->", res.json())
            return res.json()
        else:
            logger.info(">>>>>>>> Error in segment word count calculation <<<<<<<<<")
            raise  ValueError("Sorry! Something went wrong with word count calculation.")

    @staticmethod
    def get_data(request, segment_id, mt_params):
        from .utils import get_translation
        mt_raw = MT_RawTranslation.objects.filter(segment_id=segment_id).first()
        task_assign_mt_engine = TaskAssign.objects.filter(
            Q(task__document__document_text_unit_set__text_unit_segment_set=segment_id) &
            Q(step_id=1)
        ).first().mt_engine
        if mt_raw:
            if mt_raw.mt_engine == task_assign_mt_engine:
                return MT_RawSerializer(mt_raw).data, 200, "available"


        # If MT disabled for the task
        if mt_params.get("mt_enable", True) != True:
            print("MT not enabled")
            return {}, 200, "MT disabled"

        text_unit_id = Segment.objects.get(id=segment_id).text_unit_id
        doc = TextUnit.objects.get(id=text_unit_id).document
        user = doc.doc_credit_debit_user

        # Checking if the request user is account owner or not
        if (doc.job.project.team) and (request.user != AiUser.objects.get(project__project_jobs_set__file_job_set=doc)):
            can_translate = MT_RawAndTM_View.can_translate(request, user)
            if can_translate == None:
                pass
            else:
                return MT_RawAndTM_View.can_translate(request, user)

        initial_credit = user.credit_balance.get("total_left")

        consumable_credits = MT_RawAndTM_View.get_consumable_credits(doc, segment_id, None)

        # initial_credit = 1000000

        if initial_credit > consumable_credits :
            if mt_raw:

                #############   Update   ############
                translation = get_translation(task_assign_mt_engine.id, mt_raw.segment.source, doc.source_language_code, doc.target_language_code)
                debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)

                MT_RawTranslation.objects.filter(segment_id=segment_id).update(mt_raw = translation, \
                                       mt_engine = task_assign_mt_engine, task_mt_engine=task_assign_mt_engine)
                obj = MT_RawTranslation.objects.filter(segment_id=segment_id).first()
                return MT_RawSerializer(obj).data, 200, "available"
            else:

                #########   Create   #######
                mt_raw_serlzr = MT_RawSerializer(data = {"segment": segment_id},\
                                context={"request": request})
                if mt_raw_serlzr.is_valid(raise_exception=True):
                    mt_raw_serlzr.save()
                    debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)
                    return mt_raw_serlzr.data, 201, "available"
        else:
            return {}, 424, "unavailable"

    @staticmethod
    def get_tm_data(request, segment_id):
        segment = Segment.objects.filter(id=segment_id).first()
        if segment:
            tm_ser = TM_FetchSerializer(segment)
            res = requests.post( f'http://{spring_host}:8080/pentm/source/search',\
                    data = {'pentmsearchparams': json.dumps(tm_ser.data)})
            if res.status_code == 200:
                return res.json()
            else:
                return []
        return []

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

    def get_segment_MT_params(self, segment_id):
        task_assign_obj = TaskAssign.objects.filter(
            Q(task__document__document_text_unit_set__text_unit_segment_set=segment_id) &
            Q(step_id=1)
        ).first()
        return TaskAssignSerializer(task_assign_obj).data

    def get(self, request, segment_id):
        mt_params = self.get_segment_MT_params(segment_id)
        data, status_code, can_team = self.get_data(request, segment_id, mt_params)
        mt_alert = True if status_code == 424 else False
        alert_msg = self.get_alert_msg(status_code, can_team)
        tm_data = self.get_tm_data(request, segment_id)
        return Response({**data, "tm":tm_data, "mt_alert": mt_alert,
            "alert_msg":alert_msg}, status=status_code)

# class MT_RawAndTM_View(views.APIView):############merge and split options included view
#
#     @staticmethod
#     def can_translate(request, debit_user):
#         hired_editors = debit_user.get_hired_editors if debit_user.get_hired_editors else []
#
#         # Check if the debit_user (account holder) has plan other than Business like Pro, None etc
#         if get_plan_name(debit_user) != "Business":
#             return {}, 424, "cannot_translate"
#
#         elif (request.user.is_internal_member or request.user.id in hired_editors) and \
#             (get_plan_name(debit_user)=="Business") and \
#             (UserCredits.objects.filter(Q(user_id=debit_user.id)  \
#                                      & Q(credit_pack_type__icontains="Subscription")).last().ended_at != None):
#             print("For internal & hired editors only")
#             return {}, 424, "cannot_translate"
#         else:
#             return None
#
#     @staticmethod
#     def get_consumable_credits(doc, segment,seg):
#         # segment_source = Segment.objects.get(id=segment_id).source
#         segment_source = segment.source if segment != None else seg
#         seg_data = { "segment_source" : segment_source,
#                      "source_language" : doc.source_language_code,
#                      "target_language" : doc.target_language_code,
#                      "processor_name" : "plain-text-processor",
#                      "extension":".txt"
#                      }
#         res = requests.post(url=f"http://{spring_host}:8080/segment/word_count", \
#             data={"segmentWordCountdata":json.dumps(seg_data)})
#
#         if res.status_code == 200:
#             print("Word count --->", res.json())
#             return res.json()
#         else:
#             logger.info(">>>>>>>> Error in segment word count calculation <<<<<<<<<")
#             raise  ValueError("Sorry! Something went wrong with word count calculation.")
#
#     @staticmethod
#     def get_data(request, segment, mt_params):
#
#         print("MT params ---> ", mt_params)
#
#         # get already stored MT done for first time
#         mt_raw = segment.mt_raw_translation
#         if mt_raw:
#             print("MT Raw available ---> ", mt_raw)
#             return MT_RawSerializer(mt_raw).data, 200, "available"
#
#         # If MT disabled for the task
#         if mt_params.get("mt_enable", True) != True:
#             print("MT not enabled")
#             return {}, 200, "MT disabled"
#
#         # finding the user to debit Credit
#         text_unit_id = segment.text_unit_id
#         doc = TextUnit.objects.get(id=text_unit_id).document
#         user = doc.doc_credit_debit_user
#
#         # Checking if the request user is account owner or not
#         if (doc.job.project.team) and (request.user != AiUser.objects.get
#                 (project__project_jobs_set__file_job_set=doc)):
#             can_translate = MT_RawAndTM_View.can_translate(request, user)
#             if can_translate == None:
#                 pass
#             else:
#                 return MT_RawAndTM_View.can_translate(request, user)
#
#         # credit balance of debit user
#         initial_credit = user.credit_balance.get("total_left")
#
#         # getting word count
#         consumable_credits = MT_RawAndTM_View.get_consumable_credits(doc, segment,None)
#
#         if initial_credit > consumable_credits:
#
#             # Applying Machine Translation
#             mt_engine_id = mt_params.get("mt_engine", 1)  # Google MT selected if MT selection fails
#
#             reverse_string_for_segment = "ai_workspace_okapi.segment" if \
#                             isinstance(segment, Segment) else ("ai_workspace_okapi.mergesegment"
#                         if isinstance(segment, MergeSegment) else None)
#
#             mt_raw_serlzr = MT_RawSerializer(data = { "mt_engine": mt_engine_id,
#                                                       "reverse_string_for_segment": reverse_string_for_segment,
#                                                      }, context={"request": request})
#
#             if mt_raw_serlzr.is_valid(raise_exception=True):
#                 mt_raw_serlzr.save(segment=segment)
#                 debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)
#                 return mt_raw_serlzr.data, 201, "available"
#
#         else:
#             return {}, 424, "unavailable"
#
#     @staticmethod
#     def get_tm_data(request, segment):
#         # segment = Segment.objects.filter(id=segment_id).first()
#         if segment:
#             tm_ser = TM_FetchSerializer(segment)
#             res = requests.post( f'http://{spring_host}:8080/pentm/source/search',\
#                     data = {'pentmsearchparams': json.dumps(tm_ser.data)})
#             if res.status_code == 200:
#                 return res.json()
#             else:
#                 return []
#         return []
#
#     def get_segment_MT_params(self, segment_id):
#         task_assign_obj = TaskAssign.objects.filter(
#             Q(task__document__document_text_unit_set__text_unit_segment_set=segment_id) &
#             Q(step_id=1)
#         ).first()
#         return TaskAssignSerializer(task_assign_obj).data
#
#     def get_alert_msg(self, status_code, can_team):
#         if (status_code == 424 and can_team == "unavailable"):
#             return "MT doesn't work as the credits are insufficient. Please buy more or upgrade"
#         else:
#             return "Team subscription inactive"
#
#     def get(self, request, segment_id):
#
#         segment = get_object_or_404(Segment.objects.all(), id=segment_id)\
#             .get_active_object()
#
#         mt_params = self.get_segment_MT_params(segment_id)
#
#         # data, status_code, can_team = self.get_data(request, segment_id, mt_params)
#
#         data, status_code, can_team = self.get_data(request, segment, mt_params)
#
#         mt_alert = True if status_code == 424 else False
#         alert_msg = self.get_alert_msg(status_code, can_team)
#         tm_data = self.get_tm_data(request, segment)
#         print("MT Data ---> ", data)
#         return Response({**data, "tm":tm_data, "mt_alert": mt_alert,
#             "alert_msg":alert_msg}, status=status_code)

class ConcordanceSearchView(views.APIView):

    @staticmethod
    def get_concordance_data(request, segment_id, search_string):
        segment = Segment.objects.filter(id=segment_id).first()
        if segment:
            tm_ser_data = TM_FetchSerializer(segment).data
            tm_ser_data.update({'search_source_string':search_string, "max_hits":20,\
                    "threshold": 10})
            res = requests.post( f'http://{spring_host}:8080/pentm/source/search',\
                    data = {'pentmsearchparams': json.dumps( tm_ser_data), "isCncrdSrch":"true" })
            if res.status_code == 200:
                return res.json()
            else:
                return []
        return []

    def get(self, request, segment_id):
        search_string = request.GET.get("string", None).strip('0123456789')
        concordance = []
        if search_string:
            concordance = self.get_concordance_data(request, segment_id, search_string)
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
            # response['Content-Disposition'] = 'attachment;filename*=UTF-8\'\'{}' \
            #     .format(encoded_filename)
            filename = os.path.basename(file_path)
            response['Content-Disposition'] = "attachment; filename=%s" % filename
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


    #For Downloading Audio File################only for voice project###########Need to work
    def download_audio_file(self,res,document_user,document_id,voice_gender,language_locale,voice_name):
        from ai_workspace.api_views import google_long_text_file_process
        from ai_workspace.models import MTonlytaskCeleryStatus
        filename, ext = os.path.splitext(self.get_source_file_path(document_id).split('source/')[1])
        temp_name = filename + '.txt'
        text_units = TextUnit.objects.filter(document_id=document_id)
        counter = 0
        with open(temp_name, "w") as out:
            for text_unit in text_units:
                segments = Segment.objects.filter(text_unit_id=text_unit.id)
                for segment in segments:
                    if segment.target!=None:
                        counter = counter + len(segment.target)
                        out.write(segment.target)
                        if counter>3500:
                            out.write('\n')
                            counter = 0
        file_path = temp_name
        doc = DocumentToFile.get_object(document_id)
        task = doc.task_set.first()
        ser = TaskSerializer(task)
        task_data = ser.data
        target_language = language_locale if language_locale else task_data["target_language"]
        source_lang = task_data['source_language']
        text_file = open(temp_name, "r")
        data = text_file.read()
        text_file.close()
        print("Length of file------------------------>",len(data))
        consumable_credits = get_consumable_credits_for_text_to_speech(len(data))
        initial_credit = document_user.credit_balance.get("total_left")#########need to update owner account######
        if initial_credit > consumable_credits:
            if len(data)>5000:
                celery_task = google_long_text_file_process_cel.apply_async((consumable_credits,document_user.id,file_path,task.id,target_language,voice_gender,voice_name), )
                MTonlytaskCeleryStatus.objects.create(task_id=task.id,task_name='google_long_text_file_process_cel',celery_task_id=celery_task.id)
                return Response({'msg':'Conversion is going on.Please wait',"celery_id":celery_task.id},status=400)
                #celery_task = google_long_text_file_process_cel(file_path,task.id,target_language,voice_gender,voice_name)
                #res1,f2 = google_long_text_file_process(file_path,task,target_language,voice_gender,voice_name)
            else:
                filename_ = filename + "_"+ task.ai_taskid+ "_out" + "_" + source_lang + "-" + target_language + ".mp3"
                res1,f2 = text_to_speech(file_path,target_language,filename_,voice_gender,voice_name)
                os.remove(filename_)
            debit_status, status_code = UpdateTaskCreditStatus.update_credits(document_user, consumable_credits)
            if task.task_transcript_details.first()==None:
                ser = TaskTranscriptDetailSerializer(data={"translated_audio_file":res1,"task":task.id})
            else:
                t = task.task_transcript_details.first()
                ser = TaskTranscriptDetailSerializer(t,data={"translated_audio_file":res1,"task":task.id},partial=True)
            if ser.is_valid():
                ser.save()
            print(ser.errors)
            f2.close()
            #os.remove(filename_)
            #os.remove(file_path)
            return download_file(task.task_transcript_details.last().translated_audio_file.path)
        else:
            return Response({"msg":"Insufficient credits to convert text file to audio file"},status=400)



    # FOR DOWNLOADING BILINGUAL FILE
    def remove_tags(self, string):
        return re.sub(rf'</?\d+>', "", string)
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
                if segment.is_merged and (not segment.is_merge_start):
                    continue
                segment_new = segment.get_active_object()
                worksheet.write(row, 0, segment_new.source.strip(), cell_format)
                worksheet.write(row, 1, self.remove_tags(segment_new.target), cell_format)
                row += 1
        workbook.close()

        return download_file(bilingual_file_path)


    def get(self, request, document_id):

        # Incomplete segments in db
        segment_count = Segment.objects.filter(text_unit__document=document_id).count()
        if Document.objects.get(id=document_id).total_segment_count != segment_count:
            return JsonResponse({"msg": "File under process. Please wait a little while. \
                    Hit refresh and try again"}, status=401)

        # print("Request auth type ----> ", type(request.auth))

        #token = str(request.auth)
        #token = request.GET.get("token")
        output_type = request.GET.get("output_type", "")
        voice_gender = request.GET.get("voice_gender", "FEMALE")
        voice_name = request.GET.get("voice_name",None)
        language_locale = request.GET.get("locale", None)
        #payload = jwt.decode(token, settings.SECRET_KEY, ["HS256"])
        #user_id_payload = payload.get("user_id", 0)
        #request_user = AiUser.objects.get(id=user_id_payload)
        # team_members = doc_user.get_team_members if doc_user.get_team_members else []
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
                res = self.document_data_to_file(request, document_id)
                return self.download_audio_file(res,document_user,document_id,voice_gender,language_locale,voice_name)

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
        ext = ".xliff" if output_type == "XLIFF" else \
            (".tmx" if output_type == "TMX" else ext)

        task_data["output_file_path"] = pre + "(" + task_data["source_language"] + \
                "-" + task_data["target_language"] + ")" + ext

        params_data = {**task_data, "output_type": output_type}

        res_paths = get_res_path(task_data["source_language"])

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
    # AUDIO = "AUDIO",
)

def output_types(request):
    return JsonResponse(OUTPUT_TYPES, safe=False)

class TranslationStatusList(views.APIView):
    def get(self, request):
        qs = TranslationStatus.objects.all()
        ser = TranslationStatusSerializer(qs, many=True)
        return Response(ser.data, status=200)

# class SourceSegmentsListView(viewsets.ViewSet, PageNumberPagination):
#     PAGE_SIZE = page_size = 20
#     lookup_field = "source"
#
#     @staticmethod
#     def prepare_data(data):
#         for i in data:
#             try: data[i] = json.loads(data[i])
#             except: pass
#         return data
#
#     @staticmethod
#     def get_queryset(request, data, document_id, lookup_field):
#         qs = Document.objects.all()
#         document = get_object_or_404(qs, id=document_id)
#         # segments_all = segments = document.segments
#         segments_all = segments = document.segments_for_workspace
#         status_list = data.get("status_list", [])
#         segments_merged = segments_all.filter(is_merged=True)
#
#         if status_list:
#             if 0 in status_list:
#                 segments = segments.filter(Q(status=None) | \
#                         Q(status__status_id__in=status_list)).all()
#             else:
#                 segments = segments.filter(status__status_id__in=status_list).all()
#
#         search_word = data.get("search_word", None)
#
#         if search_word not in [None, '']:
#
#             match_case = data.get("match_case", False)
#             exact_word = data.get("exact_word", False)
#
#             if match_case and exact_word:
#                 segments = segments.filter(**{f'{lookup_field}'
#                     f'__regex':f'(?<!\w){search_word}(?!\w)'})
#             elif not(match_case or exact_word):
#                 segments = segments.filter(**{f'{lookup_field}'
#                     f'__contains':f'{search_word}'})
#             elif match_case:
#                 segments = segments.filter(**{f'{lookup_field}'
#                     f'__regex':f'{search_word}'})
#             elif exact_word:
#                 # segments = segments.filter(**{f'{lookup_field}__regex':f'(?<!\w)(?i){search_word}(?!\w)'})
#                 segments = segments.filter(**{f'{lookup_field}'
#                     f'__regex':f'(?i)[^\w]{search_word}[^\w]'})  # temp regex
#
#         return segments, segments_merged, 200
#
#     # def post(self, request, document_id):
#     #     data = self.prepare_data(request.POST.dict())
#     #     segments, status = self.get_queryset(request, data, document_id, self.lookup_field)
#     #     page_segments = self.paginate_queryset(segments, request, view=self)
#     #     segments_ser = SegmentSerializer(page_segments, many=True)
#     #     res = self.get_paginated_response(segments_ser.data)
#     #     res.status_code = status
#     #     return res
#
#     def get_corrected_source_data(self, segments_ser, payload):
#
#         data = []
#         search_word = payload.get('payload', None)
#         match_case = payload.get("match_case", False)
#         exact_word = payload.get("exact_word", False)
#         status_list = payload.get("status_list", [])
#         lookup_field = self.lookup_field
#
#         for i in segments_ser.data:
#
#             if i.get("is_merged") == True and i.get('is_merge_start') == True:
#
#                 merged_segment = MergeSegment.objects.get(segments=Segment.objects.get(id=i.get("segment_id")))
#
#                 if status_list:
#                     if 0 in status_list and merged_segment.status_id == None:
#                         data.append(SegmentSerializer(merged_segment).data)
#                         continue
#                     if merged_segment.status_id in status_list:
#                         data.append(SegmentSerializer(merged_segment).data)
#                         continue
#
#                 if search_word not in [None, ""]:
#
#                     if match_case and exact_word:
#                         if re.search(f'(?<!\w){search_word}(?!\w)', merged_segment.source):
#                             data.append(SegmentSerializer(merged_segment).data)
#                             continue
#
#                     elif not (match_case or exact_word):
#                         if re.search(f'{search_word}', merged_segment.source):
#                             data.append(SegmentSerializer(merged_segment).data)
#                             continue
#
#                     elif match_case:
#                         if re.search(f'{search_word}', merged_segment.source):
#                             data.append(SegmentSerializer(merged_segment).data)
#                             continue
#
#                     elif exact_word:
#                         if re.search(f'(?i)[^\w]{search_word}[^\w]', merged_segment.source):
#                             data.append(SegmentSerializer(merged_segment).data)
#                             continue
#
#             elif i.get("is_merged") == True and i.get('is_merge_start') == False:
#                 continue
#
#             else:
#                 # data.append(i)
#                 normal_segment = Segment.objects.get(id=i.get("segment_id"))
#
#                 if status_list:
#                     if 0 in status_list and normal_segment.status_id == None:
#                         data.append(SegmentSerializer(normal_segment).data)
#                         continue
#                     if normal_segment.status_id in status_list:
#                         data.append(SegmentSerializer(normal_segment).data)
#                         continue
#
#                 if search_word not in [None, ""]:
#
#                     if match_case and exact_word:
#                         if re.search(f'(?<!\w){search_word}(?!\w)', normal_segment.source):
#                             data.append(SegmentSerializer(normal_segment).data)
#                             continue
#
#                     elif not (match_case or exact_word):
#                         if re.search(f'{search_word}', normal_segment.source):
#                             data.append(SegmentSerializer(normal_segment).data)
#                             continue
#
#                     elif match_case:
#                         if re.search(f'{search_word}', normal_segment.source):
#                             data.append(SegmentSerializer(normal_segment).data)
#                             continue
#
#                     elif exact_word:
#                         if re.search(f'(?i)[^\w]{search_word}[^\w]', normal_segment.source):
#                             data.append(SegmentSerializer(normal_segment).data)
#                             continue
#         return data
#
#     def post(self, request, document_id):
#         # print("Request data ---> ", request.POST.dict())
#         data = self.prepare_data(request.POST.dict())
#         print("Data ---> ", data)
#         print("Type of status list ----> ", type(data["status_list"]))
#         # print("Type of data ---> ", type(data))
#         segments, segments_merged, status = self.get_queryset(request, data, document_id, self.lookup_field)
#         # segment_final = segments.union(segments_merged).order_by('id')
#         print("Segments ---> ", segments)
#         print("Segments merged ---> ", segments_merged)
#
#         segment_final = segments.union(segments_merged)
#         page_segments = self.paginate_queryset(segment_final, request, view=self)
#         segments_ser = SegmentSerializer(page_segments, many=True)
#
#         data = self.get_corrected_source_data(segments_ser, data)
#
#         res = self.get_paginated_response(data)
#         res.status_code = status
#         return res
class SourceSegmentsListView(viewsets.ViewSet, PageNumberPagination):
    PAGE_SIZE = page_size = 20
    lookup_field = "source"

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
        print("seg------->",segments)
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

        segments = document.segments_for_workspace
        merge_segments = MergeSegment.objects.filter(text_unit__document=document_id)

        segments = SourceSegmentsListView.do_search(data, segments, lookup_field)
        merge_segments = SourceSegmentsListView.do_search(data, merge_segments, lookup_field)

        merge_segments_ids = []

        for merge_seg in merge_segments:
            merge_segments_ids.append(merge_seg.id)

        for seg in segments:
            if seg.id not in merge_segments_ids:
                segments.exclude(id=seg.id)

        return segments, 200

    def post(self, request, document_id):
        data = self.prepare_data(request.POST.dict())
        segments, status = self.get_queryset(request, data, document_id, self.lookup_field)
        page_len = self.paginate_queryset(range(1, segments.count() + 1), request)
        page_segments = self.paginate_queryset(segments, request, view=self)
        segments_ser = SegmentSerializer(page_segments, many=True)

        data = [SegmentSerializer(MergeSegment.objects.get(id=i.get("segment_id"))).data
                if (i.get("is_merged") == True and i.get("is_merge_start")) else i for i in segments_ser.data]

        [i.update({"segment_count": j}) for i, j in zip(data, page_len)]

        res = self.get_paginated_response(data)

        res.status_code = status
        return res

# class TargetSegmentsListAndUpdateView(SourceSegmentsListView):
#
#     lookup_field = "temp_target"
#     def get_corrected_data(self, segments_ser, payload):
#
#         data = []
#         search_word = payload.get('payload', None)
#         match_case = payload.get("match_case", False)
#         exact_word = payload.get("exact_word", False)
#         status_list = payload.get("status_list", [])
#         lookup_field = self.lookup_field
#
#         for i in segments_ser.data:
#
#             if i.get("is_merged") == True and i.get('is_merge_start') == True:
#
#                 merged_segment = MergeSegment.objects.get(segments=Segment.objects.get(id=i.get("segment_id")))
#
#                 if status_list:
#                     if 0 in status_list or merged_segment.status_id in status_list:
#                         data.append(SegmentSerializer(merged_segment).data)
#                         continue
#
#                 if search_word not in [None, ""]:
#
#                     if match_case and exact_word:
#                         if re.search(f'(?<!\w){search_word}(?!\w)', merged_segment.temp_target):
#                             data.append(SegmentSerializer(merged_segment).data)
#                             continue
#
#                     elif not (match_case or exact_word):
#                         if re.search(f'{search_word}', merged_segment.temp_target):
#                             data.append(SegmentSerializer(merged_segment).data)
#                             continue
#
#                     elif match_case:
#                         if re.search(f'{search_word}', merged_segment.temp_target):
#                             data.append(SegmentSerializer(merged_segment).data)
#                             continue
#
#                     elif exact_word:
#                         if re.search(f'(?i)[^\w]{search_word}[^\w]', merged_segment.temp_target):
#                             data.append(SegmentSerializer(merged_segment).data)
#                             continue
#
#             elif i.get("is_merged") == True and i.get('is_merge_start') == False:
#                 continue
#
#             else:
#                 # data.append(i)
#                 normal_segment = Segment.objects.get(id=i.get("segment_id"))
#
#                 if status_list:
#                     if 0 in status_list or normal_segment.status_id in status_list:
#                         data.append(SegmentSerializer(normal_segment).data)
#                         continue
#
#                 if search_word not in [None, ""]:
#
#                     if match_case and exact_word:
#                         if re.search(f'(?<!\w){search_word}(?!\w)', normal_segment.temp_target):
#                             data.append(SegmentSerializer(normal_segment).data)
#                             continue
#
#                     elif not (match_case or exact_word):
#                         if re.search(f'{search_word}', normal_segment.temp_target):
#                             data.append(SegmentSerializer(normal_segment).data)
#                             continue
#
#                     elif match_case:
#                         if re.search(f'{search_word}', normal_segment.temp_target):
#                             data.append(SegmentSerializer(normal_segment).data)
#                             continue
#
#                     elif exact_word:
#                         if re.search(f'(?i)[^\w]{search_word}[^\w]', normal_segment.temp_target):
#                             data.append(SegmentSerializer(normal_segment).data)
#                             continue
#
#         return data
#     def paginate_response(self, segments, request, status, data, is_update=False):
#         page_segments = self.paginate_queryset(segments, request, view=self)
#         segments_ser = SegmentSerializer(page_segments, many=True)
#
#         if is_update:
#             data = [
#                 SegmentSerializer(MergeSegment.objects.get(segments=Segment.objects.get(id=i.get("segment_id")))).data
#                 if i.get("is_merged") == True else i for i in segments_ser.data]
#         else:
#             data = self.get_corrected_data(segments_ser, data)
#
#         res = self.get_paginated_response(data)
#         res.status_code = status
#         return res
#     def post(self, request, document_id):
#         data = self.prepare_data(request.POST.dict())
#         print("Data ===> ", data)
#         segments, segments_merged, status = self.get_queryset(request, data, document_id, self.lookup_field)
#         segment_final = segments.union(segments_merged).order_by('id')
#         return self.paginate_response(segment_final, request, status, data)
#     @staticmethod
#     def unconfirm_status(segment, merged_segment=None):
#
#         if segment.is_merged and segment.is_merge_start:
#             merged_segment.status_id = {102: 101, 104: 103, 106: 105}.get(
#                 merged_segment.status_id, merged_segment.status_id)
#
#         elif segment.is_merged and segment.is_merge_start == False:
#             pass
#
#         else:
#             segment.status_id = {102: 101, 104: 103, 106: 105}.get(
#                 segment.status_id, segment.status_id)
#
#     @staticmethod
#     def confirm_status(segment, merged_segment=None):
#
#         if segment.is_merged and segment.is_merge_start:
#             merged_segment.status_id = {101: 102, 103: 104, 105: 106}.get(
#                 merged_segment.status_id, merged_segment.status_id)
#
#         elif segment.is_merged and segment.is_merge_start == False:
#             pass
#
#         else:
#             segment.status_id = {101: 102, 103: 104, 105: 106}.get(
#                 segment.status_id, segment.status_id)
#     @staticmethod
#     def update_segments(request, data, segments, self):
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
#         else:
#             if match_case:
#                 regex = re.compile(search_word)
#             else:
#                 regex = re.compile(r'((?i)' + search_word + r')')
#
#         for instance in segments:
#
#             # if instance.get("is_merged") == True and instance.get('is_merge_start') == True:
#             if instance.is_merged == True and instance.is_merge_start == True:
#
#                 # merged_segment = MergeSegment.objects.get(segments=Segment.objects.get(id=instance.get("segment_id")))
#                 merged_segment = MergeSegment.objects.get(segments=Segment.objects.get(id=instance.id))
#
#                 self.unconfirm_status(instance, merged_segment)
#
#                 if do_confirm:
#                     self.confirm_status(instance, merged_segment)
#                     # merged_segment_serlzr = MergeSegmentSerializer(merged_segment, data={
#                     #     "temp_target": re.sub(regex, replace_word, merged_segment.temp_target),
#                     #     "status_id": merged_segment.status_id}, partial=True, context={"request": request})
#                     merged_segment.target = re.sub(regex, replace_word, merged_segment.temp_target)
#                     merged_segment.status_id = merged_segment.status_id
#                     merged_segment.save()
#
#                 else:
#                     self.unconfirm_status(instance, merged_segment)
#                     # merged_segment_serlzr = MergeSegmentSerializer(merged_segment, data={
#                     #     "temp_target":  re.sub(regex, replace_word, merged_segment.temp_target),
#                     #      "status_id": merged_segment.status_id}, partial=True, context={"request": request})
#
#                     merged_segment.temp_target = re.sub(regex, replace_word, merged_segment.temp_target)
#                     merged_segment.status_id = merged_segment.status_id
#                     merged_segment.save()
#
#                 # if merged_segment_serlzr.is_valid(raise_exception=True):
#                 #     merged_segment_serlzr.save()
#
#             elif instance.is_merged == True and instance.is_merge_start == False:
#                 continue
#
#             else:
#
#                 self.unconfirm_status(instance)
#                 if do_confirm:
#                     self.confirm_status(instance)
#                     segment_serlzr = SegmentSerializerV2(instance, data={"target": \
#                                                                              re.sub(regex, replace_word,
#                                                                                     instance.temp_target),
#                                                                          "status_id": instance.status_id}, \
#                                                          partial=True, context={"request": request})
#                 else:
#                     self.unconfirm_status(instance)
#                     segment_serlzr = SegmentSerializerV2(instance, data={"temp_target": \
#                                                                              re.sub(regex, replace_word,
#                                                                                     instance.temp_target),
#                                                                          "status_id": instance.status_id}, \
#                                                          partial=True, context={"request": request})
#
#                 if segment_serlzr.is_valid(raise_exception=True):
#                     segment_serlzr.save()
#
#         return segments, 200
#
#     def update(self, request, document_id):
#         data = self.prepare_data(request.POST.dict())
#         print("Prepared data ===> ", data)
#         segments, segments_merged, status = self.get_queryset(request, data, document_id, self.lookup_field)
#
#         segment_final = segments.union(segments_merged).order_by('id')
#
#         segments, status = self.update_segments(request, data, segment_final, self=self)
#         return self.paginate_response(segments, request, status, data, is_update=True)

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
        page_len = self.paginate_queryset(range(1, segments.count() + 1), request)
        page_segments = self.paginate_queryset(segments, request, view=self)
        segments_ser = SegmentSerializer(page_segments, many=True)

        data = [SegmentSerializer(MergeSegment.objects.get(id=i.get("segment_id"))).data
                if (i.get("is_merged") == True and i.get("is_merge_start")) else i for i in segments_ser.data]

        [i.update({"segment_count": j}) for i, j in zip(data, page_len)]

        res = self.get_paginated_response(data)

        res.status_code = status
        return res

    def post(self, request, document_id):
        data = self.prepare_data(request.POST.dict())
        segments, status = self.get_queryset(request, data, document_id, self.lookup_field)
        print("seg------------>",segments)
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
                # regex = re.compile(f'(?<!\w)(?i){search_word}(?!\w)')
                regex = re.compile(f'(?i)[^\w]{search_word}[^\w]')  # temp regex
        else:
            if match_case:
                regex = re.compile(search_word)
            else:
                regex = re.compile(r'((?i)' + search_word + r')')

        for instance in segments:
            instance = instance.get_active_object()
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

class FindAndReplaceTargetBySegment(TargetSegmentsListAndUpdateView):

    @staticmethod
    def get_object(segment_id):
        segments = Segment.objects.all()
        obj = get_object_or_404(segments, id=segment_id)
        return  obj

    def put(self, request, segment_id):
        segment = self.get_object(segment_id)
        data = self.prepare_data(request.POST.dict())
        search_word = data.get('search_word', '')
        replace_word = data.get('replace_word', '')
        match_case = data.get('match_case', False)
        exact_word = data.get('exact_word', False)
        do_confirm = data.get("do_confirm", False)

        if exact_word:
            if match_case:
                regex = re.compile(f'(?<!\w){search_word}(?!\w)')
            else:
                # regex = re.compile(f'(?<!\w)(?i){search_word}(?!\w)')
                regex = re.compile(f'(?i)[^\w]{search_word}[^\w]')  # temp regex

        else:
            if match_case:
                regex = re.compile(search_word)
            else:
                regex = re.compile(r'((?i)' + search_word + r')')

        segment.temp_target = re.sub(regex, replace_word, segment.temp_target)
        self.unconfirm_status(segment)
        if do_confirm:
            segment.target = segment.temp_target
            self.confirm_status(segment)
        segment.save()
        return  Response(SegmentSerializer(segment).data, status=200)

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

            if (seg.is_merged == True and seg.is_merge_start is None):
                continue
            else:
                total_seg_count += 1

            seg_new = seg.get_active_object()
            if seg_new.status_id in confirm_list:
                confirm_count += 1

        return total_seg_count, confirm_count

    def get(self, request, document_id):
        document = self.get_object(document_id)
        total_segment_count, segments_confirmed_count = self.get_progress(document)
        return JsonResponse(
            dict(total_segment_count=total_segment_count,
                 segments_confirmed_count=segments_confirmed_count), safe=False
        )

class FontSizeView(views.APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get_object(data, request):
        obj = FontSize.objects.filter(ai_user_id=request.user.id, language_id=data.get("language", None)).first()
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
            segment = get_object_or_404(Segment.objects.all(), id=id)
            return segment.segment_comments_set.all()

        if by=="document":
            document = get_object_or_404(Document.objects.all(), id=id)
            return [ comment
                for segment in document.segments.all()
                for comment in segment.segment_comments_set.all()
            ]
        return Comment.objects.none()

    def list(self, request):
        objs = self.get_list_of_objects(request)
        ser = CommentSerializer(objs, many=True)
        return Response(ser.data, status=200)

    def create(self, request):
        ser = CommentSerializer(data=request.POST.dict(), )
        if ser.is_valid(raise_exception=True):
            ser.save()
            return Response(ser.data, status=201)

    def retrieve(self, request, pk=None):
        obj = self.get_object(comment_id=pk)
        return Response(CommentSerializer(obj).data, status=200)

    def update(self, request, pk=None):
        obj = self.get_object(comment_id=pk)
        ser = CommentSerializer(obj, data=request.POST.dict(), partial=True)
        if ser.is_valid(raise_exception=True):
            ser.save()
            return Response(ser.data, status=202)

    def destroy(self, request, pk=None):
        obj = self.get_object(comment_id=pk)
        obj.delete()
        return  Response({},204)

class GetPageIndexWithFilterApplied(views.APIView):

    def get_queryset(self, document_id, status_list):
        doc = get_object_or_404(Document.objects.all(), id=document_id)
        # status_list = data.get("status_list")
        if '0' in status_list:
            segments = doc.segments.filter(Q(status=None)|\
                        Q(status__status_id__in=status_list)).all()
        else:
            segments = doc.segments.filter(status__status_id__in=status_list).all()
        return  segments

    def post(self, request, document_id, segment_id):
        print( "data---->", request.data )
        status_list = request.data.get("status_list", [])
        print("status list", status_list + [] )
        segments = self.get_queryset(document_id, status_list)
        print("segments---->", segments)
        if not segments:
            return Response( {"detail": "No segment found"}, 404 )
        ids = [
            segment.id for segment in segments
        ]

        try:
            res = ({"page_id": (ids.index(segment_id)//20)+1}, 200)
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
        obj = Segment.objects.get(id=seg_id)
        history = obj.segment_history.all().order_by('-id')
        ser = SegmentHistorySerializer(history,many=True)
        return Response(ser.data)
    except Segment.DoesNotExist:
        return Response({'msg':'Not found'}, status=404)
####################################################### Hemanth #########################################################

@api_view(['POST',])############### only available for english ###################
def paraphrasing(request):
    sentence = request.POST.get('sentence')
    try:
        text = {}
        text['sentence'] = sentence
        end_pts = settings.END_POINT +"paraphrase/"
        data = requests.post(end_pts , text)
        return JsonResponse(data.json())
    except:
        return JsonResponse({"message":"error in paraphrasing connect"},safe=False)



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
@api_view(['GET',])
@permission_classes([IsAuthenticated])
def download_audio_output_file(request):
    from ai_workspace.models import MTonlytaskCeleryStatus
    celery_id = request.GET.get('celery_id')
    document_id = request.GET.get('document_id')
    doc = Document.objects.get(id=document_id)
    task = doc.task_set.first()
    cel_task = MTonlytaskCeleryStatus.objects.filter(task = doc.task_set.first()).last()
    state = google_long_text_file_process_cel.AsyncResult(cel_task.celery_task_id).state
    if state == 'SUCCESS':
        return download_file(task.task_transcript_details.last().translated_audio_file.path)
    elif state == 'FAILURE':
        return Response({'msg':'Failure'},status=400)
    else:
        return Response({'msg':'Pending'},status=400)


@api_view(['GET',])
@permission_classes([IsAuthenticated])
def download_converted_audio_file(request):
    document_id = request.GET.get('document_id')
    doc = Document.objects.get(id=document_id)
    task = doc.task_set.first()
    return download_file(task.task_transcript_details.last().translated_audio_file.path)
