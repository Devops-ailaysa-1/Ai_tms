from ai_imagetranslation.models import (Imageload,ImageInpaintCreation,ImageTranslate,BackgroundRemovel,BackgroundRemovePreviewimg,
                                        StableDiffusionAPI,ImageTranslateResizeImage,CustomImageGenerationStyle,ImageStyleCategories,
                                            ImageModificationTechnique,ImageGenCustomization)
from ai_staff.models import Languages
from rest_framework import serializers
from PIL import Image
from ai_imagetranslation.utils import inpaint_image_creation ,image_content,stable_diffusion_api,stable_diffusion_public
from ai_workspace_okapi.utils import get_translation
from django import core
from ai_canvas.utils import thumbnail_create
import copy,os,cv2,numpy
from ai_canvas.utils import convert_image_url_to_file 
from ai_imagetranslation.utils import background_remove,background_merge
from ai_canvas.template_json import img_json,basic_json
from ai_canvas.models import CanvasUserImageAssets
import pillow_avif,io
HOST_NAME=os.getenv('HOST_NAME')

def create_thumbnail_img_load(base_dimension,image):
    wpercent = (base_dimension/float(image.size[0]))
    hsize = int((float(image.size[1])*float(wpercent)))
    img = image.resize((base_dimension,hsize), Image.ANTIALIAS)
    # img=convert_image_url_to_file(image_url=img,no_pil_object=False)
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_byte_arr = img_io.getvalue()
    # instance.thumbnail=create_thumbnail_img_load(base_dimension=300,image=Image.open(instance.image.path))
    im=core.files.File(core.files.base.ContentFile(img_byte_arr),"thumbnail.png")
    return im


class ImageloadSerializer(serializers.ModelSerializer):
    image_asset_id=serializers.PrimaryKeyRelatedField(queryset=CanvasUserImageAssets.objects.all(),required= False)
    class Meta:
        model = Imageload
        fields = ('id','image','file_name','types','height','width','thumbnail','image_asset_id')
    
    # def to_representation(self, instance):
    #     data=super().to_representation(instance)
    #     if not data.get('thumbnail',None):
    #         im = Image.open(instance.image.path)
    #         instance.thumbnail=create_thumbnail_img_load(base_dimension=300,image=im)
    #         instance.save()
    #     return super().to_representation(instance)

    def create(self, validated_data):
        image_asset_id=validated_data.pop('image_asset_id',None)
        user =  self.context['request'].user
        if image_asset_id:
            if image_asset_id.image_name.endswith(".svg"):
                raise serializers.ValidationError("image should be in png or jpg format")
            instance=Imageload.objects.create(image=image_asset_id.image,user=user)
        else:
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
        instance.thumbnail=create_thumbnail_img_load(base_dimension=300,image=im)
        instance.save()
        return instance

# class TargetInpaintimageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TargetInpaintimage
#         fields = "__all__"


class ImageInpaintCreationListSerializer(serializers.ModelSerializer):
    # tar_im_create=TargetInpaintimageSerializer(many=True,read_only=True)
    class Meta:
        model = ImageInpaintCreation
        fields = ('id','source_image','target_language','thumbnail','created_at','updated_at')

    def to_representation(self, instance):
        representation=super().to_representation(instance)
        if representation.get('target_language',None):
            representation['target_language']=instance.target_language.language.id 
        if not representation.get('thumbnail',None):
            if instance.target_canvas_json:
                target_canvas_json=instance.target_canvas_json
                # print("target_canvas_json",target_canvas_json)
                if isinstance(target_canvas_json,dict) and  'backgroundImage' in target_canvas_json.keys():
                    target_canvas_json_bs64=thumbnail_create(json_str=target_canvas_json,formats='png')
                    name=instance.source_image.project_name
                    thumb_image=core.files.File(core.files.base.ContentFile(target_canvas_json_bs64),'thumbnail_{}.png'.format(name))
                    instance.thumbnail=thumb_image
                    instance.save()
        return representation


