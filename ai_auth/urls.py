from django.urls import path,include
from ai_auth import api_views
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path
from dj_rest_auth.registration.views import VerifyEmailView
from dj_rest_auth.views import PasswordResetConfirmView
from ai_auth.soc_auth import GoogleLogin,ProzLogin


router = DefaultRouter()
router.register(r'userprofile',api_views.UserProfileCreateView,basename="user-profile-info")
router.register(r'customersupport',api_views.CustomerSupportCreateView,basename="user-profile-info")
router.register(r'contact_us',api_views.ContactPricingCreateView,basename="contact-us")
router.register(r'temp_pricing_preference',api_views.TempPricingPreferenceCreateView,basename="temp-pricing-preference")
router.register(r'usersubscribe',api_views.UserSubscriptionCreateView,basename="user-subscribe")
router.register(r'billing-info',api_views.BillingInfoView,basename="billing-info")
router.register(r'tax-info',api_views.UserTaxInfoView,basename="tax-info")
router.register(r'billing-address',api_views.BillingAddressView,basename="billing-address")
router.register(r'aiuser-profile',api_views.AiUserProfileView,basename="aiuser-profile")
router.register(r'carrier-support',api_views.CarrierSupportCreateView,basename="carrier-support")
router.register(r'co-create',api_views.CoCreateView,basename="co-create")
router.register(r'general-support',api_views.GeneralSupportCreateView,basename="general-support")
router.register(r'vendor-onboarding',api_views.VendorOnboardingCreateView,basename="vendor-onboarding")
router.register(r'team',api_views.TeamCreateView,basename="team")
router.register(r'internal-member',api_views.InternalMemberCreateView,basename="internal-member")
router.register(r'hired-editor',api_views.HiredEditorsCreateView,basename="hired-editor")
#router.register(r'user-details',api_views.UserDetailView,basename="user-details")



urlpatterns = router.urls

urlpatterns+= [
    # path('login/', api_views.MyObtainTokenPairView.as_view(), name='token_obtain_pair'),
    # path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('signup/', api_views.RegisterView.as_view(), name='auth_signup'),
    path('user-attr/', api_views.UserAttributeView.as_view(), name='user_attr'),
    #path('user-personal-info/', api_views.PersonalInformationView.as_view(), name='user_personal_info'),
    #path('user-official-info/', api_views.OfficialInformationView.as_view(), name='user_official_info'),
     path('profile-images/', api_views.ProfessionalidentityView.as_view(), name='pro_identity'),
     path('dj-rest-auth/', include('dj_rest_auth.urls')),
     path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),
     path('dj-rest-auth/registration/account-confirm-email/', VerifyEmailView.as_view(), name='account_email_verification_sent') ,
     path('userprofile/update/',api_views.UserProfileCreateView.as_view({'put':'update'})),
     path('get_payment_details_subscription/',api_views.get_payment_details),
     path('get_payment_details_addon/',api_views.get_addon_details),
     #path('profile-images/<int:pk>/', api_views.ProfessionalidentityView.as_view(), name='pro_identity'),
     path('check-subscription/',api_views.check_subscription),
     path('stripe-customer-portal/',api_views.customer_portal_session),
     path('buy-addon/',api_views.buy_addon),
     #path('buy-addon2/',api_views.buy_addon2),
     path('buy-subscription/',api_views.buy_subscription),
     path('get-user-currency/',api_views.get_user_currency),
     path('deactivate-account/',api_views.account_deactivation),
     path('activate-account/',api_views.account_activation),
     path('delete-account/',api_views.account_delete),
     path('accept/',api_views.invite_accept,name='accept'),
     path('teamlist/',api_views.teams_list),
     path('transaction-info/',api_views.TransactionSessionInfo),
     path('user-referral/',api_views.referral_users),
     path('get_team_name/',api_views.get_team_name),
     path('vendor_form_filling_status/',api_views.vendor_form_filling_status),
     path('vendor_renewal/',api_views.vendor_renewal),
     path('confirm/',api_views.vendor_renewal_invite_accept,name='confirm'),
     path('replace_password/',api_views.change_old_password,name='replace-password'),
     path('vendor_renewal_change/',api_views.vendor_renewal_change),
     path('vendor_onboard_complete/',api_views.vendor_onboard_complete),
     path('email_check/',api_views.get_user),
     path('lang_detect/',api_views.lang_detect),
     # path('dj-rest-auth/google/', GoogleLogin.as_view(), name='google_login'),
     path('ai-soc/',api_views.ai_social_login,name='ai_soc'),
     path('ai-soc-callback/',api_views.ai_social_callback,name='ai_soc_callback'),
     path('user-details/',api_views.UserDetailView.as_view({'post':'create'}),name='user-details'),
    #  path('oso-test-query/',api_views.oso_test_querys,name='oso-test-query'),

     #path('usersubscribe/<str:price_id>/',api_views.UserSubscriptionCreateView,name="user-subscribe")
     # path('get_team_members/',api_views.GetTeamMemberView.as_view(),name='get-team-members'),
     # path('external-member-invite/',api_views.external_member_invite),
     #re_path(r'^rest-auth/password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', PasswordResetConfirmView.as_view(),name='password_reset_confirm')
    path('reports-dashboard/',api_views.reports_dashboard,name='reports-dashboard'),
    path('subs-cust-portal/',api_views.subscription_customer_portal,name='subs_cust_portal'),
    path('campaign-register/',api_views.CampaignRegistrationView.as_view({'post':'create'}),name='campaign_register') ,
    # path('ai-soc/proz/', ProzLogin.as_view(), name='proz_login'),
    path('troubleshoot/',api_views.account_troubleshoot,name='account-troubleshoot'),
     path('user-info/',api_views.user_info_update,name='user-info'),
]
