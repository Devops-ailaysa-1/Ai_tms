from django.urls import path, include
from . import api_views
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'aiprompt',api_views.AiPromptViewset,basename='ai_prompt')
router.register(r'ai_image_gen',api_views.ImageGeneratorPromptViewset,basename='ai_image_gen')

urlpatterns = router.urls

urlpatterns += [
    path("prompt_result/",api_views.AiPromptResultViewset.as_view()),
    path("customize_text_generate",api_views.customize_text_openai),
    path("history/",api_views.history_delete),
    path("prompt_image_generations/" ,api_views.image_gen),
    path('customize_history/',api_views.AiPromptCustomizeViewset.as_view()),
    path('image_history/',api_views.AiImageHistoryViewset.as_view()),
    path('image/',api_views.image_gen),
    path('default_langs/',api_views.user_preffered_langs),
    #path('instant_translation_custom',api_views.instant_translation_custom)
]