class ImageInpaintCreationSerializer(serializers.ModelSerializer):
    # tar_im_create=TargetInpaintimageSerializer(many=True,read_only=True)
    class Meta:
        model = ImageInpaintCreation
        fields = ('id','source_image','target_language','target_canvas_json','target_bounding_box','export','thumbnail','created_at','updated_at')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if representation.get('target_language' ,None):
            representation['target_language'] = instance.target_language.language.id   
        return representation





class ImageTranslateSerializer(serializers.ModelSerializer):  
    image_inpaint_creation=ImageInpaintCreationSerializer(source='s_im',many=True,read_only=True)
    inpaint_creation_target_lang=serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=Languages.objects.all()),required=False,write_only=True)
    bounding_box_target_update=serializers.JSONField(required=False)
    bounding_box_source_update=serializers.JSONField(required=False)
    target_update_id=serializers.IntegerField(required=False)
    source_canvas_json=serializers.JSONField(required=False)
    target_canvas_json=serializers.JSONField(required=False)
    thumbnail=serializers.FileField(required=False)
    export=serializers.FileField(required=False)
    source_language=serializers.PrimaryKeyRelatedField(queryset=Languages.objects.all(),required= False)
    image_to_translate_id=serializers.ListField(required =False,write_only=True)
    canvas_asset_image_id=serializers.PrimaryKeyRelatedField(queryset=CanvasUserImageAssets.objects.all(),required=False,write_only=True)
    magic_erase=serializers.BooleanField(required=False,default=False)
    image_translate_delete_target=serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=ImageInpaintCreation.objects.all()),required=False,write_only=True)
    image_id =serializers.PrimaryKeyRelatedField(queryset=Imageload.objects.all(),required=False,write_only=True)
    
    class Meta:
        model=ImageTranslate
        fields=('id','image','project_name','types','height','width','mask','mask_json','inpaint_image',
            'source_canvas_json','source_bounding_box','source_language','image_inpaint_creation',
            'inpaint_creation_target_lang','bounding_box_target_update','bounding_box_source_update',
            'target_update_id','target_canvas_json','thumbnail','export','image_to_translate_id','canvas_asset_image_id',
            'created_at','updated_at','magic_erase','image_translate_delete_target','image_load','image_id')
       
        
    def to_representation(self, instance):
        representation=super().to_representation(instance)
        if representation.get('source_language' , None):
            representation['source_language']=instance.source_language.language.id 
        if representation.get('image',None):
            representation['image']=instance.image.url
        if representation.get('mask',None):
            representation['mask']=instance.mask.url
        if representation.get('inpaint_image',None):
            representation['inpaint_image']=instance.inpaint_image.url  #
        if representation.get('create_inpaint_pixel_location',None):
            representation['create_inpaint_pixel_location']=instance.create_inpaint_pixel_location.url
        return representation
    
    @staticmethod
    def image_shape(image):
        im = Image.open(image)
        width, height = im.size
        #thumb_nail=create_thumbnail_img_load(base_dimension=300,image=im)
        return width,height #thumb_nail
    
    def create(self, validated_data):
        user=self.context['request'].user
        magic_erase=validated_data.pop('magic_erase')
        data={**validated_data ,'user':user}
        if validated_data.get('image',None):
            instance=ImageTranslate.objects.create(**data)
            width,height=self.image_shape(instance.image.path)
            instance.width=width
            instance.height=height 
            # instance.thumbnail=thumb_nail
            instance.types=str(validated_data.get('image')).split('.')[-1]
            if not instance.project_name:
                img_obj=ImageTranslate.objects.filter(user=instance.user.id,project_name__icontains='Untitled project')
                if img_obj:
                    instance.project_name='Untitled project ({})'.format(str(len(img_obj)+1))
                else:
                    instance.project_name='Untitled project'
            instance.save()
            return instance
    
    def target_check(self,instance,target_list,src_lang):
        for tar_lang in target_list:
            if ImageInpaintCreation.objects.filter(source_image=instance,target_language=tar_lang.locale.first(),
                                                   source_image__source_language=src_lang).exists():
                raise serializers.ValidationError({"msg":"language pair already exists"})
    
    def img_trans(self,instance,inpaint_creation_target_lang,src_lang):
        if not instance.source_canvas_json:
            raise serializers.ValidationError({'msg':'source json is not sent'})
        tar_json_copy=copy.deepcopy(instance.source_canvas_json)
        tar_json_copy['background']="rgba(231,232,234,0)"
        for tar_lang in inpaint_creation_target_lang:
            tar_bbox=ImageInpaintCreation.objects.create(source_image=instance,target_language=tar_lang.locale.first()) 
            tar_json_copy['projectid']={'langId':tar_bbox.id,'langNo':src_lang.id ,"pages": 1,
                                            "page":1,'projId':instance.id,'projectType':'image-translate'}
            for i in tar_json_copy['objects']:
                if 'text' in i.keys():
                    translate_bbox=get_translation(1,source_string=i['text'],source_lang_code=instance.source_language.locale_code,
                                                    target_lang_code=tar_lang.locale.first().locale_code)
                    i['text']=translate_bbox
                if i['name'] == "Background-static":
                    i['name']='Background-current'
            tar_bbox.target_canvas_json=tar_json_copy
            tar_bbox.save()
            thumb_image=thumbnail_create(tar_bbox.target_canvas_json,formats='png')
            thumb_image=core.files.File(core.files.base.ContentFile(thumb_image),'thumb_image.png')
            tar_bbox.thumbnail=thumb_image
            tar_bbox.save()

    def update(self, instance, validated_data):
        src_lang = validated_data.get('source_language' ,None)
        inpaint_creation_target_lang = validated_data.get('inpaint_creation_target_lang' ,None)
        image_to_translate_id = validated_data.get('image_to_translate_id',None)
        canvas_asset_image_id=validated_data.get('canvas_asset_image_id' ,None)
        mask_json=validated_data.get('mask_json')
        magic_erase=validated_data.get('magic_erase')
        bounding_box_source_update=validated_data.get('bounding_box_source_update',None)
        bounding_box_target_update=validated_data.get('bounding_box_target_update',None)
        target_update_id=validated_data.get('target_update_id',None)
        source_canvas_json=validated_data.get('source_canvas_json',None)
        target_canvas_json=validated_data.get('target_canvas_json',None)
        thumbnail=validated_data.get('thumbnail',None)
        export=validated_data.get('export',None)
        image_id=validated_data.get('image_id',None)
        image_translate_delete_target=validated_data.get('image_translate_delete_target',None)

        if magic_erase and mask_json:
            instance.mask_json=mask_json
            instance.save()
            inpaint_out_image,text_box_list=inpaint_image_creation(instance,magic_erase=True)
            content=image_content(inpaint_out_image)
            inpaint_image_file=core.files.File(core.files.base.ContentFile(content),"file.png")
            instance.inpaint_image=inpaint_image_file 
            instance.save()

        if image_translate_delete_target:
            for i in image_translate_delete_target:
                i.delete()

        if canvas_asset_image_id:
            instance.image=canvas_asset_image_id.image
            instance.height=canvas_asset_image_id.height
            instance.width=canvas_asset_image_id.width
            instance.save()
        
        if image_id:
            instance.image

        if validated_data.get('image'):
            instance.image = validated_data.get('image')
            width , height = self.image_shape(instance.image)
            instance.width = width
            instance.height = height
            instance.types  = str(validated_data.get('image')).split('.')[-1]
            
        if validated_data.get('project_name' ,None):
            instance.project_name = validated_data.get('project_name')
            instance.save()
            
        if validated_data.get('mask_json',None):
            instance.mask_json = validated_data.get('mask_json')
            instance.save()
            
        if src_lang :
            instance.source_language = src_lang.locale.first()
            instance.save()
            
        if inpaint_creation_target_lang and src_lang and mask_json: #and image_to_translate_id: ##check target lang and source lang
            self.target_check(instance,inpaint_creation_target_lang,src_lang.locale.first())
            thumb_mask_image=thumbnail_create(mask_json,formats='mask')
            mask_image=core.files.File(core.files.base.ContentFile(thumb_mask_image),'mask.png')
            instance.mask_json=mask_json
            instance.mask=mask_image
            instance.save()
            ####to create instance for source language
            if not instance.source_bounding_box:
                inpaint_out_image,source_bounding_box,text_box_list=inpaint_image_creation(instance,magic_erase=False)  
                src_json=copy.deepcopy(source_bounding_box)
                basic_json_copy=copy.deepcopy(basic_json)
                basic_json_copy['background']= "rgba(231,232,234,0)"
                instance.source_bounding_box=src_json 
                content=image_content(inpaint_out_image)
                inpaint_image_file=core.files.File(core.files.base.ContentFile(content),"file.png")
                instance.inpaint_image=inpaint_image_file 
                instance.save()
                img_json_copy=copy.deepcopy(img_json)
                img_json_copy['src']=HOST_NAME+instance.inpaint_image.url
                img_json_copy['width']=int(instance.width)
                img_json_copy['height']=int(instance.height)
                basic_json_copy['objects']=[img_json_copy]+text_box_list
                basic_json_copy['backgroundImage']['width']=int(instance.width)
                basic_json_copy['backgroundImage']['height']=int(instance.height)
                basic_json_copy['projectid']={'langId':None,'langNo':src_lang.id,"pages": 1,"page":1,'projId':instance.id,'projectType':'image-translate'}
                basic_json_copy['perPixelTargetFind']=False
                instance.source_canvas_json=basic_json_copy
                instance.save()
            inpaint_creation_target_lang.append(src_lang)
            self.img_trans(instance,inpaint_creation_target_lang,src_lang)
            # image_inpaint_create=ImageInpaintCreation.objects.create(source_image=instance,target_language=src_lang.locale.first(),target_canvas_json=basic_json_copy) 
            # thumb_image=thumbnail_create(image_inpaint_create.target_canvas_json,formats='png')
            # thumb_image=core.files.File(core.files.base.ContentFile(thumb_image),'thumb_image.png')
            # image_inpaint_create.thumbnail=thumb_image
            # image_inpaint_create.save()
            instance.save()
            return instance

        if inpaint_creation_target_lang:
            if not instance.source_language:
                raise serializers.ValidationError({'msg':'source language not selected'})
            src_lang=instance.source_language
            self.target_check(instance,inpaint_creation_target_lang,src_lang)
            self.img_trans(instance,inpaint_creation_target_lang,src_lang)
            instance.save()
            return instance

        ####update for target and source json 
        
        if validated_data.get('mask_json'): #also creation of mask image using node server  ###changes
            if not instance.s_im.all():
                print(instance.s_im.all())
                instance.mask_json=mask_json
                instance.save()
            else:
                instance.mask_json=mask_json
                thumb_mask_image=thumbnail_create(mask_json,formats='mask')
                mask=core.files.File(core.files.base.ContentFile(thumb_mask_image),'mask.png')
                instance.mask=mask
                instance.save()
                if not instance.inpaint_image:
                    raise serializers.ValidationError({'msg':"no object removal image is generated"})
                inpaint_out_image,_,text_box_list=inpaint_image_creation(instance,inpaintparallel=True,magic_erase=False)
                content=image_content(inpaint_out_image)
                inpaint_image_file=core.files.File(core.files.base.ContentFile(content),"inpaint_file.png")
                instance.inpaint_image=inpaint_image_file
                instance.save()
                source_canvas_json=copy.deepcopy(instance.source_canvas_json)
                obj_list=source_canvas_json['objects']
                obj_list[0]['src']=HOST_NAME+instance.inpaint_image.url
                source_canvas_json['objects']=obj_list+text_box_list
                instance.source_canvas_json=source_canvas_json
                instance.save()
                for tar_ins in instance.s_im.all():
                    if not tar_ins.target_canvas_json:
                        raise serializers.ValidationError({'msg':'target json not present'})
                    tar_json=copy.deepcopy(tar_ins.target_canvas_json)
                    text_box_list_new=[]
                    for text_box in text_box_list:
                        txt_box=copy.deepcopy(text_box)
                        if 'text' in txt_box:
                            translate_bbox=get_translation(1,source_string=txt_box['text'],source_lang_code='en',target_lang_code=tar_ins.target_language.locale_code)
                            txt_box['text']=translate_bbox
                        text_box_list_new.append(txt_box)
                    tar_json['objects'][0]['src']=HOST_NAME+instance.inpaint_image.url
                    obj_list=tar_json['objects']
                    tar_json['objects']=obj_list+text_box_list_new
                    tar_ins.target_canvas_json=tar_json
                    tar_ins.save()
            return instance
              
        if export and target_update_id:
            im_export=ImageInpaintCreation.objects.get(id=target_update_id,source_image=instance)
            im_export.export=export
            im_export.save()

        if thumbnail and target_update_id:
            im_thumbnail=ImageInpaintCreation.objects.get(id=target_update_id,source_image=instance)
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
            if im_cre.source_image.source_language == im_cre.target_language:
                print("src and tar id are same")
                im_cre.source_image.source_canvas_json=target_canvas_json
                im_cre.save()
            im_cre.target_canvas_json = target_canvas_json
            im_cre.save()
        return instance 



