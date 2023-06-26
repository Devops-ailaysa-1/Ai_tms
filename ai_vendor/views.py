from ai_auth.models import AiUser
from rest_framework.parsers import MultiPartParser, FormParser
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
from ai_auth.vendor_onboard_list import users_list
from ai_workspace.models import Job,Project,ProjectContentType,ProjectSubjectField
from ai_workspace_okapi.models import Document
from django_oso.auth import authorize
from django.http import Http404

from .models import (VendorBankDetails, VendorLanguagePair, VendorServiceInfo,
                     VendorServiceTypes, VendorsInfo, VendorSubjectFields,VendorContentTypes,
                     VendorMtpeEngines, SavedVendor)#, AvailableVendors,ProjectboardDetails,ProjectPostJobDetails)
from .serializers import (ServiceExpertiseSerializer,
                          VendorBankDetailSerializer,VendorLanguagePairCloneSerializer,
                          VendorLanguagePairSerializer,
                          VendorServiceInfoSerializer, VendorsInfoSerializer,
                          SavedVendorSerializer)
from ai_staff.models import (Languages,Spellcheckers,SpellcheckerLanguages,
                            VendorLegalCategories, CATSoftwares, VendorMemberships,
                            MtpeEngines, SubjectFields,ServiceTypeunits, LanguageMetaDetails)
from ai_auth.models import AiUser, Professionalidentity,VendorOnboarding
import json,requests
from django.http import JsonResponse,HttpResponse
# from django.core.mail import EmailMessage
# from django.template import Context
# from django.template.loader import get_template
# from django.template.loader import render_to_string



def integrity_error(func):
    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IntegrityError:
            return Response({'message': "Integrity error"}, 409)
    return decorator

class VendorsInfoCreateView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]
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
        print("cv_file------->",cv_file)
        serializer = VendorsInfoSerializer(data={**request.POST.dict(),'cv_file':cv_file})
        if serializer.is_valid():
            serializer.save(user_id = user_id)
            if cv_file:
                obj = VendorOnboarding.objects.create(name=request.user.fullname,email=request.user.email,cv_file=cv_file,status=1)
                if request.user.email in users_list:
                    request.user.is_vendor = True
                    request.user.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self,request):
        user_id=request.user.id
        cv_file=request.FILES.get('cv_file')
        vendor_info = VendorsInfo.objects.get(user_id=request.user.id)
        if cv_file:
            serializer = VendorsInfoSerializer(vendor_info,data={**request.POST.dict(),'cv_file':cv_file},partial=True)
            try:
                ins = VendorOnboarding.objects.get(email=request.user.email)
                ins.cv_file = cv_file
                ins.save()
            except:pass
        else:
            serializer = VendorsInfoSerializer(vendor_info,data={**request.POST.dict()},partial=True)
        if serializer.is_valid():
            serializer.save_update()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request):
        instance = VendorsInfo.objects.get(user_id=request.user.id)
        if request.POST.get('cv_file',None) != None :
            instance.cv_file=None
        instance.save()
        return Response({"msg":"Deleted Successfully"},status=200)

class VendorServiceListCreate(viewsets.ViewSet, PageNumberPagination):
    permission_classes =[IsAuthenticated]


    def get_queryset(self):
        print(self.request.user)
        queryset=VendorLanguagePair.objects.filter(user_id=self.request.user.id).all()
        return queryset

    def list(self,request):
        queryset = self.get_queryset()
        res ={}
        for i in queryset:
            q2 = VendorLanguagePair.objects.filter(Q(source_lang = i.source_lang)&Q(target_lang=i.target_lang)&Q(user_id=i.user_id))
            tt = str(i.source_lang.language) + '-->' + str(i.target_lang.language)
            ser = VendorLanguagePairSerializer(q2,many=True)
            res[tt]=ser.data
        # serializer = VendorLanguagePairSerializer(queryset,many=True)
        return Response(res)

   # def retrieve(self, request, pk=None):
   #      queryset = VendorLanguagePair.objects.filter(user_id=self.request.user.id).all()
   #      user = get_object_or_404(queryset, pk=pk)
   #      serializer = VendorLanguagePairSerializer(user)
   #      return Response(serializer.data)

    @integrity_error
    def create(self,request):
        user_id = request.user.id
        data={**request.POST.dict()}
        # data = request.data
        serializer = VendorLanguagePairSerializer(data={**request.POST.dict()},context={'request':request})
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            #return Response(data={"Message":"VendorServiceInfo Created"}, status=status.HTTP_201_CREATED)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @integrity_error
    def update(self,request,pk):
        queryset = VendorLanguagePair.objects.filter(user_id=self.request.user.id).all()
        vendor = get_object_or_404(queryset, pk=pk)
        ser=VendorLanguagePairSerializer(vendor,data={**request.POST.dict()},context={'request':request},partial=True)
        print(ser.is_valid())
        print(ser.errors)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        queryset = VendorLanguagePair.objects.filter(user_id=self.request.user.id).all()
        lang_pair = get_object_or_404(queryset, pk=pk)
        lang_pair.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET',])
