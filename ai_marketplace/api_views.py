from rest_framework import filters,generics
from rest_framework.pagination import PageNumberPagination
import django_filters
from ai_marketplace import forms as m_forms
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter as SF, OrderingFilter as OF
from django.shortcuts import render
from os.path import join
from ai_auth.models import AiUser
from ai_staff.models import Languages,ContentTypes
from django.conf import settings
from notifications.signals import notify
from notifications.models import Notification
from django.db.models import Q, Max
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
                    Thread,BidPropasalDetails,ChatMessage,ProjectPostSubjectField,BidProposalServicesRates)
from .serializers import(ProjectPostSerializer,ProjectPostTemplateSerializer,
                        BidChatSerializer,BidPropasalDetailSerializer,
                        ThreadSerializer,GetVendorDetailSerializer,VendorServiceSerializer,
                        GetVendorListSerializer,ChatMessageSerializer,ChatMessageByDateSerializer,
                        SimpleProjectSerializer,AvailablePostJobSerializer,ProjectPostStepsSerializer,
                        PrimaryBidDetailSerializer)
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
# Create your views here.


@api_view(['GET','POST',])
@permission_classes([IsAuthenticated])
def get_vendor_detail(request):
    uid=request.POST.get('vendor_id')
    user=AiUser.objects.get(uid=uid)
    serializer = GetVendorDetailSerializer(user,context={'request':request})
    return Response(serializer.data)
    # job_id=request.GET.get('job_id')
    # source_lang=request.GET.get('source_lang')
    # target_lang=request.GET.get('target_lang')
    # uid=request.POST.get('vendor_id')
    # print(uid)
    # try:
    #     user=AiUser.objects.get(uid=uid)
    #     user_id = user.id
    #     lang = VendorLanguagePair.objects.get((Q(source_lang_id=source_lang) & Q(target_lang_id=target_lang) & Q(user_id=user_id)))
    #     # serializer1= VendorServiceSerializer(lang)
    #     # out.append(serializer1.data)
    #     serializer2= VendorLanguagePairCloneSerializer(lang)
    #     out.append(serializer2.data)
    #     serializer = GetVendorDetailSerializer(user,context={'request':request})
    #     out.append(serializer.data)
    # except:
    #     out = "Matching details does not exist"
    # return Response({"out":out})



# @api_view(['POST',])
# @permission_classes([IsAuthenticated])
# def assign_available_vendor_to_customer(request):
#     uid=request.POST.get('vendor_id')
#     bid_id = request.POST.get('bid_id',None)
#     print(bid_id)
#     if uid:
#         vendor_id=AiUser.objects.get(uid=uid).id
#     elif bid_id:
#         vendor_id=BidPropasalDetails.objects.get(id=bid_id).vendor_id
#     customer_id=request.user.id
#     serializer=AvailableVendorSerializer(data={"vendor":vendor_id,"customer":customer_id})
#     if serializer.is_valid():
#         serializer.save()
#         if bid_id:
#             try:
#                 Bid_info = BidPropasalDetails.objects.get(id=bid_id)
#                 serializer2 = BidPropasalDetailSerializer(Bid_info,data={'status':4},partial=True)
#                 if serializer2.is_valid():
#                     serializer2.save()
#                 else:
#                     print(serializer2.errors)
#             except:
#                 print("No bid detail exists")
#         return Response(data={"Message":"Vendor Assigned to User Successfully"})
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST',])
@permission_classes([IsAuthenticated])
def post_project_primary_details(request):
    project_id=request.POST.get('project_id')
    project = get_object_or_404(Project.objects.all(), id=project_id)
                     # ai_user=self.request.user)
    jobs = project.project_jobs_set.all()
    contents = project.proj_content_type.all()
    subjects = project.proj_subject.all()
    jobs = JobSerializer(jobs, many=True)
    contents = ProjectContentTypeSerializer(contents,many=True)
    subjects = ProjectSubjectSerializer(subjects,many=True)
    result = {'project_name':project.project_name,'jobs':jobs.data,'subjects':subjects.data,'contents':contents.data}
    return JsonResponse({"res":result},safe=False)
    # jobslist=Job.objects.filter(project_id=project_id).values('source_language_id','target_language_id')
    # result={}
    # tar_lang=[]
    # for i in jobslist:
    #     lang=i.get('target_language_id')
    #     tar_lang.append(lang)
    # jobs=[{"src_lang":i.get('source_language_id'),"tar_lang":tar_lang}]
    # result["jobs"]=jobs
    # subjectfield = ProjectSubjectField.objects.filter(project_id=project_id).all()
    # subjects=[]
    # for i in subjectfield:
    #     subjects.append({'subject':i.subject_id})
    # result["subjects"]=subjects
    # content_type = ProjectContentType.objects.filter(project_id=project_id).all()
    # contents=[]
    # for j in content_type:
    #     contents.append({'content_type':j.content_type_id})
    # result["contents"]=contents
    # result["project_name"]=Project.objects.get(id=project_id).project_name
    # # proj_detail = Project.objects.select_related('proj_subject','proj_content_type').filter(id=1)\
    # #               .values('proj_content_type__content_type_id', 'proj_subject__subject_id','project_name')
    # # proj_detail={"project_name":proj_detail[0].get('project_name'),"subject":proj_detail[0].get('proj_subject__subject_id'),"content_type":proj_detail[0].get('proj_content_type__content_type_id')}
    # # result["projectpost_detail"]=proj_detail
    # return JsonResponse({"res":result},safe=False)


