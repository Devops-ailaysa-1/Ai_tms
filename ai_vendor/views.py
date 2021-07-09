from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import VendorsInfoSerializer
from .models import VendorsInfo
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
