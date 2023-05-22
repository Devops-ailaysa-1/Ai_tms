from ai_imagetranslation.models import (Imageload,ImageInpaintCreation,ImageTranslate)
from ai_staff.models import Languages
from rest_framework import serializers
from PIL import Image
from ai_imagetranslation.utils import inpaint_image_creation ,image_content
from ai_workspace_okapi.utils import get_translation
from django import core
from ai_canvas.utils import thumbnail_create
import copy
class ImageloadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Imageload
        fields = ('id','image','file_name','types','height','width')
        
    def create(self, validated_data):
        user =  self.context['request'].user
        data = {**validated_data ,'user':user}
        instance =  Imageload.objects.create(**data)
        file_name = instance.image.name.split('/')[-1]
        types = file_name.split(".")[-1]
        instance.file_name = file_name
        instance.types = types
        im = Image.open(instance.image.path)
        width, height = im.size
        instance.height = height
        instance.width = width
        instance.save()
        return instance

from ai_canvas.template_json import img_json,basic_json
class ImageInpaintCreationSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ImageInpaintCreation
        fields = "__all__"
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if representation.get('target_language' ,None):
            representation['target_language'] = instance.target_language.language.id   
        return representation

class ImageTranslateSerializer(serializers.ModelSerializer):  
    image_inpaint_creation=ImageInpaintCreationSerializer(source='s_im',many=True,read_only=True)
    inpaint_creation_target_lang=serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=Languages.objects.all()),
                                                        required=False,write_only=True)
    bounding_box_target_update=serializers.JSONField(required=False)
    bounding_box_source_update=serializers.JSONField(required=False)
    target_update_id=serializers.IntegerField(required=False)
    source_canvas_json=serializers.JSONField(required=False)
    target_canvas_json=serializers.JSONField(required=False)
    thumbnail=serializers.FileField(required=False)
    export=serializers.FileField(required=False)
    source_language=serializers.PrimaryKeyRelatedField(queryset=Languages.objects.all(),required= False)
    image_to_translate_id=serializers.ListField(required =False,write_only=True)
    # image_id = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=Imageload.objects.all()),required=True)
    
    class Meta:
        model=ImageTranslate
        fields=('id','image','project_name','types','height','width','mask','mask_json','inpaint_image',
            'source_canvas_json','source_bounding_box','source_language','image_inpaint_creation',
            'inpaint_creation_target_lang','bounding_box_target_update','bounding_box_source_update',
            'target_update_id','target_canvas_json','thumbnail','export','image_to_translate_id',
            'created_at','updated_at')
        #,'image_id')
        
    def to_representation(self, instance):
        representation=super().to_representation(instance)
        if representation.get('source_language' , None):
            representation['source_language']=instance.source_language.language.id  
        return representation
    
    @staticmethod
    def image_shape(image):
        im = Image.open(image)
        width, height = im.size
        return width,height
    
    def create(self, validated_data):
        user =  self.context['request'].user
        data = {**validated_data ,'user':user}
        if validated_data.get('image',None):
            instance=ImageTranslate.objects.create(**data)
            width,height = self.image_shape(instance.image.path)
            instance.width=width
            instance.height=height 
            instance.types=str(validated_data.get('image')).split('.')[-1]
            instance.save()
            return instance
            
    def update(self, instance, validated_data):
        src_lang = validated_data.get('source_language' ,None)
        inpaint_creation_target_lang = validated_data.get('inpaint_creation_target_lang' ,None)
        image_to_translate_id = validated_data.get('image_to_translate_id' ,None)
        mask_json=validated_data.get('mask_json')
        if validated_data.get('image'):
 
            instance.image = validated_data.get('image')
            width , height = self.image_shape(instance.image)
            instance.width = width
            instance.height = height
            instance.types  = str(validated_data.get('image')).split('.')[-1]

        if validated_data.get('mask_json'): #also creation of mask image using node server  ###changes
            instance.mask_json = mask_json
            instance.save()
            
        if validated_data.get('project_name' ,None):
            instance.project_name = validated_data.get('project_name')
            instance.save()
            
        if validated_data.get('mask'):
            instance.mask = validated_data.get('mask')
            instance.save()
            
        if src_lang :
            instance.source_language = src_lang.locale.first()
            instance.save()
            
        if inpaint_creation_target_lang and src_lang and mask_json: #and image_to_translate_id: ##check target lang and source lang
            thumb_mask_image=thumbnail_create(mask_json,formats='mask')
            mask_image = core.files.File(core.files.base.ContentFile(thumb_mask_image),'mask.png')
            instance.mask_json=mask_json
            instance.mask=mask_image
            instance.save()
            ####to create instance for source language
            if not instance.source_bounding_box:
                inpaint_out_image,source_bounding_box,text_box_list=inpaint_image_creation(instance)  #inpaint_image_creation.apply_async((instance,),0)
                src_json=copy.deepcopy(source_bounding_box)
                basic_json_copy=copy.deepcopy(basic_json)
                instance.source_bounding_box=src_json 
                content=image_content(inpaint_out_image)
                inpaint_image_file=core.files.File(core.files.base.ContentFile(content),"file.png")
                instance.inpaint_image=inpaint_image_file 
                instance.save()
                img_json_copy=copy.deepcopy(img_json)
                img_json_copy['src']=instance.inpaint_image.file.url
                img_json_copy['width']=instance.width
                img_json_copy['height']=instance.height
                basic_json_copy['objects']=[img_json_copy].extend(text_box_list)
                basic_json_copy['width']=instance.width
                basic_json_copy['height']=instance.height
                instance.source_canvas_json=basic_json_copy
                instance.save()
            ####to create instance for target language
            for tar_lang in inpaint_creation_target_lang:
                tar_bbox=ImageInpaintCreation.objects.create(source_image=instance,target_language=tar_lang.locale.first())   
                source_bbox=source_bounding_box
                for text in source_bbox.values(): 
                    translate_bbox=get_translation(1,source_string=text['text'],source_lang_code='en',
                                                     target_lang_code=tar_lang.locale.first().locale_code)
                    text['text']=translate_bbox
                tar_bbox.target_bounding_box=source_bbox
                tar_bbox.save()
            instance.save()
            return instance
 
        ####update for target and source json 
        bounding_box_source_update=validated_data.get('bounding_box_source_update',None)
        bounding_box_target_update=validated_data.get('bounding_box_target_update',None)
        target_update_id=validated_data.get('target_update_id',None)
        source_canvas_json=validated_data.get('source_canvas_json',None)
        target_canvas_json=validated_data.get('target_canvas_json',None)
        thumbnail=validated_data.get('thumbnail',None)
        export=validated_data.get('export',None)
        
        if export and target_update_id:
            im_export=ImageInpaintCreation.objects.get(id = target_update_id , source_image = instance)
            im_export.export=export
            im_export.save()
        
        if thumbnail and target_update_id:
            im_thumbnail=ImageInpaintCreation.objects.get(id = target_update_id , source_image = instance)
            im_thumbnail.thumbnail=thumbnail
            im_thumbnail.save()
            
        if bounding_box_target_update and target_update_id:
            im_cre=ImageInpaintCreation.objects.get(id=target_update_id,source_image=instance)
            im_cre.target_bounding_box=bounding_box_target_update
            im_cre.save()
            
        if bounding_box_source_update:
            instance.source_bounding_box = bounding_box_source_update
            instance.save()
            
        if source_canvas_json:
             instance.source_canvas_json=source_canvas_json
             instance.save()
             
        if target_canvas_json and target_update_id:
            im_cre = ImageInpaintCreation.objects.get(id=target_update_id,source_image=instance)
            im_cre.target_canvas_json = target_canvas_json
            im_cre.save()
        return instance 



# class ImageloadRetrieveLSerializer(serializers.ModelSerializer):
#     image_inpaint_creation = ImageInpaintCreationSerializer(source='s_im',many=True,read_only=True)