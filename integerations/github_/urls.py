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

]




