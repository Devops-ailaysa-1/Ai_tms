from ai_imagetranslation.models import (Imageload,ImageInpaintCreation,ImageTranslate,BackgroundRemovel,BackgroundRemovePreviewimg,
                                        StableDiffusionAPI,ImageTranslateResizeImage,CustomImageGenerationStyle,ImageStyleCategories,
                                            ImageModificationTechnique,CustomImageGenerationStyle,ImageStyleCategories,
                                            GeneralPromptList,ImageStyleSD,AspectRatio,SDImageResolution)
from ai_staff.models import Languages
from rest_framework import serializers
from PIL import Image
from ai_imagetranslation.utils import inpaint_image_creation ,image_content,stable_diffusion_api,stable_diffusion_public
from ai_workspace_okapi.utils import get_translation
from django import core
from django.db.models import Case, When
from ai_canvas.utils import thumbnail_create
import copy,os,cv2,numpy
from ai_canvas.utils import convert_image_url_to_file 
from ai_imagetranslation.utils import background_remove,background_merge ,create_thumbnail_img_load
from ai_canvas.template_json import img_json,basic_json
from ai_canvas.models import CanvasUserImageAssets
from ai_canvas.serializers import create_design_jobs_and_tasks
import io
from ai_workspace.models import ProjectType,Project,Steps,ProjectSteps
HOST_NAME=os.getenv('HOST_NAME')




class ImageloadSerializer(serializers.ModelSerializer):
    image_asset_id=serializers.PrimaryKeyRelatedField(queryset=CanvasUserImageAssets.objects.all(),required= False)
    class Meta:
        model = Imageload
        fields = ('id','image','file_name','types','height','width','thumbnail','image_asset_id')
    
 

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
    mask_json=serializers.JSONField(required=False)
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
            representation['source_language']=instance.source_language_for_translate.language.id 
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
        return width,height #thumb_nail
    
    def create(self, validated_data):
        # user=self.context['request'].user

        request = self.context['request']
        user = request.user.team.owner  if request.user.team  else request.user
        created_by = request.user
        magic_erase=validated_data.pop('magic_erase')

        project_type = ProjectType.objects.get(id=6)
        default_step = Steps.objects.get(id=1)
        project_instance = Project.objects.create(project_type =project_type, ai_user=user,created_by=user)
        project_steps = ProjectSteps.objects.create(project=project_instance,steps=default_step)


        data={**validated_data ,'user':user}
        if validated_data.get('image',None):
            instance=ImageTranslate.objects.create(**data)
            width,height=self.image_shape(instance.image.path)
            instance.width=width
            instance.height=height
            instance.created_by=created_by
            # instance.mask_json=mask_json
            # instance.thumbnail=thumb_nail
            instance.types=str(validated_data.get('image')).split('.')[-1]
            instance.project = project_instance
            instance.project_name = project_instance.project_name
            # if not instance.project_name:
            #     img_obj=ImageTranslate.objects.filter(user=instance.user.id,project_name__icontains='Untitled project')
            #     if img_obj:
            #         instance.project_name='Untitled project ({})'.format(str(len(img_obj)+1))
            #     else:
            #         instance.project_name='Untitled project'
            instance.save()
            return instance
    
    def target_check(self,instance,target_list,src_lang):
        for tar_lang in target_list:
            if ImageInpaintCreation.objects.filter(source_image=instance,target_language=tar_lang.locale.first(),
                                                   source_image__source_language_for_translate=src_lang).exists():
                raise serializers.ValidationError({"msg":"language pair already exists"})
    
    def img_trans(self,instance,inpaint_creation_target_lang,src_lang):
        if not instance.source_canvas_json:
            raise serializers.ValidationError({'msg':'source json is not sent'})
        tar_json_copy=copy.deepcopy(instance.source_canvas_json)
        tar_json_copy['background']="rgba(231,232,234,0)"
        for tar_lang in inpaint_creation_target_lang:
            lang_dict={'source_language':src_lang,'target_language':tar_lang}
            print(src_lang , type(src_lang))

            ##############job__creations#############

            tar_bbox=ImageInpaintCreation.objects.create(source_image=instance,source_language=src_lang.locale.first(),
                                                         target_language=tar_lang.locale.first()) 
            img_trans_jobs,img_trans_tasks=create_design_jobs_and_tasks([lang_dict], instance.project)
            #print("JB & Tasks----------------------->", img_trans_jobs,img_trans_tasks)
            tar_bbox.job=img_trans_jobs[0][0]
            ########## job__creation #####
            
            tar_json_copy['projectid']={'langId':tar_bbox.id,'langNo':src_lang.id ,"pages": 1,
                                            "page":1,'projId':instance.id,'projectType':'image-translate'}
            for i in tar_json_copy['objects']:
                if 'text' in i.keys():
                    translate_bbox=get_translation(1,source_string=i['text'],source_lang_code=instance.source_language_for_translate.locale_code,
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
                try: i.job.delete()
                except: pass
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
            instance.source_language_for_translate = src_lang.locale.first()
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
           
            # thumb_image=thumbnail_create(image_inpaint_create.target_canvas_json,formats='png')
            # thumb_image=core.files.File(core.files.base.ContentFile(thumb_image),'thumb_image.png')
            # image_inpaint_create.thumbnail=thumb_image
            # image_inpaint_create.save()
            instance.save()
            return instance

        if inpaint_creation_target_lang:
            if not instance.source_language_for_translate:
                raise serializers.ValidationError({'msg':'source language not selected'})
            lang_locale = instance.source_language_for_translate
            src_lang=instance.source_language_for_translate.language #instance.source_language_for_translate is languagelocale obj inside img_trans fun again convert to language locale
            print(src_lang) #source_language_for_translate.language is language obj
            self.target_check(instance,inpaint_creation_target_lang,lang_locale)
            self.img_trans(instance,inpaint_creation_target_lang,src_lang)
            instance.save()
            return instance

        ####update for target and source json 
        
        if validated_data.get('mask_json'): #also creation of mask image using node server  ###changes
            if not instance.s_im.all():
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
            if im_cre.source_image.source_language_for_translate == im_cre.target_language:
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
                'thumbnail','source_language_for_translate','image_load','image')

