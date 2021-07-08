from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter() #
router.register(r"project", api_views.ProjectView, basename="project")

urlpatterns = router.urls

	