from rest_framework import serializers
from ai_canvas.models import (CanvasTemplates,CanvasDesign,CanvasUserImageAssets,CanvasTranslatedJson,CanvasSourceJsonFiles,CanvasTargetJsonFiles,
                            TemplateGlobalDesign ,MyTemplateDesign,MyTemplateDesignPage,TextTemplate,TemplateKeyword,FontFile,CanvasDownloadFormat,TemplateTag)#TemplatePage
from ai_staff.models import Languages,LanguagesLocale  
from django.http import HttpRequest
from ai_canvas.utils import install_font
from ai_canvas.utils import json_src_change ,canvas_translate_json_fn,thumbnail_create,json_sr_url_change
from django import core
from ai_imagetranslation.utils import image_content 
from ai_workspace_okapi.utils import get_translation
import copy
from ai_canvas.template_json import basic_json
from ai_staff.models import SocialMediaSize
from PIL import Image
import cv2
from ai_imagetranslation.serializer import create_thumbnail_img_load
class LocaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LanguagesLocale
        fields = ('id','language_id','language_locale_name','locale_code')
 
class LanguagesSerializer(serializers.ModelSerializer):
    code = serializers.CharField(required=False)
    class Meta:
        model = Languages
        fields = ('id','language','code')
 
    def to_representation(self, instance):
        code = instance.locale.first().locale_code
        data = super().to_representation(instance)
        data['code'] = code
        return data

class CanvasTargetJsonFilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CanvasTargetJsonFiles
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.thumbnail:
            # thumbnail =  "/".join(instance.thumbnail.path.split("/")[2:])
            data['thumbnail'] = "media/"+instance.thumbnail.name
        else:
            data['thumbnail'] = None
        return data

class CanvasTranslatedJsonSerializer(serializers.ModelSerializer):
    tranlated_json = CanvasTargetJsonFilesSerializer(source = 'canvas_json_tar',many=True,required=False)

    class Meta:
        model = CanvasTranslatedJson
        fields = "__all__"
        extra_kwargs = {'id':{'read_only':True},
                'created_at':{'read_only':True},'updated_at':{'read_only':True},
                }
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['source_language'] = instance.source_language.language.id
        representation['target_language']= instance.target_language.language.id
        return representation

class CanvasTemplateSerializer(serializers.ModelSerializer):  
    class Meta:
        model = CanvasTemplates
        fields = "__all__"

class CanvasSourceJsonFilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CanvasSourceJsonFiles
        fields = "__all__"

    extra_kwargs = { 
            'export_file':{'write_only':True},
            'undo_hide_src':{'write_only':True}
    }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.thumbnail:
            data['thumbnail'] ="media/"+instance.thumbnail.name
        if instance.export_file:
            data['export_file'] = "media/"+instance.export_file.name
        return data

