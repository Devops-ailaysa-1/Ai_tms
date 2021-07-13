from ai_auth.authentication import IsCustomer
from ai_auth.models import AiUser
from rest_framework import viewsets
from rest_framework.response import Response
from .serializers import ProjectSerializer, JobSerializer,FileSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Project, Job, File
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from rest_framework.parsers import MultiPartParser, FormParser

class IsCustomer(permissions.BasePermission):

    def has_permission(self, request, view):
        # user = (get_object_or_404(AiUser, pk=request.user.id))
        if request.user.user_permissions.filter(codename="user-attribute-exist").first():
            return True

class ProjectView(viewsets.ModelViewSet):
    permission_classes = [IsCustomer]
    serializer_class = ProjectSerializer
    # queryset = Project.objects.all()

    def get_queryset(self):
        return Project.objects.filter(ai_user=self.request.user)

    def create(self, request):
        serializer = ProjectSerializer(data=request.data, context={"request": request})
        if serializer.is_valid(raise_exception=True):
            try:
                serializer.save()
            except IntegrityError:
                return Response(status=409)
            return Response(serializer.data)

class JobView(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    
    def get_queryset(self):
        return Job.objects.filter(project__ai_user=self.request.user)

    def create(self, request):
        serializer = self.serializer_class(data = request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save() 
            return Response(serializer.data)

class FileView(viewsets.ModelViewSet):
    serializer_class = FileSerializer
    parser_classes = [MultiPartParser, FormParser]
    def get_queryset(self):
        return File.objects.filter(project__ai_user=self.request.user)

    def create(self, request):
        serializer = FileSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=201)





#  /////////////////  References  \\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# from django.contrib.auth.models import Permission, User
# from django.contrib.contenttypes.models import ContentType
# content_type = ContentType.objects.get_for_model( UserAttribute 
# permission = Permission.objects.get( content_type = content_type , codename='user-attribute-exist')