class ImageTranslateListSerializer(serializers.ModelSerializer):
    class Meta:
        model=ImageTranslate
        fields=('id','width','height','project_name','updated_at','created_at','types',
                'thumbnail','source_language','image_load','image')


def back_groung_rm_json_update():
    pass


class BackgroundRemovePreviewimgSerializer(serializers.ModelSerializer):
    class Meta:
        model=BackgroundRemovePreviewimg
        fields=('id','image_url')


class BackgroundRemovelSerializer(serializers.ModelSerializer):
    # canvas_json=serializers.JSONField(required=False)
    preview_json=serializers.JSONField(required=False)
    back_ground_rm_preview_im=BackgroundRemovePreviewimgSerializer(many=True,required=False)
    canvas_json=serializers.JSONField(required=True)
    erase_mask_json=serializers.JSONField(required=False)
    class Meta:
        model=BackgroundRemovel
        fields=('id','image_json_id','image_url','image','canvas_json','preview_json','back_ground_rm_preview_im','erase_mask_json')
        extra_kwargs={'image_url':{'write_only':True},
                      'image_json_id':{'write_only':True},
                      'image':{'write_only':True},}

    def create(self, validated_data):
        user=self.context['request'].user
        canvas_json=validated_data.get('canvas_json',None)
        preview_json=validated_data.get('preview_json',None)
        if canvas_json: 
            data={'image_url':canvas_json['src'],'image_json_id':canvas_json['name'] ,'user':user}
            instance=BackgroundRemovel.objects.create(**data)
            image_path_create=convert_image_url_to_file(instance.image_url)
            instance.image=image_path_create
            instance.save()
            back_ground_create=background_remove(instance.image.path)
            instance.image=back_ground_create
            instance.save()
            tar_json=copy.deepcopy(canvas_json)
            preview_json=copy.deepcopy(preview_json)
            tar_json['src']=HOST_NAME+instance.image.url
            tar_json['brs']=3
            preview_json['brs']=3
            preview_json['src']=HOST_NAME+instance.image.url
            instance.back_ground_rm_preview_im.create(image_url=instance.image.url)
            instance.canvas_json =tar_json
            instance.save()
            return instance
        else:
            raise serializers.ValidationError("no canvas_json is loaded")
    
    def update(self, instance, validated_data):
        image_url=validated_data.get('image_url',None)
        erase_mask_json=validated_data.get('erase_mask_json',None)
        if image_url:
            instance.back_ground_rm_preview_im.create(image_url=image_url)

        if erase_mask_json:  ##
            mask_image=thumbnail_create(erase_mask_json,formats='mask') 
            image_data=core.files.File(core.files.base.ContentFile(mask_image),'mask_image.jpg')
            mask_img = numpy.asarray(Image.open(image_data).convert("RGB"))
            original_img=cv2.imread(instance.image.path)
            back_ground_create=background_merge(mask_img,original_img)
            instance.image=back_ground_create
            instance.save()
            tar_json=copy.deepcopy(instance.canvas_json)
            preview_json=copy.deepcopy(instance.preview_json)
            tar_json['src']=HOST_NAME+instance.image.url
            tar_json['brs']=3
            preview_json['brs']=3
            preview_json['src']=HOST_NAME+instance.image.url
            instance.back_ground_rm_preview_im.create(image_url=instance.image.url)
            instance.canvas_json =tar_json
            instance.save()
        return instance

