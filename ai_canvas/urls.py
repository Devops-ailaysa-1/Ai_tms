
 
from ai_canvas import api_views
from rest_framework.routers import DefaultRouter
router = DefaultRouter()


router.register(r'canvas-templates',api_views.CanvasTemplateViewset,basename='canvas_templates')
router.register(r'languages',api_views.LanguagesViewset,basename='languages')
router.register(r'languageslocale',api_views.LanguagesLocaleViewset,basename='languagescode')
router.register(r'canvas-user-images',api_views.CanvasUserImageAssetsViewset,basename='canvas_user_images')
router.register(r'canvas-design-list' ,api_views.CanvasDesignListViewset,basename='canvasdesignlist')
router.register(r'canvas-designs',api_views.CanvasDesignViewset,basename='canvas_designs')
router.register(r'template-design',api_views.TemplateGlobalDesignViewset ,basename='templatedesign')
urlpatterns = router.urls
urlpatterns += [
    
]