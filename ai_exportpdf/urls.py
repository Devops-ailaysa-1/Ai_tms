from ai_exportpdf import views
from django.conf.urls.static import static
from django.contrib.auth import settings
from rest_framework.routers import DefaultRouter
from django.urls import path


router = DefaultRouter()
router.register(r'convertpdftodocx',views.Pdf2Docx,basename='pdf')
urlpatterns = router.urls


urlpatterns+= path('convert' , views.ConversionPortableDoc.as_view() , name='convertdoc' ),
urlpatterns += path("docx_file_download/", views.docx_file_download, name="pdf_docx_download"),

urlpatterns += static(settings.MEDIA_URL, document_root= settings.MEDIA_ROOT)

urlpatterns += [
path('convert_pdf_from_task/<int:task_id>/',views.project_pdf_conversion),
path('revoke_pdf',views.celery_revoke),
# path('stop_task',views.stop_task)
]
