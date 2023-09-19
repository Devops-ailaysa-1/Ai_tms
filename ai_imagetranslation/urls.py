from ai_imagetranslation import api_views  
from rest_framework import routers
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
router = routers.DefaultRouter()
router.register(r'imageloadlist',api_views.ImageloadViewset ,basename= 'imageuploadlist')
router.register(r'imagetranslate' , api_views.ImageTranslateViewset ,basename= 'inpaintimage') ########
router.register(r'backgroundremove' , api_views.BackgroundRemovelViewset ,basename= 'background-remove')
router.register(r'stable-diffusion',api_views.StableDiffusionAPIViewset,basename='stablediffusion')
router.register(r'sd-image-style',api_views.ImageModificationTechniqueViewSet,basename='sd-im')
# router.register(r'sdstyle',api_views.ImageModificationTechniqueV2ViewSet,basename='sd-imv2')

urlpatterns =  router.urls
urlpatterns+=[path('imagetranslate-list', api_views.ImageInpaintCreationListView.as_view(),name='imagetranslatelistview'),
              path('image-download',api_views.image_translation_project_view,name="image_download"),
              path('image-list',api_views.ImageTranslateListViewset.as_view({'get': 'list'}),name='image-trans-list'),
              path('generated-image-download/<int:id>',api_views.download_ai_image_generated_file_stable,name='generated-image'),
              path('prompt-list',api_views.GeneralPromptListView.as_view(),name='general-prompt'),
              path('custom-image-generator/', api_views.CustomImageGenerationStyleListView.as_view(), name='post-list-create'),
              path('sdstyle/', api_views.ImageModificationTechniqueV2ViewSet.as_view(), name='post-list-create'),
              path('image-gen-resolution',api_views.AspectRatioViewSet.as_view(),name='image-resolution' )
              ]
urlpatterns+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


 