class ProjectPostInfoCreateView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            print(request.user.id)
            projectpost_id = request.GET.get('project_post_id')
            if projectpost_id:
                queryset = ProjectboardDetails.objects.filter(Q(id=projectpost_id) & Q(customer_id = request.user.id)).all()
                print(queryset)
            else:
                queryset = ProjectboardDetails.objects.filter(customer_id = request.user.id).all()
            serializer = ProjectPostSerializer(queryset,many=True)
            return Response(serializer.data)
        except:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def create(self, request):
        template = request.POST.get('is_template',None)
        if template: ####template create only added.........update and delete need to be included#############
            serializer1 = ProjectPostTemplateSerializer(data={**request.POST.dict(),'customer_id':request.user.id})
            if serializer1.is_valid():
                serializer1.save()
        customer = request.user.id
        serializer = ProjectPostSerializer(data={**request.POST.dict(),'customer_id':customer})#,context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

    def update(self,request,pk):
        projectpost_info = ProjectboardDetails.objects.get(id=pk)
        serializer = ProjectPostSerializer(projectpost_info,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

    def delete(self,request,pk):
        projectpost_info = ProjectboardDetails.objects.get(id=pk)
        projectpost_info.delete()
        return Response(status=204)


@api_view(['GET',])
@permission_classes([IsAuthenticated])
def user_projectpost_list(request):
    customer_id = request.user.id
    new=[]
    try:
        queryset = ProjectboardDetails.objects.filter(customer_id=customer_id).all()
        print(queryset)
        for i in queryset:
            jobs =ProjectPostJobDetails.objects.filter(projectpost = i.id).count()
            project = i.proj_name
            projectpost_id=i.id
            bids = BidPropasalDetails.objects.filter(projectpost_id = i.id).count()
            out=[{'jobs':jobs,'project':project,'bids':bids,'projectpost_id':projectpost_id}]
            new.extend(out)
        return JsonResponse({'out':new},safe=False)
    except:
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST',])
@permission_classes([IsAuthenticated])
def shortlisted_vendor_list_send_email_new(request):
    projectpost_id=request.POST.get('projectpost_id')
    projectpost = ProjectboardDetails.objects.get(id=projectpost_id)
    jobs = projectpost.get_postedjobs
    lang_pair = VendorLanguagePair.objects.none()
    for obj in jobs:
        query = VendorLanguagePair.objects.filter(Q(source_lang_id=obj.src_lang_id) & Q(target_lang_id=obj.tar_lang_id) & Q(deleted_at=None))
        lang_pair = lang_pair|query
    res={}
    for object in lang_pair:
        print(object.user.fullname)
        if object.user_id in res:
            res[object.user_id].get('lang').append({'source':object.source_lang.language,'target':object.target_lang.language})
        else:
            res[object.user_id]={'name':object.user.fullname,'user_email':object.user.email,'lang':[{'source':object.source_lang.language,'target':object.target_lang.language}],'project_deadline':projectpost.proj_deadline,'bid_deadline':projectpost.bid_deadline}
    auth_forms.vendor_notify_post_jobs(res)
    return Response({"msg":"mailsent"})


# @api_view(['POST',])
# @permission_classes([IsAuthenticated])
# def shortlisted_vendor_list_send_email(request):
#     projectpost_id=request.POST.get('projectpost_id')
#     new=[]
#     userslist=[]
#     jobs=ProjectPostJobDetails.objects.filter(projectpost_id=projectpost_id).all()
#     project_deadline=ProjectboardDetails.objects.get(id=projectpost_id).proj_deadline
#     bid_deadline=ProjectboardDetails.objects.get(id=projectpost_id).bid_deadline
#     for i in jobs:
#         res=VendorLanguagePair.objects.filter(Q(source_lang_id=i.src_lang_id) & Q(target_lang_id=i.tar_lang_id)).all()
#         if res:
#             for j in res:
#                 out=[]
#                 print(i.id)
#                 print(j.user_id)
#                 serializer=AvailableJobSerializer(data={'projectpostjob':i.id,'vendor':j.user_id,'projectpost':projectpost_id})
#                 if serializer.is_valid():
#                     serializer.save()
#                 print(serializer.errors)
#                 src_lang=Languages.objects.get(id=i.src_lang_id).language
#                 tar_lang=Languages.objects.get(id=i.tar_lang_id).language
#                 user_id=VendorLanguagePair.objects.get(id=j.id).user_id
#                 out=[{"lang":[{"src_lang":src_lang,"tar_lang":tar_lang}],"user_id":user_id}]
#                 if user_id not in userslist:
#                     new.extend(out)
#                     userslist.append(user_id)
#                 else:
#                     for k in new:
#                         if k.get("user_id")==user_id:
#                             k.get("lang").extend(out[0].get("lang"))
#     print(new)
#     if new:
#         for data in new:
#             user_id=data.get('user_id')
#             user=AiUser.objects.get(id=user_id).fullname
#             email=AiUser.objects.get(id=user_id).email
#             print(email)
#             template = 'email.html'
#             context = {'user': user, 'lang':data.get('lang'),'proj_deadline':project_deadline,'bid_deadline':bid_deadline}
#             content = render_to_string(template, context)
#             subject='Regarding Available jobs'
#             msg = EmailMessage(subject, content, settings.DEFAULT_FROM_EMAIL, to=[email,])
#             msg.content_subtype = 'html'
#             msg.send()
#         return JsonResponse({"message":"Email Successfully Sent"},safe=False)
#     else:
#         return JsonResponse({"message":"No Match Found"},safe=False)




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

    # if bid_id:
    #     user=BidPropasalDetails.objects.get(id=bid_id).vendor_id
    #     if user == user1:
    #         projectpostjob = BidPropasalDetails.objects.get(id=bid_id).projectpostjob_id
    #         projectpost = ProjectPostJobDetails.objects.get(id=projectpostjob).projectpost_id
    #         user2 = ProjectboardDetails.objects.get(id=projectpost).customer_id
    #     else:
    #         user2 = user
    # else:
    #     user2=AiUser.objects.get(uid=uid).id
    # serializer = ThreadSerializer(data={'first_person':user1,'second_person':user2,'bid':bid_id})
    # if serializer.is_valid():
    #     serializer.save()
        # Bid_info = BidPropasalDetails.objects.get(id=bid_id)
        # serializer2 = BidPropasalDetailSerializer(Bid_info,data={'status':2},partial=True)
        # if serializer2.is_valid():
        #     serializer2.save()
    #     return JsonResponse(serializer.data, status=201)
    # else:
    #     return JsonResponse(serializer.errors, status=400)


class BidPostInfoCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        # try:
        print(request.user.id)
        id = request.GET.get('id')
        queryset = BidPropasalDetails.objects.filter(Q(service_and_rates__bid_vendor=request.user.id)).all()
        serializer = BidPropasalDetailSerializer(queryset,many=True)
        return Response(serializer.data)
        # except:
        #     return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request):
        post_id = request.POST.get('post_id')
        post = ProjectboardDetails.objects.get(id=post_id)
        sample_file=request.FILES.get('sample_file')
        serializer = BidPropasalDetailSerializer(data={**request.POST.dict(),'projectpost_id':post_id,'sample_file':sample_file,'vendor_id':request.user.id})#,context={'request':request})
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)


    def put(self,request,bid_proposal_id):
        Bid_info = BidPropasalDetails.objects.get(id=bid_proposal_id)
        # Bid_info = get_object_or_404(queryset, id=bid_proposal_id)
        sample_file=request.FILES.get('sample_file')
        if sample_file:
            serializer = BidPropasalDetailSerializer(Bid_info,data={**request.POST.dict(),'sample_file_upload':sample_file},partial=True)
        else:
            serializer = BidPropasalDetailSerializer(Bid_info,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)


