from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from guardian.shortcuts import get_objects_for_user
from django.shortcuts import get_object_or_404, get_list_or_404

from .serializers import GitlabOAuthTokenSerializer, RepositorySerializer
from .enums import DJ_APP_NAME, APP_NAME
from .models import GitlabApp, FetchInfo, Repository

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