def clone_lang_pair(request,id):
    existing_lang_pair_id=id
    queryset=VendorLanguagePair.objects.filter(Q(user_id=request.user.id)&Q(id=existing_lang_pair_id)).all()
    if queryset:
        serializer = VendorLanguagePairCloneSerializer(queryset,many=True)
        return Response(serializer.data)
    else:
        return Response({"message":"No such lang_pair_id exists"})


class VendorExpertiseListCreate(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def list(self,request):
        queryset = self.get_queryset()
        serializer = ServiceExpertiseSerializer(queryset,many=True)
        return Response(serializer.data)
    def get_queryset(self):
        print(self.request.user.id)
        queryset=AiUser.objects.filter(id=self.request.user.id).all()
        return queryset

    def create(self,request):
        id = request.user.id
        print(id)
        # data = request.data
        serializer = ServiceExpertiseSerializer(data={**request.POST.dict()},context={'request':request})
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
            # return Response(data={"Message":"VendorExpertiseInfo Created"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self,request,pk):
        queryset = AiUser.objects.filter(id=pk).all()
        User = get_object_or_404(queryset, pk=pk)
        ser= ServiceExpertiseSerializer(User,data={**request.POST.dict()},partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        else:
            return Response(ser.errors)


class VendorsBankInfoCreateView(APIView):
    permission_classes = [IsAuthenticated]
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
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self,request):
        user_id=request.user.id
        data = request.POST.dict()
        vendor_bank_info = VendorBankDetails.objects.get(user_id=request.user.id)
        serializer = VendorBankDetailSerializer(vendor_bank_info,data=data,partial=True)
        if serializer.is_valid():
            serializer.save_update()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET','POST',])
def feature_availability(request):
    from ai_workspace.models import Task
    doc_id= request.POST.get("doc_id")
    task_id = request.POST.get("task_id")
    if doc_id:
        try:
            doc = Document.objects.get(id=doc_id)
        except Document.DoesNotExist:
            raise Http404
        # doc = Document.objects.get(id=doc_id)
        authorize(request, resource=doc, actor=request.user, action="read")
        lang_code = doc.target_language_code
        target_lang_id = Job.objects.get(file_job_set=doc_id).target_language_id
        source_lang_id = Job.objects.get(file_job_set=doc_id).source_language_id
    if task_id:
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            raise Http404
        authorize(request, resource=task, actor=request.user, action="read")
        lang_code = task.job.target_language_code
        target_lang_id = task.job.target_language_id
        source_lang_id = task.job.source_language_id
    print("Targetlang--------->",target_lang_id)
    # CHECK FOR SPELLCHECKER AVAILABILITY
    try:
        spellchecker_id = SpellcheckerLanguages.objects.get(language_id=target_lang_id).spellchecker.id
        data = 1
        # show_ime = False
    except:
        data = 0
        # show_ime = True

    # CHECK FOR IME
    lang_meta = LanguageMetaDetails.objects.filter(language_id=target_lang_id)
    show_ime = True if lang_meta and lang_meta.first().ime == True else False

    #Check for paraphrase and grammercheck
    show_paraphrase_and_grammercheck = True if lang_code == 'en' else False
    # CHECK FOR NER AVAILABILITY
    # show_ner = True if LanguageMetaDetails.objects.get(language_id=source_lang_id).ner != None else False

    return JsonResponse({"out":data, "show_ime":show_ime, "show_paraphrase_and_grammercheck":show_paraphrase_and_grammercheck}, safe = False)

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

class SavedVendorView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self,request):
        glossary_selected = SavedVendor.objects.filter(customer=self.request.user).all()
        serializer = SavedVendorSerializer(glossary_selected, many=True)
        return Response(serializer.data)

    def create(self, request):
        vendor = request.POST.get('vendor')
        user = request.user.team.owner if request.user.team else request.user 
        serializer = SavedVendorSerializer(data={'customer':user.id,'vendor':vendor})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self,request,pk):
        pass
        # data = request.POST.dict()
        # serializer = SavedVendorSerializer(data=data,partial=True)
        # if serializer.is_valid(raise_exception=True):
        #     serializer.save()
        #     return Response(serializer.data)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        user = request.user.team.owner if request.user.team else request.user 
        obj = SavedVendor.objects.get(Q(customer=user) & Q(vendor=pk))
        print("Obj----->",obj)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



