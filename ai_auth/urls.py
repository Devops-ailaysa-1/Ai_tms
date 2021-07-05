from django.urls import path
from ai_auth import api_views
from rest_framework_simplejwt.views import TokenRefreshView

from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path


urlpatterns = [
    path('login/', api_views.MyObtainTokenPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('signup/', api_views.RegisterView.as_view(), name='auth_signup'),
    path('user-attr/', api_views.UserAttributeView.as_view(), name='user_attr'),
    path('user-personal-info/', api_views.PersonalInformationView.as_view(), name='user_personal_info'),
    path('user-official-info/', api_views.OfficialInformationView.as_view(), name='user_official_info'),
     path('profile-images/', api_views.ProfessionalidentityView.as_view(), name='pro_identity'),
     
]



