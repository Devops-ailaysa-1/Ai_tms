from django.contrib import admin
from django.urls import path,include
# import debug_toolbar

from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path

from ai_auth.admin import staff_admin_site

from django.views.generic import TemplateView
from allauth.socialaccount.providers.github import views
# from rest_framework import permissions
# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi

# # Swagger documentation setup
# schema_view = get_schema_view(
#     openapi.Info(
#         title="Ailaysa",
#         default_version='v1.1.2',
#         description="Ailayas Api",
#         terms_of_service="https://ailaysa.com/terms-of-service",
#         contact=openapi.Contact(email="admin@ailaysa.com"),
#         #license=openapi.License(name="MIT License"),
#     ),
#     public=True,
#     permission_classes=[permissions.AllowAny],
# )


def trigger_error(request):
    division_by_zero = 1 / 0


urlpatterns = [

    # SENTRY CHECK
    path('sentry-debug/', trigger_error),

    path('admin/', admin.site.urls),
    path("staff/", staff_admin_site.urls),
    path('app/',include('ai_staff.urls')),
    path('auth/',include('ai_auth.urls')),
    path('vendor/',include('ai_vendor.urls')),
    path('', include('django.contrib.auth.urls')),
    path("workspace/", include('ai_workspace.urls')),
    path('openai/',include('ai_openai.urls')),
    path("workspace_okapi/", include("ai_workspace_okapi.urls")),
    path('marketplace/',include('ai_marketplace.urls')),
    path('glex/',include('ai_glex.urls')),
    path("stripe/", include("djstripe.urls", namespace="djstripe")),
    path("accounts/", include("allauth.urls")),
    path("", TemplateView.as_view(template_name="index.html"), ),
    # path("integerations/", include("integerations.github_.urls")),
    # path("integerations/", include("integerations.gitlab_.urls")),
    path("nlp/", include("ai_nlp.urls")),
    path("tm/", include("ai_tm.urls")),

    path("aipay/", include("ai_pay.urls")),
    path('exportpdf/',include("ai_exportpdf.urls")),
    path("qa/", include("ai_qa.urls")),
    path("bi/", include("ai_bi.urls")),
    #path("celery-progress/", include("celery_progress.urls")),
   # path('__debug__/', include('debug_toolbar.urls')),
#     re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
#    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
#    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# if settings.MANAGEMENT:
#     urlpatterns += [path("management/", include("ai_management.urls"))]
#urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
