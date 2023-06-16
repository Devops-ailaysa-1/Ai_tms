from django import urls
from django.contrib import admin
from django.urls import path
from rest_framework import routers
from ai_staff import api_views
from ai_staff import views
from rest_framework.authtoken.views import obtain_auth_token
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static

router = routers.DefaultRouter()
router.register(r'subscriptionpricing', api_views.SubscriptionPricingCreateView,basename='subscription-pricing')
router.register(r'subscriptionfeatures', api_views.SubscriptionFeaturesCreateView,basename='subscription-features')
router.register(r'addon_details',api_views.CreditsAddonsCreateView,basename='addon-details')
router.register(r'indian-states',api_views.IndianStatesView,basename='indian-states')
router.register(r'stripe-tax-ids',api_views.StripeTaxIdView,basename='stripe-tax-ids')
router.register(r'general-support-topics',api_views.SupportTopicsView,basename='general-support-topics')
router.register(r'job-positions',api_views.JobPositionsView,basename='job-positions')
router.register(r'roles',api_views.TeamRoleView,basename='team-role')

router.register(r'mt-language-support',api_views.MTLanguageSupportView,basename='mt-language-support')
router.register(r'voice-support-language',api_views.VoiceSupportLanguages,basename='voice-support-language')
router.register(r'prompt-categories-list',api_views.PromptCategoriesViewset,basename='prompt-categories-list')
router.register(r'prompt-tone',api_views.PromptTonesViewset,basename='prompt-tone')

router.register(r'font-data',api_views.FontDataViewset ,basename='fontdata')
router.register(r'font-language',api_views.FontLanguageViewset,basename='fontlanguage')
router.register(r'design-shape',api_views.DesignShapeViewset,basename='design_shape')
 
urlpatterns = router.urls

urlpatterns += [
     path('servicetypes/', api_views.ServiceTypesView.as_view(), name='servicetypes'),
     path('servicetypes/<int:pk>', api_views.ServiceTypesView.as_view(), name='servicetypes_pk'),
     path('currencies/', api_views.CurrenciesView.as_view(), name='currencies'),
     path('currencies/<int:pk>', api_views.CurrenciesView.as_view(), name='currencies_pk'),
     path('countries/', api_views.CountriesView.as_view(), name='countries'),
     path('countries/<int:pk>', api_views.CountriesView.as_view(), name='countries_pk'),
     path('subjectfield/', api_views.SubjectFieldsView.as_view(), name='subject_field'),
     path('subjectfield/<int:pk>', api_views.SubjectFieldsView.as_view(), name='subject_field_pk'),
     path('contenttype/', api_views.ContentTypesView.as_view(), name='contenttype'),
     path('contenttype/<int:pk>', api_views.ContentTypesView.as_view(), name='contenttype_pk'),
     path('mtpe-engines/', api_views.MtpeEnginesView.as_view(), name='mtpe_engines'),
     path('mtpe-engines/<int:pk>', api_views.MtpeEnginesView.as_view(), name='mtpe_engines_pk'),
     path('supportfiles/', api_views.SupportFilesView.as_view(), name='supportfiles'),
     path('supportfiles/<int:pk>', api_views.SupportFilesView.as_view(), name='supportfiles_pk'),
     path('timezones/', api_views.TimezonesView.as_view(), name='timezones'),
     path('timezones/<int:pk>', api_views.TimezonesView.as_view(), name='timezones_pk'),
     path('language/', api_views.LanguagesView.as_view(), name='language'),
     path('language/<int:pk>', api_views.LanguagesView.as_view(), name='language_pk'),
     path('languagelocale/', api_views.LanguagesLocaleView.as_view(), name='languagelocale'),
	 path('languagelocale/<int:langid>', api_views.LanguagesLocaleView.as_view(), name='languagelocale_langid'),
     path('languagelocale/<int:pk>', api_views.LanguagesLocaleView.as_view(), name='languagelocale_pk'),
     path('billunits/', api_views.BillingunitsView.as_view(), name='billunits'),
     path('billunits/<int:pk>', api_views.BillingunitsView.as_view(), name='billunits_pk'),
     path('servicetypeunits/', api_views.ServiceTypeunitsView.as_view(), name='billunits'),
     path('support_types/',api_views.SupportTypeView.as_view(),name = 'support-types'),
     path('mt_engines/',api_views.AilaysaSupportedMtpeEnginesView.as_view({'get': 'list'}),name = 'mt-engines'),
     path('get_plan_details/',api_views.get_plan_details),
     path('get_price_details/',api_views.get_pricing_details),
     path('get-addons-details/',api_views.get_addons_details),
     #path('mt_engines/',api_views.AilaysaSupportedMtpeEnginesView.as_view(),name = 'mt-engines'),
     path('project_types/',api_views.ProjectTypeView.as_view({'get': 'list'}),name = 'project-type'),
     path('sub_category/',api_views.ProjectTypeDetailView.as_view({'get': 'list'}),name = 'project-type-detail'),
     path('get_languages/',api_views.get_languages),
     path('vendor_language_pair_currency/',api_views.vendor_language_pair_currency),
     path('extension-image/<extension>', api_views.FileExtensionImage.as_view(), name='extension-image'),
     path('ai_tones/',api_views.PromptTonesViewset.as_view({'get': 'list'}), name='ai-tones'),
     path('ai_categories/',api_views.PromptCategoriesViewset.as_view({'get': 'list'}), name='ai-categories'),
     path('ai_customize/',api_views.AiCustomizeViewset.as_view({'get':'list'}),name='ai-customize'),
     #path('ai_subcategories/<int:category_id>/',api_views.PromptSubCategoriesViewset.as_view({'get': 'list'}),name='ai-subcategories')
    # path('timezones/<int:pk>', api_views.TimezonesView.as_view(), name='timezones_pk'),
     #path('insert',views.Bulk_insert)
     path('social-media-size/', api_views.SocialMediaSizeViewset_ser.as_view({'get': 'list'}), name='socialmediasize'),
     path('image-gen-resolution/',api_views.ImageGeneratorResolutionViewset.as_view({'get':'list'})),
      # path('design-shape/',api_views.DesignShapeViewset.as_view({'get':'list'})),
]

 
