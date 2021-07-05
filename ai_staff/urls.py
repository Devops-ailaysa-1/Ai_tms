from django import urls
from django.contrib import admin
from django.urls import path
from rest_framework import routers
from ai_staff import api_views
from ai_staff import views
from rest_framework.authtoken.views import obtain_auth_token
from django.urls import path,include

router = routers.DefaultRouter()
#router.register(r'servicetypes', api_views.ServiceTypesView,basename='servicetypes')
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
    # path('timezones/<int:pk>', api_views.TimezonesView.as_view(), name='timezones_pk'),
    path('insert',views.Bulk_insert)


]
