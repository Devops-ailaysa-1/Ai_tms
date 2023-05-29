from rest_framework import serializers
from ai_canvas.models import (CanvasTemplates,CanvasDesign,CanvasUserImageAssets,
                            CanvasTranslatedJson,CanvasSourceJsonFiles,CanvasTargetJsonFiles,
                            TemplateGlobalDesign ,TemplatePage ,MyTemplateDesign,MyTemplateDesignPage,TextTemplate,TemplateKeyword,FontFile)
from ai_staff.models import Languages,LanguagesLocale  
from django.http import HttpRequest
from ai_canvas.utils import json_src_change ,canvas_translate_json_fn,thumbnail_create
from django import core
from ai_imagetranslation.utils import image_content

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

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.thumbnail:
            data['thumbnail'] ="media/"+instance.thumbnail.name
        if instance.export_file:
            data['export_file'] = "media/"+instance.export_file.name
        return data
import copy
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
    target_canvas_json = serializers.JSONField(required=False,write_only=True)

    class Meta:
        model = CanvasDesign
        fields =  ('id','file_name','source_json','width','height','created_at','updated_at',
                    'canvas_translation','canvas_translation_tar_thumb', 'canvas_translation_target',
                    'canvas_translation_tar_lang','source_json_file','src_page','thumbnail_src',
                    'export_img_src','src_lang','tar_page','target_json_file','canvas_translation_tar_export',
                    'temp_global_design','my_temp','target_canvas_json')
        
        extra_kwargs = { 
            'canvas_translation_tar_thumb':{'write_only':True},
            'canvas_translation_target':{'write_only':True},
            'canvas_translation_tar_lang':{'write_only':True},
            'source_json_file':{'write_only':True},
            'src_page':{'write_only':True},
            'thumbnail_src':{'write_only':True},
            'src_lang':{'write_only':True}
        }


    def thumb_create(self,json_str,formats,multiplierValue):
        thumb_image_content= thumbnail_create(json_str=json_str,formats=formats)
        thumb_name = self.instance.file_name+'_thumbnail.png' if self.instance and self.instance.file_name else 'thumbnail.png'
        thumbnail_src = core.files.File(core.files.base.ContentFile(thumb_image_content),thumb_name)
        return thumbnail_src

    def create(self,validated_data):
        req_host = self.context.get('request', HttpRequest()).get_host()
        source_json_file = validated_data.pop('source_json_file',None)
        thumbnail_src = validated_data.pop('thumbnail_src',None)
        export_img_src = validated_data.pop('export_img_src',None)
        user = self.context['request'].user
        data = {**validated_data ,'user':user}
        instance=CanvasDesign.objects.create(**data)
        self.instance=instance
        if source_json_file:
            source_json_file=json_src_change(source_json_file,req_host,instance)
            thumbnail_src=self.thumb_create(json_str=source_json_file,formats='png',multiplierValue=1) 
            can_json=CanvasSourceJsonFiles.objects.create(canvas_design=instance,json = source_json_file,
                                                 page_no=1,thumbnail=thumbnail_src,export_file=export_img_src)
            src_json=can_json.json
            src_json['projectid']={"pages": 1,'page':1,"langId": None,"langNo": None,"projId": instance.id,"projectType": "design"}
            
            can_json.json=src_json
            can_json.save()
        return instance

    def update(self, instance, validated_data):
        req_host = self.context.get('request', HttpRequest()).get_host()
        canvas_translation_tar_lang=validated_data.get('canvas_translation_tar_lang')
        canvas_translation_tar_thumb=validated_data.get('canvas_translation_tar_thumb',None)
        canvas_translation_tar_export = validated_data.get('canvas_translation_tar_export',None)
        canvas_translation_target = validated_data.get('canvas_translation_target',None)
        canvas_translation = validated_data.get('canvas_translation',None)
        source_json_file = validated_data.get('source_json_file',None)
        thumbnail_src = validated_data.get('thumbnail_src',None)
        export_img_src = validated_data.get('export_img_src',None)
        src_page = validated_data.get('src_page',None)
        src_lang = validated_data.get('src_lang',None)
        tar_page = validated_data.get('tar_page',None)
        target_json_file = validated_data.get('target_json_file',None)
        target_canvas_json = validated_data.get('target_canvas_json',None)
        if tar_page and canvas_translation and target_canvas_json:

            canvas_translation_tar_thumb = self.thumb_create(json_str=target_canvas_json,formats='png',multiplierValue=1) 
            CanvasTargetJsonFiles.objects.create(canvas_trans_json=canvas_translation,json=target_canvas_json ,
                                                 page_no=tar_page,thumbnail=canvas_translation_tar_thumb,export_file=canvas_translation_tar_export)

        if canvas_translation_tar_lang and src_lang:
            for tar_lang in canvas_translation_tar_lang:

                trans_json=CanvasTranslatedJson.objects.create(canvas_design=instance,source_language=src_lang.locale.first(),
                                                               target_language=tar_lang.locale.first())
                trans_json_pro=copy.deepcopy(trans_json.canvas_design.canvas_json_src.last().json)
                                                            
                trans_json_pro['projectid']['langNo']=trans_json.source_language.id
                source_json_files_all=trans_json.canvas_design.canvas_json_src.all()
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
            canvas_translation_tar_thumb=self.thumb_create(json_str=canvas_trans.json,
                                        formats='png',multiplierValue=1)
            # thumbnail should be update if json file is updated
            canvas_trans.thumbnail=canvas_translation_tar_thumb
            canvas_trans.export_file=canvas_translation_tar_export
            if target_json_file:
                if hasattr(target_json_file ,'json'):
                    target_json_file = json_src_change(target_json_file.json,req_host,instance)
                    # print("outside----->json, canvas_translation_target")
                canvas_trans.json = target_json_file
            canvas_trans.save()
            # if thumbnail_page_path and os.path.exists(thumbnail_page_path):
            #     os.remove(thumbnail_page_path)
 
        # for source json file and thumbnail update
        if source_json_file and src_page:
            canva_source = CanvasSourceJsonFiles.objects.get_or_create(canvas_design=instance,page_no=src_page)[0]
            source_json_file = json_src_change(source_json_file,req_host,instance)
            canva_source.json = source_json_file
            thumbnail_src = self.thumb_create(json_str=source_json_file,formats='png',multiplierValue=1)
            # thumbnail_page_path = canva_source.thumbnail.path if canva_source.thumbnail else ""
            # print("thumbnail_page_path------>",thumbnail_page_path)
            # print('path exist',os.path.exists(thumbnail_page_path))
            canva_source.thumbnail = thumbnail_src
            canva_source.export_file = thumbnail_src ###   export_img_src same as thumbnail_src
            canva_source.save()
            # if thumbnail_page_path and os.path.exists(thumbnail_page_path):
            #     os.remove(thumbnail_page_path)
            # print('path exist',os.path.exists(thumbnail_page_path))

        elif thumbnail_src and src_page:
            canva_source = CanvasSourceJsonFiles.objects.get(canvas_design=instance,page_no=src_page)
            # thumbnail_page_path = canva_source.thumbnail.path if canva_source.thumbnail else ""
            # print("thumbnail_page_path------>",thumbnail_page_path)
            # print('path exist',os.path.exists(thumbnail_page_path))
            thumbnail_src = self.thumb_create(json_str=canva_source.json,formats='png',multiplierValue=1)
            canva_source.thumbnail = thumbnail_src
            canva_source.export_file = thumbnail_src  ##export_img_src same as thumbnail_src
            canva_source.save()   
            # if thumbnail_page_path and os.path.exists(thumbnail_page_path):
            #     os.remove(thumbnail_page_path)
            # print('path exist',os.path.exists(thumbnail_page_path))

        if validated_data.get('temp_global_design',None):
            temp_global_design = validated_data.get('temp_global_design')
            temp_pages = temp_global_design.template_globl_pag.all()
            page_len = len(instance.canvas_json_src.all())
            for temp_page in temp_pages:
                thumbnail_page = temp_page.thumbnail_page
                export_page = temp_page.export_page
                json_page = temp_page.json_page
                page_len+=1
                # thumbnail_page = self.thumb_create(json_str=json_page,formats='png',multiplierValue=1)
                CanvasSourceJsonFiles.objects.create(canvas_design=instance,thumbnail=thumbnail_page,
                                                     export_file=export_page,json=json_page,page_no=page_len)
        if validated_data.get('my_temp',None):
            my_temp = validated_data.get('my_temp')
            my_temp_pages = my_temp.my_template_page.all()
            page_len = len(instance.canvas_json_src.all())
            for my_temp_page in my_temp_pages:
                thumbnail_page = my_temp_page.my_template_thumbnail
                export_page = my_temp_page.my_template_export
                json_page = my_temp_page.my_template_json
                page_len+=1
                CanvasSourceJsonFiles.objects.create(canvas_design=instance,thumbnail=thumbnail_page,
                                                     export_file=export_page,json=json_page,page_no=page_len)
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
        return data

