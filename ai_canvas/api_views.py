from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets  ,generics
from rest_framework.response import Response
from ai_staff.models import ( Languages,LanguagesLocale,SocialMediaSize,FontFamily,FontFamily,FontLanguage,FontData,ImageCategories,DesignShape,DesignShapeCategory)
from ai_canvas.models import (CanvasTemplates ,CanvasUserImageAssets,CanvasDesign,CanvasSourceJsonFiles,
                              CanvasTargetJsonFiles,TemplateGlobalDesign,MyTemplateDesign,
                              TemplateKeyword,TextTemplate,FontFile,SourceImageAssetsCanvasTranslate,
                              ThirdpartyImageMedium,CanvasDownloadFormat,EmojiCategory,EmojiData,AiAssertscategory,AssetImage,AssetCategory)
                            #   PromptCategory,PromptEngine,TemplateBackground) #TemplatePage
from ai_staff.serializer import ImageCategoriesSerializer,DesignShapeCategoryserializer,DesignShapeSerializer
from ai_canvas.serializers import (CanvasTemplateSerializer ,LanguagesSerializer,LocaleSerializer,
                                   CanvasUserImageAssetsSerializer,CanvasDesignSerializer,CanvasDesignListSerializer,
                                   MyTemplateDesignRetrieveSerializer,
                                   MyTemplateDesignSerializer ,AssetCategorySerializer,
                                   TextTemplateSerializer,TemplateKeywordSerializer,FontFileSerializer,SocialMediaSizeValueSerializer,CanvasDownloadFormatSerializer,
                                   TemplateGlobalDesignSerializerV2,CategoryWiseGlobaltemplateSerializer,
                                   EmojiCategorySerializer,EmojiDataSerializer,TemplateGlobalDesignSerializer,
                                   CanvasTargetJsonSerializer,CanvasSourceJsonFilesSerializer,AiAssertsSerializer,
                                   AiAssertscategoryserializer,AssetImageSerializer)
                                #    PromptCategoryserializer) #TemplateGlobalDesignRetrieveSerializer,TemplateGlobalDesignSerializer
from ai_canvas.pagination import (CanvasDesignListViewsetPagination ,TemplateGlobalPagination ,MyTemplateDesignPagination)
from django.db.models import Q,F
from itertools import chain
from zipfile import ZipFile
import io
import django_filters
from ai_staff.serializer import FontFamilySerializer ,SocialMediaSizeSerializer
import os, urllib
from django.http import JsonResponse, Http404, HttpResponse
from rest_framework.pagination import PageNumberPagination 
from rest_framework.decorators import api_view,permission_classes
from django.conf import settings
import os ,zipfile,requests
from django.http import Http404,JsonResponse
from ai_workspace_okapi.utils import get_translation 
from ai_canvas.utils import convert_image_url_to_file,paginate_items ,export_download
from ai_staff.models import ImageCategories
from concurrent.futures import ThreadPoolExecutor
from django.core.paginator import Paginator
import uuid
import urllib.request
from django import core 
from rest_framework import filters ,serializers
from django_filters.rest_framework import DjangoFilterBackend
HOST_NAME=os.getenv("HOST_NAME")
from django.shortcuts import get_object_or_404
import json
from django.core.exceptions import ValidationError
IMAGE_THUMBNAIL_CREATE_URL =  os.getenv("IMAGE_THUMBNAIL_CREATE_URL")
from ai_imagetranslation.models import StableDiffusionAPI
from ai_imagetranslation.utils import stable_diffusion_public
from ai_imagetranslation.serializer import StableDiffusionAPISerializer
import random
from ai_staff.models import FontFamily,FontData
import base64
from ai_staff.serializer import DesignShapeSerializer
from ai_staff.models import DesignShape
# HOST_NAME="http://0.0.0.0:8091"

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
            'safesearch': "true"
        }





class LanguagesViewset(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,]
    
    def list(self, request):
        queryset = Languages.objects.all().order_by('language')
        serializer = LanguagesSerializer(queryset,many=True)
        return Response(serializer.data)

class LanguagesLocaleViewset(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,]
    
    def list(self, request):
        queryset = LanguagesLocale.objects.all()
        serializer = LocaleSerializer(queryset,many=True)
        return Response(serializer.data)