import pandas as pd
from ai_staff.models import Currencies ,ServiceTypeunits ,ServiceTypes
from io import BytesIO

import xlsxwriter
def vendor_lang_sheet():
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    
    header = workbook.add_format({
            'bold': True,
            'bg_color': '#ffffcc',
            'color': 'black',
            'align': 'centre',
            'valign': 'top',
            'border': 1,
            'locked': True
        })
    worksheet = workbook.add_worksheet('Vendor Language Pairs')

    worksheet2 = workbook.add_worksheet('Languages')
    languages=list(Languages.objects.all().values_list('language',flat=True))
    worksheet2.write('A1','Languages')
    for i in range(len(languages)):
        a='A{}'.format(i+2)
        worksheet2.write(a,languages[i])

    worksheet2.add_table('A1:A{}'.format(len(languages)+1),{'name': 'Languages','autofilter': False,'columns': [{'header': 'Languages'}]} ) 
 

    worksheet.write('A1', 'Source Language',header)
    worksheet.write('B1', 'Target Language',header)
    worksheet.write('C1', 'Currency',header)
    worksheet.write('D1', 'Service',header)
    worksheet.write('E1', 'Unit Type',header)
    worksheet.write('F1', 'Unit Rate',header) 
    worksheet.write('G1','Hourly Rate',header)
    worksheet.write('H1','Reverse',header)
    currency=['EUR','GBP','INR','USD']
    service=['MTPE (MPE)','Human Translation (HUT)']
    unit_type=['Word','Char']
    boolean=['True','False']
    worksheet.data_validation('A2:A1048576', {'validate': 'list', 'source': '=Languages!$A$2:$A$109'})    
    worksheet.data_validation('B2:B1048576', {'validate': 'list', 'source': '=Languages!$A$2:$A$109'})
    worksheet.data_validation('C2:C1048576', {'validate': 'list', 'source': currency})
    worksheet.data_validation('D2:D1048576', {'validate': 'list', 'source': service})
    worksheet.data_validation('E2:E1048576', {'validate': 'list', 'source': unit_type})
    worksheet.data_validation('F2:F1048576', {'validate': 'integer','criteria': 'between', 'minimum': 0, 'maximum': 999999})
    worksheet.data_validation('G2:G1048576', {'validate': 'integer','criteria': 'between', 'minimum': 0, 'maximum': 999999})
    worksheet.data_validation('H2:H1048576', {'validate': 'list','source':boolean})
    worksheet2.hide()
    workbook.close()
    xlsx_data = output.getvalue()
    return xlsx_data


def check_null_rows(df):
    fields_to_check = ['Source Language','Target Language']
    check_fields_empty = df[fields_to_check].notnull().all(axis=1)
    print("Check---->",check_fields_empty)
    #check_row_empty=df.notnull().all(axis=1)
    return all(check_fields_empty)

def check_lang_pair(df):
    return any(list(df['Source Language']==df['Target Language']))


