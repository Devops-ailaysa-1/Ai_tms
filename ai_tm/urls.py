from django import urls
from django.urls import path,include
from . import apiviews
from rest_framework.routers import DefaultRouter
from django.conf.urls import url

router = DefaultRouter()
# router.register(r'vendorserviceinfo',views.VendorServiceListCreate,basename="vendor-service-info")

urlpatterns = router.urls

urlpatterns += [
    path('tmx_list_create/<int:project_id>',apiviews.TmxUploadView.as_view(), name='tmx-upload'),

    ]