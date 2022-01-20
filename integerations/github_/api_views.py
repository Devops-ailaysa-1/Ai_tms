from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import permissions
from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
import requests, json, os,mimetypes
from rest_framework.decorators import api_view
from datetime import datetime, timedelta
from django.db.models import Q
from rest_framework.decorators import permission_classes
from rest_framework import serializers
from django.http import JsonResponse, Http404, HttpResponse
import rest_framework
from rest_framework.renderers import JSONRenderer
from django.core.files.uploadedfile import InMemoryUploadedFile

from .serializers import GithubOAuthTokenSerializer, RepositorySerializer,\
    BranchSerializer, ContentFileSerializer, LocalizeIdsSerializer,ProjectSerializer,\
    FileSerializer, JobSerializer, JobDataPrepareSerializer, FileDataPrepareSerializer,\
    GithubHookSerializerD1, GithubHookSerializerD2, HookDeckCallSerializer, \
    HookDeckResponseSerializer, HookDeckSerializer
from .models import GithubOAuthToken, Repository, FetchInfo, Branch, ContentFile, HookDeck
from .utils import DjRestUtils
from .tasks import update_files
from guardian.shortcuts import get_objects_for_user
from ai_workspace.models import Project, Task
from ai_auth.models import AiUser

import pytz, pickle,sys
from io import BytesIO
import pickle
from pymongo import MongoClient
cli = MongoClient ( 'localhost', 27017)
import hmac, hashlib
import os
import uuid
import cryptocode

CRYPT_PASSWORD = os.environ.get("CRYPT_PASSWORD")

@api_view(["POST"])
def repo_update_view(request, slug):
    decoded = cryptocode.decrypt(slug, CRYPT_PASSWORD)

    if not decoded:
        raise ValueError("Hook URL invalid!!!")

    user = AiUser.objects.filter(email=decoded).first()

    if (not user) or (user != request.user):
        raise ValueError("URL user doest not match with request user!!!")

    dump_data = pickle.dumps(request.data)
    db = cli["samples"]
    coll = db["github_hook_data"]
    coll.insert_one({"data": dump_data})
    gd = GithubHookSerializerD1(data=request.data)
    gd.is_valid(raise_exception=True)
    gd2 = GithubHookSerializerD2(data=gd.data.get("payload"))
    gd2.is_valid(raise_exception=True)
    data = gd2.data
    data["updated_files"] = { file for _ in data.get("commits") for file in _.get("modified") }

    repo_fullname, branch_name = data["repository"]["full_name"], data["ref"]

    for file_path in data["updated_files"] :
        update_files.delay(repo_fullname=repo_fullname,
            branch_name=branch_name, file_path=file_path)

    return Response(data)

def validate_signature(payload, secret):
    # Get the signature from the payload
    signature_header = payload['headers']['X-Hub-Signature']
    sha_name, github_signature = signature_header.split('=')
    if sha_name != 'sha1':
        print('ERROR: X-Hub-Signature in payload headers was not sha1=****')
        return False

    # Create our own signature
    body = payload['body']
    local_signature = hmac.new(secret.encode('utf-8'), msg=body.encode('utf-8'), digestmod=hashlib.sha1)

    # See if they match
    return hmac.compare_digest(local_signature.hexdigest(), github_signature)

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        return request.user.has_perm(f"github_.change_"
            f"{obj.__class__.__name__.lower()}", obj)


class GithubOAuthTokenViewset(viewsets.ModelViewSet):
    serializer_class = GithubOAuthTokenSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def create(self, request, *args, **kwargs):
        data = request.data.dict()

        print("id---->", request.user.id)
        serlzr_obj = GithubOAuthTokenSerializer(data={**data,
            "ai_user": request.user.id})

        print("initial data---->", serlzr_obj.initial_data)
        if serlzr_obj.is_valid(raise_exception=True):
            serlzr_obj.save()
            return Response(serlzr_obj.data, status=201)

    def get_queryset(self):
        return  get_objects_for_user(self.request.user,
            'github_.change_githuboauthtoken')
        # return GithubOAuthToken.objects\
            #.all()#.filter(ai_user=self.request.user)\


    # def get_object(self):
    #     obj = super(GithubOAuthTokenViewset, self).get_object()
    #     if obj.ai_user == self.request.user:
    #         return obj
    #     raise Http404

class RepositoryViewset(viewsets.ModelViewSet):
    serializer_class = RepositorySerializer
    permission_classes = [IsOwnerOrReadOnly]
    model = Repository

    def get_queryset(self):
        pk = self.kwargs.get("pk", None)
        if pk == None:
            raise ValueError("Primary Key is missing to fetch...")

        github_oauth_token = get_object_or_404(
            GithubOAuthToken.objects.all(), id=pk)
        # ================ perm =========================
        perm = self.request.user.has_perm("github_.change_githuboauthtoken",
                github_oauth_token)
        print("perm--->", perm)
        if not perm:
            raise ValueError("You have not permitted to access")
        # ================ perm ========================
        fetch_info, created = FetchInfo.objects.\
            get_or_create(github_token=github_oauth_token)

        if created or (datetime.now(tz=pytz.UTC) - timedelta(days=2) >
                fetch_info.last_fetched_on):
            Repository.create_all_repositories_of_github(github_token_id=pk)
            fetch_info.save() # updating last fetch time

        qs = get_objects_for_user(self.request.user,
                             'github_.change_repository')

        objects = get_list_or_404(qs, github_token_id=pk)
        return objects

    # def get_object(self):
    #     pk = self.kwargs.get("pk", None)
    #     if pk == None:
    #         raise ValueError("Primary Key is missing to fetch...")
    #
    #

    # def list(self, request, pk=None):#pk ---> github oauth pk
    #     qs = self.get_queryset()
    #     return JsonResponse(data={"data": "checking"}, safe=False)
    #     # self.kwargs[]
    #     # serlzr = RepositorySerializer()


