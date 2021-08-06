from ai_auth.models import AiUser
from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.test.client import RequestFactory
from rest_framework import pagination, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import IntegrityError
from ai_workspace.models import Job,Project,ProjectContentType,ProjectSubjectField

from .models import (VendorBankDetails, VendorLanguagePair, VendorServiceInfo,
                     VendorServiceTypes, VendorsInfo, VendorSubjectFields,VendorContentTypes,
                     VendorMtpeEngines, AssignedVendors,ProjectboardDetails,ProjectPostJobDetails)
from .serializers import (LanguagePairSerializer, ServiceExpertiseSerializer,
                          VendorBankDetailSerializer,
                          VendorLanguagePairSerializer,AssignedVendorSerializer,
                          VendorServiceInfoSerializer, VendorsInfoSerializer,
                          ProjectPostSerializer)
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



def integrity_error(func):
    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IntegrityError:
            return Response({'message': "Integrity error"}, 409)
    return decorator

class VendorsInfoCreateView(APIView):

    def get(self, request):
        try:
            queryset = VendorsInfo.objects.get(user_id=request.user.id)
            serializer = VendorsInfoSerializer(queryset)
            return Response(serializer.data)
        except:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request):
        cv_file=request.FILES.get('cv_file')
        user_id = request.user.id
        # data = request.POST.dict()
        print("cv_file------->",cv_file)
        serializer = VendorsInfoSerializer(data={**request.POST.dict(),'cv_file':cv_file})
        if serializer.is_valid():
            serializer.save(user_id = user_id)
            return Response(serializer.data)
        print("errors", serializer.errors)

    def put(self,request):
        user_id=request.user.id
        print("cv_file---->",request.FILES.get('cv_file'))
        cv_file=request.FILES.get('cv_file')
        # data = request.POST.dict()
        vendor_info = VendorsInfo.objects.get(user_id=request.user.id)
        if cv_file:
            serializer = VendorsInfoSerializer(vendor_info,data={**request.POST.dict(),'cv_file':cv_file},partial=True)
        else:
            serializer = VendorsInfoSerializer(vendor_info,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save_update()
            return Response(serializer.data)


class VendorServiceListCreate(viewsets.ViewSet, PageNumberPagination):
    # permission_classes =[IsAuthenticated]
    # page_size = settings.REST_FRAMEWORK["PAGE_SIZE"]
    # def get_custom_page_size(self, request, view):
    #     try:
    #         self.page_size = self.request.query_params.get('limit',10)
    #         print("limit--->",self.request.query_params.get('limit'))
    #     except (ValueError, TypeError):
    #         pass
    #     return super().get_page_size(request)
    # def paginate_queryset(self, queryset, request, view=None):
    #     self.page_size = self.get_custom_page_size(request, view)
    #     return super().paginate_queryset(queryset, request, view)
    # def list(self,request):
    #     queryset = self.get_queryset()
    #     pagin_tc = self.paginate_queryset( queryset, request , view=self )
    #     serializer = VendorLanguagePairSerializer(pagin_tc, many=True, context={'request': request})
    #     response =self.get_paginated_response(serializer.data)
    #     return  Response(response.data)
    # def get_queryset(self):
    #     search_word =  self.request.query_params.get('search_word',None)
    #     print(search_word)
    #     queryset=VendorLanguagePair.objects.filter(user_id=self.request.user.id).all()
    #     if search_word:
    #         if search_word.isalpha()==True:
    #             lang_id=Languages.objects.get(language__contains=search_word).id
    #             print(lang_id)
    #             queryset = queryset.filter(
    #                         Q(source_lang=lang_id) | Q(target_lang=lang_id)
    #                     )
    #         else:
    #             queryset = queryset.filter(
    #                         Q(id=search_word))
    #             print(queryset)
    #     return queryset
    def list(self,request):
        queryset = self.get_queryset()
        serializer = VendorLanguagePairSerializer(queryset,many=True)
        return Response(serializer.data)
    def get_queryset(self):
        queryset=VendorLanguagePair.objects.filter(user_id=self.request.user.id).all()
        return queryset
    @integrity_error
    def create(self,request):
        user_id = request.user.id
        data={**request.POST.dict()}
        # data = request.data
        serializer = VendorLanguagePairSerializer(data={**request.POST.dict()},context={'request':request})
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save(user_id=user_id)
            #return Response(data={"Message":"VendorServiceInfo Created"}, status=status.HTTP_201_CREATED)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def update(self,request,pk):
        queryset = VendorLanguagePair.objects.all()
        vendor = get_object_or_404(queryset, pk=pk)
        ser=VendorLanguagePairSerializer(vendor,data={**request.POST.dict()},partial=True)
        if ser.is_valid():
            ser.save()
            # ser.save(user_id=request.user.id)
            return Response(ser.data)
    def delete(self,request,pk):
        queryset = VendorLanguagePair.objects.all()
        vendor = get_object_or_404(queryset, pk=pk)
        vendor.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class VendorExpertiseListCreate(viewsets.ViewSet):
    def list(self,request):
        queryset = self.get_queryset()
        serializer = ServiceExpertiseSerializer(queryset,many=True)
        return Response(serializer.data)
    def get_queryset(self):
        queryset=AiUser.objects.filter(id=self.request.user.id).all()
        return queryset
    def create(self,request):
        id = request.user.id
        # data = request.data
        serializer = ServiceExpertiseSerializer(data={**request.POST.dict()})
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save(id=id)
            return Response(serializer.data)
            # return Response(data={"Message":"VendorExpertiseInfo Created"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def update(self,request,pk=None):
        queryset = AiUser.objects.all()
        User = get_object_or_404(queryset, pk=request.user.id)
        ser= ServiceExpertiseSerializer(User,data={**request.POST.dict()},partial=True)
        if ser.is_valid():
            ser.save()
            # ser.update(vendor,validated_data=request.data)
            return Response(ser.data)
        else:
            return Response(ser.errors)


class VendorsBankInfoCreateView(APIView):

    def get(self, request):
        try:
            queryset = VendorBankDetails.objects.get(user_id=request.user.id)
            serializer = VendorBankDetailSerializer(queryset)
            return Response(serializer.data)
        except:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request):
        user_id = request.user.id
        data = request.POST.dict()
        serializer = VendorBankDetailSerializer(data=data)#,context={'request':request})
        if serializer.is_valid():
            serializer.save(user_id=user_id)
            return Response(serializer.data)

    def put(self,request):
        user_id=request.user.id
        data = request.POST.dict()
        vendor_bank_info = VendorBankDetails.objects.get(user_id=request.user.id)
        serializer = VendorBankDetailSerializer(vendor_bank_info,data=data,partial=True)
        if serializer.is_valid():
            serializer.save_update()
            return Response(serializer.data)



