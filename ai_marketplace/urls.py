from django import urls
from django.urls import path,include
from ai_marketplace import views
from rest_framework.routers import DefaultRouter
from django.conf.urls import url

router = DefaultRouter()
# router.register(r'bidchat',views.BidChatView,basename="bid-chat")

urlpatterns = router.urls

urlpatterns+= [
    path('get_vendor_list/',views.get_vendor_list,name="get-vendor-list"),
    path('get_vendor_detail/',views.get_vendor_detail,name="get-vendor-detail"),
    path('hire_vendor/',views.assign_available_vendor_to_customer,name="assign-vendor"),
    path('post_job_primary_details/',views.post_job_primary_details,name="post-job-primary-details"),
    path('post_job/<int:id>/',views.ProjectPostInfoCreateView.as_view(),name='job-post'),
    path('send_email/',views.shortlisted_vendor_list_send_email,name='send-email'),
    path('bidchat/<int:id>/',views.BidChatView.as_view(),name="bid-chat"),
    path('bidchat/',views.BidChatView.as_view(),name="bid-chat"),
    ]