class CanvasDesignSerializer(serializers.ModelSerializer):
    source_json = CanvasSourceJsonFilesSerializer(source='canvas_json_src',many=True,read_only=True)
    source_json_file = serializers.JSONField(required=False,write_only=True)
    target_json_file = serializers.JSONField(required=False,write_only=True)
    thumbnail_src = serializers.FileField(allow_empty_file=False,required=False,write_only=True)
    export_img_src = serializers.FileField(allow_empty_file=False,required=False,write_only=True)
    #page_no = serializers.IntegerField(read_only=True)    
    canvas_translation = CanvasTranslatedJsonSerializer(many=True,read_only=True,source='canvas_translate')
    canvas_translation_target = serializers.PrimaryKeyRelatedField(queryset=CanvasTranslatedJson.objects.all(),required=False,write_only=True)
    canvas_translation_tar_thumb = serializers.FileField(allow_empty_file=False,required=False,write_only=True)
    canvas_translation_tar_export = serializers.FileField(allow_empty_file=False,required=False,write_only=True)
    canvas_translation_tar_lang = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=Languages.objects.all()),
                                                        required=False,write_only=True)
    src_page = serializers.IntegerField(required=False,write_only=True)
    src_lang = serializers.PrimaryKeyRelatedField(queryset=Languages.objects.all(),required=False,write_only=True)
    tar_page = serializers.IntegerField(required=False,write_only=True)
    temp_global_design = serializers.PrimaryKeyRelatedField(queryset=TemplateGlobalDesign.objects.all(),required=False)
    my_temp = serializers.PrimaryKeyRelatedField(queryset=MyTemplateDesign.objects.all(),required=False)
    target_canvas_json=serializers.JSONField(required=False,write_only=True)
    next_page=serializers.BooleanField(required=False,write_only=True)
    duplicate=serializers.BooleanField(required=False,write_only=True)
    social_media_create=serializers.PrimaryKeyRelatedField(queryset=SocialMediaSize.objects.all(),required=False)
    update_new_textbox=serializers.BooleanField(required=False,write_only=True)
    new_project=serializers.BooleanField(required=False,write_only=True)
    # project_category=serializers.PrimaryKeyRelatedField(queryset=SocialMediaSize.objects.all(),required=False)
    # width=serializers.CharField(required=False)
    # height=serializers.CharField(required=False)
    class Meta:
        model = CanvasDesign
        fields =  ('id','file_name','source_json','width','height','created_at','updated_at',
                    'canvas_translation','canvas_translation_tar_thumb', 'canvas_translation_target',
                    'canvas_translation_tar_lang','source_json_file','src_page','thumbnail_src',
                    'export_img_src','src_lang','tar_page','target_json_file','canvas_translation_tar_export',
                    'temp_global_design','my_temp','target_canvas_json','next_page','duplicate','social_media_create','update_new_textbox','new_project')
        
        extra_kwargs = { 
            'canvas_translation_tar_thumb':{'write_only':True},
            'canvas_translation_target':{'write_only':True},
            'canvas_translation_tar_lang':{'write_only':True},
            'source_json_file':{'write_only':True},
            'src_page':{'write_only':True},
            'thumbnail_src':{'write_only':True},
            'src_lang':{'write_only':True},
            'next_page':{'write_only':True},
            'duplicate':{'write_only':True},
            'social_media_create':{'write_only':True},
            'update_new_textbox':{'write_only':True},}

    def thumb_create(self,json_str,formats,multiplierValue):
        thumb_image_content= thumbnail_create(json_str=json_str,formats=formats)
        thumb_name = self.instance.file_name+'_thumbnail.png' if self.instance and self.instance.file_name else 'thumbnail.png'
        thumbnail_src = core.files.File(core.files.base.ContentFile(thumb_image_content),thumb_name)
        return thumbnail_src

    def create(self,validated_data):
        req_host=self.context.get('request', HttpRequest()).get_host()
        source_json_file=validated_data.pop('source_json_file',None)
        thumbnail_src=validated_data.pop('thumbnail_src',None)
        export_img_src=validated_data.pop('export_img_src',None)
        social_media_create=validated_data.pop('social_media_create',None)
        next_page=validated_data.pop('next_page',None)
        duplicate=validated_data.pop('duplicate',None)
        new_project=validated_data.pop('new_project',None)
        width=validated_data.get('width',None)
        height=validated_data.get('height',None)
        update_new_textbox=validated_data.pop('update_new_textbox',None)
        # project_category=validated_data.get('project_category',None)
        user = self.context['request'].user
        data = {**validated_data ,'user':user}
        instance=CanvasDesign.objects.create(**data)
        self.instance=instance
 
        # print("instance.file_name",instance.file_name)
        if not instance.file_name:
            can_obj=CanvasDesign.objects.filter(file_name__icontains='Untitled project')
            # print("can_obj",can_obj)
            if can_obj:
                instance.file_name='Untitled project ({})'.format(str(len(can_obj)+1))
            else:
                instance.file_name='Untitled project' 
            instance.save()

        if source_json_file and social_media_create and width and height:
            source_json_file=json_src_change(source_json_file,req_host,instance)
            thumbnail_src=self.thumb_create(json_str=source_json_file,formats='png',multiplierValue=1) 
            can_json=CanvasSourceJsonFiles.objects.create(canvas_design=instance,json = source_json_file,page_no=1,thumbnail=thumbnail_src,export_file=export_img_src)
            src_json=can_json.json
            src_json['projectid']={"pages": 1,'page':1,"langId": None,"langNo": None,"projId": instance.id,"projectType": "design",
                                   "project_category_label":social_media_create.social_media_name,"project_category_id":social_media_create.id}
            
            can_json.json=src_json    
            can_json.save()
            instance.save()
            return instance


        if social_media_create and width and height:
            basic_jsn=copy.copy(basic_json)
            basic_jsn['backgroundImage']['width']=int(width)
            basic_jsn['backgroundImage']['height']=int(height)
            thumbnail_src=self.thumb_create(json_str=basic_jsn,formats='png',multiplierValue=1) 
            basic_jsn['projectid']={"pages": 1,'page':1,"langId": None,"langNo": None,"projId": instance.id,"projectType": "design",
                                    "project_category_label":social_media_create.social_media_name,"project_category_id":social_media_create.id}
            can_json=CanvasSourceJsonFiles.objects.create(canvas_design=instance,json = basic_jsn,page_no=1,thumbnail=thumbnail_src,export_file=export_img_src)
            # json=can_json.json
            # for i in json['objects']:
            #     if 'textbox' == i['type']:
            #         i['user_text']=i['text']
            # can_json.json=json
            # can_json.save()
            instance.height=int(width)
            instance.width=int(height)
            # instance.file_name=social_media_create.social_media_name
            instance.save()
            return instance
            
        if social_media_create:
            basic_jsn=copy.copy(basic_json)
            basic_jsn['backgroundImage']['width']=int(social_media_create.width)
            basic_jsn['backgroundImage']['height']=int(social_media_create.height)
            thumbnail_src=self.thumb_create(json_str=basic_jsn,formats='png',multiplierValue=1) 
            basic_jsn['projectid']={"pages": 1,'page':1,"langId": None,"langNo": None,"projId": instance.id,
                                    "projectType": "design","project_category_label":social_media_create.social_media_name,"project_category_id":social_media_create.id}
            
            can_json=CanvasSourceJsonFiles.objects.create(canvas_design=instance,json = basic_jsn,page_no=1,thumbnail=thumbnail_src,export_file=export_img_src)
            instance.height=int(social_media_create.height)
            instance.width=int(social_media_create.width)
            # instance.file_name=social_media_create.social_media_name
            instance.save()
            return instance
          


    def update(self, instance, validated_data):
        req_host = self.context.get('request', HttpRequest()).get_host()
        canvas_translation_tar_lang=validated_data.get('canvas_translation_tar_lang')
        canvas_translation_tar_thumb=validated_data.get('canvas_translation_tar_thumb',None)
        canvas_translation_tar_export=validated_data.get('canvas_translation_tar_export',None)
        canvas_translation_target=validated_data.get('canvas_translation_target',None)
        canvas_translation=validated_data.get('canvas_translation',None)
        source_json_file=validated_data.get('source_json_file',None)
        thumbnail_src=validated_data.get('thumbnail_src',None)
        export_img_src=validated_data.get('export_img_src',None)
        src_page=validated_data.get('src_page',None)
        src_lang=validated_data.get('src_lang',None)
        tar_page=validated_data.get('tar_page',None)
        target_json_file=validated_data.get('target_json_file',None)
        target_canvas_json=validated_data.get('target_canvas_json',None)
        next_page=validated_data.get('next_page',None)
        duplicate=validated_data.get('duplicate',None)
        update_new_textbox=validated_data.get('update_new_textbox',None)
        social_media_create=validated_data.get('social_media_create',None)
        width=validated_data.get('width',None)
        height=validated_data.get('height',None)
        new_project=validated_data.get('new_project',None)
        temp_global_design = validated_data.get('temp_global_design',None)

        if social_media_create and src_page and source_json_file and width and height: ##########################this one same fun below 
            can_src=CanvasSourceJsonFiles.objects.get(canvas_design=instance,page_no=src_page)
            source_json_file['projectid']['project_category_label']=social_media_create.social_media_name
            source_json_file['projectid']['project_category_id']=social_media_create.id
            can_src.json=source_json_file
            can_src.save()
            instance.width=int(width)
            instance.height=int(height)
            instance.save()
            return instance

        if social_media_create and src_page and source_json_file:
            can_src=CanvasSourceJsonFiles.objects.get(canvas_design=instance,page_no=src_page)
            source_json_file['projectid']['project_category_label']=social_media_create.social_media_name
            source_json_file['projectid']['project_category_id']=social_media_create.id
            # for i in source_json_file['objects']:
            #     print(list(i.keys()))
            #     if 'textbox' == i['type'] and "temp_text" not in i.keys():
            #         print("1212")
            #         i['temp_text']=i['text']
            # can_src.json=source_json_file
            # print("-------------------------")
            instance.width=int(social_media_create.width)
            instance.height=int(social_media_create.height)
            can_src.save()
            instance.save()
            return instance

        if update_new_textbox and src_page:
            canvas_src_pages=instance.canvas_json_src.get(page_no=src_page)
            text_box=""
            json=canvas_src_pages.json
            for i in json['objects']:
                if (i['type']=='textbox') and ("isTranslate" in i.keys()) and (i['isTranslate'] == False):
                    text_box=i
                if text_box and ("text" in text_box.keys()):
                    text=text_box['text']
                    canvas_tar_lang=instance.canvas_translate.all()
                    for tar_json in canvas_tar_lang:
                        src=tar_json.source_language.locale_code
                        tar=tar_json.target_language.locale_code
                        for j in tar_json.canvas_json_tar.all():
                            json=j.json
                            copy_txt_box=copy.copy(text_box)
                            trans_text=get_translation(1,source_string=text,source_lang_code=src,target_lang_code=tar)
                            copy_txt_box['text']=trans_text    
                            obj_list=json['objects']
                            obj_list.append(copy_txt_box)
                            j.save()
                    i['isTranslate']=True
            canvas_src_pages.save()
            return instance

        if next_page:
            src_json_page=instance.canvas_json_src.last().json
            src_json_page['objects'].clear()
            pages=len(instance.canvas_json_src.all())
            page=pages+1
            src_json_page['projectid']={"pages": pages+1,'page':page,"langId": None,"langNo": None,"projId": instance.id,"projectType": "design"}
            src_json_page['background']="rgba(255,255,255,0.1)"
            thumbnail=self.thumb_create(json_str=src_json_page,formats='png',multiplierValue=1)
            CanvasSourceJsonFiles.objects.create(canvas_design=instance,json=src_json_page,page_no=pages+1,thumbnail=thumbnail)
 
            for count,src_js in enumerate(instance.canvas_json_src.all()):
                src_js.json['projectid']['pages']=pages+1
                src_js.json['projectid']['page']=count+1
                src_js.save()

        if duplicate and src_page:
            can_src=CanvasSourceJsonFiles.objects.get(canvas_design=instance,page_no=src_page)
            CanvasSourceJsonFiles.objects.create(canvas_design=instance,json=can_src.json,thumbnail=can_src.thumbnail,page_no=len(instance.canvas_json_src.all())+1)
    
        if tar_page and canvas_translation and target_canvas_json:
            canvas_translation_tar_thumb = self.thumb_create(json_str=target_canvas_json,formats='png',multiplierValue=1) 
            CanvasTargetJsonFiles.objects.create(canvas_trans_json=canvas_translation,json=target_canvas_json ,
                                                 page_no=tar_page,thumbnail=canvas_translation_tar_thumb,export_file=canvas_translation_tar_export)

        if canvas_translation_tar_lang and src_lang:
            for count,tar_lang in enumerate(canvas_translation_tar_lang):

                trans_json=CanvasTranslatedJson.objects.create(canvas_design=instance,source_language=src_lang.locale.first(),
                                                               target_language=tar_lang.locale.first())
                trans_json_project=copy.deepcopy(trans_json.canvas_design.canvas_json_src.last().json)
                trans_json_project['projectid']['langNo']=trans_json.source_language.id
                source_json_files_all=trans_json.canvas_design.canvas_json_src.all() ####list of all canvas src json 
                # trans_json.canvas_src_json
                for count,src_json_file in enumerate(source_json_files_all):
                    src_json_file.json=json_src_change(src_json_file.json,req_host,instance)
                    src_json_file.save()
                    res=canvas_translate_json_fn(src_json_file.json,src_lang.locale.first().locale_code,tar_lang.locale.first().locale_code)
                     
                    if res[tar_lang.locale.first().locale_code]:
                        tar_json_form=res[tar_lang.locale.first().locale_code]             
                        tar_json_thum_image=self.thumb_create(json_str=tar_json_form,formats='png',multiplierValue=1) 
                        can_tar_ins=CanvasTargetJsonFiles.objects.create(canvas_trans_json=trans_json,thumbnail=tar_json_thum_image,
                                                             json=tar_json_form,page_no=src_json_file.page_no)
                        tar_json_pro=can_tar_ins.json
                        tar_json_pro['projectid']={"pages":len(source_json_files_all),'page':count+1,"langId": trans_json.id,
                                                   "langNo": tar_lang.id,"projId": instance.id,"projectType": "design"}
                        can_tar_ins.json=tar_json_pro
                        can_tar_ins.save()

        if canvas_translation_target and tar_page:
            canvas_trans = canvas_translation_target.canvas_json_tar.get(page_no=tar_page)
            canvas_translation_tar_thumb=self.thumb_create(json_str=canvas_trans.json,formats='png',multiplierValue=1)
            # thumbnail should be update if json file is updated
            canvas_trans.thumbnail=canvas_translation_tar_thumb
            canvas_trans.export_file=canvas_translation_tar_export
            if target_json_file:
                if hasattr(target_json_file ,'json'):
                    target_json_file = json_src_change(target_json_file.json,req_host,instance)
                    # print("outside----->json, canvas_translation_target")
                canvas_trans.json = target_json_file
            canvas_trans.save()
 

        if source_json_file and src_page:
            canva_source = CanvasSourceJsonFiles.objects.get_or_create(canvas_design=instance,page_no=src_page)[0]
            if '' not in source_json_file:
                source_json_file['projectid']={"pages": 1,'page':1,"langId": None,"langNo": None,"projId": instance.id,"projectType": "design"}
            # source_json_file = json_src_change(source_json_file,req_host,instance)
            source_json_file=json_sr_url_change(source_json_file,instance)
            canva_source.json = source_json_file
            print("this function dont want to exec")
            thumbnail_src = self.thumb_create(json_str=source_json_file,formats='png',multiplierValue=1)
            # print("inside----->>> src json and src page")
            # thumbnail_path=canva_source.thumbnail.path
            # thumbnail_name=thumbnail_path.split("/")[-1]
            canva_source.thumbnail = thumbnail_src
            # canva_source.export_file = thumbnail_src ###   export_img_src same as thumbnail_src
            canva_source.save()
 

        elif thumbnail_src and src_page:
            canva_source = CanvasSourceJsonFiles.objects.get(canvas_design=instance,page_no=src_page)
 
            thumbnail_src = self.thumb_create(json_str=canva_source.json,formats='png',multiplierValue=1)
            canva_source.thumbnail = thumbnail_src
            canva_source.export_file = thumbnail_src  ##export_img_src same as thumbnail_src
            canva_source.save()   
            # if thumbnail_page_path and os.path.exists(thumbnail_page_path):
            #     os.remove(thumbnail_page_path)
            # print('path exist',os.path.exists(thumbnail_page_path))

        if temp_global_design and new_project:
            width=temp_global_design.width
            height=temp_global_design.height
            json=temp_global_design.json
            category=temp_global_design.category
            user = self.context['request'].user
            new_proj=CanvasDesign.objects.create(user=user,width=width,height=height)
            json['projectid']={"pages": 1,'page':1,"langId": None,"langNo": None,"projId": new_proj.id,
                                    "projectType": "design","project_category_label":category.social_media_name,"project_category_id":category.id}
            CanvasSourceJsonFiles.objects.create(new_proj=new_proj,json=json,page_no=1)
            return new_proj

        if temp_global_design:
            json_page = temp_global_design.json #
            page_len = len(instance.canvas_json_src.all())+1
            thumbnail_page = self.thumb_create(json_str=json_page,formats='png',multiplierValue=1)
            CanvasSourceJsonFiles.objects.create(canvas_design=instance,thumbnail=thumbnail_page,json=json_page,page_no=page_len)


        # if validated_data.get('my_temp',None):
        #     my_temp = validated_data.get('my_temp')
        #     my_temp_pages = my_temp.my_template_page.all()
        #     page_len = len(instance.canvas_json_src.all())
        #     for my_temp_page in my_temp_pages:
        #         thumbnail_page = my_temp_page.my_template_thumbnail
        #         # export_page = my_temp_page.my_template_export
        #         json_page = my_temp_page.my_template_json
        #         page_len+=1
        #         CanvasSourceJsonFiles.objects.create(canvas_design=instance,thumbnail=thumbnail_page,
        #                                              json=json_page,page_no=page_len)
        return super().update(instance=instance, validated_data=validated_data)


