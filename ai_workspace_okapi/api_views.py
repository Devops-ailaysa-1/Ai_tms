from datetime import datetime
from .serializers import (DocumentSerializer, SegmentSerializer, DocumentSerializerV2,
                          SegmentSerializerV2, MT_RawSerializer, DocumentSerializerV3,
                          TranslationStatusSerializer, FontSizeSerializer, CommentSerializer,
                          TM_FetchSerializer)
from ai_workspace.serializers import TaskCreditStatusSerializer, TaskSerializer
from .models import Document, Segment, MT_RawTranslation, TextUnit, TranslationStatus, FontSize, Comment
from rest_framework import viewsets, authentication
from rest_framework import views
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from ai_auth.models import AiUser, UserAttribute, UserCredits
from ai_staff.models import AiUserType,SpellcheckerLanguages
from django.http import HttpResponse
from ai_workspace.models import Task, TaskCreditStatus
from rest_framework.response import  Response
from rest_framework.views import APIView
from django.db.models import F, Q
import requests, boto3
import json, os, re, time, jwt, xlsxwriter
import pickle
import logging
from rest_framework.exceptions import APIException
from spellchecker import SpellChecker
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from django.http import  HttpResponse, JsonResponse
from .okapi_configs import CURRENT_SUPPORT_FILE_EXTENSIONS_LIST
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from django.http import  FileResponse
from rest_framework.views import APIView
from django.db.models import Q
import urllib.parse
from .serializers import PentmUpdateSerializer
from wiktionaryparser import WiktionaryParser
from ai_workspace.api_views import UpdateTaskCreditStatus
from django.urls import reverse
from json import JSONDecodeError
from ai_workspace.models import File
from .utils import SpacesService,text_to_speech
from django.contrib.auth import settings
from ai_auth.utils import get_plan_name
from .utils import download_file, bl_title_format, bl_cell_format


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
        print("remove keys--->", remove_keys)
        [data.pop(i) for i in remove_keys]
        if check_fields != []:
            raise ValueError("OKAPI request fields not setted correctly!!!")

    @staticmethod
    def create_document_for_task_if_not_exists(task):

        if task.document != None:
            print("*** Document exists *****")
            return task.document

        elif Document.objects.filter(file_id=task.file_id).exists():
            doc = Document.objects.filter(file_id=task.file_id).last()
            doc_data = DocumentSerializerV3(doc).data

            serializer = (DocumentSerializerV2(data={**doc_data,\
                                    "file": task.file.id, "job": task.job.id,
                                },))
            if serializer.is_valid(raise_exception=True):
                document = serializer.save()
                task.document = document
                print("********   Document written using existing file  ***********")
                task.save()

        else:
            ser = TaskSerializer(task)
            data = ser.data
            DocumentViewByTask.correct_fields(data)
            # print("data--->", data)
            params_data = {**data, "output_type": None}
            res_paths = {"srx_file_path":"okapi_resources/okapi_default_icu4j.srx",
                         "fprm_file_path": None,
                         "use_spaces" : settings.USE_SPACES
                         }
            doc = requests.post(url=f"http://{spring_host}:8080/getDocument/", data={
                "doc_req_params":json.dumps(params_data),
                "doc_req_res_params": json.dumps(res_paths)
            })

            if doc.status_code == 200 :
                doc_data = doc.json()
                # print("Doc data from spring---> ", doc_data)
                serializer = (DocumentSerializerV2(data={**doc_data,\
                                    "file": task.file.id, "job": task.job.id,
                                },))
                if serializer.is_valid(raise_exception=True):
                    document = serializer.save()
                    task.document = document
                    task.save()
            else:
                # logging.debug(msg=f"error raised while process the document, the task id is {task.id}")
                logger.info(">>>>>>>> Something went wrong with file reading <<<<<<<<<")
                raise  ValueError("Sorry! Something went wrong with file processing.")

        return document

    def get(self, request, task_id, format=None):
        task = self.get_object(task_id=task_id)
        document = self.create_document_for_task_if_not_exists(task)
        # page_segments = self.paginate_queryset(document.segments, request, view=self)
        # segments_ser = SegmentSerializer(page_segments, many=True)
        # return self.get_paginated_response(segments_ser.data)
        doc = DocumentSerializerV2(document).data
        return Response(doc, status=201)


