from django.urls import path
from ai_nlp import api_views

urlpatterns = [
    path('ner', api_views.named_entity, name='ner'),
    path('synonyms', api_views.wordapi_synonyms, name='synonyms'),
]