class CanvasDesignListSerializer(serializers.ModelSerializer):
    thumbnail_src = serializers.FileField(allow_empty_file=False,required=False,write_only=True)
    translate_available = serializers.BooleanField(required=False,default=False)
    class Meta:
        model = CanvasDesign
        fields = ('id','file_name','width','height','thumbnail_src','translate_available','updated_at')
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if hasattr(instance.canvas_json_src.first(),'thumbnail'):
            # if 'thumbnail_src' in data.keys():
            data['thumbnail_src']= instance.canvas_json_src.first().thumbnail.url
        if instance.canvas_translate.all():
            data['translate_available'] = True

        # if not instance.project_category:
            
        #     data['project_category']
        return data

class CanvasUserImageAssetsSerializer(serializers.ModelSerializer):
    image = serializers.FileField(required=False)
    class Meta:
        model = CanvasUserImageAssets
        fields = ("id","image_name","image",'thumbnail','height','width')

    def to_representation(self, instance):
        data=super().to_representation(instance)
        if not data.get('thumbnail',None):
            extension=instance.image.path.split('.')[-1]
            if extension !='svg':
                im = Image.open(instance.image.path)
                instance.thumbnail=create_thumbnail_img_load(base_dimension=300,image=im)
            else:
                print("svg")
                instance.thumbnail=instance.image
            instance.save()
        return super().to_representation(instance)
         

    def create(self, validated_data):
        user =  self.context['request'].user
        data = {**validated_data ,'user':user}
        instance = CanvasUserImageAssets.objects.create(**data)
        if validated_data.get('image',None):
            extension=instance.image.path.split('.')[-1]
            if extension=='jpg':
                extension='jpeg'
            
            img = cv2.imread(instance.image.path)
            if extension !='svg':
                height,width,_ = img.shape
                content= image_content(img)
                im =core.files.base.ContentFile(content,name=instance.image.name.split('/')[-1])
                instance.thumbnail=create_thumbnail_img_load(base_dimension=300,image=Image.fromarray(img))
                instance.image = im
                instance.height=height
                instance.width=width
                instance.save()
                # if any([True if i>2048 else False for i in [width, height]]):
                #     scale_val = min([2048/width, 2048/ height])
                #     new_width = round(scale_val*width)
                #     new_height = round(scale_val*height)
                #     im = cv2.resize(im ,(new_height,new_width))
                #     content= image_content(im)
                #     instance.thumbnail=Image.fromarray(im)
                #     im =core.files.base.ContentFile(content,name=instance.image.name.split('/')[-1])
                #     instance.image = im
                #     instance.save()
        return instance
    
