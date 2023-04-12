from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets  ,generics
from rest_framework.response import Response
from ai_staff.models import ( Languages,LanguagesLocale)
from ai_canvas.models import (CanvasTemplates ,CanvasUserImageAssets,CanvasDesign,CanvasSourceJsonFiles,
                              CanvasTargetJsonFiles,TemplateGlobalDesign,TemplatePage)
from ai_canvas.serializers import (CanvasTemplateSerializer ,LanguagesSerializer,LocaleSerializer,
                                   CanvasUserImageAssetsSerializer,CanvasDesignSerializer,CanvasDesignListSerializer,
                                   TemplateGlobalDesignSerializer ,TemplateGlobalDesignRetrieveSerializer)
from django.http import Http404 
from ai_canvas.pagination import CanvasDesignListViewsetPagination ,TemplateGlobalPagination
from rest_framework.pagination import PageNumberPagination 

class LanguagesViewset(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,]
    
    def list(self, request):
        queryset = Languages.objects.all()
        serializer = LanguagesSerializer(queryset,many=True)
        return Response(serializer.data)

class LanguagesLocaleViewset(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,]
    
    def list(self, request):
        queryset = LanguagesLocale.objects.all()
        serializer = LocaleSerializer(queryset,many=True)
        return Response(serializer.data)

class CanvasTemplateViewset(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,]

    def get_object(self, pk):
        try:
            return CanvasTemplates.objects.get(id=pk)
        except CanvasTemplates.DoesNotExist:
            raise Http404
            
    def retrieve(self,request,pk):
        obj =self.get_object(pk)
        serializer = CanvasTemplateSerializer(obj)
        return Response(serializer.data)

    def create(self,request):
        thumbnail = request.FILES.get('thumbnail')
        serializer = CanvasTemplateSerializer(data={**request.POST.dict(),'thumbnail':thumbnail})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
    
    def list(self, request):
        queryset = CanvasTemplates.objects.all()
        serializer = CanvasTemplateSerializer(queryset,many=True)
        return Response(serializer.data)

    def update(self,request,pk):
        obj =self.get_object(pk)
        serializer = CanvasTemplateSerializer(obj,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors,status=400)
        
    def destroy(self,request,pk):
        try:
            obj = CanvasTemplates.objects.get(id=pk)
            obj.delete()
            return Response({'msg':'deleted successfully'},status=200)
        except:
            return Response({'msg':'deletion unsuccessfull'},status=400)
        
class CanvasUserImageAssetsViewset(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,]
    def get_object(self, pk):
        try:
            return CanvasUserImageAssets.objects.get(id=pk)
        except CanvasUserImageAssets.DoesNotExist:
            raise Http404

    def create(self,request):
        image = request.FILES.get('image')
        serializer = CanvasUserImageAssetsSerializer(data={**request.POST.dict(),'image':image},context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
    
    def list(self, request):
        queryset = CanvasUserImageAssets.objects.all()
        serializer = CanvasUserImageAssetsSerializer(queryset,many=True)
        return Response(serializer.data)
    
    def retrieve(self,request,pk):
        obj =self.get_object(pk)
        serializer = CanvasUserImageAssetsSerializer(obj)
        return Response(serializer.data)
    
    def update(self,request,pk):
        obj =self.get_object(pk)
        serializer = CanvasUserImageAssetsSerializer(obj,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors,status=400)
        
    def destroy(self,request,pk):
        try:
            obj = CanvasUserImageAssets.objects.get(id=pk)
            obj.delete()
            return Response({'msg':'deleted successfully'},status=200)
        except:
            return Response({'msg':'deletion unsuccessfull'},status=400)
        


###########################################################################

class CanvasDesignViewset(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,]

    def get_object(self, pk):
        try:
            return CanvasDesign.objects.get(id=pk)
        except CanvasDesign.DoesNotExist:
            raise Http404

    def create(self,request):
        thumbnail = request.FILES.get('thumbnail')
        serializer = CanvasDesignSerializer(data=request.data,context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
    
    def list(self, request):
        queryset = CanvasDesign.objects.all()
        serializer = CanvasDesignSerializer(queryset,many=True)
        return Response(serializer.data)

    def retrieve(self,request,pk):
        obj =self.get_object(pk)
        serializer = CanvasDesignSerializer(obj)
        return Response(serializer.data)
    
    def update(self,request,pk):
        obj =self.get_object(pk)
        serializer = CanvasDesignSerializer(obj,data=request.data,partial=True,context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors,status=400)
        
    def destroy(self,request,pk):
        can_src = request.query_params.get('can_src',None)
        can_tar = request.query_params.get('can_tar',None)
        page_no =request.query_params.get('page_no',None)
        try:
            obj = CanvasDesign.objects.get(id=pk)
            if can_src and page_no:
                CanvasSourceJsonFiles.objects.get(id=can_src,page_no=page_no).delete()
            elif can_tar and page_no:
                CanvasTargetJsonFiles.objects.get(id=can_tar,page_no=page_no).delete()
            else:
                obj.delete()
            return Response({'msg':'deleted successfully'},status=200)
        except:
            return Response({'msg':'deletion unsuccessfull'},status=400)
        

class CanvasDesignListViewset(viewsets.ViewSet,PageNumberPagination):
    pagination_class = CanvasDesignListViewsetPagination

    def list(self,request):
        queryset = CanvasDesign.objects.all().order_by('-updated_at')
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = CanvasDesignListSerializer(pagin_tc,many=True)
        response = self.get_paginated_response(serializer.data)
        return response
    


class TemplateGlobalDesignViewset(viewsets.ViewSet ,PageNumberPagination):
    pagination_class = TemplateGlobalPagination 
 
    def list(self,request):
        queryset = TemplateGlobalDesign.objects.all().order_by('-updated_at')
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = TemplateGlobalDesignSerializer(pagin_tc,many=True)
        response = self.get_paginated_response(serializer.data)
        return response
    
    def create(self,request):
        thumbnail_page = request.FILES.get('thumbnail_page')
        export_page = request.FILES.get('export_page')
        serializer = TemplateGlobalDesignSerializer(data = request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
    
    def update(self,request,pk):
        thumbnail_page = request.FILES.get('thumbnail_page')
        export_page = request.FILES.get('export_page')
        queryset = TemplateGlobalDesign.objects.get(id=pk)
        serializer = TemplateGlobalDesignSerializer(queryset ,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors,status=400)
    
    def get(self,request,pk):
        queryset = TemplateGlobalDesign.objects.get(id=pk)
        serializer = TemplateGlobalDesignSerializer(queryset)
        return Response(serializer.data)
    
    def destroy(self,request,pk):
        page_no = request.query_params.get('page_no',None)
        try:
            if page_no:
                temp_design = TemplateGlobalDesign.objects.get(id=pk)
                TemplatePage.objects.get(template_page=temp_design,page_no=page_no).delete()
            else:
                TemplateGlobalDesign.objects.get(id=pk).delete()
            return Response({'msg':'deleted'})
        except:
            print("error in del")
            return Response({'msg':'template Does not exist'})


class TemplateGlobalDesignRetrieveViewset(generics.RetrieveAPIView):
    queryset = TemplateGlobalDesign.objects.all()
    serializer_class = TemplateGlobalDesignRetrieveSerializer
    lookup_field = 'id'