######viewed by all#############
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
            obj = CanvasTemplates.objects.get(user=request.user,id=pk)
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
        user = request.user.team.owner if request.user.team else request.user
        ids=[canvas_in.id for canvas_in in CanvasUserImageAssets.objects.filter(user=user) if image_check(canvas_in.image.path)]
        queryset=CanvasUserImageAssets.objects.filter(id__in=ids).order_by("-id")
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
            user = self.request.user.team.owner if self.request.user.team else self.request.user
            return CanvasUserImageAssets.objects.get(user,id=pk)
        except CanvasUserImageAssets.DoesNotExist:
            raise Http404

    def create(self,request):
        image = request.FILES.get('image')
        user = request.user.team.owner if request.user.team else request.user
        if image and str(image).split('.')[-1] not in ['svg', 'png', 'jpeg', 'jpg','avif']:
            return Response({'msg':'only .svg, .png, .jpeg, .jpg suppported file'},status=400)
        serializer = CanvasUserImageAssetsSerializer(data={**request.POST.dict(),'image':image},context={'request':request,'user':user,'created_by':request.user})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
    
    def list(self, request):
        user = request.user.team.owner if request.user.team else request.user
        queryset = CanvasUserImageAssets.objects.filter(user=user).order_by('-id')
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
            user = request.user.team.owner if request.user.team else request.user
            obj = CanvasUserImageAssets.objects.get(user=user,id=pk)
            obj.delete()
            return Response({'msg':'deleted successfully'},status=200)
        except:
            return Response({'msg':'deletion unsuccessfull'},status=400)
        


###########################################################################
import copy
def page_no_update(can_page,is_update,page_len):
    if can_page:
        for i in can_page:
            src_json=copy.deepcopy(i.json)
            if is_update:
                updated_page_no=int(i.page_no)-1
                print("is__update",i)
                i.page_no = updated_page_no
                updated_page_no = 1 if updated_page_no < 1 else updated_page_no
                src_json['projectid']['page']=updated_page_no
            else:
                print("no_update")
            src_json['projectid']['pages']=page_len
            i.json=src_json
            i.save()

# def len_page_update(can_page,page_len):
#     if can_page:
#         for i in can_page:
#             updated_page_no=int(i.page_no)-1
#             src_json=copy.deepcopy(i.json)
#             i.page_no = updated_page_no
#             src_json['projectid']['pages']=page_len
#             i.json=src_json
#             i.save()
# elif tar_page_no and tar_lang:
#     CanvasTargetJsonFiles.objects.get(canvas_trans_json__canvas_design=obj,canvas_trans_json__target_language=tar_lang,page_no=tar_page_no).delete()
#     can_page=CanvasTargetJsonFiles.objects.filter(canvas_trans_json__canvas_design=obj,canvas_trans_json__target_language=tar_lang,page_no__gt=tar_page_no)
#     for i in can_page:
#         updated_page_no=int(i.page_no)-1
#         tar_json=copy.deepcopy(i.json)
#         i.page_no = updated_page_no
#         tar_json['projectid']['page']=updated_page_no
#         tar_json['projectid']['pages']=len(can_page)
#         i.json=tar_json
#         i.save()
    # return Response({'msg':'deleted successfully'},status=200)