class BackgroundRemovePreviewimgSerializer(serializers.ModelSerializer):
    class Meta:
        model=BackgroundRemovePreviewimg
        fields=('id','image_url')


class BackgroundRemovelSerializer(serializers.ModelSerializer):
    # canvas_json=serializers.JSONField(required=False)
    preview_json=serializers.JSONField(required=False)
    back_ground_rm_preview_im=BackgroundRemovePreviewimgSerializer(many=True,required=False)
    canvas_json=serializers.JSONField(required=True)
    eraser_transparent_json=serializers.JSONField(required=False)
    # back_ground_mask=serializers.JSONField(required=False)
    class Meta:
        model=BackgroundRemovel
        fields=('id','image_json_id','image_url','image','canvas_json','preview_json','back_ground_rm_preview_im',
                'eraser_transparent_json','mask','eraser_transparent_mask') #back_ground_mask
        
        extra_kwargs={'image_url':{'write_only':True},
                      'image_json_id':{'write_only':True},
                      'image':{'write_only':True},
                      }
        
    def to_representation(self, instance):
        representation=super().to_representation(instance)
        if instance.mask:
            representation['mask'] = HOST_NAME+instance.mask.url
        return representation

    def create(self, validated_data):
        user=self.context['request'].user
        canvas_json=validated_data.get('canvas_json',None)
        preview_json=validated_data.get('preview_json',None)
        
        if canvas_json: 
            data={'image_url':canvas_json['src'],'image_json_id':canvas_json['name'] ,'user':user}
            instance=BackgroundRemovel.objects.create(**data)
            image_path_create=convert_image_url_to_file(instance.image_url)
            instance.original_image=image_path_create
            instance.save()
            back_ground_create=background_remove(instance)
            instance.image=back_ground_create
            instance.save()
            tar_json=copy.deepcopy(canvas_json)
            tar_json['sourceImage']=HOST_NAME+instance.original_image.url
            # preview_json=copy.deepcopy(preview_json)
            tar_json['src']=HOST_NAME+instance.image.url
            tar_json['bgMask'] = HOST_NAME+instance.mask.url
            tar_json['brs']=2
            tar_json['bgId']=instance.id
            # preview_json['brs']=2
            # preview_json['src']=HOST_NAME+instance.image.url
            instance.back_ground_rm_preview_im.create(image_url=instance.image.url)
            instance.canvas_json =tar_json
            instance.save()
            return instance
        else:
            raise serializers.ValidationError("no canvas_json is loaded")
    
    def update(self, instance, validated_data):
        image_url=validated_data.get('image_url',None)
        # erase_mask_json=validated_data.get('erase_mask_json',None)
        # back_ground_mask=validated_data.get('back_ground_mask',None)
        eraser_transparent_json=validated_data.get('eraser_transparent_json',None)
        if image_url:
            instance.back_ground_rm_preview_im.create(image_url=image_url)
        
        if eraser_transparent_json:
            eraser_transparent_mask=thumbnail_create(eraser_transparent_json,formats='backgroundMask') 
            instance.mask=core.files.File(core.files.base.ContentFile(eraser_transparent_mask),'background_mask_image.jpg')
            instance.save()
            mask_img = numpy.asarray(Image.open(instance.mask.path).convert("RGB"))
            original_img=cv2.imread(instance.original_image.path)
            back_ground_create=background_merge(mask_img,original_img)
            instance.image=back_ground_create
            instance.save()
            tar_json=copy.deepcopy(instance.canvas_json)
            # preview_json=copy.deepcopy(instance.preview_json)
            tar_json['src']=HOST_NAME+instance.image.url
            tar_json['bgMask'] = HOST_NAME+instance.mask.url
            # preview_json['src']=HOST_NAME+instance.image.url
            instance.back_ground_rm_preview_im.create(image_url=instance.image.url)
            instance.canvas_json =tar_json
            instance.save()
        return instance


