from rest_framework.filters import SearchFilter

class ProjectTypeSearchFilter(SearchFilter):

    def get_search_fields(self, view, request):
        project_filter = request.query_params.get("filter")

        if project_filter == "news":
            return [
                'pib_stories__headline',                # <-- News headline
                'pib_stories__ministry_department__name', # <-- Ministry/department name
                'project_name',
                'project_files_set__filename',
                'project_jobs_set__source_language__language',
                'project_jobs_set__target_language__language',
            ]

        # Default search for other project types
        return [
            'project_name',
            'project_files_set__filename',
            'project_jobs_set__source_language__language',
            'project_jobs_set__target_language__language',
        ]
