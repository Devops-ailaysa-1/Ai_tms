from rest_framework import serializers
from ai_canvas.models import (CanvasTemplates,CanvasDesign,CanvasUserImageAssets,CanvasTranslatedJson,CanvasSourceJsonFiles,CanvasTargetJsonFiles,
                            TemplateGlobalDesign ,MyTemplateDesign,MyTemplateDesignPage,TextTemplate,TemplateKeyword,FontFile,
                            CanvasDownloadFormat,TemplateTag,TextboxUpdate,EmojiCategory,EmojiData,AiAssertscategory,AiAsserts,AssetCategory,AssetImage)
                            # PromptCategory,PromptEngine)#TemplatePage
from ai_staff.models import Languages,LanguagesLocale ,ImageCategories
   
from ai_staff.models import Languages,LanguagesLocale  
from django.http import HttpRequest
from ai_canvas.utils import json_src_change ,canvas_translate_json_fn,thumbnail_create,json_sr_url_change,install_font
from django import core
from ai_workspace_okapi.utils import get_translation
import copy
from ai_canvas.template_json import basic_json
from ai_staff.models import SocialMediaSize
from PIL import Image
import os
from django.db.models import Q
from ai_imagetranslation.utils import create_thumbnail_img_load,convert_image_url_to_file
from ai_canvas.models import AiAssertscategory,AiAsserts
from ai_workspace.models import ProjectType,Project,Steps,ProjectSteps
HOST_NAME=os.getenv("HOST_NAME")


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
        fields = ("id",'tranlated_json',"canvas_design",'source_language','target_language','created_at','updated_at','undo_hide_tar')
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

#
#
def get_or_none(classmodel, **kwargs):
    try:
        return classmodel.objects.get(**kwargs)
    except classmodel.DoesNotExist:
        return None

def create_design_jobs_and_tasks(data, project):
    print("creating job and task")
    print("Data----------->",data)
    from ai_workspace.models import Job,Task,TaskAssign
    j_klass = Job
    t_klass = Task
    canvas_jobs = Job.objects.bulk_create_of_design_project(data, project=project,klass=j_klass) 
    jobs = project.project_jobs_set.all()
    canvas_tasks = Task.objects.create_design_tasks_of_jobs(jobs=jobs,klass=t_klass)
    task_assign = TaskAssign.objects.assign_task(project=project)
    return canvas_jobs,canvas_tasks


 

from copy import deepcopy
def assigne_json_change(json_copy):
    json_cpy_2=copy.deepcopy(json_copy)
    if 'template_json' in  json_cpy_2.keys():
        for count ,i in enumerate(json_cpy_2['template_json']['objects']):
            if 'objects' in i.keys():
                assigne_json_change(i)
            # print(i.keys())
            # if 'evented'== i.keys():
                # print(i.keys())
            i['evented'] = False
            # if 'selectable'== i.keys():
            i['selectable'] =False
 
    else:
        for count, i in enumerate(json_cpy_2['objects']):
            if 'objects' in i.keys():
                assigne_json_change(i)
            # if 'evented'== i.keys():
            i['evented'] = False
            # if 'selectable'== i.keys():
            i['selectable'] =False
    return json_cpy_2


