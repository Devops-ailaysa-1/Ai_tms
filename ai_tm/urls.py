from django import urls
from django.urls import path,include
from . import api_views
from rest_framework.routers import DefaultRouter
from django.conf.urls import url

router = DefaultRouter()
# router.register(r'vendorserviceinfo',views.VendorServiceListCreate,basename="vendor-service-info")

urlpatterns = router.urls

urlpatterns += [
    path('tmx_list_create/<int:project_id>',api_views.TmxUploadView.as_view(), name='tmx-upload'),
    path('project_analysis/<int:project_id>',api_views.get_project_analysis),
    ]
