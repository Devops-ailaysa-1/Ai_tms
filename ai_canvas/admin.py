from django.contrib import admin

# Register your models here.
from ai_canvas.models import AssetCategory,AssetImage


admin.site.register(AssetCategory)
admin.site.register(AssetImage)
# admin.site.register(TemplateBackground)