####################################################################################################
# class TemplatePageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TemplatePage
#         fields = '__all__'

class SocialMediaSizeValueSerializer(serializers.ModelSerializer):
    class Meta:
        model=SocialMediaSize
        fields=('id','social_media_name','width','height')

class TemplateTagSerializer(serializers.ModelSerializer):
    class Meta:
        model=TemplateTag
        fields=('id','tag_name')
        

class TemplateGlobalDesignSerializerV2(serializers.ModelSerializer):
    template_tag =TemplateTagSerializer(many=True,required=False,source='template_global_page')
    template_list=serializers.CharField(required=False)
    category=serializers.PrimaryKeyRelatedField(queryset=SocialMediaSize.objects.all(),required=True)
    json=serializers.JSONField(required=True)
    template_lang=serializers.PrimaryKeyRelatedField(queryset=Languages.objects.all(),required=True)
    is_pro=serializers.BooleanField(default=False)
    is_published=serializers.BooleanField(default=False)

    class Meta:
        model=TemplateGlobalDesign
        fields=('id','template_tag','template_list','json','template_name','category','is_pro','is_published',
                'template_lang','description','thumbnail_page')
        extra_kwargs = { 
            'template_list':{'write_only':True},}

    def thumb_create(self,json_str,formats,multiplierValue):
        thumb_image_content=thumbnail_create(json_str=json_str,formats=formats)
        thumb_name=self.instance.file_name+'_thumbnail.png' if self.instance and self.instance.file_name else 'thumbnail.png'
        thumbnail_src=core.files.File(core.files.base.ContentFile(thumb_image_content),thumb_name)
        return thumbnail_src

    def to_representation(self, instance):
        data=super().to_representation(instance)
        data['template_lang'] = instance.template_lang.locale.first().locale_code
        data['category'] = instance.category.social_media_name
        data['width'] =  instance.category.width
        data['height'] =  instance.category.height 
        return data

    def create(self, validated_data):
        template_list=validated_data.pop('template_list',None)
        template_lists=template_list.split(",")
        instance = TemplateGlobalDesign.objects.create(**validated_data)
        json=copy.copy(instance.json)
        json['projectid']=None
        instance.json=json
        instance.save()
        thumbnail_page = self.thumb_create(json_str=instance.json,formats='png',multiplierValue=1)
        instance.thumbnail_page=thumbnail_page
        instance.save()
        for template_list in template_lists:
            TemplateTag.objects.create(tag_name=template_list,global_template=instance)
        return instance