@api_view(['POST',])
@permission_classes([IsAuthenticated])
def post_bid_primary_details(request):############need to include currency conversion###############
    projectpost = request.POST.get('projectpost')
    post = ProjectboardDetails.objects.get(id = projectpost)
    ser = PrimaryBidDetailSerializer(post,context={'request':request})
    return Response(ser.data)



@api_view(['GET',])
@permission_classes([IsAuthenticated])
def get_available_job_details(request):
    present = datetime.now()
    query = ProjectboardDetails.objects.filter(bid_deadline__gte = present)
    ser = AvailablePostJobSerializer(query,many=True,context={'request':request})
    return Response(ser.data)



@api_view(['POST',])
@permission_classes([IsAuthenticated])
def bid_proposal_status(request):
    bid_service_rate_id= request.POST.get('id')
    obj = BidProposalServicesRates.objects.get(id = bid_service_rate_id)
    status = json.loads(request.POST.get('status'))
    if status == 2 or status == 4:
        BidProposalServicesRates.objects.filter(id = bid_service_rate_id).update(status = status)
    elif status == 3:
        if request.user.team: user = request.user.team.owner
        else: user = request.user
        if user != obj.bid_vendor:
            tt,created = HiredEditors.objects.get_or_create(user_id=user.id,hired_editor_id=obj.bid_vendor_id,role_id=2,defaults = {"status":1,"added_by_id":request.user.id})
            if created == False:
                if tt.status == 1:
                    tt.status = 2
                    tt.save()
                return Response({"msg":"Already in HiredEditors List....Redirect to Assign Page"})
            elif created == True:
                print(obj)
                uid = urlsafe_base64_encode(force_bytes(tt.id))
                token = invite_accept_token.make_token(tt)
                link = join(settings.TRANSEDITOR_BASE_URL,settings.EXTERNAL_MEMBER_ACCEPT_URL, uid,token)
                context = {'name':obj.bid_vendor.fullname,'team':user.fullname,'link':link,'job':obj.bidpostjob.source_target_pair_names,
                           'hourly_rate': str(obj.mtpe_hourly_rate) + '(' + obj.currency.currency_code + ')' + ' per ' + obj.mtpe_count_unit.unit,\
                            'unit_rate':str(obj.mtpe_rate) + '(' + obj.currency.currency_code + ')'+ ' per ' + obj.mtpe_count_unit.unit,\
                            'job_id':obj.bidpostjob.postjob_id,'project':obj.bid_proposal.projectpost.proj_name,\
                            'date':obj.bid_proposal.created_at.date().strftime('%d-%m-%Y')}
                print("Mail------>",obj.bid_vendor.email)
                m_forms.external_member_invite_mail_after_bidding(context,obj.bid_vendor.email)
                msg_send(user,obj.bid_vendor)
            BidProposalServicesRates.objects.filter(id = bid_service_rate_id).update(status = status)
            return JsonResponse({"msg":"Invite send...added to your HiredEditors list"})
        else:
            return JsonResponse({"msg":"error"})
    return JsonResponse({"msg":"status updated"})


