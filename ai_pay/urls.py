from django.urls import path
from ai_pay import api_views


urlpatterns = [
    path('con-onboard', api_views.AiConnectOnboarding.as_view({"post":"create"}), name='con-onboard'),
    path('con-checkout', api_views.CreateChargeVendor.as_view({"post":"create"}), name='con-checkout'),
     path('con-invoice', api_views.CreateInvoiceVendor.as_view({"post":"create"}), name='con-invoice'),
]



