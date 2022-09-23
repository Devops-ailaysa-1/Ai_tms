from django.urls import path
from ai_exportpdf import views
from django.conf.urls.static import static
from ai_tms import settings
from rest_framework.routers import DefaultRouter
 
router = DefaultRouter()
router.register(r'convertpdftodocx',views.PDFTODOCX,basename='pdf')
# urlpatterns = [
#     # path('convertpdftodocx' , views.exportpdf_to_docx_main),
#     # path('getconverteddocx' , views.get_finished_convertio_pdf),
#     path('convertpdftodocx', views.PDFTODOCX.as_view()),
# ] 
urlpatterns = router.urls  
urlpatterns += static(settings.DOCX_URL, document_root= settings.DOCX_ROOT)