#serializers.ModelSerializer
class CanvasDesignSerializer(serializers.ModelSerializer): 
    source_json = CanvasSourceJsonFilesSerializer(source='canvas_json_src',many=True,read_only=True)
    source_json_file = serializers.JSONField(required=False,write_only=True)
    target_json_file = serializers.JSONField(required=False,write_only=True)
    thumbnail_src = serializers.FileField(allow_empty_file=False,required=False,write_only=True)
    export_img_src = serializers.FileField(allow_empty_file=False,required=False,write_only=True)
    #page_no = serializers.IntegerField(read_only=True)
    canvas_translation = serializers.SerializerMethodField()    
    #canvas_translation = CanvasTranslatedJsonSerializer(many=True,read_only=True,source='canvas_translate')
    canvas_translation_target = serializers.PrimaryKeyRelatedField(queryset=CanvasTranslatedJson.objects.all(),required=False,write_only=True)
    canvas_translation_tar_thumb = serializers.FileField(allow_empty_file=False,required=False,write_only=True)
    canvas_translation_tar_export = serializers.FileField(allow_empty_file=False,required=False,write_only=True)
    canvas_translation_tar_lang = serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=Languages.objects.all()),required=False,write_only=True)
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
    delete_target_design_lang=serializers.ListField(child=serializers.PrimaryKeyRelatedField(queryset=CanvasTranslatedJson.objects.all()),
                                        required=False,write_only=True)
    change_source_lang= serializers.PrimaryKeyRelatedField(queryset=Languages.objects.all(),required=False)
    assigned = serializers.ReadOnlyField(source='project.assigned')
    assign_enable = serializers.SerializerMethodField()
    # project_category=serializers.PrimaryKeyRelatedField(queryset=SocialMediaSize.objects.all(),required=False)
    # width=serializers.IntegerField(required=False)
    # height=serializers.IntegerField(required=False)
    #ProjectQuickSetupSerializer.Meta.fields +

    class Meta:
        model = CanvasDesign
        fields = ('id','file_name','project','source_json','width','height','created_at','updated_at',
                    'canvas_translation','canvas_translation_tar_thumb', 'canvas_translation_target',
                    'canvas_translation_tar_lang','source_json_file','src_page','thumbnail_src',
                    'export_img_src','src_lang','tar_page','target_json_file','canvas_translation_tar_export',
                    'temp_global_design','my_temp','target_canvas_json','next_page','duplicate','social_media_create','update_new_textbox',
                    'new_project','delete_target_design_lang','change_source_lang','assigned','assign_enable',) 
        
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
# canvas_translate.all()[0].job.job_tasks_set.last().task_info.last().task_assign_info
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get('assigned',None): #assign_enable assigned
            print("assigned")
            src_json = data['source_json']
            for count,i in enumerate(src_json):
                i = assigne_json_change(i['json'])
                src_json[count]['json'] = i   
            data['source_json'] = src_json
            return data 
        else:
            return data 

            
         
    
    # def get_assigned(self,obj):
    #     return obj.project.assigned

    def get_assign_enable(self, instance):
        user = self.context.get("request").user
        try:
            if instance.project.team:
                cached_value = True if ((instance.project.team.owner == user)\
                    or(instance.project.team.internal_member_team_info.all().\
                    filter(Q(internal_member_id = user.id) & Q(role_id=1)))\
                    or(instance.project.team.owner.user_info.all()\
                    .filter(Q(hired_editor_id = user.id) & Q(role_id=1))))\
                    else False
            else:
                cached_value = True if ((instance.project.ai_user == user) or\
                (instance.project.ai_user.user_info.all().filter(Q(hired_editor_id = user.id) & Q(role_id=1))))\
                else False
            return cached_value
        except: return None

    def get_canvas_translation(self,obj):
        user = self.context.get('user')
        pr_managers = self.context.get('managers')
        print("User------------->",user)
        print("Prmanagers--------------->",pr_managers)
        queryset = obj.canvas_translate.filter((Q(job__job_tasks_set__task_info__assign_to=user)\
                                                & Q(job__job_tasks_set__task_info__task_assign_info__isnull=False)\
                                                & Q(job__job_tasks_set__task_info__task_assign_info__task_ven_status='task_accepted'))\
                                                |Q(job__job_tasks_set__task_info__assign_to__in=pr_managers)|\
                                                Q(job__project__ai_user=user))
        
        return CanvasTranslatedJsonSerializer(queryset,many=True,read_only=True,source='canvas_translate').data

    def thumb_create(self,json_str,formats,multiplierValue):
        thumb_image_content= thumbnail_create(json_str=json_str,formats=formats)
        thumb_name = self.instance.file_name+'_thumbnail.png' if self.instance and self.instance.file_name else 'thumbnail.png'
        thumbnail_src = core.files.File(core.files.base.ContentFile(thumb_image_content),thumb_name)
        return thumbnail_src

    def create(self,validated_data):
        req_host=self.context.get('request', HttpRequest()).get_host()
        my_temp=validated_data.pop('my_temp',None)
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
        temp_global_design=validated_data.pop('temp_global_design',None)
        # project_category=validated_data.get('project_category',None)
        request = self.context['request']
        user = request.user.team.owner  if request.user.team  else request.user
        created_by = request.user
        # user = self.context['request'].user
        # project_type = ProjectType.objects.get(id=7)
        # project_instance =  Project.objects.create(project_type =project_type, ai_user=user,created_by=user)
        project_type = ProjectType.objects.get(id=6) #Designer Project
        default_step = Steps.objects.get(id=1)
        project_instance =  Project.objects.create(project_type =project_type, ai_user=user,created_by=user)
        project_steps = ProjectSteps.objects.create(project=project_instance,steps=default_step)
        print("prIns--------------->",project_instance)

        # if not social_media_create:
        #     raise serializers.ValidationError('no social_media_resolution')

        if my_temp:
            data = {**validated_data ,'user':user,'created_by':created_by}
            new_proj=CanvasDesign.objects.create(**data) #file_name
            project_instance.project_name = new_proj.file_name
            project_instance.save()
            page_instance = my_temp.my_template_page.first()
            # file_name = my_temp.file_name
            width = my_temp.width
            height = my_temp.height
            category=my_temp.project_category
            json = page_instance.my_template_json
            thumbnail = page_instance.my_template_thumbnail
            new_proj.height = height
            new_proj.width = width
            json['projectid']={"pages": 1,'page':1,"langId": None,"langNo": None,"projId": new_proj.id,
                                    "projectType": "design","project_category_label":category.social_media_name,"project_category_id":category.id}
            CanvasSourceJsonFiles.objects.create(canvas_design=new_proj,json=json,page_no=1,thumbnail=thumbnail)
            return new_proj

        if temp_global_design and new_project:
            name = temp_global_design.template_name
            width=temp_global_design.category.width
            height=temp_global_design.category.height
            json=temp_global_design.json
            category=temp_global_design.category
            thumbnail=temp_global_design.thumbnail_page
            user = self.context['request'].user
            new_proj=CanvasDesign.objects.create(user=user,width=width,height=height,created_by=created_by)
            new_proj.file_name = name
            project_instance.project_name = name
            project_instance.save()
            new_proj.project= project_instance
            # new_proj.file_name = project_instance.project_name
            new_proj.save()
            json['projectid']={"pages": 1,'page':1,"langId": None,"langNo": None,"projId": new_proj.id,
                                    "projectType": "design","project_category_label":category.social_media_name,"project_category_id":category.id}
            CanvasSourceJsonFiles.objects.create(canvas_design=new_proj,json=json,page_no=1,thumbnail=thumbnail)
            return new_proj  ###returned
        else:
            data = {**validated_data ,'user':user,'created_by':created_by}
            instance=CanvasDesign.objects.create(**data)
            instance.project = project_instance
            instance.file_name = project_instance.project_name
            instance.save()
            self.instance=instance
            #return instance

        
        # if not instance.file_name:
        #     print("Inside 1")
        #     can_obj=CanvasDesign.objects.filter(user=instance.user.id,file_name__icontains='Untitled project')
        #     # print("can_obj",can_obj)
        #     if can_obj:
        #         instance.file_name='Untitled project ({})'.format(str(len(can_obj)+1))
        #     else:
        #         instance.file_name='Untitled project' 
        #     instance.save()

        if source_json_file and social_media_create and width and height:
            source_json_file=json_src_change(source_json_file,req_host,instance,text_box_save=False)
            thumbnail_src=self.thumb_create(json_str=source_json_file,formats='png',multiplierValue=1) 
            can_json=CanvasSourceJsonFiles.objects.create(canvas_design=instance,json=source_json_file,page_no=1,thumbnail=thumbnail_src,export_file=export_img_src)
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

            instance.height=int(width)
            instance.width=int(height)
            instance.file_name=social_media_create.social_media_name
            project_instance.project_name = social_media_create.social_media_name
            project_instance.save()
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
            instance.file_name=social_media_create.social_media_name
            instance.save()
            project_instance.project_name = social_media_create.social_media_name
            project_instance.save()
            return instance
        return instance
              
          
    def update_text_box_target(self,instance,text_box,is_append):
        text=text_box['text']
        text_id=text_box['name']
        canvas_tar_lang=instance.canvas_translate.all()
        for tar_json in canvas_tar_lang:
            src=tar_json.source_language.locale_code
            tar=tar_json.target_language.locale_code
            for j in tar_json.canvas_json_tar.all():
                json=j.json
                if is_append:
                    copy_txt_box=copy.copy(text_box)
                    trans_text=get_translation(1,source_string=text,source_lang_code=src,target_lang_code=tar,user_id=instance.user.id)
                    copy_txt_box['text']=trans_text 
                    copy_txt_box['mt_text']=trans_text  ####appended new text_box
                    obj_list=json['objects']
                    obj_list.append(copy_txt_box)
                    j.save()
                else:
                    for tar_jsn in json['objects']:
                        if 'textbox' == tar_jsn['type'] and text_id == tar_jsn['name']:
                            tar_jsn['text']=get_translation(1,source_string=text,source_lang_code=src,target_lang_code=tar,user_id=instance.user.id)
                    j.save()

    def lang_translate(self,instance,src_lang,source_json_files_all,req_host,canvas_translation_tar_lang):
        for count,tar_lang in enumerate(canvas_translation_tar_lang):
            lang_dict={'source_language':src_lang,'target_language':tar_lang}
            if CanvasTranslatedJson.objects.filter(canvas_design=instance,source_language=src_lang.locale.first(),target_language=tar_lang.locale.first()).exists():
                pairs='language pair already exists {}_{}'.format(src_lang.locale.first().locale_code,tar_lang.locale.first().locale_code)
                raise serializers.ValidationError({'msg':pairs})
            if src_lang.locale.first() == tar_lang.locale.first():
                raise serializers.ValidationError({'msg':'looks like same language pair {} '.format(tar_lang.locale.first().locale_code)})
            trans_json=CanvasTranslatedJson.objects.create(canvas_design=instance,source_language=src_lang.locale.first(),target_language=tar_lang.locale.first())
            canvas_jobs,canvas_tasks=create_design_jobs_and_tasks([lang_dict], instance.project)
            trans_json.job=canvas_jobs[0][0]
            trans_json.save()
            trans_json_project=copy.deepcopy(trans_json.canvas_design.canvas_json_src.last().json)
            trans_json_project['projectid']['langNo']=trans_json.source_language.id
            for count,src_json_file in enumerate(source_json_files_all):
                src_json_file.json=json_src_change(src_json_file.json,req_host,instance,text_box_save=True)
                src_json_file.save()
                res=canvas_translate_json_fn(src_json_file.json,src_lang.locale.first().locale_code,tar_lang.locale.first().locale_code,instance.user.id)
                if res[tar_lang.locale.first().locale_code]:
                    tar_json_form=res[tar_lang.locale.first().locale_code]             
                    tar_json_thum_image=self.thumb_create(json_str=tar_json_form,formats='png',multiplierValue=1)
                    can_tar_ins=CanvasTargetJsonFiles.objects.create(canvas_trans_json=trans_json,thumbnail=tar_json_thum_image,json=tar_json_form,page_no=src_json_file.page_no)
                    tar_json_pro=can_tar_ins.json
                    tar_json_pro['projectid']={"pages":len(source_json_files_all),'page':count+1,"langId": trans_json.id,
                                                "langNo": tar_lang.id,"projId": instance.id,"projectType": "design"}
                    can_tar_ins.json=tar_json_pro
                    can_tar_ins.save()

        

    def resize_scale(self,source_json_file,width,height,canvas_width,canvas_height):
        scale_multiplier_x=width/canvas_width
        scale_multiplier_y=height/canvas_height
        for i in source_json_file['objects']:
            i['scaleX']=i['scaleX']*scale_multiplier_x
            i['scaleY']=i['scaleY']*scale_multiplier_x
            i['left']=i['left']*scale_multiplier_x
            i['top']=i['top']*scale_multiplier_y
        return source_json_file

    def update(self, instance, validated_data):
        print("------------------inside update-----------------------")
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
        my_temp=validated_data.pop('my_temp',None)
        update_new_textbox=validated_data.get('update_new_textbox',None)
        social_media_create=validated_data.get('social_media_create',None)
        width=validated_data.get('width',None)
        height=validated_data.get('height',None)
        new_project=validated_data.get('new_project',None)
        temp_global_design = validated_data.get('temp_global_design',None)
        delete_target_design_lang=validated_data.get('delete_target_design_lang',None)
        change_source_lang=validated_data.get('change_source_lang',None)
        name = validated_data.get('file_name',None)

        if name:
            instance.file_name = name
            proj_inst = Project.objects.get(id = instance.project.id)
            proj_inst.project_name =name
            proj_inst.save()
            instance.save()

        if change_source_lang:
            CanvasTranslatedJson.objects.filter(canvas_design=instance).update(source_language=change_source_lang.locale.first())

        if delete_target_design_lang:
            for i in delete_target_design_lang:
                try: i.job.delete()
                except: pass
                i.delete()

        if social_media_create and width and height: ##########################this one same fun below  ####custome resize
            # can_src=CanvasSourceJsonFiles.objects.get(canvas_design=instance,page_no=src_page)
            can_srcs=instance.canvas_json_src.all()
            for can_src in can_srcs:
                source_json_file=copy.deepcopy(can_src.json)
                source_json_file=self.resize_scale(source_json_file,width,height,instance.width,instance.height)
                source_json_file['projectid']['project_category_label']=social_media_create.social_media_name
                source_json_file['projectid']['project_category_id']=social_media_create.id
                source_json_file['backgroundImage']['width']=int(width)
                source_json_file['backgroundImage']['height']=int(height)
                can_src.json=source_json_file
                can_src.save()
            instance.width=int(width)
            instance.height=int(height)
            project_instance = Project.objects.get(id = instance.project.id)
            project_instance.project_name = social_media_create.social_media_name
            project_instance.save()
            instance.save()
            return instance

        if update_new_textbox and src_page:
            canvas_src_pages=instance.canvas_json_src.get(page_no=src_page)
            text_box=""
            json=canvas_src_pages.json
            for i in json['objects']:
                is_append=0
                if (i['type']=='textbox') and get_or_none(TextboxUpdate,text_id=i['name'],canvas=instance):
                    text_box_instance=TextboxUpdate.objects.get(text_id=i['name'],canvas=instance)
                    if text_box_instance.text != i['text']:
                        text_box_instance.text=i['text']
                        text_box_instance.save()
                        text_box=i
                elif (i['type']=='textbox') and ("isTranslate" in i.keys()) and (i['isTranslate'] == False):
                    text_box=i
                    TextboxUpdate.objects.create(canvas=instance,text=text_box['text'],text_id=text_box['name'])
                    is_append=1
                if text_box and ("text" in text_box.keys()):
                    self.update_text_box_target(instance,text_box,is_append)
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
            pages = len(instance.canvas_json_src.all())
            page=pages+1
            src_json_page=can_src.json
            src_json_page['projectid']={"pages": pages+1,'page':page,"langId": None,"langNo": None,"projId": instance.id,"projectType": "design"}

            CanvasSourceJsonFiles.objects.create(canvas_design=instance,json=src_json_page,thumbnail=can_src.thumbnail,page_no=len(instance.canvas_json_src.all())+1)

            for count,src_js in enumerate(instance.canvas_json_src.all()):
                src_js.json['projectid']['pages']=pages+1
                src_js.json['projectid']['page']=count+1
                src_js.save()


        if tar_page and canvas_translation and target_canvas_json:
            canvas_translation_tar_thumb = self.thumb_create(json_str=target_canvas_json,formats='png',multiplierValue=1) 
            CanvasTargetJsonFiles.objects.create(canvas_trans_json=canvas_translation,json=target_canvas_json ,
                                                 page_no=tar_page,thumbnail=canvas_translation_tar_thumb,export_file=canvas_translation_tar_export)

        if canvas_translation_tar_lang and src_lang:
            print("translating")
            source_json_files_all=instance.canvas_json_src.all()
            for count,src_json_file in enumerate(source_json_files_all):
                for text in src_json_file.json['objects']:
                    if text['type']== 'textbox' and 'name' in text.keys():
                        print("--------------------------",text['name'])
                        # text['evented'] = True
                        # text['']
                        TextboxUpdate.objects.get_or_create(canvas=instance,text=text['text'],text_id=text['name'])
            self.lang_translate(instance,src_lang,source_json_files_all,req_host,canvas_translation_tar_lang)
            return instance

        if canvas_translation_target and tar_page:         ######################Target__update
            canvas_trans = canvas_translation_target.canvas_json_tar.get(page_no=tar_page)
            canvas_translation_tar_thumb=self.thumb_create(json_str=canvas_trans.json,formats='png',multiplierValue=1) ##thumb
   
            canvas_trans.thumbnail=canvas_translation_tar_thumb ##thumb
            canvas_trans.thumbnail=thumbnail_src if thumbnail_src else canvas_trans.thumbnail
            canvas_trans.export_file=canvas_translation_tar_export
            if target_json_file:
                if hasattr(target_json_file ,'json'):
                    target_json_file = json_src_change(target_json_file.json,req_host,instance,text_box_save=False)
                canvas_trans.json = target_json_file
            canvas_trans.save()
            return instance

        if canvas_translation_tar_lang:
            src_lang=instance.canvas_translate.last().source_language.language
            source_json_files_all=instance.canvas_json_src.all()
            self.lang_translate(instance,src_lang,source_json_files_all,req_host,canvas_translation_tar_lang)
            return instance
 
        if source_json_file and src_page: ########################## source__update
            canva_source = CanvasSourceJsonFiles.objects.get(canvas_design=instance,page_no=src_page)
            # if '' not in source_json_file:
            #     source_json_file['projectid']={"pages": 1,'page':1,"langId": None,"langNo": None,"projId": instance.id,"projectType": "design"}
            source_json_file=json_sr_url_change(source_json_file,instance)
            canva_source.json = source_json_file           
            thumbnail_src = self.thumb_create(json_str=source_json_file,formats='png',multiplierValue=1) ##thumb
            canva_source.thumbnail = thumbnail_src ##thumb
            canva_source.save()

        if temp_global_design:
            src_json_page = temp_global_design.json #
            pages = len(instance.canvas_json_src.all())
            page=pages+1
            src_json_page['projectid']={"pages": pages+1,'page':page,"langId": None,"langNo": None,"projId": instance.id,"projectType": "design"}
            thumbnail_page = self.thumb_create(json_str=src_json_page,formats='png',multiplierValue=1)
            CanvasSourceJsonFiles.objects.create(canvas_design=instance,thumbnail=thumbnail_page,json=src_json_page,page_no=pages+1)
            for count,src_js in enumerate(instance.canvas_json_src.all()):
                src_js.json['projectid']['pages']=pages+1
                src_js.json['projectid']['page']=count+1
                src_js.save()
        
        if my_temp:
            page_instance = my_temp.my_template_page.first()
            thumbnail_page = page_instance.my_template_thumbnail
            src_json_page = page_instance.my_template_json
            pages = len(instance.canvas_json_src.all())
            page=pages+1
            src_json_page['projectid']={"pages": pages+1,'page':page,"langId": None,"langNo": None,"projId": instance.id,"projectType": "design"}
            CanvasSourceJsonFiles.objects.create(canvas_design=instance,thumbnail=thumbnail_page,json=src_json_page,page_no=pages+1)
            for count,src_js in enumerate(instance.canvas_json_src.all()):
                src_js.json['projectid']['pages']=pages+1
                src_js.json['projectid']['page']=count+1
                src_js.save()

        return super().update(instance=instance, validated_data=validated_data)
    

        # if my_temp:
        #     data = {**validated_data ,'user':user}
        #     new_proj=CanvasDesign.objects.create(**data)
        #     
        #     # file_name = my_temp.file_name
        #     width = my_temp.width
        #     height = my_temp.height
        #     category=my_temp.project_category
        #     
        #     
        #     new_proj.height = height
        #     new_proj.width = width
        #     json['projectid']={"pages": 1,'page':1,"langId": None,"langNo": None,"projId": new_proj.id,
        #                             "projectType": "design","project_category_label":category.social_media_name,"project_category_id":category.id}
        #     CanvasSourceJsonFiles.objects.create(canvas_design=new_proj,json=json,page_no=1,thumbnail=thumbnail)
        #     return new_proj


