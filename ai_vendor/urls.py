from django import urls
from django.urls import path,include
from ai_vendor import views



urlpatterns = [
    path('vendor_info/',views.VendorsInfoCreateView.as_view(), name='vendor-info'),
    ]
