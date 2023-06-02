from django.urls import path
from ai_pay import api_views
#from ai_pay.api_views import POViewSet,POListView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'invo-ailaysa-gen', api_views.AilaysaGeneratedInvoiceViewset, basename='invo_ailaysa_gen')
urlpatterns = router.urls




urlpatterns += [
    path('con-onboard/', api_views.AiConnectOnboarding.as_view({"post":"create"}), name='con-onboard'),
    path('con-checkout/', api_views.CreateChargeVendor.as_view({"post":"create"}), name='con-checkout'),
     path('con-invoice/', api_views.CreateInvoiceVendor.as_view({"post":"create"}), name='con-invoice'),
    path('po-list/',api_views.POListView.as_view(),name= 'po_list'),
    path('po-req-pay/',api_views.po_request_payment,name='po_req_pay'),
    path('po-pdf/',api_views.po_pdf_get,name='get_po_pdf'),
    path('invo-pdf/',api_views.invoice_pdf_get,name='get_invo_pdf'),
    path('invo-list/',api_views.InvoiceListView.as_view(),name='invo_list'),
    path('invo-stripe-cancel/',api_views.cancel_stripe_invoice,name='invo_stripe_cancel'),
    path('po-assign-info/',api_views.ProjectPOTaskView.as_view({'get': 'list'}),name='po_assign_info'),
    path('po/',api_views.PurchaseOrderView.as_view({'get': 'list'}),name='po'),
]



