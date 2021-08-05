from django.urls import path, include
from . import api_views, views
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework import routers
app_name = "ws_okapi"

router = routers.DefaultRouter()

router.register(r"comment", api_views.CommentView, basename="comment")

urlpatterns = router.urls

urlpatterns+=[
    # path("task/", TaskView.as_view(), name = "tasks"),
    path("document/<int:task_id>/", api_views.DocumentViewByTask.as_view(), name="document"),
    path("document_by_doc_id/<int:document_id>", api_views.DocumentViewByDocumentId.as_view(), name="document-by-document-id"),
    path("file_extensions/", api_views.get_supported_file_extensions, name="get-file-extensions"),
    path("segments/<int:document_id>/", api_views.SegmentsView.as_view(), name="segments"),
    path("segment/update/<int:segment_id>", api_views.SegmentsUpdateView.as_view({"put":"update"}), name="segment-update"),
    path("mt_raw_and_tm/<int:segment_id>", api_views.MT_RawAndTM_View.as_view(), name="mt-raw"),
    path("document/to/file/<int:document_id>", api_views.DocumentToFile.as_view(), name="document-convert-to-file"),
    path("outputtypes", api_views.output_types, name="output-types"),
    path("translation_status/list", api_views.TranslationStatusList.as_view(), name="translation-status-list"),
    path("source/segments/filter/<int:document_id>", api_views.SourceSegmentsListView.as_view({"post": "post"}), name="seg-filter"),
    path("target/segments/filter/<int:document_id>", api_views.TargetSegmentsListAndUpdateView.as_view({"post": "post", "put":"update"}), name="seg-filter"),
    path("progress/<int:document_id>", api_views.ProgressView.as_view(), name="document-progress"),
    path("font_size", api_views.FontSizeView.as_view(), name="user-font-size"),
    # path("comments", api_views)
]


urlpatterns+=[
    path("document_list/dj", views.DocumentListView.as_view(), name="document-list"),
    path("segment_list/dj/<int:document_id>", views.SegmentListView.as_view(), name="segments-list"),
    path("segment/update/dj/<int:segment_id>", views.SegmentUpdateView.as_view(), name="segment-update-dj"),
    path("download/to/file/dj", views.DownloadDocumentToFileView.as_view(), name="download-document-to-file")

]
