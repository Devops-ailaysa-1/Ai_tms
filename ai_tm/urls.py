from django import urls
from django.urls import path,include
from . import api_views
from rest_framework.routers import DefaultRouter
from django.conf.urls import url

router = DefaultRouter()
router.register(r'tmx_list_create',api_views.TmxUploadView,basename="tmx-upload")
router.register(r'user_defined_rate',api_views.UserDefinedRateView,basename="user-defined-rate")

urlpatterns = router.urls

urlpatterns += [
    #path('tmx_list_create/<int:project_id>',api_views.TmxUploadView.as_view(), name='tmx-upload'),
    path('project_analysis/<int:project_id>',api_views.get_project_analysis),
    path('get_report/', api_views.ReportDownloadView.as_view(), name='download-analysis-report'),

    ]
