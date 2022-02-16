from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from guardian.shortcuts import get_objects_for_user

from .serializers import GitlabOAuthTokenSerializer
from .enums import DJ_APP_NAME, APP_NAME

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

