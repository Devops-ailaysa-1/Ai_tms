from ai_imagetranslation.models import (Imageload,ImageInpaintCreation,ImageUpload)
from ai_staff.models import Languages
from rest_framework import serializers
from PIL import Image
from ai_imagetranslation.utils import inpaint_image_creation ,image_content
from ai_workspace_okapi.utils import get_translation
from django import core

class ImageloadSerializer(serializers.ModelSerializer):
    # image = serializers.FileField(required = True)
    
    class Meta:
        model = Imageload
        fields = ('id','image','file_name','types','height','width')
        
    
class ImageInpaintCreationSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ImageInpaintCreation
        fields = "__all__"
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if representation.get('target_language' ,None):
            representation['target_language'] = instance.target_language.language.id
        return representation
    


class ImageUploadSerializer(serializers.ModelSerializer):  
    image_inpaint_creation = ImageInpaintCreationSerializer(source= 's_im' ,many=True,read_only=True)
    inpaint_creation_target_lang = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=Languages.objects.all())
                            ,required=False,write_only=True)
    bounding_box_target_update = serializers.JSONField( required = False)
    bounding_box_source_update = serializers.JSONField( required = False)
    target_update_id = serializers.IntegerField(required = False)
    source_canvas_json =  serializers.JSONField(required = False)
    target_canvas_json = serializers.JSONField( required = False)
    thumbnail = serializers.FileField(required = False)
    export = serializers.FileField(required = False)
    source_language = serializers.PrimaryKeyRelatedField(queryset=Languages.objects.all() ,required= False)
    image_to_translate_id = serializers.ListField(required = False,write_only = True )
    
    
    class Meta:
        model = ImageUpload
        fields = ("id",'image','project_name','types','height','width','mask','mask_json','inpaint_image',
            'source_canvas_json','source_bounding_box','source_language','image_inpaint_creation',
            'inpaint_creation_target_lang','bounding_box_target_update','bounding_box_source_update',
            'target_update_id','target_canvas_json','thumbnail','export','image_to_translate_id',
            'created_at','updated_at')
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if representation.get('source_language' , None):
            representation['source_language'] = instance.source_language.language.id  
        return representation
    
    @staticmethod
    def image_shape(image):
        im = Image.open(image)
        width, height = im.size
        return width,height
    
    def to_internal_value(self, data):
        # print("data-->" , data)
        return super().to_internal_value(data)
    
    def create(self, validated_data):
        if validated_data.get('image'):
            image = validated_data['image']
            width , height = self.image_shape(image)
            validated_data['width'] = width
            validated_data['height'] = height
            validated_data['types']=  str(validated_data.get('image')).split('.')[-1]
        instance = ImageUpload.objects.create(**validated_data)
        return instance
            
    def update(self, instance, validated_data):
        if validated_data.get('image'):
            instance.image = validated_data.get('image')
            width , height = self.image_shape(instance.image)
            instance.width = width
            instance.height = height
            instance.types  = str(validated_data.get('image')).split('.')[-1]
        src_lang = validated_data.get('source_language' ,None)
        inpaint_creation_target_lang = validated_data.get('inpaint_creation_target_lang' ,None)
        image_to_translate_id = validated_data.get('image_to_translate_id' ,None)
        
        if validated_data.get('mask_json'):
            instance.mask_json = validated_data.get('mask_json')
            instance.save()
            
        if validated_data.get('project_name' ,None):
            instance.project_name = validated_data.get('project_name')
            # print("project_name-->" , instance.project_name)
            instance.save()
            
        if validated_data.get('mask'):
            instance.mask = validated_data.get('mask')
            instance.save()
            
        if src_lang :
            instance.source_language = src_lang.locale.first()
            instance.save()
            
        if inpaint_creation_target_lang and src_lang and image_to_translate_id: ##check target lang and source lang
            im_details = ImageUpload.objects.filter(id__in = image_to_translate_id)
            for im in im_details:
                inpaint_out_image , source_bounding_box = inpaint_image_creation(im)
                im.source_bounding_box = source_bounding_box
                content = image_content(inpaint_out_image)
                inpaint_image_file= core.files.File(core.files.base.ContentFile(content),"file.png")
                im.inpaint_image = inpaint_image_file 
                im.save()
                for tar_lang in inpaint_creation_target_lang:
                    tar_bbox =  ImageInpaintCreation.objects.create(source_image = im , 
                                                    target_language = tar_lang.locale.first() )  #tar_lang.locale.first()
                    source_bbox = source_bounding_box
                    for text in source_bbox.values(): 
                        translate_bbox = get_translation(text['text'],'en',tar_lang.locale.first().locale_code)
                        text['text'] = translate_bbox
                    tar_bbox.target_bounding_box = source_bbox
                    tar_bbox.save()
            return im
 
        ####update for target and source json 
        bounding_box_source_update = validated_data.get('bounding_box_source_update' ,None)
        bounding_box_target_update = validated_data.get('bounding_box_target_update' ,None)
        target_update_id = validated_data.get('target_update_id' ,None)
        source_canvas_json = validated_data.get('source_canvas_json' ,None)
        target_canvas_json = validated_data.get('target_canvas_json' ,None)
        thumbnail = validated_data.get('thumbnail' , None)
        export = validated_data.get('export' , None)
        
        if export and target_update_id:
            im_export = ImageInpaintCreation.objects.get(id = target_update_id , source_image = instance)
            im_export.export = export
            im_export.save()
        
        if thumbnail and target_update_id:
            im_thumbnail = ImageInpaintCreation.objects.get(id = target_update_id , source_image = instance)
            im_thumbnail.thumbnail = thumbnail
            im_thumbnail.save()
            
        if bounding_box_target_update and target_update_id:
            im_cre = ImageInpaintCreation.objects.get(id = target_update_id , source_image = instance)
            im_cre.target_bounding_box = bounding_box_target_update
            im_cre.save()
            
        if bounding_box_source_update:
            instance.source_bounding_box = bounding_box_source_update
            instance.save()
            
        if source_canvas_json:
             instance.source_canvas_json = source_canvas_json
             instance.save()
             
        if target_canvas_json and target_update_id:
            im_cre = ImageInpaintCreation.objects.get(id = target_update_id , source_image = instance)
            im_cre.target_canvas_json = target_canvas_json
            im_cre.save()
        return instance 
    
         