class DocumentViewByDocumentId(views.APIView):
    @staticmethod
    def get_object(document_id):
        docs = Document.objects.all()
        document = get_object_or_404(docs, id=document_id)
        return  document

    def get(self, request, document_id):
        #doc_user = AiUser.objects.get(project__project_jobs_set__file_job_set=document_id).id
        doc_user = AiUser.objects.get(project__project_jobs_set__file_job_set=document_id)
        team_members = doc_user.get_team_members if doc_user.get_team_members else []
        hired_editors = doc_user.get_hired_editors if doc_user.get_hired_editors else []
        if (request.user == doc_user) or (request.user in team_members) or (request.user in hired_editors):
            dict = {'download':'enable'} if (request.user == doc_user) else {'download':'disable'}
            document = self.get_object(document_id)
            data = DocumentSerializerV2(document).data
            data.update(dict)
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
        segments = document.segments_without_blank
        len_segments = segments.count()
        page_len = self.paginate_queryset(range(1,len_segments+1), request)
        # print(page_len)
        page_segments = self.paginate_queryset(segments, request, view=self)
        segments_ser = SegmentSerializer(page_segments, many=True)
        [i.update({"segment_count":j}) for i,j in  zip(segments_ser.data, page_len)]
        return self.get_paginated_response(segments_ser.data)

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
    @staticmethod
    def get_object(segment_id):
        qs = Segment.objects.all()
        segment = get_object_or_404(qs, id = segment_id)
        return segment

    @staticmethod
    def get_update(segment, data,request):
        segment_serlzr = SegmentSerializerV2(segment, data=data, partial=True,\
            context={"request": request})
        if segment_serlzr.is_valid(raise_exception=True):
            segment_serlzr.save()
            return segment_serlzr
        else:
            logger.info(">>>>>>>> Error in Segment update <<<<<<<<<")
            return segment_serlzr.errors

    def update_pentm(self, segment):
        data = PentmUpdateSerializer(segment).data
        res = requests.post(f"http://{spring_host}:8080/project/pentm/update", data=data)
        print("Response from spring --- >", res.json())
        if res.status_code == 200:
            print("res text--->", res.json())
        else:
            print("not successfully update")

    def update(self, request, segment_id):
        segment = self.get_object(segment_id)
        segment_serlzr = self.get_update(segment, request.data, request)
        # self.update_pentm(segment)  # temporarily commented to solve update pentm issue
        return Response(segment_serlzr.data, status=201)

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
    def get_data(request, segment_id):
        mt_raw = MT_RawTranslation.objects.filter(segment_id=segment_id).first()
        if mt_raw:
            return MT_RawSerializer(mt_raw).data, 200, "available"

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

        segment_source = Segment.objects.get(id=segment_id).source
        seg_data = {"segment_source":segment_source, "source_language":doc.source_language_code, "target_language":doc.target_language_code,\
                     "processor_name":"plain-text-processor", "extension":".txt"}

        res = requests.post(url=f"http://{spring_host}:8080/segment/word_count", \
            data={"segmentWordCountdata":json.dumps(seg_data)})
        if res.status_code == 200:
            print("Word count --->", res.json())
            consumable_credits = res.json()
        else:
            logger.info(">>>>>>>> Error in segment word count calculation <<<<<<<<<")
            raise  ValueError("Sorry! Something went wrong with word count calculation.")

        if initial_credit > consumable_credits :
            mt_raw_serlzr = MT_RawSerializer(data = {"segment": segment_id},\
                            context={"request": request})
            if mt_raw_serlzr.is_valid(raise_exception=True):
                mt_raw_serlzr.save()
                debit_status, status_code = UpdateTaskCreditStatus.update_credits(request, doc.id, consumable_credits)
                # print("DEBIT STATUS -----> ", debit_status["msg"])
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

    def get(self, request, segment_id):
        data, status_code, can_team = self.get_data(request, segment_id)
        # print("MT Data -----> ", data)
        mt_alert = True if status_code == 424 else False
        alert_msg = "MT doesn't work as the credits are insufficient. Please buy more or upgrade." if (status_code == 424 and \
            can_team == "unavailable") else "Team subscription inactive"
        tm_data = self.get_tm_data(request, segment_id)
        return Response({**data, "tm":tm_data, "mt_alert": mt_alert,
            "alert_msg":alert_msg}, status=status_code)

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
            response['X-Suggested-Filename'] = encoded_filename
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Headers"] = "*"
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


    #For Downloading Audio File################only for voice project###########
    def download_audio_file(self,res,document_id,voice_gender,language_locale):
        if res.status_code in [200, 201]:
            file_path = res.text
            doc = DocumentToFile.get_object(document_id)
            task = doc.task_set.first()
            ser = TaskSerializer(task)
            task_data = ser.data
            filename, ext = os.path.splitext(self.get_source_file_path(document_id).split('source/')[1])
            target_language = language_locale if language_locale else task_data["target_language"]
            res1 = text_to_speech(file_path,target_language,filename,voice_gender)
            return download_file(res1)
        else:
            return Response({"msg":"something went wrong"})



    # FOR DOWNLOADING BILINGUAL FILE
    def remove_tags(self, string):
        return re.sub(r'</?\d+>', "", string)
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
                worksheet.write(row, 0, segment.source.strip(), cell_format)
                worksheet.write(row, 1, self.remove_tags(segment.target), cell_format)
                row += 1
        workbook.close()

        # return JsonResponse({"msg": "file successfully created"}, safe=False)
        return download_file(bilingual_file_path)


    def get(self, request, document_id):
        token = request.GET.get("token")
        output_type = request.GET.get("output_type", "")
        voice_gender = request.GET.get("voice_gender", "FEMALE")
        language_locale = request.GET.get("locale", None)
        payload = jwt.decode(token, settings.SECRET_KEY, ["HS256"])
        user_id_payload = payload.get("user_id", 0)
        user_id_document = AiUser.objects.get(project__project_jobs_set__file_job_set=document_id).id
        if user_id_payload == user_id_document:

            # FOR DOWNLOADING SOURCE FILE
            if output_type == "SOURCE":
                return self.download_source_file(document_id)

            # FOR DOWNLOADING BILINGUAL FILE
            if output_type == "BILINGUAL":
                return self.download_bilingual_file(document_id)

            # For Downloading Audio File
            if output_type == "AUDIO":
                res = self.document_data_to_file(request, document_id)
                return self.download_audio_file(res,document_id,voice_gender,language_locale)

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
        res_paths = {"srx_file_path":"okapi_resources/okapi_default_icu4j.srx",
                     "fprm_file_path": None,
                     "use_spaces" : settings.USE_SPACES
                     }

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

