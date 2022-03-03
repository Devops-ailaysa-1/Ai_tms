from django.urls import path, include
from . import api_views
from rest_framework.routers import DefaultRouter
router = DefaultRouter()

router.register(r'glossary_list_create',api_views.GlossaryListCreateView, basename="glossary_list_create")


urlpatterns = router.urls


urlpatterns += [
]