class CategoryWiseGlobaltemplateSerializer(serializers.ModelSerializer):
    template_global_categoty=TemplateGlobalDesignSerializerV2(many=True,read_only=True)
    
    class Meta:
        fields=('id','template_global_categoty','social_media_name')
        model=SocialMediaSize
 

    def to_representation(self, instance):
        data=super().to_representation(instance)
        template=instance.template_global_categoty.all()
        # print("template",template)
        if template is not None:
            return data


# class TemplateGlobalDesignSerializer(serializers.ModelSerializer):
#     template_name = serializers.CharField(required= True)
#     # template_globl_pag = TemplatePageSerializer(many = True,required=False)
#     tag_name = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=TemplateTag.objects.all()),
#                                                 required=False,write_only=True)
#     thumbnail_page = serializers.FileField(required=False,write_only=True)
#     export_page = serializers.FileField(required=False,write_only=True)
#     json_page = serializers.JSONField(required=False,write_only=True,initial=dict)
#     # user_name = serializers.CharField(required=False)
#     page_no = serializers.CharField(required=False)
#     is_pro=serializers.BooleanField(default=False)
#     is_published=serializers.BooleanField(default=False)
#     category=serializers.PrimaryKeyRelatedField(queryset=SocialMediaSize.objects.all(),required=False)
#     template_page=serializers.PrimaryKeyRelatedField(queryset=TemplatePage.objects.all(),required=False)

