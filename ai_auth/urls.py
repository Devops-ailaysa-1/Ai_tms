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


router = DefaultRouter()
router.register(r'userprofile',api_views.UserProfileCreateView,basename="user-profile-info")
router.register(r'customersupport',api_views.CustomerSupportCreateView,basename="user-profile-info")
router.register(r'contact_us',api_views.ContactPricingCreateView,basename="contact-us")
router.register(r'temp_pricing_preference',api_views.TempPricingPreferenceCreateView,basename="temp-pricing-preference")
router.register(r'usersubscribe',api_views.UserSubscriptionCreateView,basename="user-subscribe")
router.register(r'billing-info',api_views.BillingInfoView,basename="billing-info")
router.register(r'tax-info',api_views.UserTaxInfoView,basename="tax-info")
router.register(r'billing-address',api_views.BillingAddressView,basename="billing-address")
router.register(r'user-app-preference',api_views.UserAppPreferenceView,basename="user-app-preference")


urlpatterns = router.urls

urlpatterns+= [
    # path('login/', api_views.MyObtainTokenPairView.as_view(), name='token_obtain_pair'),
    # path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('signup/', api_views.RegisterView.as_view(), name='auth_signup'),
    path('user-attr/', api_views.UserAttributeView.as_view(), name='user_attr'),
    path('user-personal-info/', api_views.PersonalInformationView.as_view(), name='user_personal_info'),
    path('user-official-info/', api_views.OfficialInformationView.as_view(), name='user_official_info'),
     path('profile-images/', api_views.ProfessionalidentityView.as_view(), name='pro_identity'),
     path('dj-rest-auth/', include('dj_rest_auth.urls')),
     path('dj-rest-auth/registration/', include('dj_rest_auth.registration.urls')),
     path('dj-rest-auth/registration/account-confirm-email/', VerifyEmailView.as_view(), name='account_email_verification_sent') ,
     path('userprofile/update/',api_views.UserProfileCreateView.as_view({'put':'update'})),
     path('get_payment_details/',api_views.get_payment_details),
     path('get_addon_details/',api_views.get_addon_details),
     # path('profile-images/<int:pk>/', api_views.ProfessionalidentityView.as_view(), name='pro_identity'),
     path('check-subscription/',api_views.check_subscription),
     path('stripe-customer-portal/',api_views.customer_portal_session),
     path('buy-addon/',api_views.buy_addon),
     #path('buy-addon2/',api_views.buy_addon2),
     path('buy-subscription/',api_views.buy_subscription),
     path('get-user-currency/',api_views.get_user_currency)
     #re_path(r'^rest-auth/password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', PasswordResetConfirmView.as_view(),name='password_reset_confirm')

]
