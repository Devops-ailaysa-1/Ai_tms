from django.contrib import admin

from .models import AiUserType, Languages,AssetUsageTypes,AilaysaSupportedMtpeEngines
# Register your models here.

admin.site.register(AiUserType)
admin.site.register(Languages)
admin.site.register(AssetUsageTypes)
admin.site.register(AilaysaSupportedMtpeEngines)