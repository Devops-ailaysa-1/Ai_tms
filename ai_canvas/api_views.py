from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets  ,generics
from rest_framework.response import Response
from ai_staff.models import ( Languages,LanguagesLocale,SocialMediaSize,FontFamily,FontFamily,FontLanguage,FontData)
from ai_canvas.models import (CanvasTemplates ,CanvasUserImageAssets,CanvasDesign,CanvasSourceJsonFiles,
                              CanvasTargetJsonFiles,TemplateGlobalDesign,MyTemplateDesign,
                              TemplateKeyword,TextTemplate,FontFile,SourceImageAssetsCanvasTranslate,
                              ThirdpartyImageMedium,CanvasDownloadFormat) #TemplatePage
from ai_canvas.serializers import (CanvasTemplateSerializer ,LanguagesSerializer,LocaleSerializer,
                                   CanvasUserImageAssetsSerializer,CanvasDesignSerializer,CanvasDesignListSerializer,
                                   MyTemplateDesignRetrieveSerializer,
                                   MyTemplateDesignSerializer ,
                                   TextTemplateSerializer,TemplateKeywordSerializer,FontFileSerializer,SocialMediaSizeValueSerializer,CanvasDownloadFormatSerializer,
                                   TemplateGlobalDesignSerializerV2,CategoryWiseGlobaltemplateSerializer) #TemplateGlobalDesignRetrieveSerializer,TemplateGlobalDesignSerializer
from ai_canvas.pagination import (CanvasDesignListViewsetPagination ,TemplateGlobalPagination ,MyTemplateDesignPagination)
from django.db.models import Q,F
from itertools import chain
from zipfile import ZipFile
import io
from ai_staff.serializer import FontFamilySerializer ,SocialMediaSizeSerializer
import os, urllib
from django.http import JsonResponse, Http404, HttpResponse
from rest_framework.pagination import PageNumberPagination 
from rest_framework.decorators import api_view,permission_classes
from django.conf import settings
import os ,zipfile,requests
from django.http import Http404,JsonResponse
from ai_workspace_okapi.utils import get_translation 
from ai_canvas.utils import convert_image_url_to_file,paginate_items
from ai_canvas.utils import export_download
from ai_staff.models import ImageCategories
from concurrent.futures import ThreadPoolExecutor
from django.core.paginator import Paginator
import uuid
import urllib.request
from django import core 
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
HOST_NAME=os.getenv("HOST_NAME")
 

free_pix_api_key = os.getenv('FREE_PIK_API')
pixa_bay_api_key =  os.getenv('PIXA_BAY_API')

pixa_bay_url='https://pixabay.com/api/'  
pixa_bay_headers={
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    }


params = {
            'key':pixa_bay_api_key,
            'order':'popular',
            'image_type':'photo+illustration',
            'orientation':'all',
            'per_page':10,
            'safesearch':True
        }


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
        queryset = CanvasTemplates.objects.all().order_by('-id')
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


def image_check(image_path):
    if image_path.endswith(".svg"):
        return False
    else:
        return True

class CanvasUserImageAssetsViewsetList(viewsets.ViewSet,PageNumberPagination):
    permission_classes = [IsAuthenticated,]
    page_size=20
    
    def list(self, request):
        ids=[canvas_in.id for canvas_in in CanvasUserImageAssets.objects.filter(user=request.user.id) if image_check(canvas_in.image.path)]
        queryset=CanvasUserImageAssets.objects.filter(id__in=ids)
        # queryset = CanvasUserImageAssets.objects.filter(user=request.user.id).order_by('-id')
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = CanvasUserImageAssetsSerializer(pagin_tc,many=True)
        response = self.get_paginated_response(serializer.data)
        return response


 
