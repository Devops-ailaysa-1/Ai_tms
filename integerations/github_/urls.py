from django import urls
from django.urls import path,include
from . import api_views
from rest_framework.routers import DefaultRouter
from django.conf.urls import url

router = DefaultRouter()

urlpatterns=[
    path("github/", api_views.GithubOAuthTokenViewset.as_view(
        {"post": "create", "get": "list"})),
    path("github/<int:pk>", api_views.GithubOAuthTokenViewset.as_view(
        {"get": "retrieve", "put": "partial_update", "delete": "destroy"})),
    path("github/repository/<int:pk>", api_views.RepositoryViewset.as_view(
        {"get":"list"})),
    path("github/repository/<int:pk>/refresh", api_views.RepositoryViewset.as_view(
        {"get":"list_refresh"})),
    path("github/repository/branch/<int:pk>", api_views.BranchViewset.as_view(
        {"get": "list"})),
    path("github/repository/branch/<int:pk>/refresh", api_views.BranchViewset.as_view(
        {"get": "list_refresh"})),
    path("github/repository/branch/contentfile/<int:pk>", api_views.ContentFileViewset.as_view(
        {"get": "list", "post":"create"})),
    path("github/repository/branch/contentfile/<int:pk>/refresh", api_views.ContentFileViewset.as_view(
        {"get": "list_refresh"})),
    path("github/hooks/<str:token>", api_views.repo_update_view, name="hooks-listen")
]




