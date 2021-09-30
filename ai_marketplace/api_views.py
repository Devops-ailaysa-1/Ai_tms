from rest_framework import filters,generics
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import render
from ai_auth.models import AiUser
from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.test.client import RequestFactory
from rest_framework import pagination, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view,permission_classes
from datetime import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from ai_workspace.models import Job,Project,ProjectContentType,ProjectSubjectField
from .models import(AvailableVendors,ProjectboardDetails,ProjectPostJobDetails,BidChat,
                    Thread,BidPropasalDetails,AvailableJobs,ChatMessage)
from .serializers import(AvailableVendorSerializer, ProjectPostSerializer,
                        AvailableJobSerializer,BidChatSerializer,BidPropasalDetailSerializer,
                        ThreadSerializer,GetVendorDetailSerializer,VendorServiceSerializer,
                        GetVendorListSerializer,ChatMessageSerializer
                        )
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
from ai_auth.models import PersonalInformation, AiUser, OfficialInformation, Professionalidentity
from ai_auth.serializers import OfficialInformationSerializer,PersonalInformationSerializer,AiUserDetailsSerializer
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
# Create your views here.


@api_view(['POST',])
@permission_classes([IsAuthenticated])
def get_vendor_detail(request):
    out=[]
    job_id=request.POST.get('job_id')
    source_lang_id=request.POST.get('source_lang_id')
    target_lang_id=request.POST.get('target_lang_id')
    if job_id:
        source_lang_id=Job.objects.get(id=job_id).source_language_id
        target_lang_id=Job.objects.get(id=job_id).target_language_id
    uid=request.POST.get('vendor_id')
    try:
        user=AiUser.objects.get(uid=uid)
        user_id = user.id
        lang = VendorLanguagePair.objects.get((Q(source_lang_id=source_lang_id) & Q(target_lang_id=target_lang_id) & Q(user_id=user_id)))
        serializer1= VendorServiceSerializer(lang)
        out.append(serializer1.data)
        serializer = GetVendorDetailSerializer(user)
        out.append(serializer.data)
    except:
        out = "Matching details does not exist"
    return Response({"out":out})



@api_view(['POST',])
@permission_classes([IsAuthenticated])
def assign_available_vendor_to_customer(request):
    uid=request.POST.get('vendor_id')
    bid_id = request.POST.get('bid_id',None)
    print(bid_id)
    if uid:
        vendor_id=AiUser.objects.get(uid=uid).id
    elif bid_id:
        vendor_id=BidPropasalDetails.objects.get(id=bid_id).vendor_id
    customer_id=request.user.id
    serializer=AvailableVendorSerializer(data={"vendor":vendor_id,"customer":customer_id})
    if serializer.is_valid():
        serializer.save()
        if bid_id:
            try:
                Bid_info = BidPropasalDetails.objects.get(id=bid_id)
                serializer2 = BidPropasalDetailSerializer(Bid_info,data={'status':4},partial=True)
                if serializer2.is_valid():
                    serializer2.save()
                else:
                    print(serializer2.errors)
            except:
                print("No bid detail exists")
        return Response(data={"Message":"Vendor Assigned to User Successfully"})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST',])
@permission_classes([IsAuthenticated])
def post_job_primary_details(request):
    project_id=request.POST.get('project_id')
    jobslist=Job.objects.filter(project_id=project_id).values('source_language_id','target_language_id')
    result={}
    tar_lang=[]
    for i in jobslist:
        lang=i.get('target_language_id')
        tar_lang.append(lang)
    jobs=[{"src_lang":i.get('source_language_id'),"tar_lang":tar_lang}]
    result["jobs"]=jobs
    subjectfield = ProjectSubjectField.objects.filter(project_id=project_id).all()
    subjects=[]
    for i in subjectfield:
        subjects.append({'subject':i.subject_id})
    result["subjects"]=subjects
    content_type = ProjectContentType.objects.filter(project_id=project_id).all()
    contents=[]
    for j in content_type:
        contents.append({'content_type':j.content_type_id})
    result["contents"]=contents
    # proj_detail = Project.objects.select_related('proj_subject','proj_content_type').filter(id=1)\
    #               .values('proj_content_type__content_type_id', 'proj_subject__subject_id','project_name')
    # proj_detail={"project_name":proj_detail[0].get('project_name'),"subject":proj_detail[0].get('proj_subject__subject_id'),"content_type":proj_detail[0].get('proj_content_type__content_type_id')}
    # result["projectpost_detail"]=proj_detail
    return JsonResponse({"res":result},safe=False)


class ProjectPostInfoCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,projectpost_id):
        try:
            print(request.user.id)
            queryset = ProjectboardDetails.objects.filter(Q(id=projectpost_id) & Q(customer_id = request.user.id)).all()
            print(queryset)
            serializer = ProjectPostSerializer(queryset,many=True)
            return Response(serializer.data)
        except:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request,project_id):
        print(project_id)
        customer = request.user.id
        print({**request.POST.dict(),'project_id':project_id})
        serializer = ProjectPostSerializer(data={**request.POST.dict(),'project_id':project_id,'customer_id':customer})#,context={'request':request})
        print(serializer.is_valid())
        print(serializer.errors)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

    def put(self,request,projectpost_id):
        projectpost_info = ProjectboardDetails.objects.get(id=projectpost_id)
        serializer = ProjectPostSerializer(projectpost_info,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)



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
            project_id=i.id
            bids = BidPropasalDetails.objects.filter(projectpost_id = i.id).count()
            out=[{'jobs':jobs,'project':project,'bids':bids,'project_id':project_id}]
            new.extend(out)
        return JsonResponse({'out':new},safe=False)
    except:
        return Response(status=status.HTTP_204_NO_CONTENT)



@api_view(['POST',])
@permission_classes([IsAuthenticated])
def shortlisted_vendor_list_send_email(request):
    projectpost_id=request.POST.get('projectpost_id')
    new=[]
    userslist=[]
    jobs=ProjectPostJobDetails.objects.filter(projectpost_id=projectpost_id).all()
    project_deadline=ProjectboardDetails.objects.get(id=projectpost_id).proj_deadline
    bid_deadline=ProjectboardDetails.objects.get(id=projectpost_id).bid_deadline
    for i in jobs:
        res=VendorLanguagePair.objects.filter(Q(source_lang_id=i.src_lang_id) & Q(target_lang_id=i.tar_lang_id)).all()
        if res:
            for j in res:
                out=[]
                print(i.id)
                print(j.user_id)
                serializer=AvailableJobSerializer(data={'projectpostjob':i.id,'vendor':j.user_id,'projectpost':projectpost_id})
                if serializer.is_valid():
                    serializer.save()
                print(serializer.errors)
                src_lang=Languages.objects.get(id=i.src_lang_id).language
                tar_lang=Languages.objects.get(id=i.tar_lang_id).language
                user_id=VendorLanguagePair.objects.get(id=j.id).user_id
                out=[{"lang":[{"src_lang":src_lang,"tar_lang":tar_lang}],"user_id":user_id}]
                if user_id not in userslist:
                    new.extend(out)
                    userslist.append(user_id)
                else:
                    for k in new:
                        if k.get("user_id")==user_id:
                            k.get("lang").extend(out[0].get("lang"))
    print(new)
    if new:
        for data in new:
            user_id=data.get('user_id')
            user=AiUser.objects.get(id=user_id).fullname
            email=AiUser.objects.get(id=user_id).email
            print(email)
            template = 'email.html'
            context = {'user': user, 'lang':data.get('lang'),'proj_deadline':project_deadline,'bid_deadline':bid_deadline}
            content = render_to_string(template, context)
            subject='Regarding Available jobs'
            msg = EmailMessage(subject, content, settings.DEFAULT_FROM_EMAIL, to=[email,])
            msg.content_subtype = 'html'
            msg.send()
        return JsonResponse({"message":"Email Successfully Sent"},safe=False)
    else:
        return JsonResponse({"message":"No Match Found"},safe=False)




