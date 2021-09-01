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
from ai_workspace.models import Job,Project,ProjectContentType,ProjectSubjectField
from .models import(AvailableVendors,ProjectboardDetails,ProjectPostJobDetails,BidChat,Thread,BidPropasalDetails,AvailableJobs)
from .serializers import(AvailableVendorSerializer, ProjectPostSerializer,
                        AvailableJobSerializer,BidChatSerializer,BidPropasalDetailSerializer,
                        ThreadSerializer,GetVendorDetailSerializer,VendorServiceSerializer)
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
from ai_auth.serializers import OfficialInformationSerializer,PersonalInformationSerializer
import json,requests
from django.http import JsonResponse
from django.core.mail import EmailMessage
from django.template import Context
from django.template.loader import get_template
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
# Create your views here.

@permission_classes((IsAuthenticated, ))
@api_view(['POST',])
def get_vendor_list(request):
    job_id=request.POST.get('job_id')
    source_lang_id=request.POST.get('source_lang_id')
    target_lang_id=request.POST.get('target_lang_id')
    if job_id:
        source_lang_id=Job.objects.get(id=job_id).source_language_id
        target_lang_id=Job.objects.get(id=job_id).target_language_id
    vendor_list = AiUser.objects.select_related('personal_info','vendor_info','vendor_lang_pair','professional_identity_info')\
                  .filter(Q(vendor_lang_pair__source_lang=source_lang_id) & Q(vendor_lang_pair__target_lang=target_lang_id) & Q(vendor_lang_pair__deleted_at=None))\
                  .values('fullname', 'personal_info__country','vendor_info__type_id','uid','vendor_info__currency','vendor_lang_pair__service__mtpe_rate','professional_identity_info')
    out=[]
    for i in vendor_list:
        pk= i.get('professional_identity_info')
        image = Professionalidentity.objects.get(id = pk).avatar if pk else None
        url = image.url if image else None
        final_dict={"Name":i.get('fullname'),"Country":i.get('personal_info__country'),"LegalCatagories":i.get('vendor_info__type_id'),"Vendor_id":i.get('uid'),
                    "currency":i.get('vendor_info__currency'),"mtpe_rate":i.get("vendor_lang_pair__service__mtpe_rate"),"Avatar":url}
        out.append(final_dict)
    return JsonResponse({'out':out},safe=False)


@permission_classes((IsAuthenticated, ))
@api_view(['POST',])
def get_vendor_detail(request):
    out=[]
    job_id=request.POST.get('job_id')
    source_lang_id=request.POST.get('source_lang_id')
    target_lang_id=request.POST.get('target_lang_id')
    if job_id:
        source_lang_id=Job.objects.get(id=job_id).source_language_id
        target_lang_id=Job.objects.get(id=job_id).target_language_id
    uid=request.POST.get('vendor_id')
    user=AiUser.objects.get(uid=uid)
    user_id = user.id
    lang = VendorLanguagePair.objects.get((Q(source_lang_id=source_lang_id) & Q(target_lang_id=target_lang_id) & Q(user_id=user_id)))
    serializer1= VendorServiceSerializer(lang)
    out.append(serializer1.data)
    serializer = GetVendorDetailSerializer(user)
    out.append(serializer.data)
    return Response({"out":out})


@permission_classes((IsAuthenticated, ))
@api_view(['POST',])
def assign_available_vendor_to_customer(request):
    uid=request.POST.get('vendor_id')
    vendor_id=AiUser.objects.get(uid=uid).id
    print(vendor_id)
    customer_id=request.user.id
    serializer=AvailableVendorSerializer(data={"vendor":vendor_id,"customer":customer_id})
    if serializer.is_valid():
        serializer.save()
        return Response(data={"Message":"Vendor Assigned to User Successfully"})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@permission_classes((IsAuthenticated, ))
@api_view(['POST',])
def post_job_primary_details(request):
    project_id=request.POST.get('project_id')
    jobslist=Job.objects.filter(project_id=project_id).values('source_language_id','target_language_id')
    out=[]
    result={}
    for i in jobslist:
        jobs=[{"src_lang":i.get('source_language_id'),"tar_lang":i.get('target_language_id')}]
        out.extend(jobs)
    result["projectpost_jobs"]=out
    proj_detail = Project.objects.select_related('proj_subject','proj_content_type').filter(id=1)\
                  .values('proj_content_type__content_type_id', 'proj_subject__subject_id','project_name')
    proj_detail={"project_name":proj_detail[0].get('project_name'),"subject":proj_detail[0].get('proj_subject__subject_id'),"content_type":proj_detail[0].get('proj_content_type__content_type_id')}
    result["projectpost_detail"]=proj_detail
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
        print(id)
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


@permission_classes((IsAuthenticated, ))
@api_view(['GET',])
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


@permission_classes((IsAuthenticated, ))
@api_view(['POST',])
def shortlisted_vendor_list_send_email(request):
    projectpost_id=request.POST.get('projectpost_id')
    new=[]
    userslist=[]
    jobs=ProjectPostJobDetails.objects.filter(projectpost_id=projectpost_id).all()
    project_deadline=ProjectboardDetails.objects.get(id=projectpost_id).proj_deadline
    bid_deadline=ProjectboardDetails.objects.get(id=projectpost_id).bid_deadline
    for i in jobs:
        res=VendorLanguagePair.objects.filter(Q(source_lang_id=i.src_lang_id) & Q(target_lang_id=i.tar_lang_id)).all()
        for j in res:
            out=[]
            print(i.id)
            print(j.user_id)
            serializer=AvailableJobSerializer(data={'projectpostjob':i.id,'vendor':j.user_id})
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



@permission_classes((IsAuthenticated, ))
@api_view(['POST',])
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
        return JsonResponse(serializer.data, status=201)
    else:
        return JsonResponse(serializer.errors, status=400)


class BidPostInfoCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request,id):
        try:
            print(request.user.id)
            queryset = BidPropasalDetails.objects.filter(projectpostjob_id=id)
            serializer = BidPropasalDetailSerializer(queryset,many=True)
            return Response(serializer.data)
        except:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request,id):
        print(id)
        projectpost_id = ProjectPostJobDetails.objects.get(id=id).projectpost_id
        sample_file=request.FILES.get('sample_file')
        print({**request.POST.dict(),'projectpostjob_id':id,'vendor_id':request.user.id,'sample_file_upload':sample_file})
        serializer = BidPropasalDetailSerializer(data={**request.POST.dict(),'projectpostjob_id':id,'vendor_id':request.user.id,'projectpost_id':projectpost_id,'sample_file_upload':sample_file})#,context={'request':request})
        print(serializer.is_valid())
        print(serializer.errors)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

    def put(self,request,bid_proposal_id):
        Bid_info = BidPropasalDetails.objects.get(id=bid_proposal_id)
        sample_file=request.FILES.get('sample_file')
        if sample_file:
            serializer = BidPropasalDetailSerializer(Bid_info,data={**request.POST.dict(),'sample_file_upload':sample_file},partial=True)
        else:
            serializer = BidPropasalDetailSerializer(Bid_info,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)


@permission_classes((IsAuthenticated, ))
@api_view(['POST',])
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