class StableDiffusionAPISerializer(serializers.ModelSerializer):
    prompt=serializers.CharField(allow_null=True,required=True)
    sdstylecategoty=serializers.PrimaryKeyRelatedField(queryset=ImageStyleSD.objects.all(),required=False,write_only=True)
    negative_prompt=serializers.CharField(allow_null=True,required=False,write_only=True)
    image_resolution=serializers.PrimaryKeyRelatedField(queryset=SDImageResolution.objects.all(),required=True,write_only=True)
    # step = serializers.IntegerField(required=True)
    class Meta:
        fields = ("id",'prompt','image','negative_prompt','sdstylecategoty','thumbnail','image_resolution','celery_id','status')   #image_resolution step
        model=StableDiffusionAPI


    # def to_representation(self, instance):
    #     representation=super().to_representation(instance)
    #     if instance.image:
    #         representation['image'] = HOST_NAME+"/"+ os.path.join("media",instance.image.name)
    #     if instance.thumbnail :
    #         representation['thumbnail'] = HOST_NAME+"/"+ os.path.join("media",instance.thumbnail.name)
    #     return representation

    def create(self, validated_data):
        user=self.context['request'].user
        prompt=validated_data.get('prompt',None)
        step=validated_data.pop('step',None)
        sdstylecategoty=validated_data.pop('sdstylecategoty',None)
        negative_prompt = validated_data.pop('negative_prompt',None)
        image_resolution=validated_data.pop('image_resolution',None)

        if sdstylecategoty.style_name not in ["None"]:
            default_prompt = sdstylecategoty.default_prompt
            if sdstylecategoty.negative_prompt:
                negative_prompt=str(negative_prompt)+" "+sdstylecategoty.negative_prompt
                print("negative_prompt",negative_prompt)
            prompt = default_prompt.format(prompt)
        if not image_resolution:
            raise serializers.ValidationError({'no image resolution'}) 
        
        
        #prompt,steps,height,width,negative_prompt

        instance=StableDiffusionAPI.objects.create(user=user,used_api="stable",prompt=prompt,model_name="SDXL",style=sdstylecategoty.style_name,
                                                   height=image_resolution.height,width=image_resolution.width,steps=41,negative_prompt=negative_prompt)

        image=stable_diffusion_public.apply_async(args=(instance.id,),) #prompt,41,height,width,negative_prompt
        

        instance.celery_id=image
        instance.status="PENDING"
        instance.save()
        return instance

