from ai_imagetranslation.api_views import ImageloadViewset,ImageTranslateViewset
from rest_framework import routers
from django.conf import settings
from django.conf.urls.static import static
router = routers.DefaultRouter()
router.register(r'imageloadlist',ImageloadViewset ,basename= 'imageuploadlist')
router.register(r'imagetranslate' , ImageTranslateViewset ,basename= 'inpaintimage')

urlpatterns =  router.urls
urlpatterns+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