import io
def read_avif_image(image_path):
    output_buffer=io.BytesIO()
    image=Image.open(image_path)
    # image = image.convert('PNG')
    image.save(output_buffer, format="PNG", optimize=True, quality=96)
    compressed_data=output_buffer.getvalue()
    return compressed_data

class CanvasDesignListSerializer(serializers.ModelSerializer):
    thumbnail_src = serializers.FileField(allow_empty_file=False,required=False,write_only=True)
    translate_available = serializers.BooleanField(required=False,default=False)
    assigned = serializers.ReadOnlyField(source='project.assigned')
    assign_enable = serializers.SerializerMethodField()
    
    class Meta:
        model = CanvasDesign
        fields = ('id','project','assigned','assign_enable','file_name','width','height','thumbnail_src','translate_available','updated_at')
        
    
    def get_assign_enable(self, instance):
        user = self.context.get("request").user
        try:
            if instance.project.team:
                cached_value = True if ((instance.project.team.owner == user)\
                    or(instance.project.team.internal_member_team_info.all().\
                    filter(Q(internal_member_id = user.id) & Q(role_id=1)))\
                    or(instance.project.team.owner.user_info.all()\
                    .filter(Q(hired_editor_id = user.id) & Q(role_id=1))))\
                    else False
            else:
                cached_value = True if ((instance.project.ai_user == user) or\
                (instance.project.ai_user.user_info.all().filter(Q(hired_editor_id = user.id) & Q(role_id=1))))\
                else False
            return cached_value
        except: return None
    
    
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # if hasattr(instance.canvas_json_src.first(),'thumbnail'):
        if instance.canvas_json_src.first() and instance.canvas_json_src.first().thumbnail:
            # if 'thumbnail_src' in data.keys():
            data['thumbnail_src']= instance.canvas_json_src.first().thumbnail.url
        else:
            data['thumbnail_src'] = None
        if instance.canvas_translate.all():
            data['translate_available'] = True
        # if not instance.project_category:     
        #     data['project_category']
        return data