class CanvasDesignViewset(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,]
    def get_queryset(self):
        pr_managers = self.request.user.team.get_project_manager if self.request.user.team and self.request.user.team.owner.is_agency else [] 
        user = self.request.user.team.owner if self.request.user.team and self.request.user.team.owner.is_agency and self.request.user in pr_managers else self.request.user
        queryset = CanvasDesign.objects.filter(((Q(project__project_jobs_set__job_tasks_set__task_info__assign_to = user) & ~Q(project__ai_user = user))\
                    |Q(project__project_jobs_set__job_tasks_set__task_info__assign_to = self.request.user))\
                    |Q(project__ai_user = self.request.user)|Q(project__team__owner = self.request.user)|Q(user = user)\
                    |Q(project__team__internal_member_team_info__in = self.request.user.internal_member.filter(role=1))).distinct().order_by('-id')
        return queryset

    def get_user(self):
        project_managers = self.request.user.team.get_project_manager if self.request.user.team else []
        user = self.request.user.team.owner if self.request.user.team and self.request.user in project_managers else self.request.user
        print("Pms----------->",project_managers)
        return user,project_managers

    def get_object(self, pk):
        try:
            queryset = self.get_queryset()
            return queryset.get(id=pk)
        except CanvasDesign.DoesNotExist:
            raise Http404

    def create(self,request):
        thumbnail = request.FILES.get('thumbnail')
        user,pr_managers = self.get_user()
        serializer = CanvasDesignSerializer(data=request.data,context={'request':request,'user':user,'managers':pr_managers})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    
    def list(self, request):
        queryset = self.get_queryset()
        user,pr_managers = self.get_user()
        serializer = CanvasDesignSerializer(queryset,many=True,context={'request':request,'user':user,'managers':pr_managers})
        return Response(serializer.data)

    def retrieve(self,request,pk):
        obj =self.get_object(pk)
        user,pr_managers = self.get_user()
        serializer = CanvasDesignSerializer(obj,context={'request':request,'user':user,'managers':pr_managers})
 
        return Response(serializer.data)
 
    
    def update(self,request,pk):
        obj =self.get_object(pk)
        user,pr_managers = self.get_user()
        serializer = CanvasDesignSerializer(obj,data=request.data,partial=True,context={'request':request,'user':user,'managers':pr_managers})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors,status=400)
        
    def destroy(self,request,pk):
        src_page_no = request.query_params.get('src_page_no',None)
        tar_page_no = request.query_params.get('tar_page_no',None)
        tar_lang = request.query_params.get('tar_lang',None)
        obj = CanvasDesign.objects.get(user=request.user,id=pk)
        project = obj.project
        if src_page_no:
            can_src_del=CanvasSourceJsonFiles.objects.filter(canvas_design=obj)
            if len(can_src_del)==1:
                print("single page")
                can_inst=can_src_del[0]
                json=copy.deepcopy(can_inst.json)
                json['objects']=[]
                json['backgroundImage']['fill']="rgba(255,255,255,1)"
                json['backgroundImage']['backgroundColor']=''
                can_inst.json=json
                thumbnail=CanvasDesignSerializer().thumb_create(json_str=json,formats='png',multiplierValue=1) 
                can_inst.thumbnail=thumbnail
                can_inst.save()
            else:
                print("multiple_ page")
                can_src_del.get(page_no=int(src_page_no)).delete()
            can_page_last=CanvasSourceJsonFiles.objects.filter(canvas_design=obj,page_no__gt=src_page_no)
            total_page= CanvasSourceJsonFiles.objects.filter(canvas_design=obj).count()
            page_no_update(can_page=can_page_last,is_update=True,page_len=total_page)
            can_page_first=CanvasSourceJsonFiles.objects.filter(canvas_design=obj,page_no__lt=src_page_no)
            page_no_update(can_page=can_page_first,is_update=False,page_len=total_page)

            return Response({'msg':'deleted successfully'},status=200)

        else:
            obj.delete()
            project.delete()
            return Response({'msg':'deleted successfully'},status=200)
 
class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'

class CustomSocialMediaSizePagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'page_size'

class CanvasDesignListViewset(viewsets.ViewSet,PageNumberPagination):
    # pagination_class = CanvasDesignListViewsetPagination
    permission_classes = [IsAuthenticated,]
    search_fields =['file_name',"canvas_translate__target_language__language__language","canvas_translate__source_language__language__language"]
    filter_backends = [DjangoFilterBackend]
    page_size = 20

    def list(self,request):
        pr_managers = self.request.user.team.get_project_manager if self.request.user.team and self.request.user.team.owner.is_agency else [] 
        user = self.request.user.team.owner if self.request.user.team and self.request.user.team.owner.is_agency and self.request.user in pr_managers else self.request.user

        queryset = CanvasDesign.objects.filter(((Q(project__project_jobs_set__job_tasks_set__task_info__assign_to = user) & ~Q(project__ai_user = user))\
                    | Q(project__project_jobs_set__job_tasks_set__task_info__assign_to = self.request.user))\
                    |Q(project__ai_user = self.request.user)|Q(project__team__owner = self.request.user)\
                    |Q(project__team__internal_member_team_info__in = self.request.user.internal_member.filter(role=1))).distinct().order_by('-id')
        
        queryset = self.filter_queryset(queryset)
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = CanvasDesignListSerializer(pagin_tc,many=True,context={'request':request})
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


# user = request.user.team.owner  if request.user.team  else request.user


class MyTemplateDesignViewset(viewsets.ViewSet ,PageNumberPagination):
    pagination_class = MyTemplateDesignPagination
    page_size = 20
    permission_classes = [IsAuthenticated,]
    search_fields =['file_name',]

    def list(self,request):
        user = request.user.team.owner if request.user.team else request.user
        queryset = MyTemplateDesign.objects.filter(user=user).order_by('-id')
        queryset = self.filter_queryset(queryset)
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = MyTemplateDesignSerializer(pagin_tc,many=True)
        response = self.get_paginated_response(serializer.data)
        return response
    
    # def retrieve(self,request,pk):
    #     queryset=MyTemplateDesign.objects.filter(id=pk).values('id','width','height','file_name','project_category','created_at',
    #                                                            'my_template_page').last()
    #     # serializer =MyTemplateDesignSerializer(queryset)
    #     return Response(queryset)

    def create(self,request):
        user = request.user.team.owner if request.user.team else request.user
        template_global_id = request.POST.get('template_global_id')
        serializer = MyTemplateDesignSerializer(data =request.data , context={'request':request,'user':user,'created_by':created_by})
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
        user = request.user.team.owner if request.user.team else request.user
        MyTemplateDesign.objects.get(user=user,id=pk).delete()
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

