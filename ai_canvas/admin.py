from django.contrib import admin

# Register your models here.
from ai_canvas.models import PromptCategory,PromptEngine


admin.site.register(PromptCategory)
admin.site.register(PromptEngine)