from django.urls import path, include
from . import api_views
from rest_framework.routers import DefaultRouter
router = DefaultRouter()

# router.register(r'glossary_list_create',api_views.GlossaryListCreateView, basename="glossary_list_create")
router.register(r'glossary_file_upload',api_views.GlossaryFileView, basename="glossary_file_upload")
router.register(r'term_upload',api_views.TermUploadView, basename="term_upload")
router.register(r'glossary_selected',api_views.GlossarySelectedCreateView, basename='glossary-selected')
router.register(r'default_glossary',api_views.MyGlossaryView, basename="my_glossary")
urlpatterns = router.urls


urlpatterns += [
    path('template/', api_views.glossary_template, name='template'),
    path('template_lite/', api_views.glossary_template_lite, name='template_lite'),
    path('tbx_write/<int:task_id>/', api_views.tbx_write, name='tbx_write'),
    path('glossaries/<int:project_id>/',api_views.glossaries_list, name='glossaries-list'),
    path('glossary_term_search/',api_views.glossary_search,name='glossary_term_search'),
    path('get_translation/<int:task_id>/', api_views.GetTranslation.as_view(), name='get-translation'),
    path('clone_source_terms_from_multiple_to_single_task/',api_views.clone_source_terms_from_multiple_to_single_task),
    path('clone_source_terms_from_single_to_multiple_task/',api_views.clone_source_terms_from_single_to_multiple_task),
    path('term_save/',api_views.adding_term_to_glossary_from_workspace,name='adding-term-to-glossary-from-workspace'),
    path('whole_glossary_term_search/',api_views.whole_glossary_term_search),
    path('glossaries_list/',api_views.GlossaryListView.as_view({'get': 'list'}),name='glossaries-list'),
    path('gloss_task_simple_download/',api_views.glossary_task_simple_download, name="gloss-simple-xlsx-download" ),
    path('term_mt/',api_views.get_word_mt)
]
