from django.urls import path, include
from . import api_views
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns= [
    # path("task/", TaskView.as_view(), name = "tasks"),
    path("document/<int:task_id>/", api_views.DocumentViewByTask.as_view(), name="document"),
    path("segments/<int:document_id>/", api_views.SegmentsView.as_view(), name="segments"),
    path("segment/update/<int:segment_id>", api_views.SegmentsUpdateView.as_view({"put":"update"}), name="segment-update")

]

urlpatterns = format_suffix_patterns(urlpatterns)