# @api_view(['GET',])
# @permission_classes([IsAuthenticated])
# def get_available_job_details(request):
#     out=[]
#     present = datetime.now()
#     available_jobs_details = AvailableJobs.objects.select_related('projectpostjob','projectpost')\
#                             .filter(vendor_id = request.user.id).values('projectpost__proj_desc','projectpost__proj_deadline','projectpostjob','projectpost__bid_deadline','projectpost__proj_name',
#                             'projectpost__customer__ai_profile_info__organisation_name','projectpost__id')
#     for i in available_jobs_details:
#         try:
#             subjects=[x.subject_id for x in ProjectPostSubjectField.objects.filter(project_id=i.get('projectpost__id'))]
#         except:
#             subjects=[]
#         apply=True if present.strftime('%Y-%m-%d %H:%M:%S') <= i.get('projectpost__bid_deadline').strftime('%Y-%m-%d %H:%M:%S') else False
#         res={"proj_name":i.get('projectpost__proj_name'),"organisation_name":i.get('projectpost__customer__ai_profile_info__organisation_name'),"job_id":i.get('projectpostjob'),"job_desc":i.get('projectpost__proj_desc'),"project_deadline":i.get('projectpost__proj_deadline'),"bid_deadline":i.get('projectpost__bid_deadline'),"subjects":subjects,"apply":apply}
#         out.append(res)
#     return JsonResponse({'out':out},safe=False)


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


class IncompleteProjectListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SimpleProjectSerializer
    pagination.PageNumberPagination.page_size = 20

    def get_queryset(self):
        queryset=[x for x in Project.objects.filter(ai_user=self.request.user.id).order_by('-id') if x.progress != "completed" ]
        return queryset


# @api_view(['GET',])
# @permission_classes([IsAuthenticated])
# def get_incomplete_projects_list(request):
    # try:
    #     new=[]
    #     project_list=[x for x in Project.objects.filter(ai_user=request.user.id) if x.progress != "completed" ]
    #     out=[]
    #     for j in project_list:
    #         out=[{"project_id":j.id,"project":j.project_name}]
    #         jobs = j.get_jobs
    #         for i in jobs:
    #             rt=[]
    #             jobs=i.source_language.language+"->"+i.target_language.language
    #             res=VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id)).distinct()
    #             rt.append({"job_id":i.id,"job":jobs,"vendors":res.count()})
    #             out.extend(rt)
    #         new.append(out)
    # except:
    #     out="No incomplete projects"
    # return JsonResponse({'project_list':new},safe=False)


@api_view(['GET',])
@permission_classes([IsAuthenticated])
def vendor_applied_jobs_list(request):
    try:
        print(request.user.id)
        queryset = BidPropasalDetails.objects.filter(vendor_id=request.user.id).all()
        serializer = BidPropasalDetailSerializer(queryset,many=True)
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
    count = user.notifications.filter(verb='Message').unread().count()
    notification_details=[]
    notification=[]
    notification.append({'total_count':count})
    # notifications = user.notifications.unread().filter(verb='Message').order_by('data','-timestamp').distinct('data')
    notifications = user.notifications.unread().filter(verb='Message').filter(pk__in=Subquery(
            user.notifications.unread().filter(verb='Message').order_by("data",'-timestamp').distinct("data").values('id'))).order_by("-timestamp")
    for i in notifications:
       count = user.notifications.filter(Q(data=i.data) & Q(verb='Message')).unread().count()
       sender = AiUser.objects.get(id =i.actor_object_id)
       try:profile = sender.professional_identity_info.avatar_url
       except:profile = None
       notification_details.append({'thread_id':i.data.get('thread_id'),'avatar':profile,'sender':sender.fullname,'sender_id':sender.id,'message':i.description,'timestamp':i.timestamp,'count':count})
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
    category = django_filters.CharFilter(field_name='vendor_info__type')
    class Meta:
        model = AiUser
        fields = ('fullname', 'email','year_of_experience','country','location','category',)


class GetVendorListViewNew(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GetVendorListSerializer
    filter_backends = [DjangoFilterBackend ,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = VendorFilterNew
    page_size = settings.REST_FRAMEWORK["PAGE_SIZE"]

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
                    .distinct().exclude(id = user.id).exclude(is_internal_member=True).exclude(is_vendor=False)
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
    job_id = request.POST.get('job_id')
    job_obj = Job.objects.get(id=job_id)
    # print(job_obj.source_language,job_obj.target_language)
    vendor = AiUser.objects.get(id=vendor_id)
    query = TaskAssignInfo.objects.filter(Q(task_ven_accepted = True) & Q(assigned_by = user) & Q(task__assign_to = vendor))
    query_final = query.filter(Q(task__job__source_language = job_obj.source_language) & Q(task__job__target_language = job_obj.target_language))
    rates =[]
    for i in query_final:
        out = [{'currency':i.currency.currency_code,'mtpe_rate':i.mtpe_rate,'mtpe_count_unit':i.mtpe_count_unit_id}]
        rates.append(out)
    return JsonResponse({"Previously Agreed Rates":rates})