class SourceSegmentsListView(viewsets.ViewSet, PageNumberPagination):
    PAGE_SIZE = page_size = 20
    lookup_field = "source"

    @staticmethod
    def prepare_data(data):
        for i in data:
            try:
                data[i] = json.loads(data[i])
            except:
                pass
        return data

    @staticmethod
    def get_queryset(request, data, document_id, lookup_field):
        qs = Document.objects.all()
        document = get_object_or_404(qs, id=document_id)
        segments_all = segments = document.segments
        status_list = data.get("status_list", [])
        print("status_list--->", status_list)
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
                    f'__contains':f'{search_word}'})
            elif match_case:
                segments = segments.filter(**{f'{lookup_field}'
                    f'__regex':f'{search_word}'})
            elif exact_word:
                # segments = segments.filter(**{f'{lookup_field}__regex':f'(?<!\w)(?i){search_word}(?!\w)'})
                segments = segments.filter(**{f'{lookup_field}'
                    f'__regex':f'(?i)[^\w]{search_word}[^\w]'})  # temp regex

        return segments, 200

    def post(self, request, document_id):
        data = self.prepare_data(request.POST.dict())
        segments, status = self.get_queryset(request, data, document_id, self.lookup_field)
        page_segments = self.paginate_queryset(segments, request, view=self)
        segments_ser = SegmentSerializer(page_segments, many=True)
        res = self.get_paginated_response(segments_ser.data)
        res.status_code = status
        return res

