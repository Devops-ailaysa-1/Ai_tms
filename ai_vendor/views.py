from ai_auth.models import AiUser
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.test.client import RequestFactory
from rest_framework import pagination, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated,AllowAny
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
                     VendorMtpeEngines, SavedVendor)
from .serializers import (ServiceExpertiseSerializer,
                          VendorBankDetailSerializer,VendorLanguagePairCloneSerializer,
                          VendorLanguagePairSerializer,
                          VendorServiceInfoSerializer, VendorsInfoSerializer,
                          SavedVendorSerializer,AMSLangpairSerializer) #
from ai_staff.models import (Languages,Spellcheckers,SpellcheckerLanguages,
                            VendorLegalCategories, CATSoftwares, VendorMemberships,
                            MtpeEngines, SubjectFields,ServiceTypeunits, LanguageMetaDetails)
from ai_auth.models import AiUser, Professionalidentity,VendorOnboarding
import json,requests,os
from django.http import JsonResponse,HttpResponse



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
        pr_managers = self.request.user.team.get_project_manager if self.request.user.team and self.request.user.team.owner.is_agency else [] 
        user = self.request.user.team.owner if self.request.user.team and self.request.user.team.owner.is_agency and self.request.user in pr_managers else self.request.user
        queryset=VendorLanguagePair.objects.filter(user_id=user.id).all()
        return queryset

    def list(self,request):
        queryset = self.get_queryset()
        res ={}
        for i in queryset:
            q2 = VendorLanguagePair.objects.filter(Q(source_lang = i.source_lang)&Q(target_lang=i.target_lang)&Q(user_id=i.user_id))
            tt = str(i.source_lang.language) + '-->' + str(i.target_lang.language)
            ser = VendorLanguagePairSerializer(q2,many=True)
            res[tt]=ser.data
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
        serializer = VendorLanguagePairSerializer(data={**request.POST.dict()},context={'request':request})
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @integrity_error
    def update(self,request,pk):
        pr_managers = self.request.user.team.get_project_manager if self.request.user.team and self.request.user.team.owner.is_agency else [] 
        user = self.request.user.team.owner if self.request.user.team and self.request.user.team.owner.is_agency and self.request.user in pr_managers else self.request.user
        queryset = VendorLanguagePair.objects.filter(user_id=user.id).all()
        vendor = get_object_or_404(queryset, pk=pk)
        ser=VendorLanguagePairSerializer(vendor,data={**request.POST.dict()},context={'request':request},partial=True)
        print(ser.is_valid())
        print(ser.errors)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self,request,pk):
        pr_managers = self.request.user.team.get_project_manager if self.request.user.team and self.request.user.team.owner.is_agency else [] 
        user = self.request.user.team.owner if self.request.user.team and self.request.user.team.owner.is_agency and self.request.user in pr_managers else self.request.user
        queryset = VendorLanguagePair.objects.filter(user_id=user.id).all()
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

    def get_queryset(self):
        queryset=AiUser.objects.filter(id=self.request.user.id).all()
        return queryset


    def list(self,request):
        queryset = self.get_queryset()
        serializer = ServiceExpertiseSerializer(queryset,many=True)
        return Response(serializer.data)


    def create(self,request):
        serializer = ServiceExpertiseSerializer(data={**request.POST.dict()},context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
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
        serializer = VendorBankDetailSerializer(data=data)
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
    
    # CHECK FOR SPELLCHECKER AVAILABILITY
    try:
        spellchecker_id = SpellcheckerLanguages.objects.get(language_id=target_lang_id).spellchecker.id
        data = 1
    except:
        data = 0

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
    languages=list(Languages.objects.all().order_by('language').values_list('language',flat=True))
    worksheet2.write('A1','Languages')
    for i in range(len(languages)):
        a='A{}'.format(i+2)
        worksheet2.write(a,languages[i])

    worksheet2.add_table('A1:A{}'.format(len(languages)+1),{'name': 'Languages','autofilter': False,'columns': [{'header': 'Languages'}]}) 
    worksheet.write('A1', 'Source Language',header)
    worksheet.write('B1', 'Target Language',header)
    worksheet.write('C1', 'Currency',header)
    worksheet.write('D1', 'Service',header)
    worksheet.write('E1', 'Unit Type',header)
    worksheet.write('F1', 'Unit Rate',header) 
    worksheet.write('G1','Hourly Rate',header)
    worksheet.write('H1','Reverse',header)
    worksheet.set_column(0, 7, 30)
    currency=['EUR','GBP','INR','USD']
    service=['MTPE (MPE)','Human Translation (HUT)']
    unit_type=['Word','Char']
    boolean=['True','False']
    worksheet.data_validation('A2:A1048576', {'validate': 'list', 'source': '=Languages!$A$2:$A$125'})    
    worksheet.data_validation('B2:B1048576', {'validate': 'list', 'source': '=Languages!$A$2:$A$125'})
    worksheet.data_validation('C2:C1048576', {'validate': 'list', 'source': currency})
    worksheet.data_validation('D2:D1048576', {'validate': 'list', 'source': service})
    worksheet.data_validation('E2:E1048576', {'validate': 'list', 'source': unit_type})
    worksheet.data_validation('F2:F1048576', {'validate': 'decimal','criteria': 'between', 'minimum': 0, 'maximum': 999999.0})
    worksheet.data_validation('G2:G1048576', {'validate': 'decimal','criteria': 'between', 'minimum': 0, 'maximum': 999999.0})
    worksheet.data_validation('H2:H1048576', {'validate': 'list','source':boolean})
    worksheet2.hide()
    workbook.close()
    xlsx_data = output.getvalue()
    return xlsx_data


def check_null_rows(df):
    fields_to_check = ['Source Language','Target Language']
    check_fields_empty = df[fields_to_check].notnull().all(axis=1)
    return all(check_fields_empty)

def check_lang_pair(df):
    return any(list(df['Source Language']==df['Target Language']))


def create_service_types(service,vender_lang_pair,unit_rate,unit_type,hourly_rate):
    if service.name=='MTPE (MPE)':
        service=VendorServiceInfo.objects.create(lang_pair=vender_lang_pair,mtpe_rate=unit_rate,
                                    mtpe_count_unit=unit_type,mtpe_hourly_rate=hourly_rate)
    else:
        service=VendorServiceTypes.objects.create(lang_pair=vender_lang_pair,services=service,
                                    unit_type=unit_type,unit_rate=unit_rate,hourly_rate=hourly_rate) 
    return service

@api_view(['POST'])
def vendor_language_pair(request):
    pr_managers = request.user.team.get_project_manager if request.user.team and request.user.team.owner.is_agency else [] 
    user = request.user.team.owner if request.user.team and request.user.team.owner.is_agency and request.user in pr_managers else request.user
    language_pair_xl_file=request.FILES.get('language_pair_xl_file')
    if not language_pair_xl_file:
        return JsonResponse({'status':'file not uploaded'})
    column_name=['Source Language','Target Language','Currency','Service','Unit Type','Unit Rate','Hourly Rate','Reverse']	
    df=pd.read_excel(language_pair_xl_file)

    if df.columns.to_list() == column_name:
        any_null=check_null_rows(df)
        lang_check=check_lang_pair(df)
        if any_null and not lang_check:
            df=df.drop_duplicates(keep="first", inplace=False)
            for _, row in df.iterrows():
                try:
                    given_src = row['Source Language'].capitalize() if row['Source Language'].split() == 1 else row['Source Language'][0].capitalize() + row['Source Language'][1:]
                    given_tar = row['Target Language'].capitalize() if row['Target Language'].split() == 1 else row['Target Language'][0].capitalize() + row['Target Language'][1:]
                    src_lang=Languages.objects.filter(language=given_src).first()
                    tar_lang=Languages.objects.filter(language=given_tar).first()
                    currency_code = 'USD' if pd.isnull(row['Currency']) else row['Currency']
                    currency=Currencies.objects.get(currency_code=currency_code)
                    service= None if pd.isnull(row['Service']) else ServiceTypes.objects.get(name=row['Service'])
                    unit_type=None if pd.isnull(row['Unit Type']) else ServiceTypeunits.objects.get(unit=row['Unit Type'])
                    unit_rate=None if pd.isnull(row['Unit Rate']) else row['Unit Rate']
                    hourly_rate=None if pd.isnull(row['Hourly Rate']) else row['Hourly Rate']
                    reverse = None if pd.isnull(row['Reverse']) else row['Reverse']
                    vender_lang_pair=VendorLanguagePair.objects.get_or_create(user=user,source_lang=src_lang,
                                                                    target_lang=tar_lang,currency=currency)
                    if service and unit_type and unit_rate:
                        ser_ven=create_service_types(service,vender_lang_pair[0],unit_rate,unit_type,hourly_rate)
                
                    if reverse:
                        src_lang,tar_lang=tar_lang,src_lang #swapping src to tar and tar to src for reverse
                        vender_lang_pair=VendorLanguagePair.objects.get_or_create(user=user,source_lang=src_lang,target_lang=tar_lang,currency=currency)
                        if service and unit_type and unit_rate:
                            ser_ven=create_service_types(service,vender_lang_pair[0],unit_rate,unit_type,hourly_rate)
                except IntegrityError as e:
                    print("Exception--------->",e)
                    try:
                        ven_lan_pair=VendorLanguagePair.objects.get_or_create(user=user,source_lang=src_lang,target_lang=tar_lang)
                        ven_service_info=VendorServiceInfo.objects.filter(lang_pair=ven_lan_pair)[0]
                        service=ven_service_info.services
                        unit_type=ven_service_info.unit_type
                        unit_rate=ven_service_info.unit_rate
                        hourly_rate=ven_service_info.hourly_rate
                        ven_service_info.save()
                    except:
                        pass
        else:
            return JsonResponse({'msg':'some null present in rolls and might contain same lang pair'},status=400)
    else:
        return JsonResponse({'msg':'column_name miss match'},status=400)
    return JsonResponse({'status':'uploaded successfully'})


@api_view(['GET',])
@permission_classes([IsAuthenticated])
def vendor_lang_pair_template(request):
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=service_provider_translation_rates.xlsx'
    xlsx_data = vendor_lang_sheet()
    response.write(xlsx_data)
    response['Access-Control-Expose-Headers']='Content-Disposition'
    return response


@api_view(['GET',])
def get_vendor_settings_filled(request):
    user = request.user
    if user.is_vendor:
        query = VendorsInfo.objects.filter(user=request.user)
        if not query or (query.last() and (query.last().cv_file == None or query.last().cv_file.name == '')):
            incomplete = True
            return Response({'incomplete status':incomplete,'msg':'Cv not uploaded'})
        else:
            query_1 = VendorLanguagePair.objects.filter(Q(user = user) & Q(deleted_at=None))
            if not query_1:
                incomplete = True
                return Response({'incomplete status':incomplete,'msg':'No lang pair exists'})
            query = query_1.filter(Q(service=None) or Q(servicetype=None))
            if query:
                incomplete = True
            else: incomplete = False
        return Response({'incomplete status':incomplete})
    else:
        return Response({'msg':'user is not a vendor'},status=400)
    



@api_view(['GET',])
@permission_classes([AllowAny])
def get_ams_agency_lang_pair_price(request):
    own_agency_email = os.getenv("AILAYSA_AGENCY_EMAIL")
    user = AiUser.objects.get(email=own_agency_email)
    obj = VendorLanguagePair.objects.filter(user = user)
    serializer = AMSLangpairSerializer(obj,many=True)
    return Response(serializer.data)
 
