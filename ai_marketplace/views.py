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
from ai_workspace.models import Job,Project,ProjectContentType,ProjectSubjectField
from .models import(AvailableVendors,ProjectboardDetails,ProjectPostJobDetails,BidChat)
from .serializers import(AvailableVendorSerializer, ProjectPostSerializer,AvailableBidSerializer,BidChatSerializer)
from ai_vendor.models import (VendorBankDetails, VendorLanguagePair, VendorServiceInfo,
                     VendorServiceTypes, VendorsInfo, VendorSubjectFields,VendorContentTypes,
                     VendorMtpeEngines)
from ai_vendor.serializers import (ServiceExpertiseSerializer,
                          VendorBankDetailSerializer,VendorLanguagePairCloneSerializer,
                          VendorLanguagePairSerializer,
                          VendorServiceInfoSerializer, VendorsInfoSerializer)
from ai_staff.models import (Languages,Spellcheckers,SpellcheckerLanguages,
                            VendorLegalCategories, CATSoftwares, VendorMemberships,
                            MtpeEngines, SubjectFields,ServiceTypeunits)
from ai_auth.models import PersonalInformation, AiUser, OfficialInformation, Professionalidentity
import json,requests
from django.http import JsonResponse
from django.core.mail import EmailMessage
from django.template import Context
from django.template.loader import get_template
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
# Create your views here.


@api_view(['POST',])
def get_vendor_list(request):
    job_id=request.POST.get('job_id')
    source_lang_id=Job.objects.get(id=job_id).source_language_id
    target_lang_id=Job.objects.get(id=job_id).target_language_id
    res=VendorLanguagePair.objects.filter(Q(source_lang_id=source_lang_id) & Q(target_lang_id=target_lang_id)).all()
    out=[]
    for i in res:
       final_dict={}
       res1 = AiUser.objects.get(id=i.user_id)
       res2 = PersonalInformation.objects.get(user_id=i.user_id)
       res3 = VendorsInfo.objects.get(user_id=i.user_id)
       final_dict={"Name":res1.fullname,"Country":res2.country_id,"LegalCatagories":res3.type_id,"Vendor_id":res1.uid}
       try:
           res4 = VendorServiceInfo.objects.get(lang_pair_id=i.id)
           a_dict={"MTPE_Unit_Rate":res4.mtpe_rate,"Currency":res3.currency_id}
           final_dict.update(a_dict)
       except:
           a_dict={"MTPE_Unit_Rate":"","Currency":""}
           final_dict.update(a_dict)
       try:
           res5 = Professionalidentity.objects.get(user_id=i.user_id)
           image=res5.avatar
           b_dict={"Avatar":image.url}
           final_dict.update(b_dict)
       except:
           b_dict={"Avatar":""}
           final_dict.update(b_dict)
       out.append(final_dict)
    return JsonResponse({"out":out},safe=False)


