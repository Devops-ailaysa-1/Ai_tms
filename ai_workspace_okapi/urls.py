from django.urls import path, include
from . import api_views
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns= [
    # path("task/", TaskView.as_view(), name = "tasks"),
    path("document/<int:task_id>/", api_views.DocumentView.as_view(), name="document"),
]

urlpatterns = format_suffix_patterns(urlpatterns)