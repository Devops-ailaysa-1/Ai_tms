from django.urls import path, include
from . import api_views
from rest_framework.routers import DefaultRouter
router = DefaultRouter()

router.register(r'glossary_list_create',api_views.GlossaryListCreateView, basename="glossary_list_create")
router.register(r'glossary_file_upload',api_views.GlossaryFileView, basename="glossary_file_upload")
router.register(r'term_upload',api_views.TermUploadView, basename="term_upload")
urlpatterns = router.urls


urlpatterns += [
]
