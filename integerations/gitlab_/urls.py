from django import urls
from django.urls import path,include
from . import api_views
from rest_framework.routers import DefaultRouter
from django.conf.urls import url

router = DefaultRouter()

urlpatterns=[
    path("gitlab/", api_views.GitlabOAuthTokenViewset.as_view(
        {"post": "create", "get": "list"})),
    path("gitlab/repository/<int:pk>", api_views.RepositoryViewset.as_view(
        {"get": "list"})),
]