@api_view(['POST',])
@permission_classes([IsAuthenticated])
def addingthread(request):
    user1=request.user.id
    bid_id=request.POST.get("bid_id")
    user=BidPropasalDetails.objects.get(id=bid_id).vendor_id
    if user == user1:
        projectpostjob = BidPropasalDetails.objects.get(id=bid_id).projectpostjob_id
        projectpost = ProjectPostJobDetails.objects.get(id=projectpostjob).projectpost_id
        user2 = ProjectboardDetails.objects.get(id=projectpost).customer_id
    else:
        user2 = user
    serializer = ThreadSerializer(data={'first_person':user1,'second_person':user2,'bid':bid_id})
    if serializer.is_valid():
        serializer.save()
        Bid_info = BidPropasalDetails.objects.get(id=bid_id)
        serializer2 = BidPropasalDetailSerializer(Bid_info,data={'status':2},partial=True)
        if serializer2.is_valid():
            serializer2.save()
        return JsonResponse(serializer.data, status=201)
    else:
        return JsonResponse(serializer.errors, status=400)


class BidPostInfoCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,id):
        try:
            print(request.user.id)
            queryset = BidPropasalDetails.objects.filter(Q(projectpostjob_id=id)&Q(vendor_id=request.user.id)).all()
            serializer = BidPropasalDetailSerializer(queryset,many=True)
            return Response(serializer.data)
        except:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request,id):
        print(id)
        projectpost_id = ProjectPostJobDetails.objects.get(id=id).projectpost_id
        sample_file=request.FILES.get('sample_file')
        # print({**request.POST.dict(),'projectpostjob_id':id,'vendor_id':request.user.id,'sample_file_upload':sample_file})
        serializer = BidPropasalDetailSerializer(data={**request.POST.dict(),'projectpostjob_id':id,'vendor_id':request.user.id,'projectpost_id':projectpost_id,'sample_file_upload':sample_file,'status':1})#,context={'request':request})
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
def post_bid_primary_details(request):
    projectpostjob = request.POST.get('projectpostjob')
    vendor_id = request.user.id
    print(vendor_id)
    source_lang_id=ProjectPostJobDetails.objects.get(id=projectpostjob).src_lang_id
    target_lang_id=ProjectPostJobDetails.objects.get(id=projectpostjob).tar_lang_id
    service_details = VendorLanguagePair.objects.filter((Q(source_lang_id=source_lang_id) & Q(target_lang_id=target_lang_id) & Q(user_id=vendor_id)))\
                      .select_related('service').values('service__mtpe_rate','service__mtpe_hourly_rate','service__mtpe_count_unit')
    if service_details:
        out=[{"mtpe_rate":service_details[0].get('service__mtpe_rate'),"mtpe_hourly_rate":service_details[0].get('service__mtpe_hourly_rate'),"mtpe_count_unit":service_details[0].get('service__mtpe_count_unit')}]
    else:
        out = "No service details exists"
    return JsonResponse({'out':out},safe=False)



@api_view(['GET',])
@permission_classes([IsAuthenticated])
def get_available_job_details(request):
    # available_jobs = AvailableJobs.objects.filter(vendor_id = request.user.id).all()
    out=[]
    available_jobs_details = AvailableJobs.objects.select_related('projectpostjob','projectpost')\
                            .filter(vendor_id = request.user.id).values('projectpost__proj_desc','projectpost__proj_deadline','projectpostjob')
    for i in available_jobs_details:
        res={"job_id":i.get('projectpostjob'),"job_desc":i.get('projectpost__proj_desc'),"deadline":i.get('projectpost__proj_deadline')}
        out.append(res)
    return JsonResponse({'out':out},safe=False)



class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass


class VendorFilter(django_filters.FilterSet):
    content_type = NumberInFilter(field_name="vendor_contentype__contenttype_id",lookup_expr='in')
    subject = NumberInFilter(field_name='vendor_subject__subject_id',lookup_expr='in')
    year_of_experience =NumberInFilter(field_name='vendor_info__year_of_experience')
    fullname =django_filters.CharFilter(field_name='fullname',lookup_expr='icontains')
    class Meta:
        model = AiUser
        fields = ('fullname', 'email', 'content_type','subject','year_of_experience',)


class GetVendorListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GetVendorListSerializer
    filter_backends = [DjangoFilterBackend ,filters.SearchFilter,filters.OrderingFilter]
    filterset_class = VendorFilter
    ordering_fields = ('vendor_contentype__contenttype_id', 'vendor_subject__subject_id')
    page_size = settings.REST_FRAMEWORK["PAGE_SIZE"]


    def get_queryset(self):
        job_id= self.request.query_params.get('job_id')
        min_price =self.request.query_params.get('min_price')
        max_price =self.request.query_params.get('max_price')
        count_unit = self.request.query_params.get('count_unit')
        source_lang_id=self.request.query_params.get('source_lang_id')
        target_lang_id=self.request.query_params.get('target_lang_id')
        contenttype_id = self.request.query_params.get('content_type')
        subject=self.request.query_params.get('subject')
        if job_id:
            source_lang_id=Job.objects.get(id=job_id).source_language_id
            target_lang_id=Job.objects.get(id=job_id).target_language_id
        queryset = queryset_all = AiUser.objects.select_related('ai_profile_info','vendor_info','professional_identity_info')\
                    .filter(Q(vendor_lang_pair__source_lang=source_lang_id) & Q(vendor_lang_pair__target_lang=target_lang_id) & Q(vendor_lang_pair__deleted_at=None)).distinct()
        if max_price and min_price and count_unit:
            ids=[]
            for i in queryset.values('vendor_lang_pair__id'):
                ids.append(i.get('vendor_lang_pair__id'))
            queryset= queryset_all = queryset.filter(Q(vendor_lang_pair__service__mtpe_count_unit_id=count_unit)&Q(vendor_lang_pair__service__mtpe_rate__range=(min_price,max_price))&Q(vendor_lang_pair__service__lang_pair_id__in=ids)).distinct()
        if  contenttype_id:
            contentlist = contenttype_id.split(',')
            queryset = queryset.filter(Q(vendor_contentype__contenttype_id__in=contentlist)).annotate(number_of_match=Count('vendor_contentype__contenttype_id',0)).order_by('-number_of_match').distinct()
        if subject:
            subjectlist=subject.split(',')
            queryset = queryset.filter(Q(vendor_subject__subject_id__in = subjectlist)).annotate(number_of_match=Count('vendor_subject__subject_id',0)).order_by('-number_of_match').distinct()
        return queryset



class ChatMessageListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,thread_id):
        try:
            queryset = ChatMessage.objects.filter(thread_id = thread_id).all()
            print(queryset)
            serializer = ChatMessageSerializer(queryset,many=True)
            return Response(serializer.data)
        except:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request,thread_id):
        serializer = ChatMessageSerializer(data={**request.POST.dict(),'thread':thread_id},context={'request':request})
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def put(self,request,chatmessage_id):
        user=request.user.id
        chat_info = ChatMessage.objects.get(id=chatmessage_id)
        serializer = ChatMessageSerializer(chat_info,data={**request.POST.dict()},context={'request':request},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)


@api_view(['GET',])
@permission_classes([IsAuthenticated])
def get_incomplete_projects_list(request):
    try:
        project_list=[x for x in Project.objects.filter(ai_user=request.user.id) if x.progress != "completed" ]
        out=[]
        for j in project_list:
            jobs = j.get_jobs
            for i in jobs:
                rt=[]
                jobs=i.source_language.language+"->"+i.target_language.language
                res=VendorLanguagePair.objects.filter(Q(source_lang_id=i.source_language_id) & Q(target_lang_id=i.target_language_id)).distinct()
                rt.append({"project":j.project_name,"job_id":i.id,"job":jobs,"vendors":res.count()})
                out.extend(rt)
    except:
        out="No incomplete projects"
    return JsonResponse({'project_list':out},safe=False)
