from django import urls
from django.urls import path,include
from ai_marketplace import api_views,views
from rest_framework.routers import DefaultRouter
from django.conf.urls import url
import notifications.urls

router = DefaultRouter()
router.register(r'project_post',api_views.ProjectPostInfoCreateView,basename="project-post")

urlpatterns = router.urls

urlpatterns+= [
    path('get_vendor_detail/',api_views.get_vendor_detail,name="get-vendor-detail"),
    path('post_project_primary_details/',api_views.post_project_primary_details,name="post-job-primary-details"),
    path('bid_proposal_status/',api_views.bid_proposal_status),
    path('send_email/',api_views.shortlisted_vendor_list_send_email_new,name='send-email'),
    path('chat/<int:thread_id>/',api_views.ChatMessageListView.as_view({'get': 'list','post':'create'}),name='chat'),
    path('chat_update/<int:chatmessage_id>/',api_views.ChatMessageListView.as_view({'put':'update','delete':'destroy'}),name='chat-update'),
    path('addingthread/',api_views.addingthread),
    path('bid_proposal/',api_views.BidPostInfoCreateView.as_view(),name='bid-proposal-get'),
    path('getting_bidpost_primary_details/',api_views.post_bid_primary_details),
    path('project_posts_list/',api_views.user_projectpost_list),
    path('availablejobs/',api_views.get_available_job_details),
    path('get_vendor_list/',api_views.GetVendorListViewNew.as_view(),name='get-vendor-list'),
    path('get_incomplete_projects_list/',api_views.IncompleteProjectListView.as_view(),name='get-incomplete-project'),
    path('get_available_threads/',api_views.get_available_threads),
    url('^notifications/', include(notifications.urls, namespace='notifications')),
    path('chat/unread/notifications/',api_views.chat_unread_notifications,name='chat-notifications'),
    path('general/unread/notifications/',api_views.general_notifications),
    path('messages/',views.messages_page),
    path('get_recent_messages/',api_views.get_last_messages),
    ]