def create_service_types(service,vender_lang_pair,unit_rate,unit_type,hourly_rate):
    if service.name=='MTPE (MPE)':
        service=VendorServiceInfo.objects.create(lang_pair=vender_lang_pair,mtpe_rate=unit_rate,
                                    mtpe_count_unit=unit_type,mtpe_hourly_rate=hourly_rate)
        print("ser------>",service)
    else:
        service=VendorServiceTypes.objects.create(lang_pair=vender_lang_pair,services=service,
                                    unit_type=unit_type,unit_rate=unit_rate,hourly_rate=hourly_rate)
        print("ser--------->",service)
    return service

@api_view(['POST'])
def vendor_language_pair(request):
    user=request.user
    language_pair_xl_file=request.FILES.get('language_pair_xl_file')
    if not language_pair_xl_file:
        return JsonResponse({'status':'file not uploaded'})
    column_name=['Source Language','Target Language','Currency','Service','Unit Type','Unit Rate','Hourly Rate','Reverse']	
    df=pd.read_excel(language_pair_xl_file)
    # if not df.empty:
    #     return JsonResponse({'status':'empty file upload'})
    if df.columns.to_list() == column_name:
        any_null=check_null_rows(df)
        print("anyNull---->",any_null)
        print("Df-------->",df)
        #df=df.dropna()
        lang_check=check_lang_pair(df)
        if any_null and not lang_check:
            df=df.drop_duplicates(keep="first", inplace=False)
            print("Df-------->",df)
            for _, row in df.iterrows():
                try:
                    print("Inside Try")
                    src_lang=Languages.objects.get(language=row['Source Language'])
                    tar_lang=Languages.objects.get(language=row['Target Language'])
                    currency_code = 'USD' if pd.isnull(row['Currency']) else row['Currency']
                    print("Cur------>",currency_code)
                    currency=Currencies.objects.get(currency_code=currency_code)
                    service= None if pd.isnull(row['Service']) else ServiceTypes.objects.get(name=row['Service'])
                    unit_type=None if pd.isnull(row['Unit Type']) else ServiceTypeunits.objects.get(unit=row['Unit Type'])
                    unit_rate=None if pd.isnull(row['Unit Rate']) else row['Unit Rate']
                    hourly_rate=None if pd.isnull(row['Hourly Rate']) else row['Hourly Rate']
                    reverse = None if pd.isnull(row['Reverse']) else row['Reverse']
                    vender_lang_pair=VendorLanguagePair.objects.create(user=user,source_lang=src_lang,
                                                                    target_lang=tar_lang,currency=currency)
                    print("Vendor_lang----->",vender_lang_pair)
                    if service and unit_type and unit_rate:
                        ser_ven=create_service_types(service,vender_lang_pair,unit_rate,unit_type,hourly_rate)
                
                    if reverse:
                        vender_lang_pair=VendorLanguagePair.objects.create(user=user,source_lang=tar_lang,
                                                                    target_lang=src_lang,currency=currency)
                        print("Vendor_lang----->",vender_lang_pair)
                        if service and unit_type and unit_rate:
                            ser_ven=create_service_types(service,vender_lang_pair,unit_rate,unit_type,hourly_rate)
                except IntegrityError as e:
                    print("Exception--------->",e)
                    pass
                    # return JsonResponse({'status':'Unique contrient same language pairs exists in your records'})
        else:
            return JsonResponse({'status':'some null present in rolls and might contain same lang pair'})
    else:
        return JsonResponse({'status':'column_name miss match'})
    return JsonResponse({'status':'uploaded successfully'})

#from rest_framework.permissions import AllowAny
@api_view(['GET',])
@permission_classes([IsAuthenticated])
def vendor_lang_pair_template(request):
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Vendor_language_pairs.xlsx'
    xlsx_data = vendor_lang_sheet()
    response.write(xlsx_data)
    response['Access-Control-Expose-Headers']='Content-Disposition'
    return response


