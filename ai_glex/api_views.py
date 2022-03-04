from django.shortcuts import render
from rest_framework import pagination
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from rest_framework.authtoken.models import Token
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework import viewsets, filters, status
from django_filters.rest_framework import  DjangoFilterBackend
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from .models import Glossary, GlossaryFiles, TermsModel
from .serializers import GlossarySerializer,GlossaryFileSerializer,TermsSerializer
import json
from ai_workspace.serializers import Job
# Create your views here.
############ GLOSSARY GET & CREATE VIEW #######################
class GlossaryListCreateView(viewsets.ViewSet, PageNumberPagination):
    filter_backends = (filters.SearchFilter,DjangoFilterBackend,)
    search_fields = ('glossary_Name')
    ordering_fields = ['modified_date']
    ordering = ['-modified_date']
    permission_classes = [IsAuthenticated]
    page_size = settings.REST_FRAMEWORK["PAGE_SIZE"]

    def get_custom_page_size(self, request, view):
        try:
            self.page_size = self.request.query_params.get('limit', 10)
        except (ValueError, TypeError):
            pass
        return super().get_page_size(request)

    def paginate_queryset(self, queryset, request, view=None):
        self.page_size = self.get_custom_page_size(request, view)
        return super().paginate_queryset(queryset, request, view)

    def get_queryset(self):
        queryset = queryset_all = Glossary.glossaryobjects.filter(user=self.request.user.id).all().order_by('-modified_date')
        search_word =  self.request.query_params.get('search_word',0)
        status = 200
        if search_word:
            queryset = queryset.filter(
                        Q(glossary_Name__contains=search_word) | Q(subject_field__contains=search_word)
                    )
        if not queryset:
            queryset = queryset_all
            status = 422
        return queryset, status

    def list(self, request):
        queryset, status = self.get_queryset()
        pagin_tc = self.paginate_queryset( queryset, request , view=self )
        serializer = GlossarySerializer(pagin_tc, many=True, context={'request': request})
        # return  self.get_paginated_response (serializer.data)
        response =self.get_paginated_response(serializer.data)
        return  Response(response.data, status=status)

    def create(self, request):
        file = request.FILES.getlist("uploadfile")
        print(file)
        serializer = GlossarySerializer(data={**request.POST.dict(),"files":file},context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(data={"Message":"Glossary created"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk):
        try:
            queryset = Glossary.objects.get(Q(id=pk) & Q(user=request.user))
        except Glossary.DoesNotExist:
            return Response(status=204)
        serializer =GlossarySerializer(queryset,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        queryset = Glossary.objects.filter(user=request.user)
        glossary = get_object_or_404(queryset, pk=pk)
        glossary.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


#########  FILE UPLOAD  #######################
class GlossaryFileView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        files = request.FILES.getlist("glossary_file")
        job = json.loads(request.POST.get('job'))
        obj = Job.objects.get(id=job)
        data = [{"project": obj.project.id, "file": file, "job":job, "usage_type":8} for file in files]
        serializer = GlossaryFileSerializer(data=data,many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        else:
            return Response (serializer.errors,status=400)

    def delete(self,request,pk=None):
        file_delete_ids = request.POST.getlist('file_delete_ids')
        job = request.POST.get('job')
        [GlossaryFiles.objects.filter(job=job,id=i).delete() for i in file_delete_ids]
        return Response({"Msg":"Files Deleted"})


class TermUploadView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def list(self, request):
        job = request.GET.get('job')
        queryset = TermsModel.objects.filter(job_id = job)
        serializer = TermsSerializer(queryset, many=True, context={'request': request})
        return  Response(serializer.data)

    def create(self, request):
        job = request.POST.get('job')
        job_obj = Job.objects.get(id=job)
        glossary = job_obj.project.glossary_project.id
        serializer = TermsSerializer(data={**request.POST.dict(),"job":job,"glossary":glossary})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk):
        queryset = TermsModel.objects.get(id=pk)
        serializer =TermsSerializer(queryset,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        term = TermsModel.objects.get(id=pk)
        term.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