mime_type={'svg':'image/svg+xml',
        'png':'image/png',
        'jpeg':'image/jpeg',
        'jpg':'image/jpeg',
        'zip':'application/zip',
        'png-transparent':'image/png',
        'pdf':'application/pdf',
        'text':'text/plain',
        'pdf-print':'application/pdf',
        'pdf-standard':'application/pdf',
        'jpeg-print':'image/jpeg'}

def download_file_canvas(file_path,mime_type,name):
    response = HttpResponse(file_path, content_type=mime_type)
    response['Content-Disposition'] = 'attachment;filename*=UTF-8\'\'{}'.format(name)
    response['X-Suggested-Filename'] = name
    #response['Content-Disposition'] = "attachment; filename=%s" % filename
    response['Access-Control-Expose-Headers'] = 'Content-Disposition'
    return response



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

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def instant_canvas_translation(request):
#     text_list = request.POST.getlist('text')
#     src_lang_id = request.POST.get('src_lang_id',None)
#     tar_lang_id = request.POST.get('tar_lang_id')
#     if src_lang_id:
#         src_lang_code = Languages.objects.get(id=src_lang_id).locale.first().locale_code
#     tar_lang_code = Languages.objects.get(id=tar_lang_id).locale.first().locale_code
#     text_translation = get_translation(1,text_list,'en',tar_lang_code)
#     return Response({'translated_text_list':text_translation})

##################################
#######view for all user#########
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
        user = request.user.team.owner if request.user.team else request.user
        query_set=FontFile.objects.filter(user=user)
        serializer=FontFileSerializer(query_set ,many =True)
        return Response(serializer.data)

    def retrieve(self,request,pk):
        user = request.user.team.owner if request.user.team else request.user
        query_set=FontFile.objects.get(user=user,id = pk)
        serializer=FontFileSerializer(query_set )
        return Response(serializer.data)
        
    def create(self,request):
        font_file=request.FILES.get('font_file',None)
        user = request.user.team.owner if request.user.team else request.user
        print({**request.POST.dict(),'font_family':font_file})
        serializer=FontFileSerializer(data={**request.POST.dict(),'font_family':font_file,'user':user.id,'created_by':request.user.id})
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
        user = request.user.team.owner if request.user.team else request.user
        query_set=FontFile.objects.get(user=user,id=pk)
        query_set.delete()
        return Response(status=204)


class FontFamilyFilter(django_filters.FilterSet):
    font_search = django_filters.CharFilter(field_name='font_family_name', label='renamed_field')

    class Meta:
        model = FontFamily
        fields= ['font_family_name']
            
    def filter_queryset(self,queryset):
        queryset=queryset.filter(font_family_name__icontains=self.data['font_search'])
        return queryset
 
###########view for all user###########
class FontFamilyViewset(viewsets.ViewSet,PageNumberPagination):
    
    page_size = 20
    def lang_fil(self,request):
        f_lang=FontLanguage.objects.get(id=request.GET['language'])
        f_d=FontData.objects.filter(font_lang=f_lang)
        queryset=f_d.annotate(font_family_name=F('font_family__font_family_name'))
        return queryset
    
    def list(self, request):
        font_search=request.query_params.get('font_search',None)
        language=request.query_params.get('language',None)
        catagory=request.query_params.get('catagory',None)
        queryset = FontFamily.objects.all().exclude(Q(font_family_name__icontains='material')|Q(font_family_name__icontains='barcode')).order_by('font_family_name')  
        if font_search and language:
            queryset=self.lang_fil(request)            
            filters = FontFamilyFilter(request.GET, queryset=queryset)
            queryset = filters.qs
        elif font_search:
            queryset=queryset.filter(Q(font_family_name__icontains=font_search)).order_by('font_family_name')
        elif language:
            queryset=self.lang_fil(request)
        elif catagory:
            queryset=FontFamily.objects.filter(catagory__id=catagory)
        elif catagory and font_search:
            queryset=FontFamily.objects.filter(catagory__id=catagory)
            queryset=queryset.filter(Q(font_family_name__icontains=font_search)).order_by('font_family_name')
        else:
            font_file=FontFile.objects.filter(user=request.user)
            if font_file:
                font_file=font_file.annotate(font_family_name=F("name"))
                queryset=list(chain(font_file, queryset))
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = FontFamilySerializer(pagin_tc,many=True)
        response = self.get_paginated_response(serializer.data)
        if response.data["next"]:
            response.data["next"] = response.data["next"].replace("http://", "https://")
        if response.data["previous"]:
                response.data["previous"] = response.data["previous"].replace("http://", "https://")
        return response


###########view for all user ##############

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
     

###########view for all user ##############