class CanvasUserImageAssetsSerializer(serializers.ModelSerializer):
    image = serializers.FileField(required=False)
    class Meta:
        model = CanvasUserImageAssets
        fields = ("id","image_name","image")

    def create(self, validated_data):
        import cv2
        user =  self.context['request'].user
        data = {**validated_data ,'user':user}
        instance = CanvasUserImageAssets.objects.create(**data)
        if validated_data.get('image',None):
            extension=instance.image.path.split('.')[-1]
            if extension=='jpg':
                extension='jpeg'
            
            im = cv2.imread(instance.image.path)
            if extension !='svg':
                width, height,channel = im.shape
                if any([True if i>2048 else False for i in [width, height]]):
                    scale_val = min([2048/width, 2048/ height])
                    new_width = round(scale_val*width)
                    new_height = round(scale_val*height)
                    im = cv2.resize(im , (new_height,new_width))
                    content= image_content(im)
                    im = core.files.base.ContentFile(content,name=instance.image.name.split('/')[-1])
                    instance.image = im
                    instance.save()
        return instance
    
####################################################################################################
class TemplatePageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplatePage
        fields = '__all__'

class TemplateGlobalDesignSerializer(serializers.ModelSerializer):
    file_name = serializers.CharField(required= True)
    # template_globl_pag = TemplatePageSerializer(many = True,required=False)
    thumbnail_page = serializers.FileField(required=False,write_only=True)
    export_page = serializers.FileField(required=False,write_only=True)
    json_page = serializers.JSONField(required=False,write_only=True,initial=dict)
    # user_name = serializers.CharField(required=False)
    page_no = serializers.CharField(required=False)
    class Meta:
        model = TemplateGlobalDesign
        fields = ('id','width','height','thumbnail_page', 'export_page','file_name',
                  'page_no','json_page') # ,'' ,'user_name' 'template_globl_pag', 'export_page, file_name
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        template_page_first = TemplatePage.objects.filter(template_page = instance).first()
        if template_page_first:
            if template_page_first.thumbnail_page:
                data['thumbnail_page'] = template_page_first.thumbnail_page.url
            else:
                data['thumbnail_page'] = None
        return data

    def thumb_create(self,json_str,formats,multiplierValue):
        thumb_image_content=thumbnail_create(json_str=json_str,formats=formats)
        thumb_name=self.instance.file_name+'_thumbnail.png' if self.instance and self.instance.file_name else 'thumbnail.png'
        thumbnail_src=core.files.File(core.files.base.ContentFile(thumb_image_content),thumb_name)
        return thumbnail_src

    def create(self, validated_data):
        thumbnail_page = validated_data.pop('thumbnail_page',None)
        export_page = validated_data.pop('export_page',None)
        json_page = validated_data.pop('json_page',None)
        instance = TemplateGlobalDesign.objects.create(**validated_data)
        self.instance = instance
        if json_page:
            thumbnail_page = self.thumb_create(json_str=json_page,formats='png',multiplierValue=1)
            TemplatePage.objects.create(template_page=instance,thumbnail_page=thumbnail_page,export_page=export_page,
                                        json_page=json_page,page_no=1)
        return instance


    def update(self, instance, validated_data):
        instance.file_name=validated_data.get('file_name',instance.file_name)
        instance.width = validated_data.get('width',instance.width)
        instance.height = validated_data.get('height',instance.height)
        json_page = validated_data.pop('json_page',None)
        page_no = validated_data.pop('page_no',None)
        thumbnail_page = validated_data.pop('thumbnail_page',None)
        export_page = validated_data.pop('export_page',None)
        if json_page and page_no:
            if TemplatePage.objects.filter(page_no=page_no).exists():
                template_page_update=TemplatePage.objects.get(template_page=instance,page_no=page_no)
                if json_page:
                    thumbnail_page = self.thumb_create(json_str=json_page,formats='png',multiplierValue=1)
                    template_page_update.json_page = json_page
                    template_page_update.thumbnail_page = thumbnail_page
                if export_page:
                    template_page_update.export_page = export_page
                template_page_update.save()
            else:
                thumbnail_page = self.thumb_create(json_str=json_page,formats='png',multiplierValue=1)
                TemplatePage.objects.create(template_page=instance,thumbnail_page=thumbnail_page,export_page=export_page,
                                        json_page=json_page,page_no=page_no)
        if validated_data.get('template_global_id',None):
            template_global_id = validated_data.get('template_global_id')
        return instance 
    

