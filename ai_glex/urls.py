from django.urls import path, include
from . import api_views
from rest_framework.routers import DefaultRouter
router = DefaultRouter()

# router.register(r'glossary_list_create',api_views.GlossaryListCreateView, basename="glossary_list_create")
router.register(r'glossary_file_upload',api_views.GlossaryFileView, basename="glossary_file_upload")
router.register(r'term_upload',api_views.TermUploadView, basename="term_upload")
urlpatterns = router.urls


urlpatterns += [
    path('template/', api_views.glossary_template, name='template'),
    path('template_lite/', api_views.glossary_template_lite, name='template_lite'),
    path('tbx_write/<int:task_id>/', api_views.tbx_write, name='tbx_write'),
]