class SocialMediaSizeViewset(viewsets.ViewSet,PageNumberPagination):
    filter_backends = [DjangoFilterBackend]
    # pagination_class = CustomSocialMediaSizePagination
    page_size = 30
    search_fields = ['social_media_name']
    def list(self,request):
        queryset = SocialMediaSize.objects.all().exclude(social_media_name__icontains='Custom').order_by('social_media_name')
        queryset = self.filter_queryset(queryset)
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = SocialMediaSizeSerializer(pagin_tc,many=True)
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
        params['safesearch']="true"
    if page:
        params['page']=page
        params['per_page']=20
        params['safesearch']="true"
    if search:
        params['q']=search
        params['safesearch']="true"
    if category and search:
        params['catagory']=category
        params['q']=search
        params['safesearch']="true"
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
            'orientation':'all','per_page':10,'safesearch':"true"}
    params['q']=category
    params['catagory']=str(category).lower()
    pixa_bay = requests.get(pixa_bay_url, params=params,headers=pixa_bay_headers) 
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
    page_size = 20
    def create(self,request):
        print("request.data",request.POST.dict())
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
        serializer=TemplateGlobalDesignSerializer(query_set )
        return Response(serializer.data)
    

class CategoryWiseGlobaltemplateViewset(viewsets.ViewSet,PageNumberPagination):
    permission_classes = [IsAuthenticated,]
    page_size = 20
    filter_backends = [DjangoFilterBackend]
 
    search_fields =['template_global_categoty__template_name','social_media_name','template_global_categoty__description',
                    'template_global_categoty__template_lang__language','template_global_categoty__template_global_page__tag_name']
# template_global_categoty__template_global_page__tag_name__icontains

    def list(self,request):
        social_media_name_id=request.query_params.get('social_media_name_id',None)
        search=request.query_params.get('search',None)
        if social_media_name_id:
            queryset=SocialMediaSize.objects.filter(id=social_media_name_id)
        else:
            queryset=SocialMediaSize.objects.all().order_by("social_media_name") 
        queryset_2 = self.filter_queryset(queryset)
        pagin_tc = self.paginate_queryset(queryset_2, request , view=self)
        serializer=CategoryWiseGlobaltemplateSerializer(pagin_tc,many=True) #CategoryWiseGlobaltemplateViewSerializer
        data=[i for i in serializer.data if i['template_global_categoty']]
        response = self.get_paginated_response(data)
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
    
def text_download(json):
    text=[]
    for i in json['objects']:
        if i['type']== 'textbox':
            text.append(i['text'])
            text.append("\n")
    return "".join(text)

def format_extension_change(file_format):
    files = {'png-transparent':'png' ,  'pdf-print':'pdf',  'pdf-standard' :'pdf' , 'pdf-print':'pdf','jpeg-print':'jpeg'}
    return files.get(file_format,file_format)

