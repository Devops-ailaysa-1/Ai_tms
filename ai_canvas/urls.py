
from django.urls import path
from ai_canvas import api_views
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static
router = DefaultRouter()


router.register(r'canvas-templates',api_views.CanvasTemplateViewset,basename='canvas_templates')
router.register(r'languages',api_views.LanguagesViewset,basename='languages')
router.register(r'languageslocale',api_views.LanguagesLocaleViewset,basename='languagescode')
router.register(r'canvas-user-images',api_views.CanvasUserImageAssetsViewset,basename='canvas_user_images')
router.register(r'canvas-design-list' ,api_views.CanvasDesignListViewset,basename='canvasdesignlist')
router.register(r'canvas-designs',api_views.CanvasDesignViewset,basename='canvas_designs')
router.register(r'template-design',api_views.TemplateGlobalDesignViewset,basename='templatedesign')
router.register(r'mytemplate-design',api_views.MyTemplateDesignViewset,basename='mytemplatedesign')
router.register(r'text-keyword', api_views.TemplateKeywordViewset,basename= 'textkeyword')
router.register(r'text-template', api_views.TextTemplateViewset,basename='texttemplate')
router.register(r'font-file', api_views.FontFileViewset,basename='fontfile')
router.register(r'font-family',api_views.FontFamilyViewset ,basename='fontfamily')
router.register(r'social-media',api_views.SocialMediaSizeViewset ,basename='socialmediasize')
 
# router.register(r'image-collections',api_views.ImageListMediumViewset ,basename='imagemedium')
urlpatterns = router.urls
urlpatterns += [
    path('template-design-get/<int:id>/', api_views.TemplateGlobalDesignRetrieveViewset.as_view(),name='templatedesignget'),     
    path('mytemplate-design-get/<int:id>', api_views.MyTemplateDesignRetrieveViewset.as_view(),name='mytemplatedesignget'),
    path('canvas-download/',api_views.canvas_download,name="canvas_download"),
    path('image-term/',api_views.free_pix_api,name='freepixapi'),
    path('instane-translate/',api_views.instant_canvas_translation,name='instant_canvas_translation'),
    path('images/',api_views.pixabay_api,name='pixabayapi'),
    path('canvas-export',api_views.canvas_export_download,name='canvas_export_download'),
    path('image-list-category',api_views.image_list,name='image_list'),
    path('social-media-size/', api_views.SocialMediaSizeViewset.as_view({'get': 'list'}), name='socialmediasize'),
]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


urlpatterns +=static(settings.EXPORT_IMAGE_URL, document_root=settings.EXPORT_IMAGE_ROOT) 