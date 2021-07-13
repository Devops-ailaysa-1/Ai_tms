from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework import viewsets,status
from rest_framework.response import Response
from .serializers import VendorsInfoSerializer,VendorLanguagePairSerializer,VendorServiceInfoSerializer,ServiceExpertiseSerializer,VendorBankDetailSerializer
from .models import VendorsInfo,VendorLanguagePair,VendorServiceInfo,VendorServiceTypes,VendorSubjectFields,VendorBankDetails
from django.shortcuts import get_object_or_404
from django.test.client import RequestFactory
from ai_auth.models import AiUser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
# from rest_framework import pagination
# from rest_framework.pagination import PageNumberPagination

class VendorsInfoCreateView(APIView):

    def get(self, request):
        queryset = VendorsInfo.objects.get(user_id=request.user.id)
        serializer = VendorsInfoSerializer(queryset)
        return Response(serializer.data)

    def post(self, request):
        user_id = request.user.id
        data = request.data
        serializer = VendorsInfoSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user_id = user_id)
            return Response(serializer.data)

    def put(self,request):
        user_id=request.user.id
        data = request.data
        vendor_info = VendorsInfo.objects.get(user_id=request.user.id)
        serializer = VendorsInfoSerializer(vendor_info,data=data,partial=True)
        if serializer.is_valid():
            serializer.save_update()
            return Response(serializer.data)


class VendorServiceListCreate(viewsets.ViewSet):
    permission_classes =[IsAuthenticated]
    def list(self,request):
        queryset = self.get_queryset()
        serializer = VendorLanguagePairSerializer(queryset,many=True)
        return Response(serializer.data)
    def get_queryset(self):
        queryset=VendorLanguagePair.objects.filter(user_id=self.request.user.id).all()
        return queryset
    def create(self,request):
        user_id = request.user.id
        data = request.data
        serializer = VendorLanguagePairSerializer(data=data)
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save(user_id=user_id)
            return Response(data={"Message":"VendorServiceInfo Created"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def update(self,request,pk):
        queryset = VendorLanguagePair.objects.all()
        vendor = get_object_or_404(queryset, pk=pk)
        ser=VendorLanguagePairSerializer(vendor,data=request.data,partial=True)
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
        data = request.data
        serializer = ServiceExpertiseSerializer(data=data)
        print(serializer.is_valid())
        if serializer.is_valid():
            serializer.save(id=id)
            return Response(serializer.data)
            # return Response(data={"Message":"VendorExpertiseInfo Created"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def update(self,request,pk):
        queryset = AiUser.objects.all()
        User = get_object_or_404(queryset, pk=pk)
        ser= ServiceExpertiseSerializer(User,data=request.data,partial=True)
        if ser.is_valid():
            ser.save()
            # ser.update(vendor,validated_data=request.data)
            return Response(ser.data)


class VendorsBankInfoCreateView(APIView):

    def get(self, request):
        queryset = VendorBankDetails.objects.get(user_id=request.user.id)
        serializer = VendorBankDetailSerializer(queryset)
        return Response(serializer.data)

    def post(self, request):
        user_id = request.user.id
        data = request.data
        serializer = VendorBankDetailSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user_id = user_id)
            return Response(serializer.data)

    def put(self,request):
        user_id=request.user.id
        data = request.data
        vendor_bank_info = VendorBankDetails.objects.get(user_id=request.user.id)
        serializer = VendorBankDetailSerializer(vendor_bank_info,data=data,partial=True)
        if serializer.is_valid():
            serializer.save_update()
            return Response(serializer.data)




# class VendorBankInfoListCreate(viewsets.ViewSet):
#     def list(self,request):
#         queryset = self.get_queryset()
#         serializer = VendorLanguagePairSerializer(queryset,many=True)
#         return Response(serializer.data)


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