from PIL import Image
def download__page(pages_list,file_format,export_size,page_number_list,lang,projecct_file_name ):
    format_ext = format_extension_change(file_format)
    if len(pages_list)==1:
        if file_format=="text":
            export_src=text_download(pages_list[0].json)
            file_name="{}_page_{}_{}.{}".format(projecct_file_name,str(pages_list[0].page_no),lang,"txt")
        else:
            img_res=export_download(pages_list[0].json,file_format,export_size)
            file_name="{}_page_{}_{}.{}".format(projecct_file_name,str(pages_list[0].page_no),lang,format_ext)
            export_src=core.files.File(core.files.base.ContentFile(img_res),file_name)
        response=download_file_canvas(export_src,mime_type[file_format.lower()],file_name)
    else:
        buffer=io.BytesIO()
        paths_img_obj=[]
        with zipfile.ZipFile(buffer, mode="a") as archive:
            for src_json in pages_list:
                
                if file_format=="text":
                    file_name = 'page_{}_{}.{}'.format(src_json.page_no,lang,"txt")
                    path='{}/{}'.format(lang,file_name)
                    values=text_download(src_json.json)
                else:
                    file_name = 'page_{}_{}.{}'.format(src_json.page_no,lang,format_ext)
                    path='{}/{}'.format(lang,file_name)
                    file_format = 'png' if file_format == 'pdf-standard' else file_format
                    values=export_download(src_json.json,file_format,export_size)

                if format_ext == 'pdf':
                    paths_img_obj.append(Image.open(io.BytesIO(values)).convert('RGB'))
                else:
                    archive.writestr(path,values)
        if format_ext == 'pdf':
            output_buffer=io.BytesIO()
            paths_img_obj[0].save(output_buffer,'PDF',save_all=True, append_images=paths_img_obj[1:])
            export_src=core.files.File(core.files.base.ContentFile(output_buffer.getvalue()),file_name+'.pdf')
            response=download_file_canvas(file_path=export_src,mime_type=mime_type["pdf"],name=projecct_file_name+'.pdf')
        else:
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
    canvas=CanvasDesign.objects.get(user=request.user, id=canvas_id)
    page_number_list=list(map(int,page_number_list)) if page_number_list else None
    page_src=[]
    file_format = file_format.replace(" ","-") if file_format else ""
    # format_ext = 'png' if file_format == 'png-transparent' else file_format
    format_ext = format_extension_change(file_format=file_format)
    canvas_src_json=canvas.canvas_json_src.all()
    if not canvas.file_name:
        can_obj=CanvasDesign.objects.filter(user=request.user.id,file_name__icontains='Untitled project')
        canvas.file_name='Untitled project ({})'.format(str(len(can_obj)+1)) if can_obj else 'Untitled project'
        canvas.save()
    if any(canvas.canvas_translate.all()):
        canvas_trans_inst=canvas.canvas_translate.all()
        src_lang=canvas_trans_inst[0].source_language.language.language
        src_code=canvas_trans_inst[0].source_language.language_id
        if language==0: #all languages with number of pages
            src_jsons=canvas.canvas_json_src.filter(page_no__in=page_number_list)
            buffer=io.BytesIO()
            with zipfile.ZipFile(buffer, mode="a") as archive:
                for src_json in src_jsons:
                    if file_format=="text":
                        values=text_download(src_json.json)
                        file_name = '{}_page_{}.{}'.format(canvas.file_name,src_json.page_no,"txt")
                        path='{}/{}'.format(src_lang,file_name)
                        
                    else:
                        file_name = '{}_page_{}.{}'.format(canvas.file_name,src_json.page_no,format_ext)
                        path='{}/{}'.format(src_lang,file_name)
                        values=export_download(src_json.json,file_format,export_size)
                    archive.writestr(path,values)
                for tar_lang in canvas_trans_inst:
                    tar_jsons=canvas_trans_inst.get(target_language=tar_lang.target_language).canvas_json_tar.filter(page_no__in=page_number_list)
                    for tar_json in tar_jsons:
                        if file_format=="text":
                            values=text_download(tar_json.json)
                            file_name='{}_{}_page_{}.{}'.format(canvas.file_name,tar_json.page_no,tar_lang.target_language.language,"txt")
                            path='{}/{}'.format(tar_lang.target_language.language,file_name)
                        else:
                            values=export_download(tar_json.json,file_format,export_size)
                            file_name='{}_{}_page_{}.{}'.format(canvas.file_name,tar_json.page_no,tar_lang.target_language.language,format_ext)
                            path='{}/{}'.format(tar_lang.target_language.language,file_name)
                        archive.writestr(path,values)
            if buffer.getvalue():
                # if not canvas.file_name:
                #     can_obj=CanvasDesign.objects.filter(user=request.user.id,file_name__icontains='Untitled project')
                #     canvas.file_name='Untitled project ({})'.format(str(len(can_obj)+1)) if can_obj else 'Untitled project'
                #     canvas.save()
                res=download_file_canvas(file_path=buffer.getvalue(),mime_type=mime_type["zip"],name=canvas.file_name+'.zip')
                return res
            else:
                raise serializers.ValidationError({'msg':'Something went wrong'}, code=400)

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
    
######## view for all user
class EmojiCategoryViewset(viewsets.ViewSet,PageNumberPagination):
    # pagination_class = CustomPagination
    page_size = 30
    page_size_query_param = 'page_size'
    search_fields=['emoji_name']
    def list(self,request):
        catagory_id=request.query_params.get('catagory_id')
        search=request.query_params.get('search')
        if catagory_id:
            queryset= EmojiData.objects.filter(emoji_cat__id=catagory_id)
            queryset = self.filter_queryset(queryset)
        else:
            if search:
                queryset=EmojiData.objects.filter(emoji_name__icontains=search)
                
            else:
                queryset=EmojiCategory.objects.all()
                self.search_fields=['name']
                queryset = self.filter_queryset(queryset)
        
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        if catagory_id or search:
            serializer = EmojiDataSerializer(pagin_tc,many=True)
        else:
            serializer = EmojiCategorySerializer(pagin_tc,many=True)
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



from ai_canvas.models import CanvasTranslatedJson
from ai_workspace.models import TaskDetails
from ai_workspace.serializers import TaskDetailSerializer
from ai_openai.serializers import AiPromptSerializer