class ImageModificationTechniqueSerializers(serializers.ModelSerializer):

    class Meta:
        model = ImageModificationTechnique
        fields = ('id','custom_style_name','image')

    def to_representation(self, instance):
        representation=super().to_representation(instance)
        if representation.get('image' , None):
            representation['image']=HOST_NAME+instance.image.url
        return representation
        

   
class ImageStyleCategorySerializers(serializers.ModelSerializer):
    # style_category=ImageModificationTechniqueSerializers(many=True,read_only=True)
    style_category = serializers.SerializerMethodField()
    class Meta:
        model = ImageStyleCategories
        fields = ('id','style_category_name','style_category')

    def get_style_category(self, instance):
        songs = instance.style_category.all().order_by(Case(When(custom_style_name="None", then=0), default=1))
        return ImageModificationTechniqueSerializers(songs, many=True).data

class CustomImageGenerationStyleSerializers(serializers.ModelSerializer):
    style=ImageStyleCategorySerializers(many=True)
    class Meta:
        model = CustomImageGenerationStyle
        fields = ('id','style_name','style','image')


class GeneralPromptListStyleSerializers(serializers.ModelSerializer):
    class Meta:
        model =  GeneralPromptList
        fields = "__all__"

class ImageModificationTechniqueSerializerV2(serializers.ModelSerializer):
    class Meta:
        model =  ImageModificationTechnique
        fields = "__all__"
    
    def update(self, instance, validated_data):
        image = validated_data.get('image',None)
        instance.image=image
        instance.save()
        im=Image.open(instance.image.path).resize((100,100))
        im=convert_image_url_to_file(im,no_pil_object=False)
        instance.image=im
        instance.save()
        return instance

class ImageModificationTechniqueSerializerV3(serializers.ModelSerializer):
    class Meta:
        model =  ImageStyleSD
        fields = ("id","style_name","image",'negative_prompt')
    def update(self, instance, validated_data):
        image = validated_data.get('image',None)
        instance.image=image
        instance.save()
        im=Image.open(instance.image.path).resize((100,100))
        im=convert_image_url_to_file(im,no_pil_object=False)
        instance.image=im
        instance.save()
        return instance


class SDImageResolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model=SDImageResolution
        fields='__all__'

class AspectRatioSerializer(serializers.ModelSerializer):
    sd_image_res=SDImageResolutionSerializer(many=True)
    class Meta:
        model=AspectRatio
        fields=('id','sd_image_res','resolution')


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



        # if erase_mask_json:  ##
        #     mask_image=thumbnail_create(erase_mask_json,formats='mask') 
        #     image_data=core.files.File(core.files.base.ContentFile(mask_image),'mask_image.jpg')
        #     instance.mask=image_data
        #     mask_img = numpy.asarray(Image.open(image_data).convert("RGB"))
        #     original_img=cv2.imread(instance.image.path)
        #     back_ground_create=background_merge(mask_img,original_img)
        #     instance.image=back_ground_create
        #     instance.save()
        #     tar_json=copy.deepcopy(instance.canvas_json)
        #     preview_json=copy.deepcopy(instance.preview_json)
        #     tar_json['src']=HOST_NAME+instance.image.url
        #     tar_json['brs']=2
        #     preview_json['brs']=2
        #     preview_json['src']=HOST_NAME+instance.image.url
        #     instance.back_ground_rm_preview_im.create(image_url=instance.image.url)
        #     instance.canvas_json =tar_json
        #     instance.save()