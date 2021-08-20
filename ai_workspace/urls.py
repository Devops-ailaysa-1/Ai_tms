from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import api_views, views, tbx_read

router = DefaultRouter() #
router.register(r"project", api_views.ProjectView, basename="project")
router.register(r'job', api_views.JobView, basename="job")
router.register(r'file', api_views.FileView, basename="file")
router.register(r"project_setup", api_views.ProjectSetupView, basename="project_setup")
router.register(r"temp_project_setup", api_views.AnonymousProjectSetupView,\
				basename="temp_project_setup")
router.register(r"project-setup-sub", api_views.ProjectSubjectView,\
				basename="project_setup__sub")
router.register(r"project-setup-content", api_views.ProjectContentTypeView,\
				basename="project_setup__content")
router.register(r"project-create", api_views.ProjectCreateView, basename="project_create")
router.register(r"tmx_file", api_views.TmxFileView, basename="tmx-file")
router.register(r"project/quick/setup", api_views.QuickProjectSetupView,\
				basename="project-quick-setup")
router.register(r"vendor/dashboard", api_views.VendorDashBoardView,\
				basename="vendor-dashboard")
# router.register(r"tasks", api_views.TaskView, basename="tasks")


urlpatterns = router.urls

# api_views urls
urlpatterns += [
	path("tasks/", api_views.TaskView.as_view(), name="tasks"),
	path("files_jobs/<int:project_id>/", api_views.Files_Jobs_List.as_view(),\
		 name="get-files-jobs-by-project_id"),
	path("source_tmx/<int:project_id>/", api_views.TmxFilesOfProject.as_view(),\
		 name="source-tmx-files"),
	path("project/report_analysis/<int:project_id>/", api_views.ProjectReportAnalysis.as_view(),\
		 name="project-report-analysis"),
    path("getLangName/<int:id>/", api_views.getLanguageName, name="get-language-name"),
	path("project/report_analysis/<int:project_id>/", api_views.ProjectReportAnalysis.as_view(),\
		 name="project-report-analysis"),
	path("tbx_upload", api_views.TbxUploadView.as_view(), name='tbx-upload'),
	path("tbx_read", tbx_read.TermSearch, name='tbx-read'),
	path("vendor_dashboard_proj_based/<int:project_id>/", \
		api_views.VendorProjectBasedDashBoardView.as_view({"get":"list"}),\
		 name="vendor-dashboard-proj-based"),

]
# views urls adding for local testing


urlpatterns += [
	path("project_setup-dj", views.ProjectSetupDjView.as_view(), name="project_setup-dj-view"),# Project Create
	path("dj/login", views.LoginView.as_view(), name="dj-login"),
	path("dj/logout", views.LoginOutView.as_view(), name="dj-logout"),
	path("tasks_dj/<int:project_id>/", views.TaskCreateViewDj.as_view(), name="task-create-dj"),
	path("tasks/dj", views.TaskListView.as_view(), name="task-list-dj"),
	# path("document/<int:project_id>/dj", views.DocumentView.as_view(), name="document-view"), # Segments will be listed here

	# path("source_tmx", )
	# path("project-setup-sub", api_views.projectSubjectView.as_view(), name="project_setup__sub"),
]