class VendorLangPairCreate(viewsets.ViewSet):

    def list(self,request):
        queryset = self.get_queryset()
        serializer=LanguagePairSerializer(queryset,many=True)
        return Response(serializer.data)

    def get_queryset(self):
        queryset=VendorLanguagePair.objects.filter(user_id=self.request.user.id).all()
        return queryset

    def create(self,request):
        id = request.user.id
        data = request.data
        serializer = LanguagePairSerializer(data=data)
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save(user_id=id)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
         queryset = VendorLanguagePair.objects.all()
         vendor = get_object_or_404(queryset, pk=pk)
         vendor.delete()
         return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, pk):
        return


class VendorServiceInfoView(viewsets.ModelViewSet):
    queryset = VendorServiceInfo.objects.all()
    serializer_class = VendorServiceInfoSerializer


@api_view(['GET','POST',])
def SpellCheckerApiCheck(request):
    doc_id= request.POST.get("doc_id")
    result=requests.get(f"http://157.245.99.128:8086/workspace/getLangName/{doc_id}/")
    content=result.json()
    targetLanguage=content.get("target_lang")
    print("TARGET LANGUAGE--->", targetLanguage)
    target_lang_id=Languages.objects.get(language=targetLanguage).id
    print(target_lang_id)
    try:
        spellchecker_id=SpellcheckerLanguages.objects.get(language_id=target_lang_id).spellchecker.id
        print(spellchecker_id)
        data=1
    except:
        data=0
    return JsonResponse({"out":data}, safe = False)

@api_view(['GET',])
def vendor_legal_categories_list(request):
    out=[]
    for i in VendorLegalCategories.objects.all():
        out.append({"label":i.name,"value":i.id})
    return JsonResponse({"out":out},safe = False)

@api_view(['GET',])
def cat_softwares_list(request):
    out=[]
    for i in CATSoftwares.objects.all():
        out.append({"label":i.name,"value":i.id})
    return JsonResponse({"out":out},safe = False)

@api_view(['GET',])
def vendor_membership_list(request):
    out=[]
    for i in VendorMemberships.objects.all():
        out.append({"label":i.membership,"value":i.id})
    return JsonResponse({"out":out},safe = False)

@api_view(['GET',])
def vendor_mtpe_engines_list(request):
    out=[]
    for i in MtpeEngines.objects.all():
        out.append({"label":i.name,"value":i.id})
    return JsonResponse({"out":out},safe = False)

@api_view(['GET',])
def vendor_subject_matter_list(request):
    out=[]
    for i in SubjectFields.objects.all():
        out.append({"label":i.name,"value":i.id})
    return JsonResponse({"out":out},safe = False)



