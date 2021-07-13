from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter() #
router.register(r"project", api_views.ProjectView, basename="project")
router.register(r'job', api_views.JobView, basename="job")
router.register(r'file', api_views.FileView, basename="file")

urlpatterns = router.urls

urlpatterns += [
    path("project_setup", api_views.ProjectSetupView.as_view(), name="project-setup"), 

]
	