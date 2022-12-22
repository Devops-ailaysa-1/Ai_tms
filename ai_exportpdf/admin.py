

from django.contrib import admin
from ai_exportpdf.models import AiPrompt ,AiPromptResult ,TokenUsage , PromptList

admin.site.register(AiPrompt)
admin.site.register(AiPromptResult)
admin.site.register(TokenUsage)
admin.site.register(PromptList)