@api_view(['POST',])
def get_vendor_detail(request):
    job_id=request.POST.get('job_id')
    source_lang_id=Job.objects.get(id=job_id).source_language_id
    target_lang_id=Job.objects.get(id=job_id).target_language_id
    uid=request.POST.get('vendor_id')
    user_id=AiUser.objects.get(uid=uid).id
    result={}
    lang = VendorLanguagePair.objects.get((Q(source_lang_id=source_lang_id) & Q(target_lang_id=target_lang_id) & Q(user_id=user_id)))
    res1 = AiUser.objects.get(uid=uid)
    res2 = PersonalInformation.objects.get(user_id=res1.id)
    res3 = OfficialInformation.objects.get(user_id=res1.id)
    res4 = VendorsInfo.objects.get(user_id=res1.id)
    result["PrimaryInfo"]={"Name":res1.fullname,"CompanyName":res3.company_name,"LegalCatagories":res4.type_id,"currency":res4.currency_id,"proz_link":res4.proz_link,"native_lang":res4.native_lang_id,"YearOfExperience":res4.year_of_experience}
    new_serv=[]
    try:
        res5 = VendorServiceInfo.objects.get(lang_pair_id=lang.id)
        out=[{"MtpeUnitRate":res5.mtpe_rate,"MtpeHourlyRate":res5.mtpe_hourly_rate,"CountUnit":res5.mtpe_count_unit_id}]
        new_serv.extend(out)
        result["service"]=new_serv
    except:
        result["service"]=[]
    try:
        res7=VendorSubjectFields.objects.filter(user_id=user_id).all()
        sub=[]
        for k in res7:
            out4=[{"subject":k.subject_id}]
            sub.extend(out4)
        result["Subject-Matter"]=sub
    except:
        result["Subject-Matter"]=[]
    try:
        res8=VendorContentTypes.objects.filter(user_id=user_id).all()
        content=[]
        for l in res8:
            out5=[{"contenttype":l.contenttype_id}]
            content.extend(out5)
        result["Content-Type"]=content
    except:
        result["Content-Type"]=[]
    return JsonResponse({"out":result},safe=False)



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

@api_view(['POST',])
def post_job_primary_details(request):
    project_id=request.POST.get('project_id')
    jobslist=Job.objects.filter(project_id = project_id).all()
    out=[]
    result={}
    for i in jobslist:
        jobs=[]
        sl=Job.objects.get(id=i.id).source_language_id
        tl=Job.objects.get(id=i.id).target_language_id
        jobs=[{"src_lang":sl,"tar_lang":tl}]
        out.extend(jobs)
    result["projectpost_jobs"]=out
    try:
        subject_field=ProjectSubjectField.objects.get(project_id=project_id).subject_id
        result["subject_field"]=subject_field
    except:
        result["subject_field"]=None
    try:
        content_type=ProjectContentType.objects.get(project_id=project_id).content_type_id
        result["content_type"]=content_type
    except:
        result["content_type"]=None
    return JsonResponse({"res":result},safe=False)


class ProjectPostInfoCreateView(APIView):

    def get(self, request,id):
        try:
            queryset = ProjectboardDetails.objects.get(id=id)
            serializer = ProjectPostSerializer(queryset)
            return Response(serializer.data)
        except:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request,id):
        print(id)
        # data = request.POST.dict()
        print({**request.POST.dict(),'project_id':id})
        serializer = ProjectPostSerializer(data={**request.POST.dict(),'project_id':id})#,context={'request':request})
        print(serializer.is_valid())
        print(serializer.errors)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

    def put(self,request):
        # data = request.POST.dict()
        job_info = ProjectboardDetails.objects.get(id=id)
        serializer = ProjectPostSerializer(job_info,data={**request.POST.dict(),'project':id},partial=True)
        if serializer.is_valid():
            serializer.save_update()
            return Response(serializer.data)

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
            serializer=AvailableBidSerializer(data={'projectpostjob':i.id,'vendor':j.user_id})
            # print("Valid---->",serializer.is_valid())
            # print("Errors---->",serializer.errors)
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




class BidChatView(APIView):

    def get(self, request, sender=None):
        try:
            projectpostjob_id=self.request.POST.get('projectpost_jobs')
            messages = BidChat.objects.filter(projectpost_jobs_id=projectpostjob_id).all()
            serializer = BidChatSerializer(messages, many=True, context={'request': request})
            return JsonResponse(serializer.data, safe=False)
        except:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request,sender=None):
        print(request.user.id)
        #data = request.POST.dict()
        serializer = BidChatSerializer(data={**request.POST.dict(),'sender':request.user.id})
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)

    def put(self,request,id):
        data = request.POST.dict()
        chat_info = BidChat.objects.get(id=id)
        serializer = BidChatSerializer(chat_info,data=data,partial=True)
        if serializer.is_valid():
            serializer.save_update()
            return Response(serializer.data)