#     template_lang=serializers.PrimaryKeyRelatedField(queryset=Languages.objects.all(),required=False)



#     class Meta:
#         model = TemplateGlobalDesign
#         fields = ('id','width','height','thumbnail_page', 'export_page','template_name',
#                   'json_page','tag_name','user_name','category','is_published','is_pro',
#                   'template_page','page_no','template_lang') # 'page_no' ,'' ,'user_name' 'template_globl_pag', 'export_page, file_name
        
#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         template_page_first = TemplatePage.objects.filter(template_page = instance).first()
#         if template_page_first:
#             if template_page_first.thumbnail_page:
#                 data['thumbnail_page'] = template_page_first.thumbnail_page.url
#             else:
#                 data['thumbnail_page'] = None
#         return data

#     def thumb_create(self,json_str,formats,multiplierValue):
#         thumb_image_content=thumbnail_create(json_str=json_str,formats=formats)
#         thumb_name=self.instance.file_name+'_thumbnail.png' if self.instance and self.instance.file_name else 'thumbnail.png'
#         thumbnail_src=core.files.File(core.files.base.ContentFile(thumb_image_content),thumb_name)
#         return thumbnail_src

#     def create(self, validated_data):
#         thumbnail_page = validated_data.pop('thumbnail_page',None)
#         export_page = validated_data.pop('export_page',None)
#         json_page = validated_data.pop('json_page',None)
#         instance = TemplateGlobalDesign.objects.create(**validated_data)
#         self.instance = instance
#         if json_page:
#             thumbnail_page = self.thumb_create(json_str=json_page,formats='png',multiplierValue=1)
#             TemplatePage.objects.create(template_page=instance,thumbnail_page=thumbnail_page,export_page=export_page,
#                                         json_page=json_page,page_no=1)
#         return instance