class CanvasUserImageAssetsSerializer(serializers.ModelSerializer):
    image = serializers.FileField(required=False)
    class Meta:
        model = CanvasUserImageAssets
        fields = ("id","image_name","image",'thumbnail','height','width',"status")

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
        user =  self.context.get('user')
        created_by = self.context.get('created_by')
        data = {**validated_data ,'user':user,'created_by':created_by}
        instance = CanvasUserImageAssets.objects.create(**data)
        if validated_data.get('image',None):
            extension=instance.image.path.split('.')[-1]
            if extension=='jpg':
                extension='jpeg'
            if extension == 'avif':
                image = read_avif_image(instance.image.path)
                im =core.files.base.ContentFile(image,name=instance.image.name.split('/')[-1])
                instance.image=im
                instance.save()
            # im = cv2.imread(instance.image.path)
            if not instance.image_name:
                instance.image_name=instance.image.path.split('/')[-1]
            if extension !='svg':
                im=Image.open(instance.image.path)
                width,height=im.size
                # height,width,_ = im.shape
                instance.thumbnail=create_thumbnail_img_load(base_dimension=300,image=im)
                instance.height=height
                instance.width=width
                instance.save()
                if any([True if i>2048 else False for i in [width, height]]):
                    scale_val = min([2048/width, 2048/ height])
                    new_width = round(scale_val*width)
                    new_height = round(scale_val*height)
                    im=im.resize((new_width,new_height))
                    # im=cv2.resize(im ,(new_width,new_height)) #
                    # content=image_content(im)
                    instance.height=new_width #  to change
                    instance.width=new_height
                    img_io = io.BytesIO()
                    im.save(img_io, format='PNG')
                    img_byte_arr = img_io.getvalue()
                    # instance.thumbnail=create_thumbnail_img_load(base_dimension=300,image=Image.open(instance.image.path))
                    im=core.files.File(core.files.base.ContentFile(img_byte_arr),instance.image.name.split('/')[-1])
                    # im =core.files.base.ContentFile(im.tobytes(),name=instance.image.name.split('/')[-1]) #content
                    instance.image=im
                    instance.save()
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
        fields=('id','template_tag','template_list','template_name','category','is_pro','is_published',
                'template_lang','description','thumbnail_page','json') #
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
        data['width']=instance.category.width
        data['height']=instance.category.height 
        return data

    def create(self, validated_data):
        template_list=validated_data.pop('template_list',None)
        if not template_list:raise serializers.ValidationError("need some tags")
        template_lists=template_list.split(",")
        instance = TemplateGlobalDesign.objects.create(**validated_data)
        json=copy.deepcopy(instance.json)
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
    template_global_categoty=TemplateGlobalDesignSerializerV2(many=True,required=False,allow_null=False)
    
    class Meta:
        fields=('id','template_global_categoty','social_media_name')
        model=SocialMediaSize
 
    def to_representation(self, instance):
        data=super().to_representation(instance)
        template=instance.template_global_categoty.all()
        # print("template",template)
        if template is not None:
            return data



