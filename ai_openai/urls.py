from django.urls import path, include
from . import api_views
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'aiprompt',api_views.AiPromptViewset,basename='ai_prompt')

urlpatterns = router.urls

urlpatterns += [
path("prompt_result/",api_views.AiPromptResultViewset.as_view()),
path("customize_text_generate",api_views.customize_text_openai),
path("history/",api_views.history_delete),
path("prompt_image_generations/" ,api_views.image_gen)
]