# @api_view(['POST',])
# def get_vendor_list(request):
#     job_id=request.POST.get('job_id')
#     source_lang_id=Job.objects.get(id=job_id).source_language_id
#     target_lang_id=Job.objects.get(id=job_id).target_language_id
#     res=VendorLanguagePair.objects.filter(Q(source_lang_id=source_lang_id) & Q(target_lang_id=target_lang_id)).all()
#     out=[]
#     for i in res:
#        final_dict={}
#        res1 = AiUser.objects.get(id=i.user_id)
#        res2 = PersonalInformation.objects.get(user_id=i.user_id)
#        res3 = VendorsInfo.objects.get(user_id=i.user_id)
#        final_dict={"Name":res1.fullname,"Country":res2.country_id,"LegalCatagories":res3.type_id,"Vendor_id":res1.uid}
#        try:
#            res4 = VendorServiceInfo.objects.get(lang_pair_id=i.id)
#            a_dict={"MTPE_Unit_Rate":res4.mtpe_rate,"Currency":res3.currency_id}
#            final_dict.update(a_dict)
#        except:
#            a_dict={"MTPE_Unit_Rate":"","Currency":""}
#            final_dict.update(a_dict)
#        try:
#            res5 = Professionalidentity.objects.get(user_id=i.user_id)
#            image=res5.avatar
#            b_dict={"Avatar":image.url}
#            final_dict.update(b_dict)
#        except:
#            b_dict={"Avatar":""}
#            final_dict.update(b_dict)
#        out.append(final_dict)
#     return JsonResponse({"out":out},safe=False)
#
#
# @api_view(['POST',])
# def get_vendor_detail(request):
#     job_id=request.POST.get('job_id')
#     source_lang_id=Job.objects.get(id=job_id).source_language_id
#     target_lang_id=Job.objects.get(id=job_id).target_language_id
#     uid=request.POST.get('vendor_id')
#     user_id=AiUser.objects.get(uid=uid).id
#     result={}
#     lang = VendorLanguagePair.objects.get((Q(source_lang_id=source_lang_id) & Q(target_lang_id=target_lang_id) & Q(user_id=user_id)))
#     res1 = AiUser.objects.get(uid=uid)
#     res2 = PersonalInformation.objects.get(user_id=res1.id)
#     res3 = OfficialInformation.objects.get(user_id=res1.id)
#     res4 = VendorsInfo.objects.get(user_id=res1.id)
#     result["PrimaryInfo"]={"Name":res1.fullname,"CompanyName":res3.company_name,"LegalCatagories":res4.type_id,"currency":res4.currency_id,"proz_link":res4.proz_link,"native_lang":res4.native_lang_id,"YearOfExperience":res4.year_of_experience}
#     new_serv=[]
#     try:
#         res5 = VendorServiceInfo.objects.get(lang_pair_id=lang.id)
#         out=[{"MtpeUnitRate":res5.mtpe_rate,"MtpeHourlyRate":res5.mtpe_hourly_rate,"CountUnit":res5.mtpe_count_unit_id}]
#         new_serv.extend(out)
#         result["service"]=new_serv
#     except:
#         result["service"]=[]
#     try:
#         res7=VendorSubjectFields.objects.filter(user_id=user_id).all()
#         sub=[]
#         for k in res7:
#             out4=[{"subject":k.subject_id}]
#             sub.extend(out4)
#         result["Subject-Matter"]=sub
#     except:
#         result["Subject-Matter"]=[]
#     try:
#         res8=VendorContentTypes.objects.filter(user_id=user_id).all()
#         content=[]
#         for l in res8:
#             out5=[{"contenttype":l.contenttype_id}]
#             content.extend(out5)
#         result["Content-Type"]=content
#     except:
#         result["Content-Type"]=[]
#     return JsonResponse({"out":result},safe=False)
#
#
#
# @api_view(['POST',])
# def assign_available_vendor_to_customer(request):
#     uid=request.POST.get('vendor_id')
#     vendor_id=AiUser.objects.get(uid=uid).id
#     print(vendor_id)
#     customer_id=request.user.id
#     serializer=AvailableVendorSerializer(data={"vendor":vendor_id,"customer":customer_id})
#     if serializer.is_valid():
#         serializer.save()
#         return Response(data={"Message":"Vendor Assigned to User Successfully"})
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
# @api_view(['POST',])
# def post_job_primary_details(request):
#     project_id=request.POST.get('project_id')
#     jobslist=Job.objects.filter(project_id = project_id).all()
#     out=[]
#     result={}
#     for i in jobslist:
#         jobs=[]
#         sl=Job.objects.get(id=i.id).source_language_id
#         tl=Job.objects.get(id=i.id).target_language_id
#         jobs=[{"src_lang":sl,"tar_lang":tl}]
#         out.extend(jobs)
#     result["projectpost_jobs"]=out
#     subject_field=ProjectSubjectField.objects.get(project_id=project_id).subject_id
#     result["subject_field"]=subject_field
#     content_type=ProjectContentType.objects.get(project_id=project_id).content_type_id
#     result["content_type"]=content_type
#     return JsonResponse({"res":result},safe=False)
#
#
# class ProjectPostInfoCreateView(APIView):
#
#     def get(self, request,id):
#         try:
#             queryset = ProjectboardDetails.objects.get(id=id)
#             serializer = ProjectPostSerializer(queryset)
#             return Response(serializer.data)
#         except:
#             return Response(status=status.HTTP_204_NO_CONTENT)
#
#     def post(self, request,id):
#         # data = request.POST.dict()
#         print({**request.POST.dict(),'project_id':id})
#         serializer = ProjectPostSerializer(data={**request.POST.dict(),'project_id':id})#,context={'request':request})
#         print(serializer.is_valid())
#         print(serializer.errors)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#
#     def put(self,request):
#         # data = request.POST.dict()
#         job_info = ProjectboardDetails.objects.get(id=id)
#         serializer = ProjectPostSerializer(job_info,data={**request.POST.dict(),'project':id},partial=True)
#         if serializer.is_valid():
#             serializer.save_update()
#             return Response(serializer.data)
#
# @api_view(['POST',])
# def shortlisted_vendor_list_send_email(request):
#     projectpost_id=request.POST.get('projectpost_id')
#     new=[]
#     userslist=[]
#     jobs=ProjectPostJobDetails.objects.filter(projectpost_id=projectpost_id).all()
#     project_deadline=ProjectboardDetails.objects.get(id=projectpost_id).proj_deadline
#     bid_deadline=ProjectboardDetails.objects.get(id=projectpost_id).bid_deadline
#     for i in jobs:
#         res=VendorLanguagePair.objects.filter(Q(source_lang_id=i.src_lang_id) & Q(target_lang_id=i.tar_lang_id)).all()
#         for j in res:
#             out=[]
#             src_lang=Languages.objects.get(id=i.src_lang_id).language
#             tar_lang=Languages.objects.get(id=i.tar_lang_id).language
#             user_id=VendorLanguagePair.objects.get(id=j.id).user_id
#             out=[{"lang":[{"src_lang":src_lang,"tar_lang":tar_lang}],"user_id":user_id}]
#             if user_id not in userslist:
#                 new.extend(out)
#                 userslist.append(user_id)
#             else:
#                 for k in new:
#                     if k.get("user_id")==user_id:
#                         k.get("lang").extend(out[0].get("lang"))
#     for data in new:
#         user_id=data.get('user_id')
#         user=AiUser.objects.get(id=user_id).fullname
#         email=AiUser.objects.get(id=user_id).email
#         print(email)
#         template = 'email.html'
#         context = {'user': user, 'lang':data.get('lang'),'proj_deadline':project_deadline,'bid_deadline':bid_deadline}
#         content = render_to_string(template, context)
#         subject='Regarding Available jobs'
#         msg = EmailMessage(subject, content, settings.DEFAULT_FROM_EMAIL, to=[email,])
#         msg.content_subtype = 'html'
#         msg.send()
#     return JsonResponse({"message":"Email Successfully Sent"},safe=False)


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


@api_view(['GET',])
def get_vendor_settings_filled(request):
    user = request.user
    if user.is_vendor:
        query = VendorsInfo.objects.filter(user=request.user)
        if not query or (query.last() and (query.last().cv_file == None or query.last().cv_file.name == '')):
            incomplete = True
            print("CV file not uploaded ")
            return Response({'incomplete status':incomplete})
        else:
            query = VendorLanguagePair.objects.filter(Q(user = user) & Q(deleted_at=None)).filter(Q(service=None) or Q(servicetype=None))
            print("Query------------>",query)
            if query:
                print("Rates are not completed")
                incomplete = True
            else: incomplete = False
        return Response({'incomplete status':incomplete})
    else:
        return Response({'msg':'user is not a vendor'},status=400)