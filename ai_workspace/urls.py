from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import api_views, views

router = DefaultRouter() #
router.register(r"project", api_views.ProjectView, basename="project")
router.register(r'job', api_views.JobView, basename="job")
router.register(r'file', api_views.FileView, basename="file")
router.register(r"project_setup", api_views.ProjectSetupView, basename="project_setup")
router.register(r"temp_project_setup", api_views.AnonymousProjectSetupView, basename="temp_project_setup")
router.register(r"project-setup-sub", api_views.ProjectSubjectView, basename="project_setup__sub")
router.register(r"project-setup-content", api_views.ProjectContentTypeView, basename="project_setup__content")
router.register(r"project-create", api_views.ProjectCreateView, basename="project_create")
# router.register(r"tasks", api_views.TaskView, basename="tasks")

urlpatterns = router.urls

# api_views urls
urlpatterns += [
	path("tasks/", api_views.TaskView.as_view(), name="tasks"),
	path("files_jobs/<int:project_id>/", api_views.Files_Jobs_List.as_view(), name="get-files-jobs-by-project_id"),
]
# views urls adding for local testing









urlpatterns += [
	path("project_setup-dj", views.ProjectSetupDjView.as_view(), name="project_setup-dj-view"),
	path("login", views.LoginView.as_view(), name="my-login"),
	path("session_test", views.session_test, name="session-test"),
	path("tasks_dj", views.TasksListViewDj.as_view(), name="tasks-dj"),
	path("task_create_dj", views.TaskCreateViewDj.as_view(), name="task-create-dj"),

	# path("project-setup-sub", api_views.projectSubjectView.as_view(), name="project_setup__sub"),

]
