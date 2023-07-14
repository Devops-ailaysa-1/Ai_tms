from rest_framework import viewsets 
from ai_imagetranslation.serializer import (ImageloadSerializer,ImageTranslateSerializer,ImageInpaintCreationListSerializer,BackgroundRemovelSerializer)
from rest_framework.response import Response
from ai_imagetranslation.models import (Imageload ,ImageTranslate,ImageInpaintCreation ,BackgroundRemovel)
from rest_framework import status
from django.http import Http404 
from rest_framework.permissions import IsAuthenticated
from ai_canvas.models import CanvasUserImageAssets
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django.http import JsonResponse
###image_upload
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination

from rest_framework.decorators import api_view,permission_classes
from ai_canvas.utils import export_download
from ai_canvas.api_views import download_file_canvas,mime_type
import io
from django import core
from zipfile import ZipFile


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


# class ImageTranslateFilter(django_filters.FilterSet):
#     project_name = django_filters.CharFilter(field_name='project_name', lookup_expr='icontains')
#     types=django_filters.CharFilter(field_name='types', lookup_expr='icontains')
#     class Meta:
#         model = ImageTranslate
#         fields = ['project_name','types']
 


class ImageTranslateViewset(viewsets.ViewSet,PageNumberPagination):
    permission_classes = [IsAuthenticated,]
    filter_backends = [DjangoFilterBackend]
    filterset_fields =['project_name','types']
    search_fields =['types','project_name','source_language__language__language','s_im__target_language__language__language']
 
    page_size=20
    def get_object(self, pk):
        try:
            return ImageTranslate.objects.get(id=pk)
        except ImageTranslate.DoesNotExist:
            raise Http404
        
    def filter_queryset(self, queryset):
        filter_backends = (DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter )
        for backend in list(filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        return queryset
    
    def list(self, request):
        queryset = ImageTranslate.objects.filter(user=request.user.id).order_by('-id')
        queryset = self.filter_queryset(queryset)
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
    
def create_image(json_page,file_format,export_size,page_number,language):
    file_format_ext = 'png' if file_format == 'png-transparent' else file_format

    base64_img=export_download(json_page,file_format,export_size)
    file_name="page_{}_{}.{}".format(str(page_number),language,file_format_ext)
    return base64_img,file_name


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def image_translation_project_view(request):
    image_id=request.query_params.get('image_id')
    language=request.query_params.get('language',0)
    export_size=request.query_params.get('export_size',1)
    file_format=request.query_params.get('file_format')
 
    language = int(language) if language else None
    file_format = file_format.replace(" ","-") if file_format else ""
    image_download={}
    image_instance=ImageTranslate.objects.get(id=image_id)
    if language==0:
        buffer=io.BytesIO()
        format_exe = 'png' if file_format == 'png-transparent' else file_format
        with ZipFile(buffer, mode="a") as archive:  
            file_name = '{}.{}'.format(image_instance.source_language.language.language,format_exe)
            src_image_json=export_download(json_str=image_instance.source_canvas_json,format=file_format, multipliervalue=export_size )
            archive.writestr(file_name,src_image_json)
            for tar_json in image_instance.s_im.all():
                tar_lang=tar_json.target_language.language.language
                file_name = '{}.{}'.format(tar_lang,format_exe)
                tar_image_json=export_download(json_str=tar_json.target_canvas_json,format=file_format, multipliervalue=export_size )
                archive.writestr(file_name,tar_image_json)
        res=download_file_canvas(file_path=buffer.getvalue(),mime_type=mime_type["zip"],name="image_download"+'.zip')
        return res
    
    elif language == image_instance.source_language.id:
        img_res,file_name=create_image(image_instance.source_canvas_json,file_format,export_size,1,
                                       image_instance.source_language.language.language)
        export_src=core.files.File(core.files.base.ContentFile(img_res),file_name)
        response=download_file_canvas(export_src,mime_type[file_format.lower()],file_name)
        return response
    
    elif language and language != image_instance.source_language.id:
        tar_inst=image_instance.s_im.get(target_language__language__id=language)
        img_res,file_name=create_image(tar_inst.target_canvas_json,file_format,export_size,1,
                                       image_instance.s_im.get(target_language_id=language).target_language.language.language)
        export_src=core.files.File(core.files.base.ContentFile(img_res),file_name)
        response=download_file_canvas(export_src,mime_type[file_format.lower()],file_name)
        return response
    else:
        image_download[image_instance.source_language.language.language] =image_instance.source_language.id
        for i in image_instance.s_im.all():
            image_download[i.target_language.language.language]=i.target_language.language.id

        lang={**{"All":0},**image_download}
        resp = {"language":  lang , "page":[]}
        return Response(resp)




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
        serializer = BackgroundRemovelSerializer(query_set,many =True)
        return Response(serializer.data)

    def retrieve(self,request,pk):
        obj =self.get_object(pk)
        query_set = BackgroundRemovel.objects.get(id = pk)
        serializer = BackgroundRemovelSerializer(query_set )
        return Response(serializer.data)
        
    def create(self,request):
        # canvas_json=request.POST.get('canvas_json')
        preview_json=request.POST.get('preview_json',None)
        serializer = BackgroundRemovelSerializer(data=request.data,context={'request':request})  
        if serializer.is_valid():
            serializer.save()
            data=serializer.data
            src=data['canvas_json']['src']
            brs=data['canvas_json']['brs']
            preview_json['src']=src
            preview_json['brs']=brs
            data['preview_json']=preview_json
            return Response(data)
        else:
            return Response(serializer.errors)


# def image_download__page(pages_list,file_format,export_size,lang,projecct_file_name ):
#     if len(pages_list)==1:
#         print("single___page",pages_list[0].json)
#         img_res,file_name=create_image(pages_list[0].json,file_format,export_size,pages_list[0].page_no,lang)
#         export_src=core.files.File(core.files.base.ContentFile(img_res),file_name)
#         response=download_file_canvas(export_src,mime_type[file_format.lower()],file_name)
        
#     else:
#         print("multiple___page")
#         buffer=io.BytesIO()
#         with ZipFile(buffer, mode="a") as archive:
#             for src_json in pages_list:
#                 file_name = 'page_{}_{}.{}'.format(src_json.page_no,lang,file_format)
#                 path='{}/{}'.format(lang,file_name)
#                 # file_format = 'png' if file_format == 'png-transparent' else file_format
#                 values=export_download(src_json.json,file_format,export_size)
#                 archive.writestr(path,values)
#         response=download_file_canvas(file_path=buffer.getvalue(),mime_type=mime_type["zip"],name=projecct_file_name+'.zip')
#     return response