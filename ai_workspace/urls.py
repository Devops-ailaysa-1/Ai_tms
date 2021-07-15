from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import api_views, views

router = DefaultRouter() #
router.register(r"project", api_views.ProjectView, basename="project")
router.register(r'job', api_views.JobView, basename="job")
router.register(r'file', api_views.FileView, basename="file")
router.register(r"project_setup", api_views.ProjectSetupView, basename="project_setup")
router.register(r"temp_project_setup", api_views.AnonymousProjectSetupView, basename="temp_project_setup")

urlpatterns = router.urls

# api_views urls
urlpatterns += [

]


# views urls adding for local testing

urlpatterns += [
	path("project_setup-dj", views.ProjectSetupDjView.as_view(), name="project_setup-dj-view"),

]
