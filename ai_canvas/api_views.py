from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets  ,generics
from rest_framework.response import Response
from ai_staff.models import ( Languages,LanguagesLocale)
from ai_canvas.models import (CanvasTemplates ,CanvasUserImageAssets,CanvasDesign,CanvasSourceJsonFiles,
                              CanvasTargetJsonFiles,TemplateGlobalDesign,TemplatePage,MyTemplateDesign,
                              TemplateKeyword,TextTemplate,FontFile,ImageListMedium)
from ai_canvas.serializers import (CanvasTemplateSerializer ,LanguagesSerializer,LocaleSerializer,
                                   CanvasUserImageAssetsSerializer,CanvasDesignSerializer,CanvasDesignListSerializer,
                                   TemplateGlobalDesignSerializer,MyTemplateDesignRetrieveSerializer,
                                   TemplateGlobalDesignRetrieveSerializer,MyTemplateDesignSerializer ,
                                   TextTemplateSerializer,TemplateKeywordSerializer,FontFileSerializer,ImageListMediumSerializer)
from ai_canvas.pagination import (CanvasDesignListViewsetPagination ,TemplateGlobalPagination ,MyTemplateDesignPagination)
from django.db.models import Q,F
from itertools import chain
from ai_staff.models import FontFamily
from ai_staff.serializer import FontFamilySerializer
from ai_staff.models import FontFamily,FontLanguage,FontData
from rest_framework.pagination import PageNumberPagination 
from rest_framework.decorators import api_view,permission_classes
from django.conf import settings
import os ,zipfile,requests
from django.http import Http404,JsonResponse
from ai_workspace_okapi.utils import get_translation

free_pix_api_key = os.getenv('FREE_PIK_API')
pixa_bay_api_key =  os.getenv('PIXA_BAY_API')