class TemplateGlobalDesignSerializer(serializers.ModelSerializer):
    template_tag =TemplateTagSerializer(many=True,required=False,source='template_global_page')
    template_list=serializers.CharField(required=False)
    category=serializers.PrimaryKeyRelatedField(queryset=SocialMediaSize.objects.all(),required=True)
    # json=serializers.JSONField(required=True)
    template_lang=serializers.PrimaryKeyRelatedField(queryset=Languages.objects.all(),required=True)
    is_pro=serializers.BooleanField(default=False)
    is_published=serializers.BooleanField(default=False)

    class Meta:
        model=TemplateGlobalDesign
        fields=('id','template_tag','template_list','template_name','category','is_pro','is_published',
                'template_lang','description','thumbnail_page','json') 
        extra_kwargs = { 
            'template_list':{'write_only':True},}


############# for no json ###############
# class TemplateGlobalDesignViewSerializer(serializers.ModelSerializer):
#     template_tag =TemplateTagSerializer(many=True,required=False,source='template_global_page')
#     class Meta:
#         model=TemplateGlobalDesign
#         fields=('id','template_tag','template_list','template_name','category','is_pro','is_published',
#                 'template_lang','description','thumbnail_page')


# class CategoryWiseGlobaltemplateViewSerializer(serializers.ModelSerializer):
#     template_global_categoty=TemplateGlobalDesignViewSerializer(many=True,required=False,allow_null=False)
    
