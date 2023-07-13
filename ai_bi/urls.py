from django.urls import path
from ai_bi import api_views,views

from rest_framework.routers import DefaultRouter


router = DefaultRouter() #
router.register(r"countries_info", api_views.Countries_listview, basename="Countries_by_user")
router.register(r"language_info", api_views.language_listview, basename="language_info_byjob")
router.register(r"aiuser_info", api_views.Aiuser_listview, basename="user_info")



urlpatterns = router.urls

urlpatterns += [
    path('get_report',api_views.reports_dashboard),
 
]