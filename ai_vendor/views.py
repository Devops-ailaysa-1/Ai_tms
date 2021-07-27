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

from .models import (VendorBankDetails, VendorLanguagePair, VendorServiceInfo,
                     VendorServiceTypes, VendorsInfo, VendorSubjectFields)
from .serializers import (LanguagePairSerializer, ServiceExpertiseSerializer,
                          VendorBankDetailSerializer,
                          VendorLanguagePairSerializer,
                          VendorServiceInfoSerializer, VendorsInfoSerializer)
from ai_staff.models import (Languages,Spellcheckers,SpellcheckerLanguages,
                            VendorLegalCategories, CATSoftwares, VendorMemberships,
                            MtpeEngines, SubjectFields)

import json,requests
from django.http import JsonResponse


class VendorsInfoCreateView(APIView):

    def get(self, request):
        try:
            queryset = VendorsInfo.objects.get(user_id=request.user.id)
            serializer = VendorsInfoSerializer(queryset)
            return Response(serializer.data)
        except:
            return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request):
        print("cv_file---->",request.FILES.get('cv_file'))
        cv_file=request.FILES.get('cv_file')
        user_id = request.user.id
        # data = request.POST.dict()
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
        serializer = VendorsInfoSerializer(vendor_info,data={**request.POST.dict(),'cv_file':cv_file},partial=True)
        if serializer.is_valid():
            serializer.save_update()
            return Response(serializer.data)


class VendorServiceListCreate(viewsets.ViewSet, PageNumberPagination):
    permission_classes =[IsAuthenticated]
    page_size = settings.REST_FRAMEWORK["PAGE_SIZE"]
    def get_custom_page_size(self, request, view):
        try:
            self.page_size = self.request.query_params.get('limit',10)
            print(self.request.query_params.get('limit'))
        except (ValueError, TypeError):
            pass
        return super().get_page_size(request)
    def paginate_queryset(self, queryset, request, view=None):
        self.page_size = self.get_custom_page_size(request, view)
        return super().paginate_queryset(queryset, request, view)
    def list(self,request):
        queryset = self.get_queryset()
        pagin_tc = self.paginate_queryset( queryset, request , view=self )
        serializer = VendorLanguagePairSerializer(pagin_tc, many=True, context={'request': request})
        response =self.get_paginated_response(serializer.data)
        return  Response(response.data)
    def get_queryset(self):
        search_word =  self.request.query_params.get('search_word',None)
        print(search_word)
        queryset=VendorLanguagePair.objects.filter(user_id=self.request.user.id).all()
        if search_word:
            if search_word.isalpha()==True:
                lang_id=Languages.objects.get(language__contains=search_word).id
                print(lang_id)
                queryset = queryset.filter(
                            Q(source_lang=lang_id) | Q(target_lang=lang_id)
                        )
            else:
                queryset = queryset.filter(
                            Q(id=search_word))
                print(queryset)
        return queryset
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



# class VendorBankInfoListCreate(viewsets.ViewSet):
#     def list(self,request):
#         queryset = self.get_queryset()
#         serializer = VendorLanguagePairSerializer(queryset,many=True)
#         return Response(serializer.data)
#
#
# class VendorServiceInfoView(viewsets.ViewSet):
#     def list(self,request):
#         context=dict(request=RequestFactory().get('/'))
#         queryset=self.get_queryset()
#         serializer = VendorServiceInfoSerializer(queryset,many=True,context=context)
#         return Response(serializer.data)
#     def get_queryset(self):
#         queryset=VendorServiceInfo.objects.all()
#         return queryset

class VendorServiceInfoView(viewsets.ModelViewSet):
    queryset = VendorServiceInfo.objects.all()
    serializer_class = VendorServiceInfoSerializer


@api_view(['GET','POST',])
def SpellCheckerApiCheck(request):
    doc_id= request.POST.get("doc_id")
    result=requests.get(f"http://157.245.99.128:8005/api/getLangName/{doc_id}/")
    content=result.json()
    targetLanguage=content.get("TargetLanguage")
    target_lang_id=Languages.objects.get(language=targetLanguage).id
    try:
        spellchecker_id=SpellcheckerLanguages.objects.get(language_id=target_lang_id).spellchecker.id
        print(spellchecker_id)
        data="spellchecker Available"
    except:
        data="spellchecker Not Available"
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
