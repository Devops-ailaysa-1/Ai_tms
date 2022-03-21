from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import UploadedTMinfoSerializer, \
    TMUploadRequestDataResolveSerializer
from django.shortcuts import get_list_or_404, \
    get_object_or_404

from .models import UploadedTMinfo

class TMFileUploadView(viewsets.ModelViewSet):
    serializer_class = UploadedTMinfoSerializer

    def get_queryset(self):
        all_objs = UploadedTMinfo.objects.all()
        objs = get_list_or_404(all_objs, owned_by=self.request.user)
        return objs

    def get_object(self):
        all_objs = UploadedTMinfo.objects.all()
        obj = get_object_or_404(all_objs, pk=self.kwargs["pk"])
        return obj

    def create(self, request, *args, **kwargs):
        data = request.data
        serlzr = TMUploadRequestDataResolveSerializer(data=[data], many=True)
        if serlzr.is_valid(raise_exception=True):
            data = Response(serlzr.data[0]).data

        serlzr = UploadedTMinfoSerializer(data=data, many=True)
        if serlzr.is_valid(raise_exception=True):
            serlzr.save(uploaded_by=request.user, owned_by=request.user)
            return Response(serlzr.data)



