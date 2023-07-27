from django.urls import path
from ai_bi import api_views,views

from rest_framework.routers import DefaultRouter


router = DefaultRouter() #
router.register(r"countries_info", api_views.Countries_listview, basename="Countries_by_user")
router.register(r"language_info", api_views.language_listview, basename="language_info")
router.register(r"aiuser_info", api_views.AiUserListview, basename="user_info")
router.register(r"vendor-info", api_views.VendorListview, basename="vendor_info")
router.register(r"user_management", api_views.BiuserManagement, basename="user-management")



urlpatterns = router.urls

urlpatterns += [
    path('get-bi-dashboard',api_views.reports_dashboard),
 
]