styles = {0:'3d-model',1:'analog-film',2:'anime',3:'cinematic' ,4:'comic-book' ,5:'digital-art',
  6:'enhance',7:'fantasy-art',8:'isometric',9:'line-art',10:'low-poly',11:'modeling-compound',12:'neon-punk',
  13:'origami',14:'photographic',15:'pixel-art',16:'tile-texture'}

samplers = {0:'DDIM',1:'DDPM',2:'K_DPMPP_2M',3:'K_DPMPP_2S_ANCESTRAL',4:'K_DPM_2',
           5:'K_DPM_2_ANCESTRAL',6:'K_EULER',7:'K_EULER_ANCESTRAL',8:'K_HEUN',9:'K_LMS'}

class StableDiffusionAPISerializer(serializers.ModelSerializer):
    # used_api=serializers.CharField(allow_null=True,required=True) 
    prompt=serializers.CharField(allow_null=True,required=True)
    # style =serializers.IntegerField(allow_null=True,required=True)
    # height=serializers.IntegerField(allow_null=True,required=True)
    # width=serializers.IntegerField(allow_null=True,required=True)
    # sampler=serializers.IntegerField(allow_null=True,required=True)
    negative_prompt=serializers.CharField(allow_null=True,required=False)
    class Meta:
        fields = ("id",'prompt','image','negative_prompt') #style height width sampler used_api
        model=StableDiffusionAPI

    def create(self, validated_data):
        user=self.context['request'].user
        # used_api=validated_data.get('used_api',None)
        prompt=validated_data.get('prompt',None)
        # style =validated_data.pop('style',None)
        # height=validated_data.pop('height',None)
        # width=validated_data.pop('width',None)
        # sampler=validated_data.pop('sampler',None)
        negative_prompt = validated_data.pop('negative_prompt',None)
        # if used_api == 'stability':
        #     image=stable_diffusion_api(prompt=prompt,weight=1,steps=20,height=height,negative_prompt=negative_prompt,width=width,
        #                                style_preset=styles[int(style)],sampler=samplers[int(sampler)])
        #     model_name='stable-diffusion-xl-beta-v2-2-2'
        # if used_api == 'stable_diffusion_api':
        image=stable_diffusion_public(prompt,weight=1,steps=31,height=512,width=512,
                                      style_preset="",sampler="",negative_prompt=negative_prompt)
        model_name='mid-j'
        instance=StableDiffusionAPI.objects.create(user=user,used_api="stable_diffusion_api",prompt=prompt,model_name=model_name,
                                                   style="",height=512,width=512,sampler="",negative_prompt=negative_prompt)
        instance.image=image
        instance.save()
        return instance
        


        # if target_update_id and mask_json:
        #     img_tar=ImageInpaintCreation.objects.get(id=target_update_id)
        #     img_tar.mask_json=mask_json
        #     thumb_mask_image=thumbnail_create(mask_json,formats='mask')
        #     mask=core.files.File(core.files.base.ContentFile(thumb_mask_image),'mask.png')
        #     img_tar.mask=mask
        #     img_tar.save()
        #     inpaint_out_image,_,text_box_list=inpaint_image_creation(img_tar)
        #     content=image_content(inpaint_out_image)
        #     inpaint_image_file=core.files.File(core.files.base.ContentFile(content),"inpaint_file.png")
        #     img_tar.inpaint_image=inpaint_image_file
        #     img_tar.save()
        #     text_box_list_new=[]
        #     for text_box in text_box_list:
        #         txt_box=copy.deepcopy(text_box)
        #         if 'text' in txt_box:
        #             translate_bbox=get_translation(1,source_string=txt_box['text'],source_lang_code='en',
        #                                              target_lang_code=img_tar.target_language.locale_code)
        #             txt_box['text']=translate_bbox
        #         text_box_list_new.append(txt_box)
        #     can_tar_json=copy.deepcopy(img_tar.target_canvas_json)
        #     obj_list=can_tar_json['objects']
        #     obj_list[0]['src']=HOST_NAME+img_tar.inpaint_image.url
        #     can_tar_json['objects']=obj_list+text_box_list_new
        #     img_tar.target_canvas_json=can_tar_json
        #     img_tar.save()
        #     return instance



