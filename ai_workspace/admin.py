from django.contrib import admin

from .models import File, Project, Job, Version, PenseiveTM, File

# Register your models here.
admin.site.register(File)
#admin.site.register(AilzaUser)
admin.site.register(Project)
admin.site.register(Job)
admin.site.register(Version)
admin.site.register(PenseiveTM)
