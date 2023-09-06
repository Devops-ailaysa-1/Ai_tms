from django.contrib import admin

# Register your models here.
from ai_canvas.models import PromptCategory,PromptEngine,TemplateBackground,CanvasUserImageAssets

from ai_canvas.models import AiAsserts,AiAssertscategory,TemplateJson

admin.site.register(PromptCategory)
admin.site.register(PromptEngine)
admin.site.register(TemplateBackground)
admin.site.register(CanvasUserImageAssets)
admin.site.register(AiAsserts)
admin.site.register(AiAssertscategory)
admin.site.register(TemplateJson)