def dict_rec_json(json_copy):
    total_sent = []
    if 'template_json' in  json_copy.keys():
        for count ,i in enumerate(json_copy['template_json']['objects']):
            if 'objects' in i.keys():
                dict_rec_json(i)
            if i['type']== 'textbox':
                text = i['text']
                total_sent.append(text)
    else:
        for count, i in enumerate(json_copy['objects']):
            if 'objects' in i.keys():
                dict_rec_json(i)
            if i['type']== 'textbox':
                text = i['text']
                total_sent.append(text)
    return total_sent

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def Designerwordcount(request):
    canvas_trans_json_id=request.query_params.get('canvas_trans_json_id')
    design_instance = CanvasTranslatedJson.objects.get(id=canvas_trans_json_id) #canvas_design__user=request.user, 
    total_sent=[]
    for i in design_instance.canvas_design.canvas_json_src.all():
         total_sent.extend(dict_rec_json(i.json))
    print(total_sent)
    wc=AiPromptSerializer().get_total_consumable_credits(source_lang=design_instance.source_language.language.language ,
                                                        prompt_string_list= total_sent)
    task_det_instance,created=TaskDetails.objects.get_or_create(task = design_instance.job.job_tasks_set.last(),
                                      project = design_instance.job.project,defaults = {"task_word_count": wc,"task_char_count":len(" ".join(total_sent))})
    ser = TaskDetailSerializer(task_det_instance)
    return Response(ser.data)

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

# import time
# from .utils import generate_random_rgba,create_thumbnail,grid_position,genarate_text,random_background_image
# class TemplateEngineGenerate(viewsets.ModelViewSet):

#     def get_queryset(self):
#         return PromptCategory.objects.all()

#     def list(self,request):
#         queryset= self.get_queryset()
#         serializers=PromptCategoryserializer(queryset,many=True)
#         return Response (serializers.data)
    
#     def create(self,request):
#         # prompt=request.POST.get("prompt",None)
#         template_id=request.POST.get("template",None)
#         template=get_object_or_404(SocialMediaSize,id=template_id)
#         prompt_id=request.POST.get("prompt_id",None)
#         sdstylecategoty=1
#         image_resolution=request.POST.get("image_resolution",None)
#         negative_prompt="bad anatomy, bad hands, three hands, three legs, bad arms, missing legs, missing arms, poorly drawn face, bad face, fused face, cloned face, worst face, three crus, extra crus, fused crus, worst feet, three feet, fused feet, fused thigh, three thigh, fused thigh, extra thigh, worst thigh, missing fingers, extra fingers, ugly fingers, long fingers, horn, extra eyes, huge eyes, 2girl, amputation, disconnected limbs"

#         # ** get image
#         if prompt_id==None:
#             print("SD creatin")
#             serializer = StableDiffusionAPISerializer(data=request.POST.dict() ,context={'request':request})
#             if serializer.is_valid():
#                 serializer.save()
#             else:
#                 return Response(serializer.errors)
            
#             id=serializer.data.get("id")
#             wait=0 
#             print("enter...........")
#             while True:
#                 ins=get_object_or_404(StableDiffusionAPI,id=id)
#                 if ins.status=="DONE":
#                     break
#                 else:
#                     wait+=1
#             print("exiting............")
#             # id=89
#             instance=get_object_or_404(StableDiffusionAPI,id=id)
#         else:
#             print("no SD creatin")
#             instance=PromptEngine.objects.filter(prompt_category__id=prompt_id).first()
#         background=TemplateBackground.objects.filter(prompt_category__id=prompt_id).first()
#         # bg_images=list(background)
#         prompt = instance.prompt
#         font = FontData.objects.filter(font_lang__name="Latin").values_list('font_family__font_family_name', flat=True)
#         font_family = list(font)
#         print("template_genarating.........................")
#         template=genarate_template(instance,template,prompt,font_family,background)        
#         return JsonResponse({"data":template})
    
# from ai_canvas.template import jsonStructure
# def genarate_template(instance,template,prompt,font_family,bg_images):
#     temp_height =int(template.height)
#     temp_width = int(template.width)
#     template_data=[]
#     for i in range(0,5):
#         print(i)
#         text_grid,image_grid=grid_position(temp_width,temp_height)
#         temp={}   
#         data=copy.deepcopy(jsonStructure) 

#         """ backgroundImage  """
#         # bg_images=bg_images.first()
#         # bg_images=bg_images.pop(random.randint(0,(len(bg_images)-1)))
#         backgroundImage =random_background_image(template,bg_images)
#         data.get("objects").append(backgroundImage)

#         print("j")
#         """  Image 0 """
#         image=genarate_image(instance,image_grid,template)
#         data.get("objects").append(image)

#         # change image attributes
#         # for key, value in style[0]["image"][0].items():
#         #             data["objects"][0][key] = value

#         """  Text 1  """
#         textbox=genarate_text(font_family,prompt,text_grid,template)
#         data.get("objects").append(textbox)
#         # change text attributes
#         # for key, value in style[i]["text"][0].items():
#         #             data["objects"][0][key] = value
        
