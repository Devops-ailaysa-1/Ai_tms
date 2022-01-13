from django import urls
from django.urls import path,include
from . import api_views
from rest_framework.routers import DefaultRouter
from django.conf.urls import url

router = DefaultRouter()


urlpatterns=[
    path("github/<int:pk>", api_views.GithubOAuthTokenViewset.as_view(
        {"get": "retrieve"})),
    path("github/", api_views.GithubOAuthTokenViewset.as_view(
        {"post": "create", "get": "list"})),
    path("github/repository/<int:pk>", api_views.RepositoryViewset.as_view(
        {"get":"list"})),
    path("github/repository/branch/<int:pk>", api_views.BranchViewset.as_view(
        {"get": "list"})),
    path("github/repository/branch/contentfile/<int:pk>", api_views.ContentFileViewset.as_view(
        {"get": "list", "post":"create"})),
    path("github/test/project", api_views.TestProjectView.as_view({"post": "create"})),
    path("github/test/project", api_views.TestProjectView.as_view({"post": "create"}))
]




