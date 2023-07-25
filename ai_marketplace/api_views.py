from rest_framework import filters,generics
from rest_framework.pagination import PageNumberPagination
import django_filters
from  django.utils import timezone
from ai_marketplace import forms as m_forms
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter as SF, OrderingFilter as OF
from django.shortcuts import render
from os.path import join
#from ai_auth.signals import email_notification_to_vendors
from ai_auth.models import AiUser
from ai_staff.models import Languages,ContentTypes
from django.conf import settings
from decimal import *
from notifications.signals import notify
from notifications.models import Notification
from django.db.models import Q, Max
from django.db import transaction
from ai_workspace.api_views import integrity_error
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.test.client import RequestFactory
from ai_auth import forms as auth_forms
from rest_framework import pagination, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view,permission_classes
from datetime import datetime
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from ai_auth.api_views import msg_send,invite_accept_token
from django.db.models import OuterRef, Subquery
from rest_framework.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ai_workspace.models import Job,Project,ProjectContentType,ProjectSubjectField,Task,TaskAssignInfo
from .models import(ProjectboardDetails,ProjectPostJobDetails,BidChat,
                    Thread,BidPropasalDetails,ChatMessage,ProjectPostSubjectField,ProjectboardTemplateDetails)
from .serializers import(ProjectPostSerializer,ProjectPostTemplateSerializer,
                        BidChatSerializer,BidPropasalDetailSerializer,
                        ThreadSerializer,GetVendorDetailSerializer,VendorServiceSerializer,
                        GetVendorListSerializer,ChatMessageSerializer,ChatMessageByDateSerializer,
                        SimpleProjectSerializer,AvailablePostJobSerializer,ProjectPostStepsSerializer,
                        PrimaryBidDetailSerializer,GetVendorListBasedonProjectSerializer,GetTalentSerializer)
from ai_vendor.models import (VendorBankDetails, VendorLanguagePair, VendorServiceInfo,
                     VendorServiceTypes, VendorsInfo, VendorSubjectFields,VendorContentTypes,
                     VendorMtpeEngines)
from ai_vendor.serializers import (ServiceExpertiseSerializer,
                          VendorBankDetailSerializer,VendorLanguagePairCloneSerializer,
                          VendorLanguagePairSerializer,VendorServiceInfoSerializer,
                           VendorsInfoSerializer)
from ai_staff.models import (Languages,Spellcheckers,SpellcheckerLanguages,
                            VendorLegalCategories, CATSoftwares, VendorMemberships,
                            MtpeEngines, SubjectFields,ServiceTypeunits)
from ai_auth.models import  AiUser, Professionalidentity, HiredEditors
from ai_auth.serializers import AiUserDetailsSerializer
import json,requests
from ai_auth.tasks import shortlisted_vendor_list_send_email_new,check_dict
from django.db.models import Count
from django.http import JsonResponse
from django.core.mail import EmailMessage
from django.template import Context
from django.template.loader import get_template
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django_filters import Filter, FilterSet,RangeFilter
import django_filters
from django_filters.filters import OrderingFilter
from ai_workspace.serializers import TaskSerializer,\
            JobSerializer, ProjectSubjectSerializer,ProjectContentTypeSerializer
import os,mimetypes
from django.http import JsonResponse,HttpResponse
from ai_workspace_okapi.utils import download_file
from django_oso.auth import authorize


# Create your views here.


@api_view(['GET','POST',])
@permission_classes([IsAuthenticated])
def get_vendor_detail(request):
    uid=request.POST.get('vendor_id')
    user=AiUser.objects.get(uid=uid)
    serializer = GetVendorDetailSerializer(user,context={'request':request})
    return Response(serializer.data)


@api_view(['POST',])
@permission_classes([IsAuthenticated])
def post_project_primary_details(request):
    project_id=request.POST.get('project_id')
    project = get_object_or_404(Project.objects.all(), id=project_id)
                     # ai_user=self.request.user)
    jobs = project.project_jobs_set.all()
    try:
        if project.voice_proj_detail.project_type_sub_category_id == 2:     ###########text-to-speech
            jobs =  project.project_jobs_set.filter(~Q(target_language=None))
            tasks = project.get_assignable_tasks
        else:  ###########speech-to-text#################
            jobs = project.project_jobs_set.all()
            tasks = project.get_tasks
    except:
        jobs = project.project_jobs_set.all()
        tasks = project.get_tasks
    contents = project.proj_content_type.all()
    subjects = project.proj_subject.all()
    jobs = JobSerializer(jobs, many=True)
    contents = ProjectContentTypeSerializer(contents,many=True)
    subjects = ProjectSubjectSerializer(subjects,many=True)
    # tasks = project.get_tasks
    task_count_detail = [{'source-target-pair':i.job.source_target_pair_names,\
                        'word_count':i.task_word_count if i.task_details.exists() else None} for i in tasks]
    result = {'project_name':project.project_name,'project_type':project.project_type_id,'task_count_detail':task_count_detail,'jobs':jobs.data,'subjects':subjects.data,'contents':contents.data}
    return JsonResponse({"res":result},safe=False)




