from ai_exportpdf import views
from django.conf.urls.static import static
from django.contrib.auth import settings
from rest_framework.routers import DefaultRouter
from django.urls import path 
router = DefaultRouter()
router.register(r'convertpdftodocx',views.Pdf2Docx,basename='pdf')
# urlpatterns = [
#     # path('convertpdftodocx' , views.exportpdf_to_docx_main),
#     # path('getconverteddocx' , views.get_finished_convertio_pdf),
#     path('convertpdftodocx', views.PDFTODOCX.as_view()),
# ] 
urlpatterns = router.urls  
urlpatterns += path("docx_file_download/<int:id>", views.docx_file_download, name="pdf_docx_download"),
urlpatterns += static(settings.MEDIA_URL, document_root= settings.MEDIA_ROOT)