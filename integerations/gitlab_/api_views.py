from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer

from guardian.shortcuts import get_objects_for_user
from django.shortcuts import get_object_or_404, get_list_or_404
from django.db import transaction

from .serializers import GitlabOAuthTokenSerializer, RepositorySerializer,\
    BranchSerializer, ContentFileSerializer, FileDataPrepareSerializer, FileSerializer,\
    ProjectSerializer, JobDataPrepareSerializer, JobSerializer, LocalizeIdsSerializer
from ..base.utils import DjRestUtils
from .enums import DJ_APP_NAME, APP_NAME
from .models import GitlabApp, FetchInfo, Repository, Branch, ContentFile, DownloadProject
from integerations.github_.models import HookDeck
from integerations.github_.serializers import HookDeckSerializer, HookDeckCallSerializer,\
    HookDeckResponseSerializer
from ai_workspace.models import Project, Task

import pytz
from datetime import datetime, timedelta


class IsOwnerOrReadOnly(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        print("checked")
        return request.user.has_perm(f"gitlab_.change_"
            f"{obj.__class__.__name__.lower()}", obj)

class GitlabOAuthTokenViewset(viewsets.ModelViewSet):
    serializer_class = GitlabOAuthTokenSerializer
    permission_classes = [IsOwnerOrReadOnly, IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data = request.data.dict()

        print("id---->", request.user.id)
        serlzr_obj = GitlabOAuthTokenSerializer(data={**data,
            "ai_user": request.user.id})

        print("initial data---->", serlzr_obj.initial_data)
        if serlzr_obj.is_valid(raise_exception=True):
            serlzr_obj.save()
            return Response(serlzr_obj.data, status=201)

    def get_queryset(self):
        return  get_objects_for_user(self.request.user,
            f'{DJ_APP_NAME}.change_{APP_NAME}app')

class RepositoryViewset(viewsets.ModelViewSet):
    serializer_class = RepositorySerializer
    permission_classes = [IsOwnerOrReadOnly]
    model = Repository

    def get_queryset(self, refresh=False):
        pk = self.kwargs.get("pk", None)
        if pk == None:
            raise ValueError("Primary Key is missing to fetch...")

        gitlab_oauth_token = get_object_or_404(
            GitlabApp.objects.all(), id=pk)
        # ================ perm =========================
        perm = self.request.user.has_perm(f"{DJ_APP_NAME}.change_{APP_NAME}app",
                gitlab_oauth_token)
        print("perm--->", perm)
        if not perm:
            raise ValueError("You have not permitted to access")
        # ================ perm ========================
        fetch_info, created = FetchInfo.objects.\
            get_or_create(github_token=gitlab_oauth_token)

        print("condition--->", created or (datetime.now(tz=pytz.UTC) - timedelta(days=2) >
                fetch_info.last_fetched_on) or refresh)

        if created or (datetime.now(tz=pytz.UTC) - timedelta(days=2) >
                fetch_info.last_fetched_on) or refresh:
            Repository.create_all_repositories(gitlab_token_id=pk)
            fetch_info.save() # updating last fetch time

        qs = get_objects_for_user(self.request.user,
                             f'{DJ_APP_NAME}.owner_repository')

        objects = get_list_or_404(qs, gitlab_token_id=pk)
        return objects

    def list_refresh(self, request, *args, **kwargs):
        objects = self.get_queryset(refresh=True)
        return Response(self.serializer_class(objects, many=True).data, status=200)


class BranchViewset(viewsets.ModelViewSet):
    serializer_class = BranchSerializer

    def get_queryset(self, refresh=False):
        print("this qs")
        pk = self.kwargs.get("pk", None)
        if pk == None:
            raise ValueError("Primary Key is missing to fetch...")

        repo = get_object_or_404(Repository.objects.all(), id=pk)

        perm = self.request.user.has_perm(f"{DJ_APP_NAME}.owner_repository",
                repo)

        if not perm:
            raise ValueError("You have not permitted to access....")

        qs = Branch.objects.filter(repo=repo).all()
        if (not qs )or (refresh):
            print("if loop")
            Branch.create_all_branches(repo=repo)

        qs = get_objects_for_user(self.request.user,
                             'gitlab_.change_branch')

        objects = get_list_or_404(qs, repo_id=pk)
        return objects

    def list_refresh(self, request, *args, **kwargs):
        objects = self.get_queryset(refresh=True)
        return Response(self.serializer_class(objects, many=True).data, status=200)


class ContentFileViewset(viewsets.ModelViewSet):
    serializer_class = ContentFileSerializer

    def get_queryset(self, refresh=False):

        pk = self.kwargs.get("pk", None)
        if pk == None:
            raise ValueError("Primary Key is missing to fetch...")

        branch = get_object_or_404(Branch.objects.all(), id=pk)

        perm = self.request.user.has_perm("gitlab_.change_branch",
                branch)

        if not perm:
            raise ValueError("You have not permitted to access....")

        qs = ContentFile.objects.filter(branch=branch).all()
        if (not qs ) or refresh:
            print("if loop")
            ContentFile.create_all_contentfiles(branch=branch)

        qs = get_objects_for_user(self.request.user,
                             'gitlab_.change_contentfile')

        objects = get_list_or_404(qs, branch_id=pk)

        return objects

    def list_refresh(self, request, *args, **kwargs):
        objects = self.get_queryset(refresh=True)
        return Response(self.serializer_class(objects, many=True).data, status=200)


    @transaction.atomic
    def create(self, request, *args, **kwargs):

        qs = self.get_queryset()

        branch = get_object_or_404(Branch.objects.all(), id=kwargs.get("pk"))

        latest_commit_sha = branch.get_branch_gh_obj.commit.get("id")

        download_project = DownloadProject(commit_hash=latest_commit_sha)
        download_project.save()

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
            serlzr.save(ai_user=request.user, project_gitlab_downloadproject=download_project)
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
                filecontent=content_file.get_content_of_file.decode(), #vary from github
                file_name=_.get("file"))
            im_uploads.append(im)

        serlzr = FileDataPrepareSerializer(data=[{"files": im_uploads,
            "content_files": contentfile_ids, "usage_type": 1}], many=True)
        if serlzr.is_valid(raise_exception=True):
            file_serlz_data = serlzr.data[0] # unnecessary nested remove

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