#     def update(self, instance, validated_data):
#         instance.template_name=validated_data.get('template_name',instance.template_name)
#         instance.width = validated_data.get('width',instance.width)
#         instance.height = validated_data.get('height',instance.height)
#         instance.user_name=validated_data.get('user_name',instance.user_name)

#         instance.is_pro = validated_data.get('is_pro',instance.is_pro)
#         instance.is_published=validated_data.get('is_published',instance.is_published)

#         template_lang=validated_data.pop('template_lang')
#         tag_name=validated_data.pop('tag_name')
#         json_page = validated_data.pop('json_page',None)
#         page_no = validated_data.pop('page_no',None)
#         thumbnail_page = validated_data.pop('thumbnail_page',None)
#         template_page= validated_data.pop('template_page',None)
#         export_page = validated_data.pop('export_page',None)

#         if json_page:

#             TemplatePage.objects.create(template_page=instance,thumbnail_page=thumbnail_page,export_page=export_page,
#                                         json_page=json_page,page_no=1)
            
#         if json_page and page_no:
#             if TemplatePage.objects.filter(page_no=page_no).exists():
#                 template_page_update=TemplatePage.objects.get(template_page=instance,page_no=page_no)
#                 if json_page:
#                     thumbnail_page = self.thumb_create(json_str=json_page,formats='png',multiplierValue=1)
#                     template_page_update.json_page = json_page
#                     template_page_update.thumbnail_page = thumbnail_page
#                 if export_page:
#                     template_page_update.export_page = export_page
#                 template_page_update.save()
#             else:
#                 thumbnail_page = self.thumb_create(json_str=json_page,formats='png',multiplierValue=1)
#                 TemplatePage.objects.create(template_page=instance,thumbnail_page=thumbnail_page,export_page=export_page,
#                                         json_page=json_page,page_no=page_no)
#         if validated_data.get('template_global_id',None):
#             template_global_id = validated_data.get('template_global_id')
#         return instance 
    

# class TemplateGlobalDesignRetrieveSerializer(serializers.ModelSerializer):
#     template_globl_pag = TemplatePageSerializer(many = True,required=False)
#     class Meta:
#         model = TemplateGlobalDesign
#         fields = ('id','file_name','width','height','template_globl_pag',) #,'user_name'


class MyTemplateDesignPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyTemplateDesignPage
        fields = '__all__'