pixa_bay_url='https://pixabay.com/api/'
pixa_bay_headers={
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
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
        queryset = CanvasUserImageAssets.objects.filter(user=request.user.id)
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
        

class CanvasDesignListViewset(viewsets.ViewSet,PageNumberPagination):
    pagination_class = CanvasDesignListViewsetPagination
    permission_classes = [IsAuthenticated,]
    def list(self,request):
        queryset = CanvasDesign.objects.filter(user=request.user.id).order_by('-updated_at')
        print("request.user.id--------------------->>>>",request.user.id , request.user)
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = CanvasDesignListSerializer(pagin_tc,many=True)
        response = self.get_paginated_response(serializer.data)
        return response
    


class TemplateGlobalDesignViewset(viewsets.ViewSet ,PageNumberPagination):
    pagination_class = TemplateGlobalPagination 
    permission_classes = [IsAuthenticated,]
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


class MyTemplateDesignViewset(viewsets.ViewSet ,PageNumberPagination):
    pagination_class = MyTemplateDesignPagination
    permission_classes = [IsAuthenticated,]
    def list(self,request):
        queryset = MyTemplateDesign.objects.filter(user=request.user.id)
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

    def destroy(self,request,pk):
        MyTemplateDesign.objects.get(id=pk).delete()
        return Response({'msg':'deleted'})
    

class MyTemplateDesignRetrieveViewset(generics.RetrieveAPIView):
    queryset = MyTemplateDesign.objects.all()
    serializer_class = MyTemplateDesignRetrieveSerializer
    lookup_field = 'id'


######################################################canvas______download################################


from ai_canvas.utils import export_download
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def canvas_export_download(request):
    format=request.POST.get('format')
    multipliervalue=request.POST.get('multipliervalue')
    canvas_design_id=request.POST.get('canvas_design_id')
    can_des=CanvasDesign.objects.get(id=canvas_design_id)
    file_path=f'{settings.MEDIA_ROOT}/{can_des.user.uid}/temp_download/'
    try:
        os.makedirs(file_path) #{design.file_name}
    except FileExistsError:
        pass
    zip_path = f'{file_path}{can_des.file_name}.zip'
 
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        can_src=can_des.canvas_json_src.all()
        for src_json_file in can_src:
            print("src_json_file---> CanvasSourceJsonFiles")
            src_json=can_des.canvas_translate.all()
            if src_json_file.json:
                compressed_data_img=export_download(json_str=src_json_file.json,format=format,multipliervalue=multipliervalue)
                src_lang=src_json[0].source_language.language_locale_name.strip() if src_json[0] else can_des.file_name
 
                src_file_name=src_lang+'.{}'.format(format)
                zipf.writestr(src_file_name, compressed_data_img)
            if src_json:
                zipf.write(file_path, 'source_target/' , zipfile.ZIP_DEFLATED )
                for j in src_json:
                    form=".{}".format(format)
                    print("src_json",j.source_language,'---',j.target_language)
                    if j.canvas_json_tar.last():
                        tar_json_file=j.canvas_json_tar.last()
                        if tar_json_file:
                            compressed_data_img=export_download(json_str=tar_json_file.json,format=format,multipliervalue=multipliervalue)
                            zipf.writestr('source_target/'+j.target_language.language_locale_name.strip()+form, compressed_data_img)
                        
        download_path = f'{settings.MEDIA_URL}{can_des.user.uid}/temp_download/{can_des.file_name}.zip'
    return JsonResponse({"url":download_path},status=200)                


 
# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def canvas_export_download(request):
#     format=request.POST.get('format')
#     multipliervalue=request.POST.get('multipliervalue')
#     canvas_design_id=request.POST.get('canvas_design_id')
#     design=CanvasDesign.objects.get(id=canvas_design_id)
#     file_path=f'{settings.MEDIA_ROOT}/{design.user.uid}/temp_download/'
#     try:
#         os.makedirs(file_path) #{design.file_name}
#     except FileExistsError:
#         pass
#     zip_path = f'{file_path}{design.file_name}.zip'
    
#     with zipfile.ZipFile(zip_path, 'w') as zipf:
#         src_insts=design.canvas_json_src.all()
        
#         for src_inst in src_insts:
#             if src_inst.json:
#                 compressed_data_img=export_download(json_str=src_inst.json,format=format,multipliervalue=multipliervalue)
#                 canvas_src_instance=design.canvas_translate.last()

#                 if canvas_src_instance:
#                     src_lang=canvas_src_instance.source_language.language_locale_name.strip()
#                 else:
#                     src_lang=design.file_name
#                 print("src_lang---------->>>",src_lang)
#                 src_file_name=src_lang+'_page_{}.{}'.format(src_inst.page_no,format)
#                 zipf.writestr(src_file_name, compressed_data_img)

#                 if canvas_src_instance:
#                     canvas_tar_inst=canvas_src_instance.canvas_json_tar.all()

#                     if canvas_tar_inst:

#                         for canvas_tar_instance in canvas_tar_inst:
#                             tar_json=canvas_tar_instance.json
#                             print(tar_json)
#                             print("------>src_lang---------->>>",src_lang)
#                             compressed_data_img=export_download(json_str=tar_json,format=format,
#                                                                 multipliervalue=multipliervalue)
#                             src_file_name=src_lang+'_page_{}.{}'.format(src_inst.page_no,format)
#                             zipf.writestr(src_file_name, compressed_data_img)
#         download_path = f'{settings.MEDIA_URL}{design.user.uid}/temp_download/{design.file_name}.zip'
#     return JsonResponse({"url":download_path},status=200)
                 



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def canvas_download(request):
    ## need to add authorization for requested user
    design_id = request.GET.get('design_id')
    canvas_translation_id = request.GET.get('canvas_translation_id',None)
    design = CanvasDesign.objects.get(id=design_id)
    zip_path = f'{settings.MEDIA_ROOT}/temp/{design.file_name}.zip'
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        ## Getting Source
        json_src = design.canvas_json_src.all()
        src_lang_code=design.canvas_translate.first().source_language.locale_code
        for src in json_src :
            if canvas_translation_id:
                break
            try:
                source_path = src.thumbnail.path
            except:
                print("no thumbnail",src.id)
            name = os.path.basename(src.thumbnail.name)
            destination = f"/source/{name}" 
            zipf.write(source_path, destination)

        ## Getting Translated
        if canvas_translation_id:
            json_tranlated = design.canvas_translate.filter(id=canvas_translation_id)
        else:
            json_tranlated = design.canvas_translate.all()

        for tar_json in json_tranlated:
            tar_pages= tar_json.canvas_json_tar.all()
            tar_lang_code = tar_json.target_language.locale_code
            for tar in tar_pages :
                try:
                    source_path = tar.thumbnail.path
                except:
                    print("no thumbnail",tar.id)
                name = os.path.basename(tar.thumbnail.name)
                destination = f"/{tar_lang_code}/{name}"
                zipf.write(source_path, destination)
        download_path = f'{settings.MEDIA_URL}temp/{design.file_name}.zip'
    return JsonResponse({"url":download_path},status=200)


###############################################################################

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
    response = requests.get(url, params=params,headers=headers)
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


class TextTemplateViewset(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,]
    def get(self, request):
        query_set=TextTemplate.objects.all()
        serializer=TextTemplateSerializer(query_set ,many =True)
        return Response(serializer.data)

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
    
    def update(self,request,pk):
        query_set=self.model.objects.get(id = pk)
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
        query_set=self.model.objects.get(id = pk)
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



class CustomPagination(PageNumberPagination):
    page_size = 20 
    page_size_query_param = 'page_size'
     
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
 
 
class  FontFamilyViewset(viewsets.ViewSet,PageNumberPagination):
    pagination_class = CustomPagination
    page_size = 20


    def lang_fil(self,request):
        f_lang=FontLanguage.objects.get(id=request.GET['language'])
        f_d=FontData.objects.filter(font_lang=f_lang)
        queryset=f_d.annotate(font_family_name=F('font_family__font_family_name')).values("font_family_name")
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
                font_file=font_file.annotate(font_family_name=F("name")).values("font_family_name")
                queryset=queryset.values("font_family_name")
                queryset=list(chain(font_file, queryset))
 
 
        pagin_tc = self.paginate_queryset(queryset, request , view=self)
        serializer = FontFamilySerializer(pagin_tc,many=True)
        response = self.get_paginated_response(serializer.data)
        if response.data["next"]:
            response.data["next"] = response.data["next"].replace("http://", "https://")
        if response.data["previous"]:
                response.data["previous"] = response.data["previous"].replace("http://", "https://")
        return response
    

from ai_canvas.utils import convert_image_url_to_file
import asyncio
async def one_iteration(pixa_json):
    preview_image=convert_image_url_to_file(pixa_json['previewURL'])
    return {'image_url' :pixa_json['webformatURL'],'tags':pixa_json['tags'],'image_name':pixa_json['type'],
                                 'preview_image':preview_image}



async def generate_url(pixa_url_list):
    coroutines=[]
    for pixa_url_value in pixa_url_list:
        coroutines.append(one_iteration(pixa_url_value))
    return await asyncio.gather(*coroutines)

class ImageListMediumViewset(viewsets.ViewSet):

    def list(self,request):
        image_search=request.query_params.get('image_search',None)
        if image_search:
            
            params = {'q':image_search,'key':pixa_bay_api_key,'order':'popular' ,'per_page':10}
            response = requests.get(pixa_bay_url, params=params,headers=pixa_bay_headers).json()
            if response and 'hits' in response and response['hits']:
                data = asyncio.run(generate_url(response['hits']))
                serializer=ImageListMediumSerializer(data=data,many=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                else:
                    return Response(serializer.errors)
        else:
            return Response({'image_search':'fill image search field'},status=200)