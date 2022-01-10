from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import permissions
from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
import requests, json, os,mimetypes
from rest_framework.decorators import api_view
from datetime import datetime
from django.db.models import Q
from rest_framework.decorators import permission_classes
from rest_framework import serializers
from django.http import JsonResponse, Http404, HttpResponse

from .serializers import GithubOAuthTokenSerializer
from .models import GithubOAuthToken

class GithubOAuthTokenViewset(viewsets.ModelViewSet):
    serializer_class = GithubOAuthTokenSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.dict()
        serlzr_obj = GithubOAuthTokenSerializer(data={**data,
            "ai_user": request.user.id}
            )
        print("initial data---->", serlzr_obj.initial_data)
        if serlzr_obj.is_valid(raise_exception=True):
            serlzr_obj.save()
            return Response(serlzr_obj.data, status=201)

    def get_queryset(self):
        return GithubOAuthToken.objects.filter(ai_user=self.request.user).all()

    def get_object(self):
        obj = super(GithubOAuthTokenViewset, self).get_object()
        if obj.ai_user == self.request.user:
            return obj
        raise Http404



