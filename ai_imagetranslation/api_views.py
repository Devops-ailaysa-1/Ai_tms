from rest_framework import viewsets 
from ai_imagetranslation.serializer import (ImageloadSerializer,ImageTranslateSerializer,ImageInpaintCreationListSerializer,BackgroundRemovelSerializer)
from rest_framework.response import Response
from ai_imagetranslation.models import (Imageload ,ImageTranslate,ImageInpaintCreation ,BackgroundRemovel)
from rest_framework import status
from django.http import Http404 
from rest_framework.permissions import IsAuthenticated
from ai_canvas.models import CanvasUserImageAssets
###image_upload
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
 
class ImageloadViewset(viewsets.ViewSet,PageNumberPagination):
    permission_classes = [IsAuthenticated,]
    page_size=20

    def get_object(self, pk):
        try:
            return Imageload.objects.get(id=pk)
        except Imageload.DoesNotExist:
            raise Http404
    def get(self, request):
        queryset = Imageload.objects.filter(user=request.user.id).order_by('-id')
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = ImageloadSerializer(pagin_tc ,many =True)
        response = self.get_paginated_response(serializer.data)
        return response
    
    def create(self,request):
        image = request.FILES.get('image')
        
        if str(image).split('.')[-1] not in ['svg', 'png', 'jpeg', 'jpg']:
            return Response({'msg':'only .svg, .png, .jpeg, .jpg suppported file'},status=400)
        serializer = ImageloadSerializer(data=request.data ,context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)
    
    def retrieve(self,request,pk):
        obj =self.get_object(pk)
        query_set = Imageload.objects.get(id = pk)
        serializer = ImageloadSerializer(query_set )
        return Response(serializer.data)
    
    def delete(self,request,pk):
        query_obj = Imageload.objects.get(id = pk)
        query_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

###image upload for inpaint processs
from django.http import JsonResponse
class ImageTranslateViewset(viewsets.ViewSet,PageNumberPagination):
    permission_classes = [IsAuthenticated,]
    page_size=20
    def get_object(self, pk):
        try:
            return ImageTranslate.objects.get(id=pk)
        except ImageTranslate.DoesNotExist:
            raise Http404

    def list(self, request):
        queryset = ImageTranslate.objects.filter(user=request.user.id).order_by('-id') 
        print("test")
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = ImageTranslateSerializer(pagin_tc ,many =True)
        response = self.get_paginated_response(serializer.data)
        return response

    def retrieve(self,request,pk):
        obj =self.get_object(pk)
        query_set = ImageTranslate.objects.get(id = pk)
        serializer = ImageTranslateSerializer(query_set )
        return Response(serializer.data)
        
    def create(self,request):
        image = request.FILES.get('image')
        image_id =  request.POST.getlist('image_id')
        canvas_asset_image_id=request.POST.get('canvas_asset_image_id')
        if image and str(image).split('.')[-1] not in ['svg', 'png', 'jpeg', 'jpg']:
            return Response({'msg':'only .svg, .png, .jpeg, .jpg suppported file'},status=400)
        
        if image:
            serializer=ImageTranslateSerializer(data=request.data,context={'request':request}) 
        
        elif image_id:
            im_details = Imageload.objects.filter(id__in = image_id)
            data = [{'image':im.image} for im in im_details]
            serializer = ImageTranslateSerializer(data=data,many=True,context={'request':request}) 

        elif canvas_asset_image_id:
             im_details = CanvasUserImageAssets.objects.get(id = canvas_asset_image_id)
             data={'image':im_details.image}
             serializer = ImageTranslateSerializer(data=data,many=False,context={'request':request}) 
             
        if serializer.is_valid():
            print(serializer.data)
            serializer.save()
            response=JsonResponse(serializer.data)
            response.status_code = 200
            response["Custom-Header"] = "Value"
            return response
        else:
            return Response(serializer.errors)
        
    def update(self,request,pk):
        obj =self.get_object(pk)
        query_set = ImageTranslate.objects.get(id=pk)
        serializer = ImageTranslateSerializer(query_set,data=request.data ,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)
                    
    def delete(self,request,pk):
        query_obj = ImageTranslate.objects.get(id = pk)
        query_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

from ai_canvas.api_views import CustomPagination
class ImageInpaintCreationListView(ListAPIView,CustomPagination):
    queryset = ImageInpaintCreation.objects.all()#.values
    serializer_class = ImageInpaintCreationListSerializer
    pagination_class = CustomPagination
    # def get_queryset(self):
    #     # Specify the fields to include in the serialized representation
    #     fields = ['id','image', 'width', 'field3']
    #     return ImageInpaintCreation.objects.only(*fields)
# class ImageloadRetrieveViewset(generics.RetrieveAPIView):
#     queryset = Imageload.objects.all()
#     serializer_class = ImageloadRetrieveRetrieveSerializer
#     lookup_field = 'id'


class BackgroundRemovelViewset(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,]
    
    def get_object(self, pk):
        try:
            return BackgroundRemovel.objects.get(id=pk)
        except BackgroundRemovel.DoesNotExist:
            raise Http404

    def get(self, request):
        query_set = BackgroundRemovel.objects.filter(user=request.user.id).order_by('id')
        serializer = BackgroundRemovelSerializer(query_set ,many =True)
        return Response(serializer.data)

    def retrieve(self,request,pk):
        obj =self.get_object(pk)
        query_set = BackgroundRemovel.objects.get(id = pk)
        serializer = BackgroundRemovelSerializer(query_set )
        return Response(serializer.data)
        
    def create(self,request):
        # canvas_json=request.POST.get('canvas_json')
        serializer = BackgroundRemovelSerializer(data=request.data,context={'request':request})  
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)
