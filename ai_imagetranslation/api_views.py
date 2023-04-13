from rest_framework import viewsets   
from ai_imagetranslation.serializer import ImageloadSerializer ,ImageUploadSerializer
from rest_framework.response import Response
from ai_imagetranslation.models import Imageload ,ImageUpload
from rest_framework import status
from PIL import Image

###image_upload

class ImageloadViewset(viewsets.ViewSet):
 
    def get(self, request):
        query_set = Imageload.objects.all()
        serializer = ImageloadSerializer(query_set ,many =True)
        return Response(serializer.data)
    
    def create(self,request):
        image = request.FILES.get('image')
        im = Image.open(image)
        width, height = im.size
        file_name = str(image)
        types = file_name.split(".")[-1]
        serializer = ImageloadSerializer(data={**request.POST.dict() ,'image':image,'height':height,"width":width,
                                           'file_name':file_name ,'types':types  })
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)
    
    def retrieve(self,request,pk):
        query_set = Imageload.objects.get(id = pk)
        serializer = ImageloadSerializer(query_set )
        return Response(serializer.data)
    
    def delete(self,request,pk):
        query_obj = Imageload.objects.get(id = pk)
        query_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

###image upload for inpaint process
class ImageUploadViewset(viewsets.ViewSet):
    model = ImageUpload
    serializer = ImageUploadSerializer
    
    def get(self, request):
        query_set = ImageUpload.objects.all()
        serializer = ImageUploadSerializer(query_set ,many =True)
        return Response(serializer.data)

    def retrieve(self,request,pk):
        query_set = ImageUpload.objects.get(id = pk)
        serializer = ImageUploadSerializer(query_set )
        return Response(serializer.data)
        
    def create(self,request):
        # image = request.FILES.get('image')
        image_id =  request.POST.getlist('image_id')
        im_details = Imageload.objects.filter(id__in = image_id)
        data = [{'image':im.image} for im in im_details]
        serializer = self.serializer(data=data ,many = True) #{**request.POST.dict() 
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)
        
    def update(self,request,pk):
        # image_to_translate_id = request.query_params.getlist('image_to_translate_id' ,None)
        # print("image_to_translate_id" ,image_to_translate_id)
        # if image_to_translate_id:
        #     image_query_set = self.model.objects.filter(id__in = image_to_translate_id)
        #     serializer = self.serializer(image_query_set,data=request.data ,partial=True ,many = True)
        # else:s
        query_set = self.model.objects.get(id = pk)
        serializer = self.serializer(query_set,data=request.data ,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)
                    
    def delete(self,request,pk):
        query_obj = self.model.objects.get(id = pk)
        query_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)