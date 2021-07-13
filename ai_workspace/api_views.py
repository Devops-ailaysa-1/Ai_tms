from rest_framework.views import APIView
from ai_auth.authentication import IsCustomer
from ai_auth.models import AiUser
from rest_framework import viewsets
from rest_framework.response import Response
from .serializers import ProjectSerializer, JobSerializer,FileSerializer, ProjectSetupSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Project, Job, File
from rest_framework import permissions
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework import status

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
        print(request.data)
        serializer = FileSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=201)




class ProjectSetupView(APIView):

    parser_classes = [MultiPartParser, FormParser, JSONParser]
 

    def post(self, request, format=None):
        print("request DATa >>",request.data)
        # print(request.data.get('logo'))
        # print("files",request.FILES.get('logo'))
        print(request.POST.dict())
        serializer = ProjectSetupSerializer(data=request.data, context={'request':request})
        if serializer.is_valid():
            try:
                serializer.save()
            except IntegrityError:
                return Response(serializer.errors, status=status.HTTP_409_CONFLICT)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



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