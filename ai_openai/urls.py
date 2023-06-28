from django.urls import path, include
from . import api_views
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'aiprompt',api_views.AiPromptViewset,basename='ai_prompt')
router.register(r'ai_image_gen',api_views.ImageGeneratorPromptViewset,basename='ai_image_gen')
router.register(r'blogcreation',api_views.BlogCreationViewset ,basename='ai_blog')
router.register(r'blogkeyword',api_views.BlogKeywordGenerateViewset ,basename='ai_keyword_gen')
router.register(r'blogtitle',api_views.BlogtitleViewset ,basename='ai_title_gen')
router.register(r'blogoutline',api_views.BlogOutlineViewset ,basename='ai_outline_gen')
router.register(r'blogoutlinesession',api_views.BlogOutlineSessionViewset ,basename='ai_outline_session_gen')
router.register(r'blogarticle',api_views.BlogArticleViewset ,basename='ai_article_gen')
router.register(r'custom_settings',api_views.AiCustomizeSettingViewset ,basename='ai_writer_settings')
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
    path('stream_article/',api_views.generate_article),
    path('credit_blog_check/',api_views.credit_check_blog),
    #path('instant_translation_custom',api_views.instant_translation_custom)
]













