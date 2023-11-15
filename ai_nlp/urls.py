from django.urls import path
from ai_nlp import api_views
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static
from django.conf import settings
router = DefaultRouter()

router.register(r'pdf-chat-upload',api_views.PdffileUploadViewset,basename='pdf_chat')
urlpatterns =  router.urls
urlpatterns += [
    path('ner', api_views.named_entity, name='ner'),
    path('synonyms', api_views.wordapi_synonyms, name='synonyms'),
    path('chat-with-pdf', api_views.pdf_chat,name='chat-pdf'), 
    path('chat-unit-remaining',api_views.pdf_chat_remaining_units,name='chat-unit-rem'),
    path('story_telling',api_views.generate_story_illus,name='story-illust')
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)