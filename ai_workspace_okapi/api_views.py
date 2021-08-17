from .serializers import (DocumentSerializer, SegmentSerializer, DocumentSerializerV2,
                          SegmentSerializerV2, MT_RawSerializer, DocumentSerializerV3,
                          TranslationStatusSerializer, FontSizeSerializer, CommentSerializer,
                          TM_FetchSerializer)
from ai_workspace.serializers import TaskSerializer
from .models import Document, Segment, MT_RawTranslation, TranslationStatus, FontSize, Comment
from rest_framework import viewsets
from rest_framework import views
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from ai_auth.models import AiUser, UserAttribute
from ai_staff.models import AiUserType
from django.http import HttpResponse
from ai_workspace.models import Task
from rest_framework.response import  Response
from django.db.models import F
import requests
import json, os, re
import pickle
import logging
from rest_framework.exceptions import APIException
from rest_framework.pagination import PageNumberPagination
from django.http import  HttpResponse, JsonResponse
from .okapi_configs import CURRENT_SUPPORT_FILE_EXTENSIONS_LIST
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import JSONParser
from django.http import  FileResponse

logging.basicConfig(filename="server.log", filemode="a", level=logging.DEBUG, )

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
        # {'source_file_path': '/home/langscape/Documents/ailaysa_github/Ai_TMS/media/u98163/u98163p2/source/test1.txt',
        #  'source_language': 'sq', 'target_language': 'hy', 'document_url': '/workspace_okapi/document/4/',
        #  'filename': 'test1.txt', 'extension': '.txt', 'processor_name': 'plain-text-processor'}
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
    def create_document_for_task_if_not_exists(task, request):
        document = task.document
        if (not document) and  (not Document.objects.filter(job=task.job, file=task.file).all()):
            ser = TaskSerializer(task)
            data = ser.data
            DocumentViewByTask.correct_fields(data)
            print("data--->", data)
            params_data = {**data, "output_type": None}
            res_paths = {"srx_file_path":"okapi_resources/okapi_default_icu4j.srx",
                         "fprm_file_path": None
                         }
            doc = requests.post(url=f"http://{spring_host}:8080/getDocument/", data={
                "doc_req_params":json.dumps(params_data),
                "doc_req_res_params": json.dumps(res_paths)
            })
            if doc.status_code == 200 :
                doc_data = doc.json()
                print("doc_data---->", doc_data)
                serializer = (DocumentSerializerV2(data={**doc_data,\
                                    "file": task.file.id, "job": task.job.id,
                                }, context={"request": request}))
                if serializer.is_valid(raise_exception=True):
                    document = serializer.save()
                    task.document = document
                    task.save()
            else:
                logging.debug(msg=f"error raised while process the document, the task id is {task.id}")
                raise  ValueError("Something went wrong in okapi file processing!!!")

        elif (not document):
            document = Document.objects.get(job=task.job, file=task.file)
            task.document = document
            task.save()
        return document

    def get(self, request, task_id, format=None):
        task = self.get_object(task_id=task_id)
        document = self.create_document_for_task_if_not_exists(task, request)
        # page_segments = self.paginate_queryset(document.segments, request, view=self)
        # segments_ser = SegmentSerializer(page_segments, many=True)
        # return self.get_paginated_response(segments_ser.data)
        return Response(DocumentSerializerV2(document).data, status=201)

class DocumentViewByDocumentId(views.APIView):
    @staticmethod
    def get_object(document_id):
        docs = Document.objects.all()
        document = get_object_or_404(docs, id=document_id)
        return  document

    def get(self, request, document_id):
        document = self.get_object(document_id)
        return Response(DocumentSerializerV2(document).data, status=200)

class SegmentsView(views.APIView, PageNumberPagination):
    PAGE_SIZE = page_size =  20

    def get_object(self, document_id):
        document = get_object_or_404(
            Document.objects.all(), id=document_id
        )
        return document

    def get(self, request, document_id):
        document = self.get_object(document_id=document_id)
        segments = document.segments
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
        segment_serlzr =  SegmentSerializerV2(segment, data=data, partial=True, context={"request": request})
        if segment_serlzr.is_valid(raise_exception=True):
            segment_serlzr.save()
            return segment_serlzr

    def update(self, request, segment_id):
        segment = self.get_object(segment_id)
        segment_serlzr = self.get_update(segment, request.data, request)
        return Response(segment_serlzr.data, status=201)