#     class Meta:
#         fields=('id','template_global_categoty','social_media_name')
#         model=SocialMediaSize

############# #######

class MyTemplateDesignPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyTemplateDesignPage
        fields = '__all__'

class MyTemplateDesignSerializer(serializers.ModelSerializer):
    # my_template_page=MyTemplateDesignPageSerializer(many=True,required=False)
    template_global_id = serializers.PrimaryKeyRelatedField(queryset=TemplateGlobalDesign.objects.all(),required=False)
    canvas_design_id = serializers.PrimaryKeyRelatedField(queryset=CanvasDesign.objects.all(),required=False)
    tar_lang =  serializers.PrimaryKeyRelatedField(queryset=Languages.objects.all(),required=False)
    trans_page_no = serializers.IntegerField(required=False) 
    src_page_no= serializers.IntegerField(required=False)
    social_media_name = serializers.CharField(source='project_category.social_media_name',required=False)
    social_media_id=serializers.IntegerField(source='project_category.id',required=False)
    class Meta:
        model = MyTemplateDesign
        fields =  ('id','width','height','template_global_id','canvas_design_id','trans_page_no','tar_lang',
                   'src_page_no','social_media_name','social_media_id') #'my_template_page'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        template_page_first = MyTemplateDesignPage.objects.filter(my_template_design = instance).first()
        if template_page_first:
            if template_page_first.my_template_thumbnail:
                data['my_template_thumbnail'] = template_page_first.my_template_thumbnail.url
            else:
                data['my_template_thumbnail'] = None
        if not instance.project_category:
            social_media_size=SocialMediaSize.objects.get(social_media_name='Instagram Ad')
            # instance.project_category=social_media_size
            # instance.save()
            data['social_media_name']='Instagram Ad'
            data['social_media_id']=social_media_size.id
        return data
    
    def mytemp_create(self,canvas_design_id,user,created_by):
        file_name=canvas_design_id.file_name
        width=canvas_design_id.width
        height=canvas_design_id.height
        if not canvas_design_id.project_category:
            social_media_size=SocialMediaSize.objects.get(social_media_name='Instagram Ad')
            canvas_design_id.project_category=social_media_size
            canvas_design_id.save()
            project_category=canvas_design_id.project_category
        else:
            project_category=canvas_design_id.project_category
        my_temp_design = MyTemplateDesign.objects.create(file_name=file_name,width=width,height=height,user=user,created_by=created_by,project_category=project_category)
        return my_temp_design

    def create(self, validated_data):
        template_global_id = validated_data.pop('template_global_id',None)
        canvas_design_id = validated_data.pop('canvas_design_id',None)
        canvas_trans_id = validated_data.pop('canvas_trans_id',None)
        trans_page_no=validated_data.pop('trans_page_no',None)
        src_page_no=validated_data.pop('src_page_no',None)
        tar_lang=validated_data.pop('tar_lang',None)
        user = self.context.get('user')
        created_by = self.context.get('created_by')

        if canvas_design_id:
            if trans_page_no and tar_lang:
                my_temp_design=self.mytemp_create(canvas_design_id,user,created_by)
                canvas_target=CanvasTargetJsonFiles.objects.get(canvas_trans_json__canvas_design=canvas_design_id,
                                                                canvas_trans_json__target_language=tar_lang,page_no=trans_page_no)
                canvas_target.json=copy.copy(canvas_trans_id.json)
                my_template_json.pop('projectid',None)
                my_template_thumbnail=canvas_target.thumbnail
                MyTemplateDesignPage.objects.create(my_template_design=my_temp_design,my_template_thumbnail=my_template_thumbnail,my_template_json=my_template_json )
 
            elif src_page_no:
                my_temp_design=self.mytemp_create(canvas_design_id,user,created_by)
                canvas_source  = canvas_design_id.canvas_json_src.get(page_no=src_page_no)
                my_template_thumbnail = canvas_source.thumbnail
                my_template_json=copy.copy(canvas_source.json)
                my_template_json.pop('projectid',None)
                MyTemplateDesignPage.objects.create(my_template_design=my_temp_design,my_template_thumbnail=my_template_thumbnail,
                                                    my_template_json=my_template_json )
            else:
                raise serializers.ValidationError({'msg':'need page number'})
            
        if template_global_id:
            file_name=template_global_id.file_name
            width=template_global_id.width
            height=template_global_id.height
            project_category=template_global_id.category
            my_template_thumbnail=template_global_id.thumbnail_page
            my_template_json=template_global_id.json
            my_temp_design = MyTemplateDesign.objects.create(file_name=file_name,width=width,height=height,user=user,project_category=project_category,created_by=created_by)
            MyTemplateDesignPage.create(my_template_design=my_temp_design,my_template_thumbnail=my_template_thumbnail,
                                                     my_template_json=my_template_json )
        return my_temp_design

