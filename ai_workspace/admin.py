from django.contrib import admin

from ai_workspace.models import File, Project, Job, Version, PenseiveTM, File, Steps, Workflows, WorkflowSteps, ProjectFilesCreateType,\
    TaskAssignInfo,Task,AiRoleandStep


# Register your models here.
admin.site.register(File)
#admin.site.register(AilzaUser)
admin.site.register(Project)
admin.site.register(Job)
admin.site.register(Version)
admin.site.register(PenseiveTM)
admin.site.register(Steps)
admin.site.register(Workflows)
admin.site.register(WorkflowSteps)

admin.site.register(ProjectFilesCreateType)
admin.site.register(TaskAssignInfo)
admin.site.register(Task)
admin.site.register(AiRoleandStep)
