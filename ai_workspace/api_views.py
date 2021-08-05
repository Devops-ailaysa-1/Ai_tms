from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from ai_auth.authentication import IsCustomer
from ai_auth.models import AiUser
from rest_framework import viewsets
from rest_framework.response import Response
from .serializers import (ProjectContentTypeSerializer, ProjectCreationSerializer, ProjectSerializer, JobSerializer,FileSerializer,FileSerializer,FileSerializer,
                            ProjectSetupSerializer, ProjectSubjectSerializer, TempProjectSetupSerializer)
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Project, Job, File, ProjectContentType, ProjectSubjectField, TempProject
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.viewsets import ModelViewSet
from ai_workspace import serializers

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


class ProjectSubjectView(viewsets.ModelViewSet):
    serializer_class = ProjectSubjectField

    def get_queryset(self):
        project_id = self.request.query_params.get('project_id')
        return ProjectSubjectField.objects.filter(project__id=project_id)


    def list(self,request):
        queryset = self.get_queryset()
        # pagin_tc = self.paginate_queryset( queryset, request , view=self )
        serializer = ProjectSubjectSerializer(queryset, many=True, context={'request': request})
        # response =self.get_paginated_response(serializer.data)
        return  Response(serializer.data)

    def create(self, request):
        serializer = self.serializer_class(data = request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)

class ProjectContentTypeView(viewsets.ModelViewSet):
    serializer_class = ProjectContentTypeSerializer

    def get_queryset(self):
        project_id = self.request.query_params.get('project_id')
        return ProjectContentType.objects.filter(project__id=project_id)


    def list(self,request):
        queryset = self.get_queryset()
        # pagin_tc = self.paginate_queryset( queryset, request , view=self )
        serializer = ProjectContentTypeSerializer(queryset, many=True, context={'request': request})
        # response =self.get_paginated_response(serializer.data)
        return  Response(serializer.data)

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
        print(request.data)
        serializer = FileSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=201)

def integrity_error(func):
    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IntegrityError:
            return Response({'message': "integrirty error"}, 409)
    return decorator

class ProjectSetupView(viewsets.ViewSet):
    serializer_class = ProjectSetupSerializer
    parser_classes = [MultiPartParser, JSONParser]
    permission_classes = []

    def get_queryset(self):
        return Project.objects.filter(ai_user=self.request.user)

    @integrity_error
    def create(self, request):
        # print("metaaa>>",request.META)
        serializer = ProjectSetupSerializer(data={**request.POST.dict(),
            "files":request.FILES.getlist('files')},context={"request":request})
        if serializer.is_valid(raise_exception=True):
            #try:
            serializer.save()
            #except IntegrityError:
              #  return Response(serializer.data, status=409)

            return Response(serializer.data, status=201)

        else:
            return Response(serializer.errors, status=409)

    def list(self,request):
        queryset = self.get_queryset()
        # pagin_tc = self.paginate_queryset( queryset, request , view=self )
        serializer = ProjectSetupSerializer(queryset, many=True, context={'request': request})
        # response =self.get_paginated_response(serializer.data)
        return  Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()
        project = get_object_or_404(queryset, pk=pk)
        serializer = ProjectSetupSerializer(project)
        return Response(serializer.data)

class ProjectCreateView(viewsets.ViewSet):
    serializer_class = ProjectCreationSerializer
    parser_classes = [MultiPartParser, JSONParser]
    permission_classes = []

    def get_queryset(self):
        return Project.objects.filter(ai_user=self.request.user)

   #@integrity_error
    def create(self, request):
        # print("metaaa>>",request.META)
        serializer = ProjectCreationSerializer(data={**request.POST.dict(),
            "files":request.FILES.getlist('files')},context={"request":request})
        if serializer.is_valid(raise_exception=True):
            #try:
            serializer.save()
            #except IntegrityError:
              #  return Response(serializer.data, status=409)

            return Response(serializer.data, status=201)

        else:
            return Response(serializer.errors, status=409)

    def list(self,request):
        queryset = self.get_queryset()
        # pagin_tc = self.paginate_queryset( queryset, request , view=self )
        serializer = ProjectCreationSerializer(queryset, many=True, context={'request': request})
        # response =self.get_paginated_response(serializer.data)
        return  Response(serializer.data)


    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()
        project = get_object_or_404(queryset, pk=pk)
        serializer = ProjectCreationSerializer(project)
        return Response(serializer.data)

    def update(self, request, pk=None):
        pass




class AnonymousProjectSetupView(viewsets.ViewSet):
    serializer_class = TempProjectSetupSerializer
    parser_classes = [MultiPartParser, JSONParser]
    permission_classes = [AllowAny,]

    def get_queryset(self):
        return TempProject.objects.filter(ai_user=self.request.user)

    @integrity_error
    def create(self, request):
        # print("metaaa>>",request.META)
        serializer = TempProjectSetupSerializer(data={**request.POST.dict(),
            "tempfiles":request.FILES.getlist('tempfiles')})
        if serializer.is_valid(raise_exception=True):
            #try:
            serializer.save()
            #except IntegrityError:
              #  return Response(serializer.data, status=409)

            return Response(serializer.data, status=201)

        else:
            return Response(serializer.errors, status=409)







#  /////////////////  References  \\\\\\\\\\\\\\\\\\\\\\\\\\\\\
# from django.contrib.auth.models import Permission, User
# from django.contrib.contenttypes.models import ContentType
# content_type = ContentType.objects.get_for_model( UserAttribute
# permission = Permission.objects.get( content_type = content_type , codename='user-attribute-exist')


# class ProjectSetupView2(APIView):

#     parser_classes = [MultiPartParser, FormParser, JSONParser]


#     def post(self, request, format=None):
#         print("request DATa >>",request.data)
#         # print(request.data.get('logo'))
#         # print("files",request.FILES.get('logo'))
#         print(request.POST.dict())
#         serializer = ProjectSetupSerializer(data=request.data, context={'request':request})
#         if serializer.is_valid():
#             try:
#                 serializer.save()
#             except IntegrityError:
#                 return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         else:
#             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
