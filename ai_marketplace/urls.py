from django import urls
from django.urls import path,include
from ai_marketplace import api_views,views
from rest_framework.routers import DefaultRouter
from django.conf.urls import url

router = DefaultRouter()
# router.register(r'bidchat',views.BidChatView,basename="bid-chat")

urlpatterns = router.urls

urlpatterns+= [
    path('get_vendor_list/',api_views.get_vendor_list,name="get-vendor-list"),
    path('get_vendor_detail/',api_views.get_vendor_detail,name="get-vendor-detail"),
    path('hire_vendor/',api_views.assign_available_vendor_to_customer,name="assign-vendor"),
    path('post_job_primary_details/',api_views.post_job_primary_details,name="post-job-primary-details"),
    path('post_job/<int:project_id>/',api_views.ProjectPostInfoCreateView.as_view(),name='job-post'),
    path('post_job_update/<int:projectpost_id>/',api_views.ProjectPostInfoCreateView.as_view(),name='job-post'),
    path('send_email/',api_views.shortlisted_vendor_list_send_email,name='send-email'),
    # path('bidchat/<int:id>/',api_views.BidChatView.as_view(),name="bid-chat"),
    # path('bidchat/',api_views.BidChatView.as_view(),name="bid-chat"),
    path('chat/',views.messages_page),
    path('addingthread/',api_views.addingthread),
    path('bid_proposal/<int:id>/',api_views.BidPostInfoCreateView.as_view(),name='bid-proposal'),
    # path('bid_proposal/',api_views.BidPostInfoCreateView.as_view(),name='bid-proposal-get'),
    path('bid_proposal_update/<int:bid_proposal_id>/',api_views.BidPostInfoCreateView.as_view(),name='bid-proposal-update'),
    path('getting_bidpost_primary_details/',api_views.post_bid_primary_details),
    path('project_posts_list/',api_views.user_projectpost_list),
    ]