class MT_RawAndTM_View(views.APIView):

    @staticmethod
    def get_data(request, segment_id):
        mt_raw = MT_RawTranslation.objects.filter(segment_id=segment_id).first()
        if mt_raw:
            return MT_RawSerializer(mt_raw), 200

        mt_raw_serlzr = MT_RawSerializer(data = {"segment": segment_id}, context={"request": request})
        if mt_raw_serlzr.is_valid(raise_exception=True):
            # mt_raw_serlzr.validated_data[""]
            mt_raw_serlzr.save()
            return mt_raw_serlzr, 201

    @staticmethod
    def get_tm_data(request, segment_id):
        segment = Segment.objects.filter(id=segment_id).first()
        if segment:
            tm_ser = TM_FetchSerializer(segment)
            res = requests.post( f'http://{spring_host}:8080/pentm/source/search', data = {'pentmsearchparams': json.dumps( tm_ser.data) })
            if res.status_code == 200:
                return res.json()
            else:
                return []
        return []

    def get(self, request, segment_id):
        data, status_code = self.get_data(request, segment_id)
        tm_data = self.get_tm_data(request, segment_id)
        return Response({**data.data, "tm":tm_data}, status=status_code)

class ConcordanceSearchView(views.APIView):

    @staticmethod
    def get_concordance_data(request, segment_id, search_string):
        segment = Segment.objects.filter(id=segment_id).first()
        if segment:
            tm_ser_data = TM_FetchSerializer(segment).data
            tm_ser_data.update({'search_source_string':search_string, "max_hits":20, "threshold": 10})
            res = requests.post( f'http://{spring_host}:8080/pentm/source/search', data = {'pentmsearchparams': json.dumps( tm_ser_data) })
            if res.status_code == 200:
                return res.json()
            else:
                return []
        return []

    def get(self, request, segment_id):
        search_string = request.GET.get("string", None)
        concordance = []
        if search_string:
            concordance = self.get_concordance_data(request, segment_id, search_string)
        return Response(concordance, status=200)

class DocumentToFile(views.APIView):
    permission_classes = []
    @staticmethod
    def get_object(document_id):
        qs = Document.objects.all()
        document = get_object_or_404(qs, id=document_id)
        return  document

    def get(self, request, document_id):
        res = self.document_data_to_file(request, document_id)
        if res.status_code in [200, 201]:
            file_path = res.text
            if os.path.isfile(res.text):
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as fh:
                        response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
                        response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
                        response["Access-Control-Allow-Origin"] = "*"
                        response["Access-Control-Allow-Headers"] = "*"
                        # print("response headers---->",  response.headers)
                        return response
            # return JsonResponse({"output_file_path": res.text}, status=201)
        return JsonResponse({"msg": "something went to wrong in okapi file processing"}, status=409)

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
        if output_type == "XLIFF":
            ext = ".xliff"
        if output_type == "TMX":
            ext = ".tmx"
        task_data["output_file_path"] = pre + ext

        params_data = {**task_data, "output_type": output_type}
        res_paths = {"srx_file_path":"okapi_resources/okapi_default_icu4j.srx",
                     "fprm_file_path": None
                     }
        res = requests.post(
            f'http://{spring_host}:8080/getTranslatedAsFile/',
            data={
                'document-json-dump': json.dumps(data),
                "doc_req_res_params": json.dumps(res_paths),
                "doc_req_params": json.dumps(params_data),
            }
        )
        return res

OUTPUT_TYPES = dict(
    ORIGINAL = "ORIGINAL",
    XLIFF = "XLIFF",
    TMX = "TMX",
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

        if status_list:
            segments = segments.filter(status__status_id__in=status_list).all()

        search_word = data.get("search_word", None)

        if search_word not in [None, '']:

            match_case = data.get("match_case", False)
            exact_word = data.get("exact_word", False)

            if match_case and exact_word:
                segments = segments.filter(**{f'{lookup_field}__regex':f'(?<!\w){search_word}(?!\w)'})
            elif not(match_case or exact_word):
                segments = segments.filter(**{f'{lookup_field}__contains':f'{search_word}'})
            elif match_case:
                segments = segments.filter(**{f'{lookup_field}__regex':f'{search_word}'})
            elif exact_word:
                segments = segments.filter(**{f'{lookup_field}__regex':f'(?<!\w)(?i){search_word}(?!\w)'})

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
            segment.status_id, segment.status_id
        )


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

        if exact_word:
            if match_case:
                regex = re.compile(f'(?<!\w){search_word}(?!\w)')
            else:
                regex = re.compile(f'(?<!\w)(?i){search_word}(?!\w)')
        else:
            if match_case:
                regex = re.compile(search_word)
            else:
                regex = re.compile(r'((?i)' + search_word + r')')

        for instance in segments:
            instance.temp_target = re.sub(regex, replace_word, instance.temp_target)
            self.update_segments(instance)
            instance.save()

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

        if exact_word:
            if match_case:
                regex = re.compile(f'(?<!\w){search_word}(?!\w)')
            else:
                regex = re.compile(f'(?<!\w)(?i){search_word}(?!\w)')
        else:
            if match_case:
                regex = re.compile(search_word)
            else:
                regex = re.compile(r'((?i)' + search_word + r')')

        segment.temp_target = re.sub(regex, replace_word, segment.temp_target)
        self.unconfirm_status(segment)
        segment.save()
        print("segment---->", segment)
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
        total_segment_count = document.total_segment_count
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