@api_view(['POST',])
def get_vendor_list(request):
    source_lang_id=request.POST.get('source_lang_id')
    target_lang_id=request.POST.get('target_lang_id')
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
    source_lang_id=request.POST.get('source_lang_id')
    target_lang_id=request.POST.get('target_lang_id')
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
def assign_vendor_to_customer(request):
    uid=request.POST.get('vendor_id')
    vendor_id=AiUser.objects.get(uid=uid).id
    print(vendor_id)
    customer_id=request.user.id
    serializer=AssignedVendorSerializer(data={"vendor":vendor_id,"customer":customer_id})
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
    subject_field=ProjectSubjectField.objects.get(project_id=project_id).subject_id
    result["subject_field"]=subject_field
    content_type=ProjectContentType.objects.get(project_id=project_id).content_type_id
    result["content_type"]=content_type
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
    jobs=ProjectPostJobDetails.objects.filter(projectpost_id=projectpost_id).all()
    out=[]
    for i in jobs:
        job_id=i.id
        source_lang_id=i.src_lang_id
        target_lang_id=i.tar_lang_id
        res=VendorLanguagePair.objects.filter(Q(source_lang_id=source_lang_id) & Q(target_lang_id=target_lang_id)).all()
        for j in res:
            email=AiUser.objects.get(id=j.user_id).email
            print(email)
            user=AiUser.objects.get(id=j.user_id).fullname
            src_lang=Languages.objects.get(id=source_lang_id).language
            tar_lang=Languages.objects.get(id=target_lang_id).language
            out=[{"src_lang":src_lang,"tar_lang":tar_lang,"job_id":job_id}]
            new.extend(out)
            template = 'email.html'
            # context = Context({'user': user, 'other_info': out})
            context = {'user': user, 'other_info': out}
            content = render_to_string(html_template, { 'context': context, })
            # content = template.render(context)
            subject='Regarding Available jobs'
            if not email:
                raise BadHeaderError('No email address given for {0}'.format(user))
            msg = EmailMessage(subject, content, settings.DEFAULT_FROM_EMAIL, to=[email,])
            msg.content_subtype = 'html'
            msg.send()
    return JsonResponse({"message":"Email Successfully Sent"},safe=False)
# @api_view(['POST',])
# def get_vendor_detail_admin(request):
#     source_lang_id=request.POST.get('source_lang_id')
#     target_lang_id=request.POST.get('target_lang_id')
#     uid=request.POST.get('vendor_id')
#     user_id=AiUser.objects.get(uid=uid).id
#     result={}
#     lang=VendorLanguagePair.objects.filter((Q(source_lang_id=source_lang_id) & Q(target_lang_id=target_lang_id) & Q(user_id=user_id)) | (Q(source_lang_id=target_lang_id) & Q(target_lang_id=source_lang_id) & Q(user_id=user_id))).all()
#     res1 = AiUser.objects.get(uid=uid)
#     res2 = PersonalInformation.objects.get(user_id=res1.id)
#     res3 = OfficialInformation.objects.get(user_id=res1.id)
#     res4 = VendorsInfo.objects.get(user_id=res1.id)
#     result["PrimaryInfo"]={"Name":res1.fullname,"Email":res1.email,"Address":res2.address,"CompanyName":res3.company_name,"LegalCatagories":res4.type_id,"currency":res4.currency_id,"proz_link":res4.proz_link,"native_lang":res4.native_lang_id,"YearOfExperience":res4.year_of_experience}
#     new_serv=[]
#     new_serv_type=[]
#     for i in lang:
#         try:
#            res5 = VendorServiceInfo.objects.get(lang_pair_id=i.id)
#            out=[{"source_lang_id":i.source_lang_id,"target_lang_id":i.target_lang_id,"MtpeUnitRate":res5.mtpe_rate,"MtpeHourlyRate":res5.mtpe_hourly_rate,"CountUnit":res5.mtpe_count_unit_id}]
#            new_serv.extend(out)
#            result["service"]=new_serv
#         except:
#            result["service"]=[]
#
#         try:
#            res6=VendorServiceTypes.objects.filter(lang_pair_id=i.id).all()
#            if res6:
#                new1=[{"source_lang_id":i.source_lang_id,"target_lang_id":i.target_lang_id}]
#                for j in res6:
#                    out3=[{"serviceType":j.services_id,"hourlyrate":j.hourly_rate,"Unitrate":j.unit_rate,"unit_type":j.unit_type_id,"minuterate":j.minute_rate}]
#                    new1.extend(out3)
#            new_serv_type.append(new1)
#            result["service-types"]=new_serv_type
#         except:
#            result["service-types"]=[]
#     try:
#         res7=VendorSubjectFields.objects.filter(user_id=user_id).all()
#         sub=[]
#         for k in res7:
#             out4=[{"subject":k.subject_id}]
#             sub.extend(out4)
#         result["Subject-Matter"]=sub
#     except:
#         result["Subject-Matter"]=[]
#
#     try:
#        res8=VendorContentTypes.objects.filter(user_id=user_id).all()
#        content=[]
#        for l in res8:
#            out5=[{"contenttype":l.contenttype_id}]
#            content.extend(out5)
#        result["Content-Type"]=content
#     except:
#        result["Content-Type"]=[]
#
#     try:
#         res9=VendorMtpeEngines.objects.filter(user_id=user_id).all()
#         mtpe=[]
#         for m in res9:
#             out6=[{"mtpe-engines":m.mtpe_engines_id}]
#             mtpe.extend(out6)
#         result["MT-Engines"]=mtpe
#     except:
#         result["MT-Engines"]=[]
#     return JsonResponse({"out":result},safe=False)
