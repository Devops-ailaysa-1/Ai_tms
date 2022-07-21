from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import api_views, views, tbx_read

router = DefaultRouter() #
router.register(r"project", api_views.ProjectView, basename="project")
router.register(r'task_assign_info',api_views.TaskAssignInfoCreateView,basename="task-assign-info")
router.register(r'job', api_views.JobView, basename="job")
router.register(r'file', api_views.FileView, basename="file")
router.register(r"project_setup", api_views.ProjectSetupView, basename="project_setup")
router.register(r"temp_project_setup", api_views.TempProjectSetupView,\
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
router.register(r'project/reference/files', api_views.ReferenceFilesView,\
				basename="project-reference-files")
# router.register(r'project-list', api_views.IncompleteProjectListView,basename="project-list")
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
    # path("getLangName/<int:id>/", api_views.getLanguageName, name="get-language-name"),
	path("project/report_analysis/<int:project_id>/", api_views.ProjectReportAnalysis.as_view(),\
		 name="project-report-analysis"),
	path("tbx_upload", api_views.TbxUploadView.as_view(), name='tbx-upload'),
	path("tbx_read", tbx_read.TermSearch, name='tbx-read'),
	path("vendor_dashboard_proj_based/<int:project_id>/", api_views.VendorProjectBasedDashBoardView\
		 .as_view({"get":"list"}), name="vendor-dashboard-proj-based"),
	path("tm/configs/<int:pk>", api_views.TM_FetchConfigsView.as_view({"put":"update"}), name="tm-configs"),
	path("test/internal/call", api_views.test_internal_call, name="test-internal-call"),
	path("tbx_list_create/<int:project_id>", api_views.TbxFileListCreateView.as_view(), name='tbx-list-create'),
	path("tbx_detail/<int:id>", api_views.TbxFileDetail.as_view(), name='tbx-detail'),
	path("tmx_list/<int:project_id>", api_views.TmxList.as_view(), name='tmx-list'),
	path("tbx_template_download", api_views.glossary_template_lite, name="tbx-template-download"),
	path("tbx_template_upload/<int:project_id>", api_views.TbxTemplateUploadView.as_view(), name="tbx-template-upload"),
	path("tbx_download/<int:tbx_file_id>", api_views.tbx_download, name="tbx-download"),
	path("task_credit_status_update/<int:doc_id>", api_views.UpdateTaskCreditStatus.as_view(), name="task-credit-update"),
	path("dashboard_credit_status", api_views.dashboard_credit_status, name="dashboard-credit-status"),
	path('create_project_from_temp_project/',api_views.create_project_from_temp_project_new),
	path('task_assign_update/',api_views.TaskAssignInfoCreateView.as_view({'put':'update'})),
	path('get_assign_to_list/',api_views.get_assign_to_list),
	path('project_list/',api_views.ProjectListView.as_view({'get': 'list'}),name='project-list'),
	path('assign_to/',api_views.AssignToListView.as_view({'get': 'list'}),name='assign-list'),
	path('tasks_list/',api_views.tasks_list),
	path('project_analysis/<int:project_id>',api_views.ProjectAnalysis.as_view(), name='project-analysis'),
	path("download/<int:project_id>/",api_views.project_download),
	path("instruction_file_download/<int:task_assign_info_id>", api_views.instruction_file_download, name="instruction-file-download"),
	path("mt_samples/",api_views.ShowMTChoices.as_view(), name='mt-samples'),
	path('transcribe_file/',api_views.transcribe_file),
	path('transcribe_and_download_text_to_speech_source/',api_views.transcribe_and_download_text_to_speech_source),
	path('download_text_to_speech_source/',api_views.download_text_to_speech_source),
	path('task/unassign/',api_views.task_unassign),
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
