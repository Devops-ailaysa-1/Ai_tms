from django.urls import include, path
from . import api_views


urlpatterns = [
    path("uploaded_tm/", api_views.TMFileUploadView.as_view(
        {"get": "list", "post": 'create'}), name="upload-tm"),
    path("uploaded_tm/<int:pk>/", api_views.TMFileUploadView.as_view(
        {"get": "retrieve", "put": "partial_update"}), name="upload-tm-detail"),
]