class MyTemplateDesignSerializer(serializers.ModelSerializer):
    template_global_id = serializers.PrimaryKeyRelatedField(queryset=TemplateGlobalDesign.objects.all(),required=False)
    canvas_design_id = serializers.PrimaryKeyRelatedField(queryset=CanvasDesign.objects.all(),required=False)
    canvas_lang_id =  serializers.PrimaryKeyRelatedField(queryset=Languages.objects.all(),required=False)
    canvas_trans_id = serializers.PrimaryKeyRelatedField(queryset=CanvasTargetJsonFiles.objects.all(),required=False)
    canvas_src_id=serializers.PrimaryKeyRelatedField(queryset=CanvasSourceJsonFiles.objects.all(),required=False)
    class Meta:
        model = MyTemplateDesign
        fields =  ('id','width','height','template_global_id','canvas_design_id','canvas_trans_id','canvas_lang_id','canvas_src_id')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        template_page_first = MyTemplateDesignPage.objects.filter(my_template_design = instance).first()
        if template_page_first:
            if template_page_first.my_template_thumbnail:
                data['my_template_thumbnail'] = template_page_first.my_template_thumbnail.url
            else:
                data['my_template_thumbnail'] = None
        return data

    def create(self, validated_data):
        template_global_id = validated_data.pop('template_global_id',None)
        canvas_design_id = validated_data.pop('canvas_design_id',None)
        canvas_trans_id = validated_data.pop('canvas_trans_id',None)
        canvas_src_id=validated_data.pop('canvas_src_id',None)
        canvas_lang_id=validated_data.pop('canvas_lang_id',None)
        user = self.context['request'].user
        if template_global_id:
            file_name=template_global_id.file_name
            width=template_global_id.width
            height=template_global_id.height
            template_globl_pag_inst = template_global_id.template_globl_pag.all()
            my_temp_design = MyTemplateDesign.objects.create(file_name=file_name,width=width,height=height,user=user)
            if any(template_globl_pag_inst):
                for glob_pag in template_globl_pag_inst:
                    my_template_thumbnail = glob_pag.thumbnail_page
                    # my_template_export=glob_pag.export_page
                    my_template_json=glob_pag.json_page
                    # page_no=glob_pag.page_no
                    MyTemplateDesignPage.objects.create(my_template_design=my_temp_design,my_template_thumbnail=my_template_thumbnail,
                                                        my_template_json=my_template_json )
             
        if canvas_design_id:
            file_name=canvas_design_id.file_name
            width=canvas_design_id.width
            height=canvas_design_id.height
            
            my_temp_design = MyTemplateDesign.objects.create(file_name=file_name,width=width,height=height,user=user)
            if canvas_trans_id:
                my_template_thumbnail = canvas_trans_id.thumbnail
 
                my_template_json=copy.copy(canvas_trans_id.json)
                my_template_json.pop('projectid',None)
                # my_template_json=json
 
                my_temp_ins=MyTemplateDesignPage.objects.create(my_template_design=my_temp_design,my_template_thumbnail=my_template_thumbnail,
                                                    my_template_json=my_template_json )
 
            elif canvas_src_id:
                canvas_source_json_inst = canvas_design_id.canvas_json_src.get(id=canvas_src_id.id)
                # canvas_source_json_inst = canvas_design_id.canvas_json_src.last()
                my_template_thumbnail = canvas_source_json_inst.thumbnail
                my_template_json=copy.copy(canvas_source_json_inst.json)
                my_template_json.pop('projectid',None)
 
                my_temp_ins_else=MyTemplateDesignPage.objects.create(my_template_design=my_temp_design,my_template_thumbnail=my_template_thumbnail,
                                                    my_template_json=my_template_json )
 
                
        return my_temp_design

class MyTemplateDesignRetrieveSerializer(serializers.ModelSerializer):
    my_template_page = MyTemplateDesignPageSerializer(many=True)
    class Meta:
        model = MyTemplateDesign
        fields = ('id','width','height','my_template_page',)


class TemplateKeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateKeyword
        fields = ('id' ,'text_template', 'text_keywords', )
        read_only_fields = ('id','text_template',)
   
class TextTemplateSerializer(serializers.ModelSerializer):
    text_template_json = serializers.JSONField(required = False)
    txt_keywords = TemplateKeywordSerializer(many=True,read_only=True,required=False,source='txt_temp') 
    text_keywords = serializers.ListField(required = True,write_only = True)
    class Meta:
        model = TextTemplate
        fields = ('id','text_thumbnail','text_template_json' ,'txt_keywords' ,'text_keywords')
        
    def create(self, validated_data):
        text_keywords=validated_data.pop('text_keywords') 
        text_temp = TextTemplate.objects.create(**validated_data)
        if text_keywords:
            for keyword in text_keywords:
                TemplateKeyword.objects.create(text_template = text_temp ,text_keywords =keyword  )
        return text_temp
    
    def update(self, instance, validated_data):
        template_keyword=TemplateKeywordSerializer()
        if validated_data.get('text_thumbnail'):
            instance.text_thumbnail = validated_data.get('text_thumbnail')
            instance.save()
        if validated_data.get('text_template_json'):
            instance.text_template_json = validated_data.get('text_template_json')
            instance.save()
        if validated_data.get('text_keywords'):
            txt_temp = validated_data.pop('text_keywords')
            [TemplateKeyword.objects.create(text_template=instance,text_keywords = key) for key in  txt_temp]
        return instance




class FontFileSerializer(serializers.ModelSerializer):
    class Meta:
        model=FontFile
        fields='__all__'

    def to_representation(self, instance):
        rep=super().to_representation(instance)
        if rep.get('font_family',None):
            rep['font_family']=instance.font_family.url
        if not rep.get('name'):
            family_name=install_font(instance.font_family.path)
            rep['name']=family_name
            instance.name=family_name
            instance.save()
        return rep

    def create(self, validated_data):
 
        instance=FontFile.objects.create(**validated_data)
        if instance.font_family:
            family_name=install_font(instance.font_family.path)
            instance.name=family_name
            instance.save()
        return instance


class CanvasDownloadFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model=CanvasDownloadFormat
        fields='__all__'

