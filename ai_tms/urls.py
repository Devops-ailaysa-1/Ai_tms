"""ai_tms URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
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
    path("workspace_okapi/", include("ai_workspace_okapi.urls")),
    path('marketplace/',include('ai_marketplace.urls')),
    path('glex/',include('ai_glex.urls')),
    path("stripe/", include("djstripe.urls", namespace="djstripe")),
    path("accounts/", include("allauth.urls")),
    path("", TemplateView.as_view(template_name="index.html"), ),
    # path("integerations/", include("integerations.github_.urls")),
    # path("integerations/", include("integerations.gitlab_.urls")),
    #path("tm/", include("ai_tm_management.urls")),
    path("nlp/", include("ai_nlp.urls")),

    path("aipay/", include("ai_pay.urls")),
    path("qa/", include("ai_qa.urls")),
   # path('__debug__/', include('debug_toolbar.urls')),
]

if settings.MANAGEMENT:
    urlpatterns += [path("management/", include("ai_management.urls"))]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
