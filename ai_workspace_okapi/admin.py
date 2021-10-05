from django.contrib import admin
from .models import MT_Engine,TranslationStatus

# Register your models here.
admin.site.register(MT_Engine)
admin.site.register(TranslationStatus)