#         """  backgroundboard   """
#         random_color= random.randint(0, 19)
#         # data["backgroundImage"]["fill"]=generate_random_rgba()
#         data["backgroundImage"]["width"]=int(temp_width)
#         data["backgroundImage"]["height"]=int(temp_height)
#         print(data)
#         # thumnail creation
#         thumbnail={}
#         thumbnail['thumb']=create_thumbnail(data,formats='png')
#         temp={"json":data,"thumb":thumbnail}
#         template_data.append(temp)
#     return template_data

from ai_canvas.serializers import DesignerListSerializer
class DesignerListViewset(viewsets.ViewSet,PageNumberPagination):
    permission_classes = [IsAuthenticated,]
    search_fields =['file_name',"canvas_translate__target_language__language__language","canvas_translate__source_language__language__language"]
    filter_backends = [DjangoFilterBackend]
    page_size = 20

    def list(self,request):
        queryset = CanvasDesign.objects.filter(user=request.user.id).order_by('-updated_at')
        # if queryset.canvas_json_src.first():
        queryset = self.filter_queryset(queryset)
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = DesignerListSerializer(pagin_tc,many=True)
        data=[]
        for obj in serializer.data:
            if obj:
                data.append(obj)
        response = self.get_paginated_response(data)
        return response
        
    
    def filter_queryset(self, queryset):
        filter_backends = (DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter )
        for backend in list(filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, view=self)
        return queryset
    
    def retrieve(self,request,pk):
        # src_id=request.GET.get("source_id",None)
        tar_id=request.GET.get("target_id",None)
        base_64=request.GET.get("base_64",None)
        if tar_id:
             queryset=get_object_or_404(CanvasTargetJsonFiles,id=tar_id)
             serializer=CanvasTargetJsonSerializer(queryset,context={"json":True},many=False)
        else:
            queryset=CanvasSourceJsonFiles.objects.filter(canvas_design__id=pk).first()
            serializer=CanvasSourceJsonFilesSerializer(queryset,many=False)
        if not base_64:
            return Response(serializer.data,status=200)
        else:
            src_json=queryset.json
            out=export_download(src_json,"png",multipliervalue=1,base_image=True)
            return JsonResponse({'base_64': out})
        


@api_view(["GET",'POST'])
def designer_asset_create(request):
    if request.method=="POST":
        image_id=request.POST.get("image_id",None)
        shape_type=request.POST.get("shape_type",None)
        instance=CanvasUserImageAssets.objects.get(id=image_id)
        image_name=os.path.basename(instance.image.url)
        image = convert_image_url_to_file(Image.open(instance.image.path),no_pil_object=False,name=image_name)
        if not shape_type:
            serializer=AiAssertsSerializer(data={**request.POST.dict(),"user":"Ailaysa","imageurl":image},context={"request":request})
        else:
            serializer= DesignShapeSerializer(data={**request.POST.dict(),"shape":image,"types":shape_type},context={"request":request})
        if serializer.is_valid():
            serializer.save()
            instance.status=True
            instance.save()
            return Response(serializer.data,status=201)
        return Response(serializer.errors)

    category=ImageCategories.objects.all()
    obj_type=AiAssertscategory.objects.all()
    shape_category=DesignShapeCategory.objects.all()
    shape_type=DesignShape._meta.get_field('types').choices
    shape_types = {key: value for key, value in shape_type}
    asset_serializer=AiAssertscategoryserializer(obj_type,many=True)
    img_category_serializer=ImageCategoriesSerializer(category,many=True)
    shape_cat_serializer=DesignShapeCategoryserializer(shape_category,many=True)

    return JsonResponse({"Image_category":img_category_serializer.data,"asset_type":asset_serializer.data,"shape_category":shape_cat_serializer.data,"shape_type":shape_types},status=200)


 




class AssetImageViewset(viewsets.ViewSet,PageNumberPagination):
    permission_classes = [IsAuthenticated,]
    page_size = 20
    

    def list(self,request):
        queryset = AssetImage.objects.all().order_by('-id')
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = AssetImageSerializer(pagin_tc,many=True)
        response = self.get_paginated_response(serializer.data)
        return response
        
    def create(self,request):
        image = request.FILES.get('image')
        serializer = AssetImageSerializer(data=request.data,context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

# AssetCategorySerializer
class AssetCategoryViewset(viewsets.ViewSet):
    def list(self,request):
        queryset = AssetCategory.objects.all().order_by('-id')
        serializer = AssetCategorySerializer(queryset,many=True)
        return Response(serializer.data)
    
    def create(self,request):
        serializer = AssetCategorySerializer(data=request.data,context={'request':request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)
    
    def delete(self,request,pk):
        query_set=AssetCategory.objects.get(id=pk)
        query_set.delete()
        return Response(status=204)
    