class CustomImageGenerationStyleSerializers(serializers.ModelSerializer):
    class Meta:
        model = CustomImageGenerationStyle
        fields = '__all__'


class ImageModificationTechniqueSerializers(serializers.ModelSerializer):
    class Meta:
        model = ImageModificationTechnique
        fields = '__all__'
   
class ImageStyleCategorySerializers(serializers.ModelSerializer):
    style_category=ImageModificationTechniqueSerializers(many=True,read_only=True)

    class Meta:
        model = ImageStyleCategories
        fields = ('id','style_category')
 
class ImageGenCustomizationSerializers(serializers.ModelSerializer):
    custom_image_gen_style=CustomImageGenerationStyleSerializers(read_only=True,source='image_style')
    image_style_category=ImageStyleCategorySerializers(read_only=True,source='style_category')

    class Meta:
        model = ImageGenCustomization
        fields = ('id','custom_image_gen_style','image_style_category')




# class X1Serializer(serializers.ModelSerializer):
#     class Meta:
#         model=X1 
#         fields='__all__'

# class X3Serializer(serializers.ModelSerializer):
#     class Meta:
#         model=X3 
#         fields=('id','name')

# class X2Serializer(serializers.ModelSerializer):
#     x3data=X3Serializer(many=True, read_only=True)
#     class Meta:
#         model=X2 
#         fields=('id','name','x3data')


# class X4Serializer(serializers.ModelSerializer):
#     x1data=X1Serializer(read_only=True,source='x1_a')
#     x2data=X2Serializer(read_only=True,source='x1_b')
#     class Meta:
#         model=X4 
#         fields=('id','x1data','x2data')



# class ImageModificationSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ImageModification
#         fields = ('id','custom_style_name')

# class CustomImagePromptStyleModificationsSerializer(serializers.ModelSerializer):
#     custom_img_modification = ImageModificationSerializer(many=True,read_only=True)
#     class Meta:
#         model = CustomImagePromptStyleModifications
#         fields = ('id','modification_cat_name','custom_img_modification')

# class CustomImageGenerationCategotySerializer(serializers.ModelSerializer):
#     custom_img_gen_cat=CustomImagePromptStyleModificationsSerializer(many=True, read_only=True)
#     class Meta:
#         model = CustomImageGenerationCategoty
#         fields = ('id','name','custom_img_gen_cat')