class MyTemplateDesignRetrieveSerializer(serializers.ModelSerializer):
    my_template_page = MyTemplateDesignPageSerializer(many=True)
    # social_media_name = serializers.ReadOnlyField(source='project_category_name')
    social_media_name = serializers.CharField(source='project_category.social_media_name')
    social_media_id=serializers.IntegerField(source='project_category.id')
    class Meta:
        model = MyTemplateDesign
        fields = ('id','width','height','social_media_name','social_media_id','my_template_page')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not instance.project_category:
            social_media_size=SocialMediaSize.objects.get(social_media_name='Instagram Ad')
            instance.project_category=social_media_size
            instance.save()
            # data['project_category']=instance.project_category_id
        return data


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

class EmojiDataSerializer(serializers.ModelSerializer):
    class Meta:
        model=EmojiData
        fields='__all__'

class EmojiCategorySerializer(serializers.ModelSerializer):
    cat_data=serializers.SerializerMethodField()
    class Meta:
        model=EmojiCategory
        fields='__all__'

    def get_cat_data(self,obj):
        return EmojiData.objects.filter(emoji_cat=obj)[:10].values_list('data',flat=True)


# class EmojiDataSerializer(serializers.ModelSerializer):
#     cat_data=EmojiCategorySerializer(many=True,required=False,source='emoji_cat_data')
    
#     class Meta:
#         model=EmojiData
#         fields=('id','emoji_cat','emoji_name','data','cat_data')

#     def get_cat_data(self,obj):
#         return EmojiCategory
    





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




####update

###
        # elif thumbnail_src and src_page:
        #     canva_source = CanvasSourceJsonFiles.objects.get(canvas_design=instance,page_no=src_page)
 
        #     thumbnail_src = self.thumb_create(json_str=canva_source.json,formats='png',multiplierValue=1)
        #     canva_source.thumbnail = thumbnail_src
        #     canva_source.export_file = thumbnail_src  ##export_img_src same as thumbnail_src
        #     canva_source.save()   

###

            # if thumbnail_page_path and os.path.exists(thumbnail_page_path):
            #     os.remove(thumbnail_page_path)
            # print('path exist',os.path.exists(thumbnail_page_path))

        # if temp_global_design and new_project:
        #     width=temp_global_design.width
        #     height=temp_global_design.height
        #     json=temp_global_design.json
        #     category=temp_global_design.category
        #     user = self.context['request'].user
        #     new_proj=CanvasDesign.objects.create(user=user,width=width,height=height)
        #     json['projectid']={"pages": 1,'page':1,"langId": None,"langNo": None,"projId": new_proj.id,
        #                             "projectType": "design","project_category_label":category.social_media_name,"project_category_id":category.id}
        #     CanvasSourceJsonFiles.objects.create(new_proj=new_proj,json=json,page_no=1)
        #     return new_proj




