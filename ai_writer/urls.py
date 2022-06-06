from django.urls import path
from django.conf import settings
from rest_framework.routers import DefaultRouter
from django.conf.urls.static import static
from ai_writer import views

router = DefaultRouter()

router.register(r"ailaysa-creator", views.CreateFileView, basename="ailaysa-creator")

urlpatterns = router.urls
urlpatterns += [

    path('hunspellcheck/', views.hunspellcheck, name='hunspellcheck'),
    path('hunspell_sentence_check/',views.hunspell_sentence_check_and_grammar_check, name='symspellcheck'),
    path('download-docx/', views.download_docx),
    path('doc-save/' ,views.docx_save ),
    path('synonyms/' , views.synonmys_lookup),
    path('paraphrase/', views.paraphrasing),
    path("openai-textgenerator/" , views.text_creater ),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)