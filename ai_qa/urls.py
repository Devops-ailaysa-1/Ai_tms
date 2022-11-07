from django.urls import path
from ai_qa import api_views

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'forbidden_file',api_views.ForbiddenFileView,basename="forbidden-file-upload")
router.register(r'untranslatable_file',api_views.UntranslatableFileView,basename="untranslatable-file-upload")

urlpatterns = router.urls

urlpatterns += [
    path('qa_check/',api_views.QA_Check),
    path('download_forbidden_file/<int:id>/',api_views.download_forbidden_file),
    path('download_untranslatable_file/<int:id>/',api_views.download_untranslatable_file),
]