class TemplateGlobalDesignRetrieveSerializer(serializers.ModelSerializer):
    template_globl_pag = TemplatePageSerializer(many = True,required=False)
    class Meta:
        model = TemplateGlobalDesign
        fields = ('id','file_name','width','height','template_globl_pag',) #,'user_name'


class MyTemplateDesignPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyTemplateDesignPage
        fields = '__all__'

class MyTemplateDesignSerializer(serializers.ModelSerializer):
    template_global_id = serializers.PrimaryKeyRelatedField(queryset=TemplateGlobalDesign.objects.all(),required=False)
    canvas_design_id = serializers.PrimaryKeyRelatedField(queryset=CanvasDesign.objects.all(),required=False)
    # canvas_lang_id =  serializers.PrimaryKeyRelatedField(queryset=Languages.objects.all(),required=False)
    canvas_trans_id = serializers.PrimaryKeyRelatedField(queryset=CanvasTranslatedJson.objects.all(),required=False)
    class Meta:
        model = MyTemplateDesign
        fields =  ('id','width','height','template_global_id','canvas_design_id','canvas_trans_id')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        template_page_first = MyTemplateDesignPage.objects.filter(my_template_design = instance).first()
        if template_page_first:
            if template_page_first.my_template_thumbnail:
                data['my_template_thumbnail'] = template_page_first.my_template_thumbnail.url
            else:
                data['my_template_thumbnail'] = None

            # if template_page_first.my_template_export:
            #     data['my_template_export'] = template_page_first.my_template_export.url
            # else:
            #     data['my_template_export'] = None
        return data

    def create(self, validated_data):
        template_global_id = validated_data.pop('template_global_id',None)
        canvas_design_id = validated_data.pop('canvas_design_id',None)
        canvas_trans_id = validated_data.pop('canvas_trans_id',None)
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
                    my_template_export=glob_pag.export_page
                    my_template_json=glob_pag.json_page
                    page_no=glob_pag.page_no
                    MyTemplateDesignPage.objects.create(my_template_design=my_temp_design,my_template_thumbnail=my_template_thumbnail,
                                                        my_template_export=my_template_export,my_template_json=my_template_json,page_no=page_no)
             
        if canvas_design_id:
            file_name=canvas_design_id.file_name
            width=canvas_design_id.width
            height=canvas_design_id.height
            canvas_translate_json_inst = canvas_design_id.canvas_translate
            my_temp_design = MyTemplateDesign.objects.create(file_name=file_name,width=width,height=height,user=user)
            if canvas_trans_id:
                can_trans_ins = canvas_translate_json_inst.get(id=canvas_trans_id.id)
                                                #canvas_translate__source_language=canvas_translate_json_inst.canvas_translate.last().source_language,
                can_trans_ins = can_trans_ins.canvas_json_tar.first()
                my_template_thumbnail = can_trans_ins.thumbnail
                my_template_export=can_trans_ins.export_file
                my_template_json=can_trans_ins.json
                page_no=can_trans_ins.page_no
                MyTemplateDesignPage.objects.create(my_template_design=my_temp_design,my_template_thumbnail=my_template_thumbnail,
                                                    my_template_export=my_template_export,my_template_json=my_template_json,page_no=page_no)
            else:
                canvas_source_json_inst = canvas_design_id.canvas_json_src.last()
                my_template_thumbnail = canvas_source_json_inst.thumbnail
                my_template_export=canvas_source_json_inst.export_file
                my_template_json=canvas_source_json_inst.json
                page_no=canvas_source_json_inst.page_no
                MyTemplateDesignPage.objects.create(my_template_design=my_temp_design,my_template_thumbnail=my_template_thumbnail,
                                                    my_template_export=my_template_export,my_template_json=my_template_json,page_no=page_no)
                
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



from ai_canvas.utils import install_font
class FontFileSerializer(serializers.ModelSerializer):
    class Meta:
        model=FontFile
        fields='__all__'

    def to_representation(self, instance):
        rep=super().to_representation(instance)
        if rep.get('font_family',None):
            rep['font_family']=instance.font_family.url
        return rep

    def create(self, validated_data):
 
        instance=FontFile.objects.create(**validated_data)
        if instance.font_family:
            install_font(instance.font_family.path)
        return instance
    