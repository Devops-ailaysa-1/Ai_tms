
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
# router.register(r'template-design',api_views.TemplateGlobalDesignViewset,basename='templatedesign')
router.register(r'mytemplate-design',api_views.MyTemplateDesignViewset,basename='mytemplatedesign')
router.register(r'text-keyword', api_views.TemplateKeywordViewset,basename= 'textkeyword')
router.register(r'text-template', api_views.TextTemplateViewset,basename='texttemplate')
router.register(r'font-file', api_views.FontFileViewset,basename='fontfile')
router.register(r'font-family',api_views.FontFamilyViewset ,basename='fontfamily')
router.register(r'social-media',api_views.SocialMediaSizeViewset ,basename='socialmediasize')
router.register(r'global-template-design',api_views.TemplateGlobalDesignViewsetV2,basename='template__global')
router.register(r'global-template-design-list',api_views.CategoryWiseGlobaltemplateViewset,basename='global-temp-desi-lst')
router.register(r'emoji-noto',api_views.EmojiCategoryViewset,basename='emoji-list')
router.register(r'designer-list',api_views.DesignerListViewset,basename='designer-lists')
router.register(r'generated-asset',api_views.AssetImageViewset,basename='generated_im')
router.register(r'asset-list',api_views.AssetCategoryViewset,basename='generated_im')

# router.register(r'template-engine',api_views.TemplateEngineGenerate,basename='template-generation')
 
# router.register(r'image-collections',api_views.ImageListMediumViewset ,basename='imagemedium')
urlpatterns = router.urls
urlpatterns += [
    # path('template-design-get/<int:id>/', api_views.TemplateGlobalDesignRetrieveViewset.as_view(),name='templatedesignget'),     
    path('mytemplate-design-get/<int:id>', api_views.MyTemplateDesignRetrieveViewset.as_view(),name='mytemplatedesignget'),
    # path('canvas-download/',api_views.canvas_download,name="canvas_download"),
    path('image-term/',api_views.free_pix_api,name='freepixapi'),
    # path('instane-translate/',api_views.instant_canvas_translation,name='instant_canvas_translation'),
    path('images/',api_views.pixabay_api,name='pixabayapi'),
    # path('canvas-export',api_views.canvas_export_download,name='canvas_export_download'),
    path('image-list-category',api_views.image_list,name='image_list'),
    path('social-media-size/', api_views.SocialMediaSizeValueViewset.as_view({'get': 'list'}), name='socialmediasize'), ##old 
    path('social-media-custom/',api_views.SocialMediaSizeCustom.as_view({'get': 'list'}), name='socialmediacustom'),
    # path('canvas_down_load/',api_views.canvas_download_combine,name='canvas_download'),
    path('file_format',api_views.CanvasDownloadFormatViewset.as_view({'get':'list'}),name='file_download_format'),
    # path('global-template-design-list',api_views.CategoryWiseGlobaltemplateViewset.as_view({'get':'list',}),name='global-temp-desi-lst'),
    path('design-download',api_views.DesignerDownload,name='designerdownload'),
    path('canvas-user-images-list',api_views.CanvasUserImageAssetsViewsetList.as_view({'get':'list'}),name='image-translate-list'),

    path('design-assert',api_views.designer_asset_create,name='designer-asset-create'),
    path('design_word_count',api_views.Designerwordcount,name='designer-wordcount-create')

]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


urlpatterns +=static(settings.EXPORT_IMAGE_URL, document_root=settings.EXPORT_IMAGE_ROOT) 
