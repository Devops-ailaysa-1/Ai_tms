from ai_exportpdf import views
from django.conf.urls.static import static
from django.contrib.auth import settings
from rest_framework.routers import DefaultRouter
from django.urls import path
router = DefaultRouter()
router.register(r'convertpdftodocx',views.Pdf2Docx,basename='pdf')
router.register(r'aiprompt',views.AiPromptViewset,basename='ai_prompt')
router.register(r'text-customize',views.AiCustomizeViewset,basename='text-customize')
urlpatterns = router.urls
urlpatterns+= path('convert' , views.ConversionPortableDoc.as_view() , name='convertdoc' ),
urlpatterns += path("docx_file_download/", views.docx_file_download, name="pdf_docx_download"),
urlpatterns += static(settings.MEDIA_URL, document_root= settings.MEDIA_ROOT)

urlpatterns += [
path('convert_pdf_from_task/<int:task_id>/',views.project_pdf_conversion),
path("text_generator/" , views.text_generator_openai ,name = "text_generator"),
path("prompt_result/",views.AiPromptResultViewset.as_view({'get': 'list'})),
path("customize_text_generate",views.customize_text_openai)

# path('/',views.c, name='word_count_check'),
]