class BranchViewset(viewsets.ModelViewSet):
    serializer_class = BranchSerializer

    def get_queryset(self):
        print("this qs")
        pk = self.kwargs.get("pk", None)
        if pk == None:
            raise ValueError("Primary Key is missing to fetch...")

        repo = get_object_or_404(Repository.objects.all(), id=pk)

        perm = self.request.user.has_perm("github_.change_repository",
                repo)

        if not perm:
            raise ValueError("You have not permitted to access....")

        qs = Branch.objects.filter(repo=repo).all()
        if not qs:
            print("if loop")
            Branch.create_all_branches(repo=repo)

        qs = get_objects_for_user(self.request.user,
                             'github_.change_branch')

        objects = get_list_or_404(qs, repo_id=pk)
        return objects

    # def list(self, request, *args, **kwargs):


class ContentFileViewset(viewsets.ModelViewSet):
    serializer_class = ContentFileSerializer

    def get_queryset(self):

        pk = self.kwargs.get("pk", None)
        if pk == None:
            raise ValueError("Primary Key is missing to fetch...")

        branch = get_object_or_404(Branch.objects.all(), id=pk)

        perm = self.request.user.has_perm("github_.change_branch",
                branch)

        if not perm:
            raise ValueError("You have not permitted to access....")

        qs = ContentFile.objects.filter(branch=branch).all()
        if not qs:
            print("if loop")
            ContentFile.create_all_contentfiles(branch=branch)

        qs = get_objects_for_user(self.request.user,
                             'github_.change_contentfile')

        objects = get_list_or_404(qs, branch_id=pk)

        return objects

    def create(self, request, *args, **kwargs):

        qs = self.get_queryset()

        print("--->", qs[0].id)

        serlzr1 = LocalizeIdsSerializer(data=request.data)

        if serlzr1.is_valid(raise_exception=True):
            data = serlzr1.data

        data = [{"is_localize_registered": True, "id": _}
                for _ in data.get('localizable_ids')]

        ser = ContentFileSerializer(qs, data=data, many=True, partial=True)

        if ser.is_valid(raise_exception=True):
            ser.save()
            data = ser.data

        serlzr = ProjectSerializer(data=request.data, )
        if serlzr.is_valid(raise_exception=True):
            serlzr.save(ai_user=request.user)
            # return Response(serlzr.data, status=200)
            project_data = serlzr.data
            project = serlzr.instance

        serlzr = JobDataPrepareSerializer(data=[request.data], many=True)
        if serlzr.is_valid(raise_exception=True):
            job_serlz_data = serlzr.data[0]

        serlzr = JobSerializer(data=job_serlz_data, many=True)
        if serlzr.is_valid(raise_exception=True):
            serlzr.save(project=project)
            job_data, jobs = serlzr.data, serlzr.instance

        im_uploads, contentfile_ids = [], []
        for _ in data:
            contentfile_ids.append(_.get("id"))
            content_file = ContentFile.objects.get(id=_.get("id"))
            # print("contents---->", content_file.get_content_of_file.decoded_content)
            im = DjRestUtils.convert_content_to_inmemoryfile(
                filecontent=content_file.get_content_of_file.decoded_content,
                file_name=_.get("file"))
            im_uploads.append(im)

        serlzr = FileDataPrepareSerializer(data=[{"files": im_uploads,
            "content_files": contentfile_ids,"usage_type": 1}], many=True)
        if serlzr.is_valid(raise_exception=True):
            file_serlz_data = serlzr.data[0]

        serlzr = FileSerializer(data=file_serlz_data, many=True)
        if serlzr.is_valid(raise_exception=True):
            serlzr.save(project=project)
            file_data, files = serlzr.data, serlzr.instance

        tasks = Task.objects.create_tasks_of_files_and_jobs_by_project(project=project)

        hookdeck = HookDeck.create_hookdeck_for_project(project=project)

        data = HookDeckSerializer(hookdeck,context={"for_hook_api_call": True}).data

        hookdeck_req_data = HookDeckCallSerializer(data=data)

        hookdeck_req_data.is_valid(raise_exception=True)

        res_json = HookDeck.create_or_get_hookdeck_url_for_data(
            data= JSONRenderer().render(data=hookdeck_req_data.data).decode())

        ser = HookDeckResponseSerializer(data=res_json)
        if ser.is_valid(raise_exception=True):
            url = ser.data["url"]

        hookdeck.hookdeck_url = url
        hookdeck.save()

        return  Response({"project":project_data, "hook": HookDeckSerializer(hookdeck).data})

class TestProjectView(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()

    def create(self, request, *args, **kwargs):
        serlzr = ProjectSerializer(data=request.data,)

        if serlzr.is_valid(raise_exception=True):
            serlzr.save(ai_user=request.user)
            return Response(serlzr.data, status=200)

class TestFIleView(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()

    def create(self, request, *args, **kwargs):
        serlzr = FileSerializer(data=request.data, many=True)

        if serlzr.is_valid(raise_exception=True):
            serlzr.save(project=Project.objects.last())
            return Response(serlzr.data, status=200)


        #
        # coll_ids = []
        #
        # for id in register_localize_ids:
        #     if id in dict_qs:
        #         obj = dict_qs[id]
        #         obj.is_loalize_registered = True
        #         obj.save()
        #         coll_ids.append(id)
        #
        # # May be celery tasks will required for file uploading
        # print("tl---->", request.data.pop("target_languages"))