class TargetSegmentsListAndUpdateView(SourceSegmentsListView):
    lookup_field = "temp_target"

    @staticmethod
    def unconfirm_status(segment):
        segment.status_id = {102:101, 104:103, 106:105}.get(
            segment.status_id, segment.status_id)

    @staticmethod
    def confirm_status(segment):
        segment.status_id = {101:102, 103:104, 105:106}.get(
            segment.status_id, segment.status_id)

    def paginate_response(self, segments, request, status):
        page_segments = self.paginate_queryset(segments, request, view=self)
        segments_ser = SegmentSerializer(page_segments, many=True)
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
                # regex = re.compile(f'(?<!\w)(?i){search_word}(?!\w)')
                regex = re.compile(f'(?i)[^\w]{search_word}[^\w]')  # temp regex
        else:
            if match_case:
                regex = re.compile(search_word)
            else:
                regex = re.compile(r'((?i)' + search_word + r')')

        for instance in segments:
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
    confirm_list = [102, 104, 106]

    @staticmethod
    def get_object(document_id):
        document = get_object_or_404(
            Document.objects.all(), id=document_id
        )
        return document

    @staticmethod
    def get_progress(document, confirm_list):
        # total_segment_count = document.total_segment_count - document.segments_with_blank.count()
        total_segment_count = Segment.objects.filter(
            text_unit__document=document
        ).count()
        segments_confirmed_count = document.segments.filter(
            status__status_id__in=confirm_list
        ).count()
        return total_segment_count, segments_confirmed_count

    def get(self, request, document_id):
        document = self.get_object(document_id)
        total_segment_count, segments_confirmed_count = self.get_progress(document, self.confirm_list)
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
def WikipediaWorkspace(request,doc_id):
    data=request.GET.dict()
    lang_list = ["zh-Hans","zh-Hant"]
    user_input=data.get("term")
    term_type=data.get("term_type","source")
    user_input=user_input.strip()
    user_input=user_input.strip('0123456789')
    doc = Document.objects.get(id=doc_id)
    src = doc.source_language_code if doc.source_language_code not in lang_list else "zh"
    tar = doc.target_language_code if doc.target_language_code not in lang_list else "zh"
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
def WiktionaryWorkSpace(request,doc_id):
    data=request.GET.dict()
    lang_list = ["zh-Hans","zh-Hant"]
    user_input=data.get("term")
    term_type=data.get("term_type")
    user_input=user_input.strip()
    user_input=user_input.strip('0123456789')
    doc = Document.objects.get(id=doc_id)
    src = doc.source_language_code if doc.source_language_code not in lang_list else "zh"
    tar = doc.target_language_code if doc.target_language_code not in lang_list else "zh"
    if term_type=="source":
        codesrc =src
        code = tar
    elif term_type=="target":
        codesrc = tar
        code = src
    res=wiktionary_ws(code,codesrc,user_input)
    return JsonResponse({"out":res}, safe = False,json_dumps_params={'ensure_ascii':False})


######  USING PY SPELLCHECKER  ######
@api_view(['GET', 'POST',])
def spellcheck(request):
    tar = request.POST.get('target')
    doc_id = request.POST.get('doc_id')
    doc = Document.objects.get(id=doc_id)
    out,res = [],[]
    try:
        spellchecker=SpellcheckerLanguages.objects.get(language_id=doc.target_language_id).spellchecker.spellchecker_name
        if spellchecker=="pyspellchecker":
            code = doc.target_language_code
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