class CanvasUserImageAssetsViewset(viewsets.ViewSet,PageNumberPagination):
    permission_classes = [IsAuthenticated,]
    page_size=20
    search_fields =['image_name']

    def get_object(self, pk):
        try:
            return CanvasUserImageAssets.objects.get(id=pk)
        except CanvasUserImageAssets.DoesNotExist:
            raise Http404

    def create(self,request):
        image = request.FILES.get('image')
        if image and str(image).split('.')[-1] not in ['svg', 'png', 'jpeg', 'jpg']:
            return Response({'msg':'only .svg, .png, .jpeg, .jpg suppported file'},status=400)
        serializer = CanvasUserImageAssetsSerializer(data={**request.POST.dict(),'image':image},context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
    
    def list(self, request):
        queryset = CanvasUserImageAssets.objects.filter(user=request.user.id).order_by('-id')
        queryset = self.filter_queryset(queryset)
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = CanvasUserImageAssetsSerializer(pagin_tc,many=True)
        response = self.get_paginated_response(serializer.data)
        return response
    
    def filter_queryset(self, queryset):
        filter_backends = (DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter )
        for backend in list(filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        return queryset
    
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
        queryset = CanvasDesign.objects.filter(user=request.user.id)
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
        
class CustomPagination(PageNumberPagination):
    page_size = 20 
    page_size_query_param = 'page_size'



 

class CanvasDesignListViewset(viewsets.ViewSet,CustomPagination):
    pagination_class = CanvasDesignListViewsetPagination
    permission_classes = [IsAuthenticated,]
    search_fields =['file_name',"canvas_translate__target_language__language__language","canvas_translate__source_language__language__language"]
    filter_backends = [DjangoFilterBackend]

    def list(self,request):
        queryset = CanvasDesign.objects.filter(user=request.user.id).order_by('-updated_at')
        queryset = self.filter_queryset(queryset)
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = CanvasDesignListSerializer(pagin_tc,many=True)
        response = self.get_paginated_response(serializer.data)
        return response
    
    def filter_queryset(self, queryset):
        filter_backends = (DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter )
        for backend in list(filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        return queryset
    
    # def get_queryset(self):
    #     queryset = super().get_queryset()
    #     search = self.request.query_params.get('search')
    #     if search:
    #         queryset = queryset.filter(file_name__icontains=search) \
    #             # | queryset.filter(canvas_translate__source_language__language__language=search) | \
    #                     # queryset.filter(canvas_translate__target_language__language__language=search)
    #     return queryset


# class TemplateGlobalDesignViewset(viewsets.ViewSet ,PageNumberPagination):
#     pagination_class = TemplateGlobalPagination 
#     permission_classes = [IsAuthenticated,]
#     def list(self,request):
#         queryset = TemplateGlobalDesign.objects.all().order_by('-updated_at')
#         pagin_tc = self.paginate_queryset(queryset, request , view=self)
#         serializer = TemplateGlobalDesignSerializer(pagin_tc,many=True)
#         response = self.get_paginated_response(serializer.data)
#         return response
    
#     def create(self,request):
#         thumbnail_page = request.FILES.get('thumbnail_page')
#         export_page = request.FILES.get('export_page')
#         serializer = TemplateGlobalDesignSerializer(data = request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors)
    
#     def update(self,request,pk):
#         thumbnail_page = request.FILES.get('thumbnail_page')
#         export_page = request.FILES.get('export_page')
#         queryset = TemplateGlobalDesign.objects.get(id=pk)
#         serializer = TemplateGlobalDesignSerializer(queryset ,data=request.data,partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors,status=400)
    
#     def get(self,request,pk):
#         queryset = TemplateGlobalDesign.objects.get(id=pk)
#         serializer = TemplateGlobalDesignSerializer(queryset)
#         return Response(serializer.data)
    
#     def destroy(self,request,pk):
#         page_no = request.query_params.get('page_no',None)
#         try:
#             if page_no:
#                 temp_design = TemplateGlobalDesign.objects.get(id=pk)
#                 TemplatePage.objects.get(template_page=temp_design,page_no=page_no).delete()
#             else:
#                 TemplateGlobalDesign.objects.get(id=pk).delete()
#             return Response({'msg':'deleted'})
#         except:
#             print("error in del")
#             return Response({'msg':'template Does not exist'})


# class TemplateGlobalDesignRetrieveViewset(generics.RetrieveAPIView):
#     queryset = TemplateGlobalDesign.objects.all()
#     serializer_class = TemplateGlobalDesignRetrieveSerializer
#     lookup_field = 'id'


class MyTemplateDesignViewset(viewsets.ViewSet ,PageNumberPagination):
    pagination_class = MyTemplateDesignPagination
    page_size = 20
    permission_classes = [IsAuthenticated,]
    search_fields =['file_name',]

    def list(self,request):
        queryset = MyTemplateDesign.objects.filter(user=request.user.id).order_by('-id')
        queryset = self.filter_queryset(queryset)
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = MyTemplateDesignSerializer(pagin_tc,many=True)
        response = self.get_paginated_response(serializer.data)
        return response
    
    def create(self,request):
        template_global_id = request.POST.get('template_global_id')
        serializer = MyTemplateDesignSerializer(data =request.data , context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
    
    def filter_queryset(self, queryset):
        filter_backends = (DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter )
        for backend in list(filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        return queryset   
    
    def destroy(self,request,pk):
        MyTemplateDesign.objects.get(id=pk).delete()
        return Response({'msg':'deleted'})
    

class MyTemplateDesignRetrieveViewset(generics.RetrieveAPIView):
    queryset = MyTemplateDesign.objects.all().order_by("-id")
    serializer_class = MyTemplateDesignRetrieveSerializer
    lookup_field = 'id'



class CanvasDownloadFormatViewset(viewsets.ViewSet):
    def list(self,request):
        queryset = CanvasDownloadFormat.objects.all()
        serializer = CanvasDownloadFormatSerializer(queryset,many=True)
        return Response(serializer.data)

######################################################canvas______download################################







# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def canvas_export_download(request):
#     format=request.POST.get('format')
#     multipliervalue=request.POST.get('multipliervalue')
#     canvas_design_id=request.POST.get('canvas_design_id')
#     can_des=CanvasDesign.objects.get(id=canvas_design_id)
#     file_path=f'{settings.MEDIA_ROOT}/{can_des.user.uid}/temp_download/'
#     try:
#         os.makedirs(file_path) #{design.file_name}
#     except FileExistsError:
#         pass
#     zip_path = f'{file_path}{can_des.file_name}.zip'
 
    
#     with zipfile.ZipFile(zip_path, 'w') as zipf:
#         can_src=can_des.canvas_json_src.all()
#         for src_json_file in can_src:
#             print("src_json_file---> CanvasSourceJsonFiles")
#             src_json=can_des.canvas_translate.all()
#             if src_json_file.json:
#                 compressed_data_img=export_download(json_str=src_json_file.json,format=format,multipliervalue=multipliervalue)
#                 src_lang=src_json[0].source_language.language_locale_name.strip() if src_json[0] else can_des.file_name
 
#                 src_file_name=src_lang+'.{}'.format(format)
#                 zipf.writestr(src_file_name, compressed_data_img)
#             if src_json:
#                 zipf.write(file_path, 'source_target/' , zipfile.ZIP_DEFLATED )
#                 for j in src_json:
#                     form=".{}".format(format)
#                     print("src_json",j.source_language,'---',j.target_language)
#                     if j.canvas_json_tar.last():
#                         tar_json_file=j.canvas_json_tar.last()
#                         if tar_json_file:
#                             compressed_data_img=export_download(json_str=tar_json_file.json,format=format,multipliervalue=multipliervalue)
#                             zipf.writestr('source_target/'+j.target_language.language_locale_name.strip()+form, compressed_data_img)
                        
#         download_path = f'{settings.MEDIA_URL}{can_des.user.uid}/temp_download/{can_des.file_name}.zip'
#     return JsonResponse({"url":download_path},status=200)                


# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def canvas_download(request):
#     ## need to add authorization for requested user
#     design_id = request.GET.get('design_id')
#     canvas_translation_id = request.GET.get('canvas_translation_id',None)
#     design = CanvasDesign.objects.get(id=design_id)
#     zip_path = f'{settings.MEDIA_ROOT}/temp/{design.file_name}.zip'
#     with zipfile.ZipFile(zip_path, 'w') as zipf:
#         ## Getting Source
#         json_src = design.canvas_json_src.all()
#         src_lang_code=design.canvas_translate.first().source_language.locale_code
#         for src in json_src :
#             if canvas_translation_id:
#                 break
#             try:
#                 source_path = src.thumbnail.path
#             except:
#                 print("no thumbnail",src.id)
#             name = os.path.basename(src.thumbnail.name)
#             destination = f"/source/{name}" 
#             zipf.write(source_path, destination)

#         ## Getting Translated
#         if canvas_translation_id:
#             json_tranlated = design.canvas_translate.filter(id=canvas_translation_id)
#         else:
#             json_tranlated = design.canvas_translate.all()

#         for tar_json in json_tranlated:
#             tar_pages= tar_json.canvas_json_tar.all()
#             tar_lang_code = tar_json.target_language.locale_code
#             for tar in tar_pages :
#                 try:
#                     source_path = tar.thumbnail.path
#                 except:
#                     print("no thumbnail",tar.id)
#                 name = os.path.basename(tar.thumbnail.name)
#                 destination = f"/{tar_lang_code}/{name}"
#                 zipf.write(source_path, destination)
#         download_path = f'{settings.MEDIA_URL}temp/{design.file_name}.zip'
#     return JsonResponse({"url":download_path},status=200)


#########################################################################################################################################




mime_type={'svg':'image/svg+xml',
        'png':'image/png',
        'jpeg':'image/jpeg',
        'jpg':'image/jpeg',
        'zip':'application/zip',
        'png-transparent':'image/png',
        'pdf':'application/pdf'}

def download_file_canvas(file_path,mime_type,name):
    print(mime_type)
    response = HttpResponse(file_path, content_type=mime_type)
    response['Content-Disposition'] = 'attachment;filename*=UTF-8\'\'{}'.format(name)
    response['X-Suggested-Filename'] = name
    #response['Content-Disposition'] = "attachment; filename=%s" % filename
    response['Access-Control-Expose-Headers'] = 'Content-Disposition'
    return response



# @api_view(["GET"])
# @permission_classes([IsAuthenticated])
# def canvas_download_combine(request):
#     design_id = request.query_params.get('design_id')
#     file_format_id=request.query_params.get('file_format_id')
#     export_size=request.query_params.get('export_size')
#     select_language=request.query_params.get('select_language')
#     page=request.query_params.get('page')
#     src_id=request.query_params.get('src_id')
#     file_format=CanvasDownloadFormat.get(id=file_format_id).format_name
#     canvas_inst=CanvasDesign.objects.get(id=design_id)
#     if src_id:
 
#         src__single_inst=canvas_inst.canvas_json_src.get(id=src_id)
#         src_lang_name=canvas_inst.canvas_translate.last().source_language.locale_code
#         if src__single_inst.json:
#             print("contains src__json")
#             if file_format=='png':
 
#                 values=export_download(src__single_inst.json,file_format,export_size)
#                 img_res=download_file_canvas(file_path=values,mime_type=mime_type[file_format],name=src_lang_name+'.'+file_format)
#                 return img_res
                # thumbnail_src=core.files.File(core.files.base.ContentFile(values),src_lang_name+'.'+file_format)



#####################
####free_____pix

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def free_pix_api(request):
    # subject_search= request.POST.get('subject_search')
    # page_no = request.POST.get('page_no')
    url = "https://api.freepik.com/v1/resources"
    headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
    'Accept-Language': 'en-GB',
    'X-Freepik-API-Key': free_pix_api_key,
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    }
    response = requests.get(url, params=request.GET.dict(),headers=headers)
    print(response.json())
    if response.status_code == 200:
        return Response(response.json(),status=200)
    else:
        return Response({'error':'something went wrong'},status=response.status_code)


################################################################


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pixabay_api(request):
    params = {**request.GET.dict(),'key':pixa_bay_api_key} 
    response = requests.get(pixa_bay_url, params=params,headers=pixa_bay_headers)
    if response.status_code == 200:
        return Response(response.json(),status=200)
    else:
        return Response({'error':'something went wrong'},status=response.status_code)
    

#################################################################

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def instant_canvas_translation(request):
    text_list = request.POST.getlist('text')
    src_lang_id = request.POST.get('src_lang_id',None)
    tar_lang_id = request.POST.get('tar_lang_id')
    if src_lang_id:
        src_lang_code = Languages.objects.get(id=src_lang_id).locale.first().locale_code
    tar_lang_code = Languages.objects.get(id=tar_lang_id).locale.first().locale_code
    text_translation = get_translation(1,text_list,'en',tar_lang_code)
    return Response({'translated_text_list':text_translation})

##################################


class TextTemplateViewset(viewsets.ViewSet,PageNumberPagination):
    permission_classes = [IsAuthenticated,]
    page_size = 20
    search_fields = ['txt_temp__text_keywords']
    def list(self, request):
        queryset=TextTemplate.objects.all()
        queryset = self.filter_queryset(queryset)
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer=TextTemplateSerializer(pagin_tc ,many =True)
        response = self.get_paginated_response(serializer.data)
        if response.data["next"]:
            response.data["next"] = response.data["next"].replace("http://", "https://")
        if response.data["previous"]:
                response.data["previous"] = response.data["previous"].replace("http://", "https://")
        return response

    def retrieve(self,request,pk):
        query_set=TextTemplate.objects.get(id = pk)
        serializer=TextTemplateSerializer(query_set )
        return Response(serializer.data)
        
    def create(self,request):
        text_thumbnail=request.FILES.get('text_thumbnail',None)
        text_keywords=request.POST.getlist('text_keywords',None)
        serializer=TextTemplateSerializer(data=request.data)
                                        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)
        
    def filter_queryset(self, queryset):
        filter_backends = (DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter )
        for backend in list(filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        return queryset 
    
    def update(self,request,pk):
        query_set=TextTemplate.objects.get(id = pk)
        text_thumbnail=request.FILES.get('text_thumbnail',None)
        text_keywords=request.POST.getlist('text_keywords',None)
        serializer=TextTemplateSerializer(query_set, data=request.data ,partial = True)
                                # 'text_keywords':text_keywords , 'text_thumbnail':text_thumbnail },partial = True)
        if serializer.is_valid():
            serializer.save()
            # print(serializer.data)
            return Response(serializer.data)
        else:
            return Response(serializer.errors)
            
    def delete(self,request,pk):
        query_set=TextTemplate.objects.get(id = pk)
        query_set.delete()
        return Response(status=204)
        
class TemplateKeywordViewset(viewsets.ViewSet):
    permission_classes=[IsAuthenticated,]
    def get(self,request):
        query_set=TemplateKeyword.objects.all()
        serializer=TemplateKeywordSerializer(query_set ,many =True)
        return Response(serializer.data) 
    

class FontFileViewset(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,]
    def get(self, request):
        query_set=FontFile.objects.filter(user=request.user.id)
        serializer=FontFileSerializer(query_set ,many =True)
        return Response(serializer.data)

    def retrieve(self,request,pk):
        query_set=FontFile.objects.get(id = pk)
        serializer=FontFileSerializer(query_set )
        return Response(serializer.data)
        
    def create(self,request):
        font_file=request.FILES.get('font_file',None)
        print({**request.POST.dict(),'font_family':font_file})
        serializer=FontFileSerializer(data={**request.POST.dict(),'font_family':font_file,'user':request.user.id})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)
        
    def update(self,request,pk):
        font_file=request.FILES.get('font_file',None)
        query_set=FontFile.objects.get(id=pk)
        serializer=FontFileSerializer(query_set,data=request.data,partial=True)                           
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)
        
    def delete(self,request,pk):
        query_set=FontFile.objects.get(id=pk)
        query_set.delete()
        return Response(status=204)




     
import django_filters

class FontFamilyFilter(django_filters.FilterSet):
    font_search = django_filters.CharFilter(field_name='font_family_name', label='renamed_field')

    class Meta:
        model = FontFamily
        fields= ['font_family_name']
            
    def filter_queryset(self,queryset):
        queryset=queryset.filter(font_family_name__icontains=self.data['font_search'])
        print("queryset---->",queryset)
        return queryset
 
 
class FontFamilyViewset(viewsets.ViewSet,PageNumberPagination):
    pagination_class = CustomPagination
    page_size = 20


    def lang_fil(self,request):
        f_lang=FontLanguage.objects.get(id=request.GET['language'])
        f_d=FontData.objects.filter(font_lang=f_lang)
        queryset=f_d.annotate(font_family_name=F('font_family__font_family_name'))#.values("font_family_name")
        return queryset
    
    def list(self, request):
        font_search=request.query_params.get('font_search',None)
        language=request.query_params.get('language',None)
        queryset = FontFamily.objects.all().exclude(Q(font_family_name__icontains='material')|Q(font_family_name__icontains='barcode')).order_by('font_family_name')
        
        if font_search and language:
            queryset=self.lang_fil(request)            
            filters = FontFamilyFilter(request.GET, queryset=queryset)
            queryset = filters.qs
        
        elif font_search:
            queryset=queryset.filter(Q(font_family_name__icontains=font_search)).order_by('font_family_name')

        elif language:
            queryset=self.lang_fil(request)
        else:
            font_file=FontFile.objects.filter(user=request.user)
            

            if font_file:
                font_file=font_file.annotate(font_family_name=F("name"))#.values("font_family_name")
                # print([{**item, 'user': True} for item in font_file])
                # queryset=queryset.values("font_family_name")
                # print([{**item, 'user': True} for item in queryset])
                queryset=list(chain(font_file, queryset))
                

        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        
        serializer = FontFamilySerializer(pagin_tc,many=True)
        response = self.get_paginated_response(serializer.data)
        if response.data["next"]:
            response.data["next"] = response.data["next"].replace("http://", "https://")
        if response.data["previous"]:
                response.data["previous"] = response.data["previous"].replace("http://", "https://")
        return response
    

class SocialMediaSizeValueViewset(viewsets.ViewSet):
    def list(self,request):
        queryset = SocialMediaSize.objects.all().exclude(social_media_name__icontains='Custom Size').order_by('social_media_name')
        serializer=SocialMediaSizeValueSerializer(queryset,many=True)
        return Response(serializer.data)

class SocialMediaSizeCustom(viewsets.ViewSet):
    def list(self,request):
        queryset = SocialMediaSize.objects.filter(social_media_name='Custom Size')[0]
        serializer=SocialMediaSizeValueSerializer(queryset)
        return Response(serializer.data)
     


class SocialMediaSizeViewset(viewsets.ViewSet,PageNumberPagination):
    pagination_class = CustomPagination
    def list(self,request):
        queryset = SocialMediaSize.objects.all().exclude(social_media_name__icontains='Custom').order_by('social_media_name')
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = SocialMediaSizeSerializer(pagin_tc,many=True)
        response = self.get_paginated_response(serializer.data)
        if response.data["next"]:
            response.data["next"] = response.data["next"].replace("http://", "https://")
        if response.data["previous"]:
                response.data["previous"] = response.data["previous"].replace("http://", "https://")
        return response
    
    def create(self,request):
        src=request.FILES.get('src',None)
        serializer=SocialMediaSizeSerializer(data={**request.POST.dict(),'src':src})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

    def update(self,request,pk):
        src=request.FILES.get('src',None)
        query_set=SocialMediaSize.objects.get(id=pk)
        serializer=SocialMediaSizeSerializer(query_set,data={**request.POST.dict(),'src':src},partial=True)                           
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)
        
    def delete(self,request,pk):
        query_set=SocialMediaSize.objects.get(id=pk)
        query_set.delete()
        return Response(status=204)
 

def req_thread(category=None,page=None,search=None):
    if category and search and page:
        params['q']=search
        params['page']=page
        params['per_page']=20
        params['catagory']=str(category).lower()
        pixa_bay = requests.get(pixa_bay_url, params=params,headers=pixa_bay_headers)
        if pixa_bay.status_code==200:
            return pixa_bay.json()
        return []
    if category:
        params['q']=category
        params['catagory']=category
        params['safesearch']=True
    if page:
        params['page']=page
        params['per_page']=20
        params['safesearch']=True
    if search:
        params['q']=search
        params['safesearch']=True
    if category and search:
        params['catagory']=category
        params['q']=search
        params['safesearch']=True
    pixa_bay = requests.get(pixa_bay_url, params=params,headers=pixa_bay_headers)
    if pixa_bay.status_code==200:
        return pixa_bay.json()
    else:
        return []

def pixa_image_url(image_url):
    opener=urllib.request.build_opener()
    opener.addheaders=[('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
    urllib.request.install_opener(opener)
    im =urllib.request.urlopen(image_url).read()
    image_file =core.files.File(core.files.base.ContentFile(im),str(uuid.uuid1())+'.'+image_url.split('/')[-1].split('.')[-1])
    return image_file


def all_cat_req(category):
    params = {'key':pixa_bay_api_key,'order':'popular','image_type':'photo',
            'orientation':'all','per_page':10,'safesearch':True}
    params['q']=category
    params['catagory']=str(category).lower()
    pixa_bay = requests.get(pixa_bay_url, params=params,headers=pixa_bay_headers) 
    print("pixa_bay",pixa_bay)
    print("pixa_bay",pixa_bay.status_code)
    return pixa_bay.json()

def process_pixabay(**kwargs):
    data=[]
    if 'image_cats' in kwargs.keys() and 'results' in kwargs.keys():
        for hit,image_cat in zip(kwargs['results'],kwargs['image_cats']):
            img_urls=[]
            for j in hit['hits']:
                img_urls.append({'preview_img':j['previewURL'],'id':j['id'],'tags':j['tags'], 'type':j['type'],'user':j['user'],'imageurl':j['fullHDURL']})
            data.append({'category':image_cat,'images':img_urls})
        return data
    if 'image_cat_see_all' in kwargs.keys():
        total_page=kwargs['image_cat_see_all']['total']//20
        for j in kwargs['image_cat_see_all']['hits']:
            data.append({'preview_img':j['previewURL'],'id':j['id'],'tags':j['tags'],'type':j['type'],'user':j['user'],'imageurl':j['fullHDURL']})
        return data,total_page

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def image_list(request):
    image_category_name=request.query_params.get('image_category_name')
    page=request.query_params.get('page')
    image_url=request.query_params.get('image_url')
    search_image=request.query_params.get('search_image')

    if image_category_name and search_image and page:
 
        page=int(page)
        image_cat_see_all=req_thread(category=image_category_name,search=search_image,page=page)

        if not image_cat_see_all:
            return Response({'image_list':[],'has_next':False},status=200)
        res,total_page=process_pixabay(image_cat_see_all=image_cat_see_all)

        has_next=False if int(total_page)==page else True
        has_prev=False if page==1 else True
        
        return Response({ 'has_next':has_next,'page':page,'has_prev':has_prev ,'image_category_name':image_category_name ,
                         'image_list':res,'total_page':total_page},status=200)

    if search_image and page:
 
        page=int(page)
        res=req_thread(search=search_image,page=page)
        if not res:
            return Response({'image_list':res,'has_next':False},status=200)
        res,total_page=process_pixabay(image_cat_see_all=res)
        has_next=False if int(total_page)==page else True
        has_prev=False if page==1 else True
        return Response({'has_next':has_next,'page':page,'has_prev':has_prev , 
                         'result_for':search_image , 'image_list':res,'total_page':total_page},status=200)

    if image_category_name and page:
 
        page=int(page)
        image_cat_see_all=req_thread(category=image_category_name,page=page)
        if not image_cat_see_all:
            return Response({'image_list':[],'has_next':False},status=200)
        res,total_page=process_pixabay(image_cat_see_all=image_cat_see_all)

        has_next=False if int(total_page)==page else True
        has_prev=False if page==1 else True
        return Response({ 'has_next':has_next,'page':page,'has_prev':has_prev ,'image_category_name':image_category_name ,
                         'image_list':res,'total_page':total_page},status=200)

    if image_url:
        image_file=pixa_image_url(image_url)
        src_img_assets_can = ThirdpartyImageMedium.objects.create(image=image_file)
        return Response({'image_url':HOST_NAME+src_img_assets_can.image.url},status=200)
    


    # itm_pr_pge=6
    image_cats=list(ImageCategories.objects.all().values_list('category',flat=True))
    # image_cats=paginate_items(image_cats,page,itm_pr_pge)[0]
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(all_cat_req,image_cats))

 
    data=process_pixabay(results=results,image_cats=image_cats)
    paginate=Paginator(data,6)  ###no of item in single page
    fin_dat=paginate.get_page(page)
    return Response({'total_page':paginate.num_pages ,'count':paginate.count,'has_next': fin_dat.has_next(),
                    'has_prev': fin_dat.has_previous(),'page': fin_dat.number,'image_list':fin_dat.object_list })

            

class TemplateGlobalDesignViewsetV2(viewsets.ViewSet,PageNumberPagination):
    permission_classes = [IsAuthenticated,]
    pagination_class = CustomPagination
    page_size = 20
    def create(self,request):
        serializer=TemplateGlobalDesignSerializerV2(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors)
        
    def list(self,request):
        queryset = TemplateGlobalDesign.objects.all().order_by("-id") #.values('template_name','category','thumbnail_page','template_lang','height','width')
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer=TemplateGlobalDesignSerializerV2(pagin_tc,many=True)
        response = self.get_paginated_response(serializer.data)
        if response.data["next"]:
            response.data["next"] = response.data["next"].replace("http://", "https://")
        if response.data["previous"]:
                response.data["previous"] = response.data["previous"].replace("http://", "https://")
        return response
    

    def retrieve(self,request,pk):
        query_set=TemplateGlobalDesign.objects.get(id = pk)
        serializer=TemplateGlobalDesignSerializerV2(query_set )
        return Response(serializer.data)
    
 
class CategoryWiseGlobaltemplateViewset(viewsets.ViewSet,PageNumberPagination):
    permission_classes = [IsAuthenticated,]
    pagination_class = CustomPagination
    page_size = 20
    filter_backends = [DjangoFilterBackend]
 
    search_fields =['category__template_name','social_media_name','category__description','category__template_lang__language',
                    'category__template_global_page__tag_name']


    def list(self,request):
        social_media_name_id=request.query_params.get('social_media_name_id',None)
        if social_media_name_id:
            queryset = SocialMediaSize.objects.filter(id=social_media_name_id)
        else:
            queryset = SocialMediaSize.objects.all().order_by("social_media_name") 
        queryset = self.filter_queryset(queryset)
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer=CategoryWiseGlobaltemplateSerializer(pagin_tc,many=True)
        response = self.get_paginated_response(serializer.data)
        if response.data["next"]:
            response.data["next"] = response.data["next"].replace("http://", "https://")
        if response.data["previous"]:
                response.data["previous"] = response.data["previous"].replace("http://", "https://")
        return response
    
    def filter_queryset(self, queryset):
        filter_backends = (DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter )
        for backend in list(filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        return queryset
    
    def destroy(self,request,pk):
        TemplateGlobalDesign.objects.get(id=pk).delete()
        return Response({'msg':'deleted successfully'})
    
def create_image(json_page,file_format,export_size,page_number,language):
    format = 'png' if file_format == 'png-transparent' else file_format
    base64_img=export_download(json_page,file_format,export_size)
    file_name="page_{}_{}.{}".format(str(page_number),language,format)
    return base64_img,file_name


def download__page(pages_list,file_format,export_size,page_number_list,lang,projecct_file_name ):
    if len(pages_list)==1:
        print("single___page",pages_list[0].json)
        img_res,file_name=create_image(pages_list[0].json,file_format,export_size,pages_list[0].page_no,lang)
        export_src=core.files.File(core.files.base.ContentFile(img_res),file_name)
        response=download_file_canvas(export_src,mime_type[file_format.lower()],file_name)
        
    else:
        print("multiple___page")
        buffer=io.BytesIO()
        with zipfile.ZipFile(buffer, mode="a") as archive:
            for src_json in pages_list:
                file_name = 'page_{}_{}.{}'.format(src_json.page_no,lang,file_format)
                path='{}/{}'.format(lang,file_name)
                file_format = 'png' if file_format == 'png-transparent' else file_format
                values=export_download(src_json.json,file_format,export_size)
                archive.writestr(path,values)
        response=download_file_canvas(file_path=buffer.getvalue(),mime_type=mime_type["zip"],name=projecct_file_name+'.zip')
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def DesignerDownload(request):
    canvas_id=request.query_params.get('canvas_id')
    file_format=request.query_params.get('file_format')
    language=request.query_params.get('language',0)
    page_number_list=request.query_params.getlist('page_number_list',None) 
    export_size=request.query_params.get('export_size',1)
    all_page=request.query_params.get('all_page',False)
    language = int(language) if language else None
    canvas=CanvasDesign.objects.get(id=canvas_id)
    page_number_list=list(map(int,page_number_list)) if page_number_list else None
    page_src=[]
    file_format = file_format.replace(" ","-") if file_format else ""
    canvas_src_json=canvas.canvas_json_src.all()
    if any(canvas.canvas_translate.all()):
        canvas_trans_inst=canvas.canvas_translate.all()
        src_lang=canvas_trans_inst[0].source_language.language.language
        src_code=canvas_trans_inst[0].source_language.language_id
        
        if language==0: #all languages with number of pages
            src_jsons=canvas.canvas_json_src.filter(page_no__in=page_number_list)
            buffer=io.BytesIO()
            print("all languages with number of pages")
            with zipfile.ZipFile(buffer, mode="a") as archive:
                for src_json in src_jsons:
                    format = 'png' if file_format == 'png-transparent' else file_format
                    file_name = 'page_{}_{}.{}'.format(src_json.page_no,src_lang,format)
                    path='{}/{}'.format(src_lang,file_name)
                    values=export_download(src_json.json,file_format,export_size)
                    archive.writestr(path,values)
                for tar_lang in canvas_trans_inst:
                    tar_jsons=canvas_trans_inst.get(target_language=tar_lang.target_language).canvas_json_tar.filter(page_no__in=page_number_list)
                    for tar_json in tar_jsons:
                        values=export_download(tar_json.json,file_format,export_size)
                        format = 'png' if file_format == 'png-transparent' else file_format
                        file_name='page_{}_{}.{}'.format(tar_json.page_no,tar_lang.target_language.language,format)
                        path='{}/{}'.format(tar_lang.target_language.language,file_name)
                        archive.writestr(path,values)
            res=download_file_canvas(file_path=buffer.getvalue(),mime_type=mime_type["zip"],name=canvas.file_name+'.zip')
            return res

        if language==src_code:
            src_pages=canvas_src_json if all_page else canvas.canvas_json_src.filter(page_no__in=page_number_list)
            res=download__page(src_pages,file_format,export_size,page_number_list,src_lang,canvas.file_name )
            return res

        elif language and language!=src_code:
            canvas_translate=canvas.canvas_translate.all()
            tar_pages=canvas_translate.get(target_language__language__id=language).canvas_json_tar.filter(page_no__in=page_number_list)
            tar_lang=Languages.objects.get(id=language).language
            res=download__page(tar_pages,file_format,export_size,page_number_list,tar_lang,canvas.file_name )
            return res

        else:
            tar_lang={}
            for i in canvas_src_json:
                page_src.append(i.page_no)
            for j in canvas.canvas_translate.all():
                tar_lang[j.target_language.language.language]=j.target_language.language_id

            lang={**{"All":0},**{src_lang:src_code}}
            resp = {"language":  {**lang,**tar_lang}, "page":page_src}
            return Response(resp)
    
    elif (page_number_list or all_page) and file_format:
        src_pages=canvas_src_json if all_page else canvas.canvas_json_src.filter(page_no__in=page_number_list)
        res=download__page(src_pages,file_format,export_size,page_number_list,"source",canvas.file_name)
        return res
    else:
        return Response({"page":list(canvas.canvas_json_src.all().values_list("page_no",flat=True))})
        