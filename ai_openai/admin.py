from django.contrib import admin

from .models import AiPrompt ,AiPromptResult ,TokenUsage ,NewsPrompt

admin.site.register(AiPrompt)
admin.site.register(AiPromptResult)
admin.site.register(TokenUsage)
admin.site.register(NewsPrompt)
#admin.site.register(InstantTranslation)

