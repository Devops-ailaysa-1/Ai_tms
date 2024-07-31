from django.contrib import admin
from ai_glex.models import MyGlossary,TermsModel,CeleryStatusForTermExtraction
# Register your models here.

admin.site.register(MyGlossary)
admin.site.register(TermsModel)
admin.site.register(CeleryStatusForTermExtraction)