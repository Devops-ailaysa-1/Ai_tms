from django.urls import path
from rest_framework import routers

from . import api_views, views

app_name = "ws_okapi"

router = routers.DefaultRouter()

router.register(r"comment", api_views.CommentView, basename="comment")
router.register(r"page_size",api_views.SegmentSizeView, basename='default-page-size')
router.register(r'selflearning',api_views.SelflearningAssetViewset,basename='self-learning')
# router.register(r'segment_diff',api_views.SegmentDiffViewset,basename='segment_difference')
urlpatterns = router.urls

myobject_detail = api_views.SegmentsUpdateView.as_view({
    'put': 'update',
    'patch': 'partial_update',
})

urlpatterns+=[
    # path("task/", TaskView.as_view(), name = "tasks"),
    path("document/<int:task_id>/", api_views.DocumentViewByTask.as_view(), name="document"),
    path("document_by_doc_id/<int:document_id>", api_views.DocumentViewByDocumentId.as_view(),\
         name="document-by-document-id"),
    path("file_extensions/", api_views.get_supported_file_extensions, name="get-file-extensions"),

    # Segment related endpoints
    path("segments/<int:document_id>/", api_views.SegmentsView.as_view(), name="segments"),
    path("segment/update/", myobject_detail, \
         name="segment-update"),
    path('merge/segment/', api_views.MergeSegmentView.as_view({"post": "create"}), name='merge-segment'),
    path("segment/restore/<int:pk>", api_views.MergeSegmentDeleteView.as_view({"delete": "destroy"}), \
         name="segment-update"),
    path('split/segment/', api_views.SplitSegmentView.as_view({"post": "create"}), name='split-segment'),
    path("mt_raw_and_tm/<int:segment_id>", api_views.MT_RawAndTM_View.as_view(), name="mt-raw"),

    
    path("document/to/file/<int:document_id>", api_views.DocumentToFile.as_view(),\
         name="document-convert-to-file"),
    path("outputtypes", api_views.output_types, name="output-types"),
    path("translation_status/list", api_views.TranslationStatusList.as_view(),\
         name="translation-status-list"),
    path("source/segments/filter/<int:document_id>", api_views.SourceSegmentsListView.as_view({"post": "post"}),\
         name="seg-filter"),
    path("target/segments/filter/<int:document_id>", api_views.TargetSegmentsListAndUpdateView.as_view(\
        {"post": "post", "put":"update"}), name="seg-filter"),
    # path("target/segment/filter/update/<int:segment_id>", api_views.FindAndReplaceTargetBySegment.as_view(\
    #     {"put":"put"}), name="seg-find-&-replace"),
    path("progress/<int:document_id>", api_views.ProgressView.as_view(), name="document-progress"),
    path("font_size", api_views.FontSizeView.as_view(), name="user-font-size"),
    #path("page_size", api_views.SegmentSizeView.as_view(), name='default-page-size'),
    path("concordance/<int:segment_id>", api_views.ConcordanceSearchView.as_view(), name="concordance-search"),
    path("segment/get/page/filter/<int:document_id>/<int:segment_id>", api_views
         .GetPageIndexWithFilterApplied.as_view(), name="get-page-id-of-segment-on-apply-filter"),
    path('wiktdata/',api_views.WiktionaryParse,name='wiktdata'),
    path('get_wikipedia/', api_views.WikipediaWorkspace, name='get-wikipedia'),
    path('get_wiktionary/', api_views.WiktionaryWorkSpace, name='get-wiktionary'),
    path('spellcheck/', api_views.spellcheck, name='spellcheck'),
    path("segment_history/",api_views.get_segment_history,name='segment-history'),
    path('synonyms/',api_views.get_word_api, name ='synonyms'),
    path('grammercheck/',api_views.grammar_check_model, name ='grammercheck'),
    path('paraphrase/',api_views.paraphrasing, name = 'paraphrase'),
    path('seg_rewrite/',api_views.paraphrasing_for_non_english),
    path('download_audio_file/',api_views.download_audio_output_file),
    path('download_mt_file/',api_views.download_mt_file),
    path('download_converted_audio_file/',api_views.download_converted_audio_file),
    #path('get_mt_raw/<int:task_id>/',api_views.get_mt_raw),
]
urlpatterns+=[
    path("document_list/dj", views.DocumentListView.as_view(), name="document-list"),
    path("segment_list/dj/<int:document_id>", views.SegmentListView.as_view(), name="segments-list"),
    path("segment/update/dj/<int:segment_id>", views.SegmentUpdateView.as_view(), name="segment-update-dj"),
    path("download/to/file/dj", views.DownloadDocumentToFileView.as_view(), name="download-document-to-file")
]
