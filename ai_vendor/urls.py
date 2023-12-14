from django import urls
from django.urls import path,include
from ai_vendor import views
from rest_framework.routers import DefaultRouter
from django.conf.urls import url

router = DefaultRouter()
router.register(r'vendorserviceinfo',views.VendorServiceListCreate,basename="vendor-service-info")
router.register(r'vendorexpertiseinfo',views.VendorExpertiseListCreate,basename="vendor-expertise-info")
router.register(r'savetalent', views.SavedVendorView,basename='save-talent')
#router.register(r'vendorlangpair',views.VendorLangPairCreate,basename="vendor-lang-pair")


urlpatterns = router.urls

urlpatterns+= [
    path('vendor_info/',views.VendorsInfoCreateView.as_view(), name='vendor-info'),
    path('vendor_bank_info/',views.VendorsBankInfoCreateView.as_view(), name='vendor-bank-info'),
    path('spellcheck_availability/',views.feature_availability,name="feature-availability"),
    path('vendor_legal_categories/',views.vendor_legal_categories_list,name="vendor-legal-categories-list"),
    path('cat_softwares/',views.cat_softwares_list, name="cat-softwares-list"),
    path('membership_list/',views.vendor_membership_list, name="vendor-membership-list"),
    path('subject_matter_list/',views.vendor_subject_matter_list, name="vendor-subject-matter-list"),
    path('mtpe_engines_list/',views.vendor_mtpe_engines_list, name="vendor-mtpe-engines-list"),
    path('vendor_lang_pair/',views.vendor_language_pair,name='language_pair'),
    # path('get_vendor_list/',views.get_vendor_list,name="get-vendor-list"),
    # path('get_vendor_detail/',views.get_vendor_detail,name="get-vendor-detail"),
    # path('assign_vendor/',views.assign_available_vendor_to_customer,name="assign-vendor"),
    # path('post_job_primary_details/',views.post_job_primary_details,name="post-job-primary-details"),
    # path('post_job/<int:id>/',views.ProjectPostInfoCreateView.as_view(),name='job-post'),
    # path('send_email/',views.shortlisted_vendor_list_send_email,name='send-email'),
    path('clone/<int:id>/',views.clone_lang_pair,name='clone'),
    # path('vendorexpertiseinfo/',views.VendorExpertiseListCreate.as_view({'get': 'list'})),
    # path('vendorexpertiseinfo/update/',views.VendorExpertiseListCreate.as_view({'put':'update'})),
    # path('vendor_service_update/<int:pk>',views.VendorServiceUpdateDeleteView.as_view(),name='vendor-servicepdate'),
    path('vendor_lang_template/',views.vendor_lang_pair_template,name='vendor-lang-pair-template'),
    path('vendor_lang_pair/',views.vendor_language_pair,name='language_pair'),
    path('editor_settings_status/',views.get_vendor_settings_filled),
    path('ams_lang_pair',views.get_ams_agency_lang_pair_price),
    ]
