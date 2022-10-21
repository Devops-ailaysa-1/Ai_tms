from django.urls import path
from ai_qa import api_views

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
urlpatterns = router.urls




urlpatterns += [
    path('qa_check/',api_views.QA_Check),
]
