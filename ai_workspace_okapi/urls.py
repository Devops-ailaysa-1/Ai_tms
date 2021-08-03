from django.urls import path, include
from . import api_views, views
from rest_framework.urlpatterns import format_suffix_patterns

app_name = "ws_okapi"
urlpatterns= [
    # path("task/", TaskView.as_view(), name = "tasks"),
    path("document/<int:task_id>/", api_views.DocumentViewByTask.as_view(), name="document"),
    path("file_extensions/", api_views.get_supported_file_extensions, name="get-file-extensions"),
    path("segments/<int:document_id>/", api_views.SegmentsView.as_view(), name="segments"),
    path("segment/update/<int:segment_id>", api_views.SegmentsUpdateView.as_view({"put":"update"}), name="segment-update"),
    path("mt_raw/<int:segment_id>", api_views.MT_RawView.as_view(), name="mt-raw"),
    path("document/to/file/<int:document_id>", api_views.DocumentToFile.as_view(), name="document-convert-to-file"),
    path("outputtypes", api_views.output_types, name="output-types"),
    path("translation_status/list", api_views.TranslationStatusList.as_view(), name="translation-status-list"),
    path("source/segments/filter/<int:document_id>", api_views.SourceSegmentsListView.as_view({"post": "post"}), name="seg-filter"),
    path("target/segments/filter/<int:document_id>", api_views.TargetSegmentsListAndUpdateView.as_view({"post": "post", "put":"update"}), name="seg-filter"),
    path("progress/<int:document_id>", api_views.ProgressView.as_view(), name="document-progress"),
    path("font_size", api_views.FontSizeView.as_view(), name="user-font-size"),
]

urlpatterns = format_suffix_patterns(urlpatterns)

urlpatterns+=[
    path("document_list/dj", views.DocumentListView.as_view(), name="document-list"),
    path("segment_list/dj/<int:document_id>", views.SegmentListView.as_view(), name="segments-list"),
    path("segment/update/dj/<int:segment_id>", views.SegmentUpdateView.as_view(), name="segment-update-dj"),
    path("download/to/file/dj", views.DownloadDocumentToFileView.as_view(), name="download-document-to-file")

]