##tar update
            # for count,tar_lang in enumerate(canvas_translation_tar_lang):

            #     trans_json=CanvasTranslatedJson.objects.create(canvas_design=instance,source_language=src_lang.locale.first(),target_language=tar_lang.locale.first())
            #     trans_json_project=copy.deepcopy(trans_json.canvas_design.canvas_json_src.last().json)
            #     trans_json_project['projectid']['langNo']=trans_json.source_language.id
            #      ####list of all canvas src json 
            #     # trans_json.canvas_src_json
            #     for count,src_json_file in enumerate(source_json_files_all):
            #         src_json_file.json=json_src_change(src_json_file.json,req_host,instance,text_box_save=True)
            #         src_json_file.save()
 
            #         res=canvas_translate_json_fn(src_json_file.json,src_lang.locale.first().locale_code,tar_lang.locale.first().locale_code)
                     
            #         if res[tar_lang.locale.first().locale_code]:
            #             tar_json_form=res[tar_lang.locale.first().locale_code]             
            #             tar_json_thum_image=self.thumb_create(json_str=tar_json_form,formats='png',multiplierValue=1) 
            #             can_tar_ins=CanvasTargetJsonFiles.objects.create(canvas_trans_json=trans_json,thumbnail=tar_json_thum_image,
            #                                                  json=tar_json_form,page_no=src_json_file.page_no)
            #             tar_json_pro=can_tar_ins.json
            #             tar_json_pro['projectid']={"pages":len(source_json_files_all),'page':count+1,"langId": trans_json.id,
            #                                        "langNo": tar_lang.id,"projId": instance.id,"projectType": "design"}
            #             can_tar_ins.json=tar_json_pro
            #             can_tar_ins.save()



# class PromptCategoryserializer(serializers.ModelSerializer):

#     class Meta:
#         model=PromptCategory
#         fields="__all__"

# class PromptEngineserializer(serializers.ModelSerializer):

#     class Meta:
#         model=PromptEngine
#         fields="__all__"
from PIL import Image

class DesignerListSerializer(serializers.ModelSerializer):
    thumbnail_src = serializers.FileField(allow_empty_file=False,required=False,write_only=True)
    translate_available = serializers.BooleanField(required=False,default=False)
    translate_src=serializers.FileField(allow_empty_file=False,required=False,write_only=True)
    # project_id=serializers.IntegerField(required=False,default=False)
    project_id=serializers.SerializerMethodField()
    class Meta:
        model = CanvasDesign
        fields = ('file_name','width','height','thumbnail_src','translate_available','updated_at',"translate_src","project_id")
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        obj=[]
        if instance.canvas_json_src.first():
            # data["project_id"]=instance.id
            obj.append(data)
        # if hasattr(instance.canvas_json_src.first(),'thumbnail'):
            data['thumbnail_src']= instance.canvas_json_src.first().thumbnail.url
            if instance.canvas_translate.all():
                data['translate_available'] = True
                tar=instance.canvas_translate.all()
                for j in tar:
                    k=j.canvas_json_tar.all()
                    ser=CanvasTargetJsonSerializer(k,many=True)
                    for i in ser.data:
                        obj.append(i)    
            return obj  
        
    def get_project_id(self,instance):
        return instance.id
    
class CanvasTargetJsonSerializer(serializers.ModelSerializer):
    thumbnail_src = serializers.FileField(allow_empty_file=False,required=False,write_only=True)
    json=serializers.FileField(allow_empty_file=False,required=False,write_only=True)
    project_id=serializers.SerializerMethodField()
    # project_id=serializers.IntegerField(required=False,default=False)

    class Meta:
        model=CanvasTargetJsonFiles
        fields=("id","canvas_trans_json","thumbnail_src","export_file","json","project_id")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        json=self.context.get("json")
        if json:
            data['json']=instance.json
        data['thumbnail_src']= instance.thumbnail.url
        # data["project_id"]=instance.canvas_trans_json.canvas_design.id
        return data
    
    def get_project_id(self,instance):
        return instance.canvas_trans_json.canvas_design.id

class CanvasTranslatedSerializer(serializers.ModelSerializer):
    # thumbnail=serializers.SerializerMethodField()
    class Meta:
        model=CanvasTranslatedJson
        fields=("canvas_design","source_language","target_language")


class AiAssertscategoryserializer(serializers.ModelSerializer):

    class Meta:
        model=AiAssertscategory
        fields="__all__"

class AiAssertsSerializer(serializers.ModelSerializer):

    class Meta:
        model=AiAsserts
        fields=('preview_img',"id","tags","type","user","category",'imageurl',"status")

    def create(self, data):
        instance=AiAsserts.objects.create(**data)
        # instance.save()
        im = Image.open(instance.imageurl.path)
        instance.preview_img=create_thumbnail_img_load(base_dimension=300,image=im)
        instance.status=True
        instance.save()
        return instance
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['imageurl']= HOST_NAME+instance.imageurl.url 
        data['preview_img']= HOST_NAME+instance.preview_img.url
        return data
    


# class AssetImageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model=AssetImage
#         fields='__all__'



class AssetImageSerializer(serializers.ModelSerializer):
     
    class Meta:
        model=AssetImage
        fields='__all__'

    
    def create(self, data):
        instance=AssetImage.objects.create(**data)
        if instance.image_category.cat_name in ["Ai Images"]:
            im = Image.open(instance.user_asset.image.path)
            instance.preview_img = create_thumbnail_img_load(base_dimension=300,image=im)
            instance.imageurl = convert_image_url_to_file(im,no_pil_object=False,name="Stock_Image.png")
            imge_cat_inst = ImageCategories.objects.filter(category=instance.image_category.cat_name).first()
            instance.category = imge_cat_inst
            instance.save()
        else:
            print("no image")
        instance.is_store=True
        instance.save()
        return instance

class AssetCategorySerializer(serializers.ModelSerializer):
    cat_asset_image=AssetImageSerializer(many=True,required=False)
    cat_name=serializers.CharField(required=True)
    class Meta:
        model=AssetCategory
        fields=('id','cat_asset_image','cat_name')

    def create(self, data):
        instance=AssetCategory.objects.create(**data)
        return instance

     