class ProjectPostInfoCreateView(viewsets.ViewSet, PageNumberPagination):
    serializer_class = ProjectPostSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['proj_name','projectpost_jobs__src_lang__language','projectpost_jobs__tar_lang__language']
    ordering_fields = ['proj_name','id']
    page_size = 20

    def filter_queryset(self, queryset):
        from rest_framework.filters import SearchFilter, OrderingFilter
        filter_backends = (DjangoFilterBackend,SearchFilter,OrderingFilter )
        for backend in list(filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        return queryset

    def get(self, request):
        #try:
        projectpost_id = request.GET.get('project_post_id')
        if projectpost_id:
            queryset = ProjectboardDetails.objects.filter(Q(id=projectpost_id) & Q(customer_id = request.user.id) & Q(deleted_at=None)).order_by('-id').all()
        else:
            queryset = ProjectboardDetails.objects.filter(deleted_at=None).filter(Q(customer_id = request.user.id) | Q(project__team__owner = request.user) | Q(project__team__internal_member_team_info__in = request.user.internal_member.filter(role=1))).order_by('-id').distinct()
            # queryset = ProjectboardDetails.objects.filter(Q(customer_id = request.user.id) & Q(deleted_at=None)).order_by('-id').all()
        queryset = self.filter_queryset(queryset)
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = ProjectPostSerializer(pagin_tc,many=True,context={'request':request})
        response = self.get_paginated_response(serializer.data)
        return response
            #return Response(serializer.data)
        # except:
        #     return Response(status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, pk):
        query = ProjectboardDetails.objects.get(id=pk)
        serializer = ProjectPostSerializer(query, many=False, context={'request': request})
        return Response(serializer.data)

    def create(self, request):
        template = request.POST.get('is_template',None)
        customer = request.user.team.owner if request.user.team else request.user
        if template: ####template create only added.........update and delete need to be included#############
            serializer1 = ProjectPostTemplateSerializer(data={**request.POST.dict(),'customer_id':customer.id})
            if serializer1.is_valid():
                serializer1.save()
        # customer = request.user.id
        serializer = ProjectPostSerializer(data={**request.POST.dict(),'customer_id':customer.id,'posted_by_id':request.user.id},context={'request':request})

        if serializer.is_valid():
            serializer.save()
            print("ID------------------->",serializer.data.get('id'))
            shortlisted_vendor_list_send_email_new.apply_async((
            serializer.data.get('id'),
            ))
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def update(self,request,pk):
        projectpost_info = ProjectboardDetails.objects.get(id=pk)
        content_delete_ids = self.request.query_params.get(\
            "content_delete_ids", [])
        subject_delete_ids = self.request.query_params.get(\
            "subject_delete_ids", [])
        job_delete_ids = self.request.query_params.get(\
            "job_delete_ids", [])

        if content_delete_ids:
            contentlist = content_delete_ids.split(',')
            projectpost_info.projectpost_content_type.filter(id__in=contentlist).delete()

        if subject_delete_ids:
            subjectlist = subject_delete_ids.split(',')
            projectpost_info.projectpost_subject.filter(id__in=subjectlist).delete()

        if job_delete_ids:
            jobslist = job_delete_ids.split(',')
            projectpost_info.projectpost_jobs.filter(id__in=jobslist).delete()

        serializer = ProjectPostSerializer(projectpost_info,data={**request.POST.dict()},context={'request':request},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self,request,pk):
        projectpost_info = ProjectboardDetails.objects.get(id=pk)
        projectpost_info.deleted_at = timezone.now()
        projectpost_info.save()
        return Response(status=204)


@api_view(['GET',])
@permission_classes([IsAuthenticated])
def user_projectpost_list(request):
    customer_id = request.user.id
    present = timezone.now()
    new=[]
    try:
        queryset = ProjectboardDetails.objects.filter(deleted_at=None).filter(Q(customer = request.user)|Q(project__team__owner = request.user)|Q(project__team__internal_member_team_info__in = request.user.internal_member.filter(role=1))).distinct()
        # queryset = ProjectboardDetails.objects.filter(Q(customer_id = request.user.id) & Q(deleted_at=None)).all()
        for i in queryset:
            jobs =ProjectPostJobDetails.objects.filter(projectpost = i.id).count()
            projectpost_title = i.proj_name
            projectpost_id=i.id
            posted_word_count = i.post_word_count
            bids = BidPropasalDetails.objects.filter(projectpost_id = i.id).count()
            post_status = "InBidding" if i.bid_deadline >= present else "Expired"
            out=[{'jobs':jobs,'projectpost_title':projectpost_title,\
                'bids':bids,'projectpost_id':projectpost_id,\
                'posted_word_count':posted_word_count,"status":post_status}]
            new.extend(out)
        return JsonResponse({'out':new},safe=False)
    except:
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET',])
@permission_classes([IsAuthenticated])
def project_post_template_options(request):
    query = ProjectboardTemplateDetails.objects.filter(Q(customer=request.user) | Q(project__team__internal_member_team_info__in = request.user.internal_member.filter(role=1))).distinct()
    out = []
    for i in query:
        res = {'id':i.id,'template_name':i.template_name,}
        out.append(res)
    return Response(out)


@api_view(['DELETE',])
@permission_classes([IsAuthenticated])
def project_post_template_delete(request,id):
    obj = ProjectboardTemplateDetails.objects.filter(Q(customer=request.user)\
         | Q(project__team__internal_member_team_info__in = request.user.internal_member.filter(role=1))).filter(Q(id = id))
    if obj:
        obj.last().delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET',])
@permission_classes([IsAuthenticated])
def project_post_template_get(request):
    template = request.GET.get('template')
    query = ProjectboardTemplateDetails.objects.filter(Q(id=template))# & Q(customer = request.user))
    if query:
        ser = ProjectPostTemplateSerializer(query,many=True)
        return Response(ser.data)
    else:
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST',])
@permission_classes([IsAuthenticated])
def addingthread(request):
    user1=request.user.id
    bid_id=request.POST.get("bid_id")
    uid=request.POST.get("vendor_id")
    user2=AiUser.objects.get(uid=uid).id
    serializer = ThreadSerializer(data={'first_person':user1,'second_person':user2,'bid':bid_id})
    if serializer.is_valid():
        serializer.save()
        return JsonResponse(serializer.data, status=201)
    else:
        return JsonResponse(serializer.errors, status=400)



class BidPostInfoCreateView(viewsets.ViewSet, PageNumberPagination):
    permission_classes = [IsAuthenticated]
    page_size = 20

    def get(self, request):
        pr_managers = self.request.user.team.get_project_manager if self.request.user.team and self.request.user.team.owner.is_agency else [] 
        user = self.request.user.team.owner if request.user.team and request.user.team.owner.is_agency and request.user in pr_managers else request.user
        if user.is_vendor == True:
            try:
                print(user.id)
                id = request.GET.get('id')
                queryset = BidPropasalDetails.objects.select_related('vendor').filter(Q(vendor=user.id)).distinct().order_by('-id').all()
                pagin_tc = self.paginate_queryset(queryset, request , view=self)
                serializer = BidPropasalDetailSerializer(pagin_tc,many=True,context={'request':request})
                response = self.get_paginated_response(serializer.data)
                return response
                # serializer = BidPropasalDetailSerializer(queryset,many=True,context={'request':request})
                # return Response(serializer.data)
            except:
                return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'msg':'user is not a vendor'})

    @integrity_error
    def create(self, request):###########Need to check#############
        pr_managers = self.request.user.team.get_project_manager if self.request.user.team and self.request.user.team.owner.is_agency else [] 
        user = self.request.user.team.owner if request.user.team and request.user.team.owner.is_agency and request.user in pr_managers else request.user
        if user.is_vendor == True:
            post_id = request.POST.get('post_id')
            post = ProjectboardDetails.objects.get(id=post_id)
            sample_file=request.FILES.get('sample_file')
            serializer = BidPropasalDetailSerializer(data={**request.POST.dict(),'projectpost_id':post_id,'sample_file':sample_file,'vendor_id':user.id},context={'request':request})
            print(serializer.is_valid())
            if serializer.is_valid():
                with transaction.atomic():
                    serializer.save()
                    #print("data----------->",serializer.data)
                queryset = BidPropasalDetails.objects.filter(projectpost_id= post_id).all()
                serializer = BidPropasalDetailSerializer(queryset,many=True,context={'request':request})
                return Response({"msg":"Bid Posted","data":serializer.data})
            return Response(serializer.errors)
        else:
            return Response({'msg':'user is not a vendor'})


    def update(self,request,pk):
        Bid_info = BidPropasalDetails.objects.get(id=pk)#bid_proposal_id
        # Bid_info = get_object_or_404(queryset, id=bid_proposal_id)
        sample_file=request.FILES.get('sample_file')
        if sample_file:
            serializer = BidPropasalDetailSerializer(Bid_info,data={**request.POST.dict(),'sample_file':sample_file},context={'request':request},partial=True)
        else:
            serializer = BidPropasalDetailSerializer(Bid_info,data={**request.POST.dict()},context={'request':request},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def delete(self,request,pk):
        Bid_info = BidPropasalDetails.objects.get(Q(id=pk) & Q(vendor=request.user))
        Bid_info.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST',])
@permission_classes([IsAuthenticated])
def post_bid_primary_details(request):############need to include currency conversion###############
    pr_managers = request.user.team.get_project_manager if request.user.team and request.user.team.owner.is_agency else [] 
    user = request.user.team.owner if request.user.team and request.user.team.owner.is_agency and request.user in pr_managers else request.user
    if user.is_vendor == True:
        projectpost = request.POST.get('projectpost')
        post = ProjectboardDetails.objects.get(id = projectpost)
        ser = PrimaryBidDetailSerializer(post,context={'request':request})
        return Response(ser.data)
    else:
        return JsonResponse({'msg':'not a vendor'})


def unit_price_float_format(price):
    formatNumber = lambda n: n if n%1 else int(n)
    return formatNumber(price)


@api_view(['POST',])
@permission_classes([IsAuthenticated])
def bid_proposal_status(request):
    bid_detail_id= request.POST.get('id')
    obj = BidPropasalDetails.objects.get(id = bid_detail_id)
    shortlist = request.POST.get('shortlist',None)
    if shortlist:
        obj.is_shortlisted = True if shortlist == 'true' else False
        obj.save()
    status = json.loads(request.POST.get('status')) if request.POST.get('status') else None
    if status == 2 or status == 4:
        BidPropasalDetails.objects.filter(id = bid_detail_id).update(status = status)
    elif status == 3:
        if request.user.team: user = request.user.team.owner
        else: user = request.user
        if user != obj.vendor:
            tt,created = HiredEditors.objects.get_or_create(user_id=user.id,hired_editor_id=obj.vendor_id,role_id=2,defaults = {"status":1,"added_by_id":request.user.id})
            if created == False:
                if tt.status == 1:
                    tt.status = 2
                    tt.save()
                BidPropasalDetails.objects.filter(id = bid_detail_id).update(status = status)
                return Response({"msg":"Already in HiredEditors List....Redirect to Assign Page"})
            elif created == True:
                print(obj)
                uid = urlsafe_base64_encode(force_bytes(tt.id))
                token = invite_accept_token.make_token(tt)
                link = join(settings.TRANSEDITOR_BASE_URL,settings.EXTERNAL_MEMBER_ACCEPT_URL, uid,token)
                context = {'name':obj.vendor.fullname,'team':user.fullname,'link':link,'job':obj.bidpostjob.source_target_pair_names,
                           'hourly_rate': str(unit_price_float_format(obj.mtpe_hourly_rate)) +'(' + obj.currency.currency_code + ')' + ' per ' + obj.mtpe_count_unit.unit if obj.mtpe_hourly_rate else None,\
                            'unit_rate':str(unit_price_float_format(obj.mtpe_rate)) + '(' + obj.currency.currency_code + ')'+ ' per ' + obj.mtpe_count_unit.unit,\
                            'job_id':obj.bidpostjob.postjob_id,'project':obj.projectpost.proj_name,\
                            'date':obj.created_at.date().strftime('%d-%m-%Y')}
                print("Mail------>",obj.vendor.email)
                m_forms.external_member_invite_mail_after_bidding(context,obj.vendor.email)
                msg_send(user,obj.vendor)
            BidPropasalDetails.objects.filter(id = bid_detail_id).update(status = status)
            return JsonResponse({"msg":"Invite send...added to your HiredEditors list"})
        else:
            return JsonResponse({"msg":"Not a customer"})
    return JsonResponse({"msg":"status updated"})



def notification_read(thread_id,user):
    list = Notification.objects.filter(Q(data={'thread_id':thread_id})&Q(recipient=user))
    # print(list)
    list.mark_all_as_read()

class ChatMessageListView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatMessageSerializer
    filter_backends = [DjangoFilterBackend,SF,OF]
    ordering_fields = ['timestamp']
    # search_fields = ['chatmessage_thread__message',]
    # ordering=('-timestamp')

    def list(self, request,thread_id):
        queryset = Thread.objects.filter(id = thread_id).all()
        if queryset:
            # queryset_1=self.filter_queryset(queryset)
            serializer = ChatMessageByDateSerializer(queryset,many=True,context={'request':request})
            user = self.request.user
            notification_read(thread_id,user)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request,thread_id):
        user = request.user.id
        sender = AiUser.objects.get(id = user)
        tt = Thread.objects.get(id=thread_id)
        receiver = tt.second_person_id if tt.first_person_id == request.user.id else tt.first_person_id
        Receiver = AiUser.objects.get(id = receiver)
        serializer = ChatMessageSerializer(data={**request.POST.dict(),'thread':thread_id,'user':user},context={'request':request})
        if serializer.is_valid():
            serializer.save()
            thread_id = serializer.data.get('thread')
            notify.send(sender, recipient=Receiver, verb='Message', description=request.POST.get('message'),thread_id=thread_id)
            return Response(serializer.data)
        return Response(serializer.errors)

    def update(self,request,chatmessage_id):
        user=request.user.id
        chat_info = ChatMessage.objects.get(id=chatmessage_id)
        serializer = ChatMessageSerializer(chat_info,data={**request.POST.dict()},context={'request':request},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

    def destroy(self, request,chatmessage_id):
        obj = ChatMessage.objects.get(id=chatmessage_id)
        obj.message='[DELETED MESSAGE]'
        obj.save()
        return Response({'msg':'deleted'})


# class IncompleteProjectListView(generics.ListAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = SimpleProjectSerializer
#     pagination.PageNumberPagination.page_size = 20
#
#     def get_queryset(self):
#         query = ProjectboardDetails.objects.filter(customer = self.request.user.id)
#         projects = [i.project_id for i in query] if query else []
#         queryset=[x for x in Project.objects.filter(ai_user=self.request.user.id).filter(~Q(id__in = projects)).order_by('-id') if x.progress != "completed" ]
#         return queryset
class IncompleteProjectListFilter(django_filters.FilterSet):

    def filter(self, qs, value):
        return (pr for pr in qs if pr.get_assignable_tasks_exists == True)




class IncompleteProjectListView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SimpleProjectSerializer
    filterset_class = IncompleteProjectListFilter

    def get_queryset(self):
        pr_managers = self.request.user.team.get_project_manager if self.request.user.team else [] 
        user = self.request.user.team.owner if self.request.user.team and self.request.user in pr_managers else self.request.user
        queryset_2 = Project.objects.select_related('voice_proj_detail').filter(voice_proj_detail__project_type_sub_category_id=2).filter(project_jobs_set__target_language=None).values('id')
        queryset = Project.objects.filter(Q(ai_user=user)\
                    |Q(team__owner = self.request.user)|Q(team__internal_member_team_info__in = self.request.user.internal_member.filter(role=1)))\
                    .filter(Q(proj_detail__isnull=True)|(Q(proj_detail__isnull=False) & Q(proj_detail__deleted_at__isnull=False)))\
                    .exclude(id__in=queryset_2).order_by('-id').distinct()
        return queryset


    def list(self,request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = SimpleProjectSerializer(queryset, many=True)
        return  Response(serializer.data)



# @api_view(['GET',])
# @permission_classes([IsAuthenticated])
# def get_incomplete_projects_list(request):
#     queryset=Project.objects.filter(Q(ai_user=request.user)\
#                 |Q(team__owner = request.user)|Q(team__internal_member_team_info__in = request.user.internal_member.filter(role=1))).\
#                 exclude(Q(proj_detail__deleted_at=None) and Q(proj_detail__customer=request.user)).order_by('-id').distinct()
#     filtered = (x for x in queryset if x.get_assignable_tasks_exists == True)
#     ser = SimpleProjectSerializer(filtered,many=True)
#     return Response(ser.data)


    # query = ProjectboardDetails.objects.filter(deleted_at=None).filter(Q(customer = request.user)\
    #         |Q(project__team__owner = request.user)|Q(project__team__internal_member_team_info__in = request.user.internal_member.filter(role=1))).distinct()
    # projects = [i.project_id for i in query] if query else []
    # queryset=[x for x in Project.objects.filter(Q(ai_user=request.user)\
    #             |Q(team__owner = request.user)|Q(team__internal_member_team_info__in = request.user.internal_member.filter(role=1))).\
    #             filter(~Q(id__in = projects)).order_by('-id').distinct() if x.progress != "completed" and x.get_assignable_tasks != []]#.filter(voice_proj_detail__isnull=True)



class JobFilter(django_filters.FilterSet):
    fullname = django_filters.CharFilter(field_name='customer__fullname',lookup_expr='icontains')
    source = django_filters.CharFilter(field_name='projectpost_jobs__src_lang__language',lookup_expr='icontains')
    target = django_filters.CharFilter(field_name='projectpost_jobs__tar_lang__language',lookup_expr='icontains')
    #subject = django_filters.CharFilter(field_name='projectpost_subject__subject',lookup_expr='icontains')
    #content = django_filters.CharFilter(field_name='projectpost_subject__content',lookup_expr='icontains')
    subject = django_filters.CharFilter(method='filter_subject')

    def filter_subject(self, queryset, name, value):
        ids = value.split(',')  # split input into a list of IDs
        return queryset.filter(projectpost_subject__subject_id__in=ids)

    class Meta:
        model = ProjectboardDetails
        fields = ('fullname', 'source','target','subject',)#'content',)
        together = ['source','target']
        # groups = [
        #     RequiredGroup(['source', 'target']),
        #  ]
class NoPagination(PageNumberPagination):
      page_size = None


class AvailableJobsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AvailablePostJobSerializer
    filter_backends = [DjangoFilterBackend ,filters.SearchFilter,filters.OrderingFilter]
    ordering_fields = ['bid_deadline','proj_deadline','id']
    ordering = ('-id')
    filterset_class = JobFilter
    pagination_class = NoPagination
    # page_size = None

    def validate(self):
        pr_managers = self.request.user.team.get_project_manager if self.request.user.team and self.request.user.team.owner.is_agency else [] 
        user = self.request.user.team.owner if self.request.user.team and self.request.user.team.owner.is_agency and self.request.user in pr_managers else self.request.user
        if user.is_vendor == False:
            raise ValidationError({"error":"user is not a vendor"})

    def get_queryset(self):
        self.validate()
        pr_managers = self.request.user.team.get_project_manager if self.request.user.team and self.request.user.team.owner.is_agency else [] 
        user = self.request.user.team.owner if self.request.user.team and self.request.user.team.owner.is_agency and self.request.user in pr_managers else self.request.user
        present = timezone.now()
        queryset= ProjectboardDetails.objects.filter(~Q(customer=user)).filter(Q(bid_deadline__gte = present) & Q(deleted_at__isnull = True) &Q(closed_at__isnull = True)).distinct()
        print("@@@@@@@@@@@2",queryset)
        return queryset




@api_view(['GET',])
@permission_classes([IsAuthenticated])
def vendor_applied_jobs_list(request):
    try:
        print(request.user.id)
        queryset = BidPropasalDetails.objects.filter(vendor_id=request.user.id).all()
        serializer = BidPropasalDetailSerializer(queryset,many=True,context={'request':request})
        return Response(serializer.data)
    except:
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET',])
@permission_classes([IsAuthenticated])
def get_my_jobs(request):
    tasks = Task.objects.filter(assign_to_id=request.user.id)
    print(tasks)
    # tasks = Task.objects.filter(assign_to_id=request.user.id)
    tasks_serlzr = TaskSerializer(tasks, many=True)
    return Response(tasks_serlzr.data, status=200)

@api_view(['GET',])
@permission_classes([IsAuthenticated])
def get_available_threads(request):
    # name = request.GET.get('name')
    threads = Thread.objects.by_user(user=request.user).filter(chatmessage_thread__isnull = False).annotate(last_message=Max('chatmessage_thread__timestamp')).order_by('-last_message')
    receivers_list =[]
    for i in threads:
        receiver = i.second_person_id if i.first_person_id == request.user.id else i.first_person_id
        Receiver = AiUser.objects.get(id = receiver)
        try:profile = Receiver.professional_identity_info.avatar_url
        except:profile = None
        data = {'thread_id':i.id}
        chats = Notification.objects.filter(Q(data=data) & Q(verb='Message'))
        count = request.user.notifications.filter(Q(data=data) & Q(verb='Message')).unread().count()
        notification = chats.order_by('-timestamp').first()
        try:
            message = notification.description
            time = notification.timestamp
        except:
            message,time=None,None
        receivers_list.append({'thread_id':i.id,'receiver':Receiver.fullname,'receiver_id':receiver,'avatar':profile,\
                                'message':message,'timestamp':time,'unread_count':count})
    contacts_list = []
    all_threads = Thread.objects.by_user(user=request.user).all()
    for thread in all_threads:
        receiver = thread.second_person_id if thread.first_person_id == request.user.id else thread.first_person_id
        Receiver = AiUser.objects.get(id = receiver)
        try:profile = Receiver.professional_identity_info.avatar_url
        except:profile = None
        contacts_list.append({'thread_id':thread.id,'receiver':Receiver.fullname,'receiver_id':receiver,'avatar':profile})
    contacts = sorted(contacts_list, key = lambda i: i['receiver'].lower())
    return JsonResponse({"receivers_list":receivers_list,"contacts_list":contacts})





@api_view(['GET',])
@permission_classes([IsAuthenticated])
def chat_unread_notifications(request):
    user = AiUser.objects.get(pk=request.user.id)
    notification_details=[]
    notification=[]
    # notifications = user.notifications.unread().filter(verb='Message').order_by('data','-timestamp').distinct('data')
    notifications = user.notifications.unread().filter(verb='Message').filter(pk__in=Subquery(
            user.notifications.unread().filter(verb='Message').order_by("data",'-timestamp').distinct("data").values('id'))).order_by("-timestamp")
    for i in notifications:
       try:
           sender = AiUser.objects.get(id =i.actor_object_id)
           count = user.notifications.filter(Q(data=i.data) & Q(verb='Message')).unread().count()
           try:profile = sender.professional_identity_info.avatar_url
           except:profile = None
           notification_details.append({'thread_id':i.data.get('thread_id'),'avatar':profile,'sender':sender.fullname,'sender_id':sender.id,'message':i.description,'timestamp':i.timestamp,'count':count})
       except:
           mark_as_read = user.notifications.filter(Q(data=i.data) & Q(actor_object_id=i.actor_object_id)).mark_all_as_read()
    total_count = user.notifications.filter(verb='Message').unread().count()
    notification.append({'total_count':total_count})
    return JsonResponse({'notifications':notification,'notification_details':notification_details})

@api_view(['GET',])
@permission_classes([IsAuthenticated])
def general_notifications(request):
    user = AiUser.objects.get(pk=request.user.id)
    notifications = user.notifications.exclude(verb='Message').unread()
    count = user.notifications.exclude(verb='Message').unread().count()
    notification_details=[]
    notification_details.append({'count':count})
    for i in notifications:
        notification_details.append({'message':i.description,'time':i.timestamp,'sender':i.actor.fullname})#'time':i.timesince()
    return JsonResponse({'notifications':notification_details})


class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass

class CharInFilter(django_filters.BaseInFilter, django_filters.CharFilter):
    pass


class VendorFilterNew(django_filters.FilterSet):
    year_of_experience =django_filters.NumberFilter(field_name='vendor_info__year_of_experience',lookup_expr='gte')
    fullname =django_filters.CharFilter(field_name='fullname',lookup_expr='icontains')
    email = django_filters.CharFilter(field_name='email',lookup_expr='exact')
    country = django_filters.NumberFilter(field_name='country_id')
    location = django_filters.CharFilter(field_name='vendor_info__location',lookup_expr='icontains')
    category = django_filters.BooleanFilter(field_name='is_agency')
    class Meta:
        model = AiUser
        fields = ('fullname', 'email','year_of_experience','country','location','category',)


class GetVendorListViewNew(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GetVendorListSerializer
    filter_backends = [DjangoFilterBackend ,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = VendorFilterNew
    search_fields = ['fullname','email']
    pagination.PageNumberPagination.page_size = settings.REST_FRAMEWORK["PAGE_SIZE"]#None

    def validate(self):
        data = self.request.GET
        if (('min_price' in data) or ('max_price' in data) or ('count_unit' in data) or ('currency' in data)):
            if not (('min_price' in data) and ('max_price' in data) and ('count_unit' in data) and ('currency' in data)):
                raise ValidationError({"error":"max_price,min_price,count_unit,currency all fields are required"})


    def get_queryset(self):
        self.validate()
        user = self.request.user
        job_id= self.request.query_params.get('job')
        min_price =self.request.query_params.get('min_price')
        max_price =self.request.query_params.get('max_price')
        count_unit = self.request.query_params.get('count_unit')
        currency = self.request.query_params.get('currency')
        source_lang=self.request.query_params.get('source_lang')
        target_lang=self.request.query_params.get('target_lang')
        contenttype = self.request.query_params.get('content')
        subject=self.request.query_params.get('subject')
        if job_id:
            source_lang=Job.objects.get(id=job_id).source_language_id
            target_lang=Job.objects.get(id=job_id).target_language_id
        queryset = queryset_all = AiUser.objects.select_related('ai_profile_info','vendor_info','professional_identity_info')\
                    .filter(Q(vendor_lang_pair__source_lang_id=source_lang) & Q(vendor_lang_pair__target_lang_id=target_lang) & Q(vendor_lang_pair__deleted_at=None))\
                    .distinct().exclude(id = user.id).exclude(is_internal_member=True).exclude(is_vendor=False).exclude(is_active=False).exclude(deactivate=True)#.exclude(email='ams@ailaysa.com')
        if max_price and min_price and count_unit and currency:
            ids=[]
            for i in queryset.values('vendor_lang_pair__id'):
                ids.append(i.get('vendor_lang_pair__id'))
            queryset= queryset_all = queryset.filter(Q(vendor_lang_pair__service__mtpe_count_unit_id=count_unit)&Q(vendor_info__currency = currency)&Q(vendor_lang_pair__service__mtpe_rate__range=(min_price,max_price))&Q(vendor_lang_pair__service__lang_pair_id__in=ids)).distinct()
        if contenttype:
            contentlist = contenttype.split(',')
            queryset = queryset.filter(Q(vendor_contentype__contenttype_id__in=contentlist)&Q(vendor_contentype__deleted_at=None)).annotate(number_of_match=Count('vendor_contentype__contenttype_id',0)).order_by('-number_of_match').distinct()
        if subject:
            subjectlist=subject.split(',')
            queryset = queryset.filter(Q(vendor_subject__subject_id__in = subjectlist)&Q(vendor_subject__deleted_at=None)).annotate(number_of_match=Count('vendor_subject__subject_id',0)).order_by('-number_of_match').distinct()
        return queryset

    # def list(self, request, *args, **kwargs):
    #     queryset = self.filter_queryset(self.get_queryset())
    #     serializer = self.serializer_class(queryset, context={'request': request, 'user': request.user},many=True)
    #     return Response(serializer.data)




@api_view(['GET',])
@permission_classes([IsAuthenticated])
def get_last_messages(request):
    threads = Thread.objects.by_user(user=request.user).filter(chatmessage_thread__isnull = False).annotate(last_message=Max('chatmessage_thread__timestamp')).order_by('-last_message')
    data=[]
    for i in threads:
        ins = {'thread_id':i.id}
        count = request.user.notifications.filter(Q(data=ins) & Q(verb='Message')).unread().count()
        # print("RR--->",count)
        obj =  ChatMessage.objects.filter(thread_id = i.id).last()
        data.append({'thread_id':i.id,'last_message':obj.message,'unread_count':count,'last_timestamp':obj.timestamp})
    return JsonResponse({"data":data},safe=False)


@api_view(['POST',])
@permission_classes([IsAuthenticated])
def get_previous_accepted_rate(request):
    user = request.user
    vendor_id = request.POST.get('vendor_id')
    jobs = request.POST.getlist('job_id')
    final_rates =[]
    final_rates_given=[]
    for j in jobs:
        job_obj = Job.objects.get(id=j)
        authorize(request, resource=job_obj, actor=request.user, action="read")
        print(job_obj.source_language,job_obj.target_language)
        vendor = AiUser.objects.get(id=vendor_id)
        query = TaskAssignInfo.objects.filter(Q(task_ven_status = 'task_accepted') & Q(assigned_by = user) & Q(task_assign__assign_to = vendor)).order_by('-id')
        query_final = query.filter(Q(task_assign__task__job__source_language = job_obj.source_language) & Q(task_assign__task__job__target_language = job_obj.target_language)).last()
        rates ={}
        out = {'currency':query_final.currency.id,'mtpe_rate':query_final.mtpe_rate,'mtpe_count_unit':query_final.mtpe_count_unit_id,'step':query_final.task_assign.step.id} if query_final else {}
        rates[j] = out
        final_rates.append(rates)
        rates_given={}
        query_1 = VendorLanguagePair.objects.filter((Q(source_lang_id=job_obj.source_language_id) & Q(target_lang_id=job_obj.target_language_id) & Q(user=vendor) & Q(deleted_at=None)))\
                .select_related('service').values('currency','service__mtpe_rate','service__mtpe_hourly_rate','service__mtpe_count_unit')
        tot_2=[]
        for i in query_1:
            currency = i.get('currency') if i.get('currency')!=None else vendor.vendor_info.currency.id
            print("SS---------->",i.get('service__mtpe_rate'))
            if i.get('service__mtpe_rate') != None:
                print("Inside if")
                out_1 = [{'currency':currency,'mtpe_rate':i.get('service__mtpe_rate'),\
                        'hourly_rate':i.get('service__mtpe_hourly_rate'),'mtpe_count_unit':i.get('service__mtpe_count_unit')}]
                if out_1:
                    tot_2.extend(out_1)
        #if tot_2:
        rates_given[j] = tot_2
        final_rates_given.append(rates_given)
    return JsonResponse({"Previously Agreed Rates":final_rates,"Given Rates":final_rates_given})



# @api_view(['POST',])
# @permission_classes([IsAuthenticated])
# def get_previous_accepted_rate(request):
#     user = request.user
#     vendor_id = request.POST.get('vendor_id')
#     jobs = request.POST.getlist('job_id')
#     final_rates =[]
#     final_rates_given=[]
#     for j in jobs:
#         job_obj = Job.objects.get(id=j)
#         authorize(request, resource=job_obj, actor=request.user, action="read")
#         print(job_obj.source_language,job_obj.target_language)
#         vendor = AiUser.objects.get(id=vendor_id)
#         print(vendor)
#         #query = TaskAssignInfo.objects.filter(Q(assigned_by = user) & Q(task__assign_to = vendor))
#         query = TaskAssignInfo.objects.filter(Q(task_ven_status = 'task_accepted') & Q(assigned_by = user) & Q(task_assign__assign_to = vendor)).order_by('-id')
#         query_final = query.filter(Q(task_assign__task__job__source_language = job_obj.source_language) & Q(task_assign__task__job__target_language = job_obj.target_language)).last()
#         rates ={}
#         tot =[]
#         for i in query_final:
#             out = [{'currency':i.currency.id,'mtpe_rate':i.mtpe_rate,'mtpe_count_unit':i.mtpe_count_unit_id,'step':i.task_assign.step.id}]
#             if out:
#                 tot.extend(out)
#         #if tot:
#         rates[j] = tot
#         final_rates.append(rates)
#         rates_given={}
#         query_1 = VendorLanguagePair.objects.filter((Q(source_lang_id=job_obj.source_language_id) & Q(target_lang_id=job_obj.target_language_id) & Q(user=vendor) & Q(deleted_at=None)))\
#                 .select_related('service').values('currency','service__mtpe_rate','service__mtpe_hourly_rate','service__mtpe_count_unit')
#         tot_2=[]
#         for i in query_1:
#             currency = i.get('currency') if i.get('currency')!=None else vendor.vendor_info.currency.id
#             out = [{'currency':currency,'mtpe_rate':i.get('service__mtpe_rate'),\
#                         'hourly_rate':i.get('service__mtpe_hourly_rate'),'mtpe_count_unit':i.get('service__mtpe_count_unit')}]
#             if out:
#                 tot_2.extend(out)
#         #if tot_2:
#         rates_given[j] = tot_2
#         final_rates_given.append(rates_given)
#     return JsonResponse({"Previously Agreed Rates":final_rates,"Given Rates":final_rates_given})

# @api_view(['POST',])
# @permission_classes([IsAuthenticated])
# def get_previous_accepted_rate(request):
#     user = request.user
#     vendor_id = request.POST.get('vendor_id')
#     job_id = request.POST.get('job_id')
#     job_obj = Job.objects.get(id=job_id)
#     authorize(request, resource=job_obj, actor=request.user, action="read")
#     print(job_obj.source_language,job_obj.target_language)
#     vendor = AiUser.objects.get(id=vendor_id)
#     print(vendor)
#     #query = TaskAssignInfo.objects.filter(Q(assigned_by = user) & Q(task__assign_to = vendor))
#     query = TaskAssignInfo.objects.filter(Q(task_ven_status = 'task_accepted') & Q(assigned_by = user) & Q(task_assign__assign_to = vendor)).order_by('-id')
#     query_final = query.filter(Q(task_assign__task__job__source_language = job_obj.source_language) & Q(task_assign__task__job__target_language = job_obj.target_language))
#     rates =[]
#     for i in query_final:
#         out = [{'currency':i.currency.id,'mtpe_rate':i.mtpe_rate,'mtpe_count_unit':i.mtpe_count_unit_id,'step':i.task_assign.step.id}]
#         rates.append(out)
#     rates_given=[]
#     query_1 = VendorLanguagePair.objects.filter((Q(source_lang_id=job_obj.source_language_id) & Q(target_lang_id=job_obj.target_language_id) & Q(user=vendor) & Q(deleted_at=None)))\
#              .select_related('service').values('currency','service__mtpe_rate','service__mtpe_hourly_rate','service__mtpe_count_unit')
#     for i in query_1:
#         currency = i.get('currency') if i.get('currency')!=None else vendor.vendor_info.currency.id
#         out = [{'currency':currency,'mtpe_rate':i.get('service__mtpe_rate'),\
#                     'hourly_rate':i.get('service__mtpe_hourly_rate'),'mtpe_count_unit':i.get('service__mtpe_count_unit')}]
#         rates_given.extend(out)
#     return JsonResponse({"Previously Agreed Rates":rates,"Given Rates":rates_given})




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def customer_mp_dashboard_count(request):
    user = request.user
    present = datetime.now()
    query = ProjectboardDetails.objects.filter(deleted_at=None).filter(Q(customer = request.user.id)\
                                    |Q(project__team__internal_member_team_info__in = request.user.internal_member.filter(role=1))).distinct()
    # query = ProjectboardDetails.objects.filter(Q(customer_id = request.user.id) & Q(deleted_at=None)).all()
    #query = ProjectboardDetails.objects.filter(customer = user)
    posted_project_count = query.count()
    inprogress_project_count = query.filter(bid_deadline__gte = present).filter(closed_at = None).count()
    bid_deadline_expired_project_count = query.filter(bid_deadline__lte = present).count()
    return JsonResponse({"posted_project_count":posted_project_count,\
    "inprogress_project_count":inprogress_project_count,\
    "bid_deadline_expired_project_count":bid_deadline_expired_project_count})






class GetVendorListBasedonProjects(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def dt(res,K):
        res_2={}
        for key, val in res.items():
            res_2[key]=val[:K]
            count_1 = sum(len(v) for k, v in res_2.items())
            if count_1<3:
                continue
            elif count_1>=4:
                res_2[key]=val[:1]
                break
        return res_2



    def list(self,request):
        user = self.request.user
        sltl_list = Project.objects.filter(ai_user = user).distinct().\
                values('project_jobs_set__source_language','project_jobs_set__target_language').\
                annotate(sltl=Count('project_jobs_set__source_language__language')).order_by('-sltl')[:5]
        query = AiUser.objects.none()
        res ={}
        users = []
        for i in sltl_list:
            source_lang = i.get('project_jobs_set__source_language')
            target_lang = i.get('project_jobs_set__target_language')
            source_lang_name = Languages.objects.get(id=source_lang).language if source_lang != None else None
            target_lang_name = Languages.objects.get(id=target_lang).language if target_lang != None else None
            queryset = AiUser.objects.select_related('ai_profile_info','vendor_info','professional_identity_info')\
                        .filter(Q(vendor_lang_pair__source_lang_id=source_lang) & Q(vendor_lang_pair__target_lang_id=target_lang) & Q(vendor_lang_pair__deleted_at=None))\
                        .distinct().exclude(id = user.id).exclude(is_internal_member=True).exclude(is_vendor=False).exclude(id__in=users).exclude(is_active=False).exclude(deactivate=True)
            if queryset:
                ser = GetVendorListBasedonProjectSerializer(queryset.first(),many=False,context={'request':request,'sl':source_lang,'tl':target_lang})
                users.append(queryset.first().id)
                tt = str(source_lang_name) + '---->' + str(target_lang_name)
                res[tt] = [ser.data]
        return Response(res)
        #print("Res-------------->",res)
        # print("Len of RES-------->",len(res))
        # return Response(res)
        # if len(res)>=3:return Response(self.dt(res,1))
        # elif len(res)==2:return Response(self.dt(res,2))
        # elif len(res)==1:return Response(self.dt(res,3))
        # else:return Response([])

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_talents(request):
    user = request.user.team.owner if request.user.team else request.user
    ser = GetTalentSerializer(user,context={'request':request})
    return Response(ser.data)


# class GetVendorListBasedonProjects(generics.ListAPIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = GetVendorListSerializer
#
#     def get_queryset(self):
#         user = self.request.user
#         sltl_list = Project.objects.filter(ai_user = user).distinct().\
#                 values('project_jobs_set__source_language','project_jobs_set__target_language').\
#                 annotate(sltl=Count('project_jobs_set__source_language__language')).order_by('-sltl')[:5]
#         query = AiUser.objects.none()
#         for i in sltl_list:
#             source_lang = i.get('project_jobs_set__source_language')
#             target_lang = i.get('project_jobs_set__target_language')
#             queryset = AiUser.objects.select_related('ai_profile_info','vendor_info','professional_identity_info')\
#                         .filter(Q(vendor_lang_pair__source_lang_id=source_lang) & Q(vendor_lang_pair__target_lang_id=target_lang) & Q(vendor_lang_pair__deleted_at=None))\
#                         .distinct().exclude(id = user.id).exclude(is_internal_member=True).exclude(is_vendor=False)
#             query = query.union(queryset)
#         return query
        # lang_pair = VendorLanguagePair.objects.none()
        # for i in sltl_list:
        #     query = VendorLanguagePair.objects.filter(Q(source_lang=i.get('project_jobs_set__source_language'))\
        #             &Q(target_lang=i.get('project_jobs_set__target_language'))&Q(deleted_at=None)).values_list('user_id',flat=True)
        #     lang_pair = lang_pair.union(query)
        # users_list = AiUser.objects.filter(id__in = lang_pair).distinct().exclude(id = user.id).exclude(is_internal_member=True).exclude(is_vendor=False)
        # return users_list




# class BidPostUpdateView(viewsets.ViewSet):
#     permission_classes = [IsAuthenticated]
#
#     def update(self,request,pk):
#         if self.request.user.is_vendor == True:
#             Bid_info = BidPropasalDetails.objects.get(id=pk)#bid_proposal_id
#             sample_file=request.FILES.get('sample_file')
#             if sample_file:
#                 serializer = BidPropasalUpdateSerializer(Bid_info,data={**request.POST.dict(),'sample_file_upload':sample_file},partial=True)
#             else:
#                 serializer = BidPropasalUpdateSerializer(Bid_info,data={**request.POST.dict()},partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#                 return Response(serializer.data)
#             return Response(serializer.errors)
#         else:
#             return Response({'msg':'user is not a vendor'})


@api_view(['GET',])
#@permission_classes([IsAuthenticated])
def sample_file_download(request,bid_propasal_id):
    sample_file = BidPropasalDetails.objects.get(id=bid_propasal_id).sample_file
    if sample_file:
        return download_file(sample_file.path)
        # fl_path = sample_file.path
        # filename = os.path.basename(fl_path)
        # # print(os.path.dirname(fl_path))
        # fl = open(fl_path, 'rb')
        # mime_type, _ = mimetypes.guess_type(fl_path)
        # response = HttpResponse(fl, content_type=mime_type)
        # response['Content-Disposition'] = "attachment; filename=%s" % filename
        # return response
    else:
        return JsonResponse({"msg":"no file associated with it"})


@api_view(['GET',])
@permission_classes([IsAuthenticated])
def sample_file_delete(request,bid_propasal_id):
    sample_file = BidPropasalDetails.objects.get(id=bid_propasal_id).sample_file
    if sample_file:
        BidPropasalDetails.objects.get(id=bid_propasal_id).sample_file.delete()
        return JsonResponse({"msg":"File Deleted Successfully"})
    else:
        return JsonResponse({"msg":"no file associated with it"})
