from rest_framework import serializers
from .models import Document, Segment, TextUnit, MT_RawTranslation, \
    MT_Engine, TranslationStatus, FontSize, Comment#, MergeSegment
import json, copy
from google.cloud import translate_v2 as translate
from ai_workspace.serializers import PentmWriteSerializer
from ai_workspace.models import  Project,Job, TaskAssign
from ai_auth.models import AiUser
from django.db.models import Q
from .utils import set_ref_tags_to_runs, get_runs_and_ref_ids, get_translation
from contextlib import closing
from django.db import connection
from django.utils import timezone
from django.apps import apps
from django.http import HttpResponse, JsonResponse
from ai_workspace_okapi.models import SegmentHistory,Segment, MergeSegment, SplitSegment, SegmentPageSize
from ai_workspace.api_views import UpdateTaskCreditStatus
import re
from .utils import split_check
import collections
import csv
import io,time

client = translate.Client()

class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("exclude_fields", None)
        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields:
            # fields = fields.split(',')
            # Drop any fields that are not specified in the `fields` argument.
            excluded = set(fields)
            for field_name in excluded:
                self.fields.pop(field_name)

class SegmentSerializer(serializers.ModelSerializer):
    segment_id = serializers.IntegerField(read_only=True, source="id")
    temp_target = serializers.CharField(read_only=True, source="get_temp_target", allow_blank=True, allow_null=True,)
    status = serializers.IntegerField(read_only=True, source="status.status_id")
    source = serializers.CharField(trim_whitespace=False, allow_blank=True)
    random_tag_ids = serializers.CharField(allow_blank=True, required=False)
    parent_segment = serializers.IntegerField(read_only=True, \
                        source="get_parent_seg_id", allow_null=True,)
    class Meta:
        model = Segment
        fields = (
            "source","target","coded_source","coded_brace_pattern","coded_ids_sequence","tagged_source",\
            "target_tags","segment_id","temp_target","status","has_comment","is_merged","is_split",\
            "text_unit","is_merge_start","random_tag_ids","parent_segment",)

        extra_kwargs = {
            "source": {"write_only": True},
            "coded_source": {"write_only": True},
            "coded_brace_pattern": {"write_only": True},
            "coded_ids_sequence": {"write_only": True},
            # "random_tag_ids" : {"read_only": True},
            "tagged_source": {"read_only": True},
            "target_tags": {"read_only": True},
            "is_merged": {"required": False, "default": False},
            "text_unit": {"read_only": True},
            "is_merge_start": {"read_only": True},
            "is_split": {"read_only": True},
            # "id",
            "parent_segment": {"read_only": True},
        }


    def to_internal_value(self, data):
        # print(self)
        data["coded_ids_sequence"] = json.dumps(data["coded_ids_sequence"])
        data["random_tag_ids"] = json.dumps(data["random_tag_ids"])
        return super().to_internal_value(data=data)

    def remove_random_tags(self, string, random_tag_list):
        if not random_tag_list:
            return string
        for id in random_tag_list:
            string = re.sub(fr'</?{id}>', "", string)
        return string

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        random_tag_id_list = json.loads(representation["random_tag_ids"])
        representation["tagged_source"] = self.remove_random_tags(representation["tagged_source"], random_tag_id_list)
        representation["target_tags"] = self.remove_random_tags(representation["target_tags"], random_tag_id_list)
        return representation

from ai_workspace.models import Task,TaskAssignInfo
import difflib
class SegmentSerializerV2(SegmentSerializer):
    temp_target = serializers.CharField(trim_whitespace=False, allow_null=True)
    target = serializers.CharField(trim_whitespace=False, required=False)
    status = serializers.PrimaryKeyRelatedField(required=False, queryset=TranslationStatus.objects.all())

    class Meta(SegmentSerializer.Meta):
        fields = ("target", "id", "temp_target", "status", "random_tag_ids", "tagged_source", "target_tags")

    def to_internal_value(self, data):
        return super(SegmentSerializer, self).to_internal_value(data=data)

    def target_check(self, obj, target):
        if obj.source[0].isspace():
            if target[0].isspace(): 
                return target
            else:
                return ' ' + target
        else:
            return target

    # def his_check(self,instance,temp_target,content,user):
    #     if temp_target != content:
    #         return True
    #     else:
    #         SegmentHistory.objects.filter(seg)


    def update_task_assign(self,task_obj,user,status_id):
        try:
            if status_id in [109,110]:step_id = 2
            else: step_id = 1
            task_assign_query = TaskAssignInfo.objects.filter(task_assign__task = task_obj).filter(task_assign__assign_to = user)
            if task_assign_query.count() == 2:
                task_assign_obj = task_assign_query.filter(task_assign__step_id=step_id).first()
            else:
                task_assign_obj = task_assign_query.first()
            print("t_a_o----->",task_assign_obj)         
            obj = task_assign_obj.task_assign
            if obj.status != 2:
                obj.status = 2
                obj.save()
            if task_assign_obj.task_assign.reassigned == True:
                assigns = TaskAssignInfo.objects.filter(task_assign__task = task_obj).filter(task_assign__step=obj.step).filter(task_assign__reassigned=False)
                print("Assigns---------->",assigns)
                for i in assigns:
                    print(i.task_assign)
                    if i.task_assign.status != 2:
                        i.task_assign.status = 2
                        i.task_assign.save()
        except:pass

    def update(self, instance, validated_data):
        print("VD----------->",validated_data)
        print("Ins-------->",instance)
        status = validated_data.get('status',None)
        print("St---------->>>",validated_data.get('status'))
        if validated_data.get('target'):
            validated_data['target'] = self.target_check(instance,validated_data.get('target'))
        if validated_data.get('temp_target'):
            validated_data['temp_target'] = self.target_check(instance,validated_data.get('temp_target'))
        status_id = status.id if status else None 
        if status_id:
            if status_id not in [109,110]:step = 1
            else:step=2
        else: step = None
        existing_step = 1 if instance.status_id not in [109,110] else 2 
        from .views import MT_RawAndTM_View
        if split_check(instance.id):seg_id = instance.id
        else:seg_id = SplitSegment.objects.filter(id=instance.id).first().segment_id
        user_1 = self.context.get('request').user
        task_obj = Task.objects.get(document_id = instance.text_unit.document.id)
        content = validated_data.get('target') if "target" in validated_data else validated_data.get('temp_target')
        seg_his_create = True if instance.temp_target!=content or step != existing_step  else False #self.his_check(instance,instance.temp_target,content,user_1)
        print("Seg-His-Create--------------->",seg_his_create)
        if "target" in validated_data:
            print("Inside if target")
            if instance.target == '':
                print("In target empty")
                if (instance.text_unit.document.job.project.mt_enable == False)\
                or status_id in [102,106,110]:
                    print("mt dable and manual confirm check")
                    user = instance.text_unit.document.doc_credit_debit_user
                    initial_credit = user.credit_balance.get("total_left")
                    consumable_credits = MT_RawAndTM_View.get_consumable_credits(instance.text_unit.document, instance.id, None)
                    consumable = max(round(consumable_credits/3),1) 
                    if initial_credit < consumable:
                        raise serializers.ValidationError("Insufficient Credits")
                    else:
                        debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable)
                        print("Credit Debited",status_code)
            res = super().update(instance, validated_data)
            instance.temp_target = instance.target
            instance.save()
            self.update_task_assign(task_obj,user_1,status_id)
            if seg_his_create:
                SegmentHistory.objects.create(segment_id=seg_id, user = self.context.get('request').user, target= content, status= status if status else instance.status)
            return res
        if seg_his_create:
            SegmentHistory.objects.create(segment_id=seg_id, user = self.context.get('request').user, target= content, status= status if status else instance.status)
        self.update_task_assign(task_obj,user_1,status_id)
        return super().update(instance, validated_data)

class SegmentSerializerV3(serializers.ModelSerializer):# For Read only
    target = serializers.CharField(read_only=True, source="get_merge_target_if_have",
        trim_whitespace=False)
    merge_segment_count = serializers.IntegerField(read_only=True,
        source="get_merge_segment_count", )
    mt_raw_target = serializers.CharField(read_only=True, source="get_mt_raw_target_if_have",
        trim_whitespace=False)

    class Meta:
        # pass
        model=Segment
        fields = ['source', 'target','mt_raw_target', 'coded_source', 'coded_brace_pattern',
            'coded_ids_sequence', "random_tag_ids", 'merge_segment_count']
        read_only_fields = ['source', 'target', 'coded_source', 'coded_brace_pattern',
            'coded_ids_sequence','mt_raw_target']
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['random_tag_ids'] = json.loads(ret['random_tag_ids'])
        ret['coded_ids_sequence'] = json.loads(ret['coded_ids_sequence'])
        return ret


    


class MergeSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MergeSegment
        fields = ("segments", "text_unit")
    def validate(self, data):
        segments = data["segments"] = sorted(data["segments"], key=lambda x: x.id)

        # Resetting the raw MT for normal segments once merged
        for segment in segments:
            try:
                MT_RawTranslation.objects.get(segment_id = segment.id).delete()
            except:
                print(f"No raw MT available for this segment --> {segment.id}")

        text_unit = data["text_unit"]
        if not all( [seg.text_unit.id==text_unit.id for seg  in segments]):
            raise serializers.ValidationError("Segments for merging should have same text_unit_id")
        return super().validate(data)

class SplitSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SplitSegment
        fields = ("segment",
                  "text_unit",
                  )
        def validate(self, data):
            segment = data['segment']
            if segment.is_merged == True or segment.is_split == True:
                raise serializers.ValidationError("The segment is already merged or split")
            return super().validate(data)

class TextUnitSerializer(serializers.ModelSerializer):
    segment_ser = SegmentSerializer(many=True ,write_only=True)

    class Meta:
        model = TextUnit
        fields = (
            'okapi_ref_translation_unit_id',  "document", "segment_ser"
        )
        extra_kwargs = {
            "document":{
                "required": False, "write_only": True
            }
        }

    def to_internal_value(self, data):
        [(data["okapi_ref_translation_unit_id"], data["segment_ser"])] = list(data.items())
        return super().to_internal_value(data=data)

class TextUnitSerializerV2(serializers.ModelSerializer):
    segment_ser = SegmentSerializerV3(many=True ,read_only=True, source="text_unit_segment_set")

    class Meta:
        model = TextUnit
        fields = (
            "segment_ser","okapi_ref_translation_unit_id"
        )

    def to_representation(self, instance):
        ret = super(TextUnitSerializerV2, self).to_representation(instance=instance)
        ret[ret.pop("okapi_ref_translation_unit_id")] = (
            ret.pop("segment_ser")
        )
        return ret


class TextUnitSerializerTest(serializers.ModelSerializer):
    class Meta:
        model = TextUnit
        fields = "__all__"


class DocumentSerializer(serializers.ModelSerializer):# @Deprecated
    text_unit_ser = TextUnitSerializer(many=True,  write_only=True)

    class Meta:
        model = Document
        fields = ("text_unit_ser", "file", "job",
                  "total_word_count", "total_char_count",
                  "total_segment_count", "created_by", "id",)


        extra_kwargs = {
            "file": {"write_only": True},
            "job": {"write_only": True},
            "created_by": {"write_only": True},
            "id": {"read_only": True, "source": "get_user_email"},
            # "text_unit_ser": dict(source="document_text_unit_set", write_only=True)
        }

    def to_internal_value(self, data):
        data["text_unit_ser"] = [
            {key:value} for key, value in data.pop("text", {}).items()
        ]
        data["created_by"] = 8
        return super().to_internal_value(data=data)


    def remove_tags(self,text):
        TAG_RE = re.compile(r'<[^>]+>')
        return TAG_RE.sub('', text)


    def pre_flow(self,user,source,document,mt_engine,target_tags):
        from .api_views import MT_RawAndTM_View
        initial_credit = user.credit_balance.get("total_left")
        consumable_credits = MT_RawAndTM_View.get_consumable_credits(document,None,source) if source else 0
        print("Consum Credits------------>",consumable_credits)
        if initial_credit > consumable_credits:
            try:
                mt = get_translation(mt_engine,str(source),document.source_language_code,document.target_language_code,user_id=document.owner_pk,cc=consumable_credits)
                if target_tags !='':
                    temp_target = mt + target_tags
                    
                    target = mt + target_tags
                else:
                    temp_target = mt
                    target = mt
                status_id = TranslationStatus.objects.get(status_id=103).id
                #debit_status, status_code = UpdateTaskCreditStatus.update_credits(user, consumable_credits)
                return target,temp_target,status_id
            except:
                target=""
                temp_target=""
                status_id=None
                return target,temp_target,status_id
        else:
            target=""
            temp_target=""
            status_id=None
            return target,temp_target,status_id


    def create(self, validated_data, **kwargs):
        from .api_views import MT_RawAndTM_View,remove_random_tags

        text_unit_ser_data  = validated_data.pop("text_unit_ser", [])
        #print("Text Unit Data----------------->",text_unit_ser_data)
        text_unit_ser_data2 = copy.deepcopy(text_unit_ser_data)

        document = Document.objects.create(**validated_data)
        pr_obj = document.job.project
        if pr_obj.pre_translate == True:
            target_get = True
            mt_engine = pr_obj.mt_engine_id
            user = pr_obj.ai_user
        else:target_get = False


        # USING SQL BATCH INSERT
        text_unit_sql = 'INSERT INTO ai_workspace_okapi_textunit (okapi_ref_translation_unit_id, document_id) VALUES {}'.format(
        ', '.join(['(%s, %s)'] * len(text_unit_ser_data)),
        )
        tu_params = []
        for text_unit in text_unit_ser_data:
            tu_params.extend([text_unit["okapi_ref_translation_unit_id"], document.id])

        with closing(connection.cursor()) as cursor:
            cursor.execute(text_unit_sql, tu_params)

        seg_params = []
        seg_count = 0
        for text_unit in text_unit_ser_data:
            text_unit_id = TextUnit.objects.get(Q(okapi_ref_translation_unit_id=text_unit["okapi_ref_translation_unit_id"]) & \
                                            Q(document_id=document.id)).id
            segs = text_unit.pop("segment_ser", [])

            for seg in segs:
                seg_count += 1
                tagged_source, _ , target_tags = (
                        set_ref_tags_to_runs(seg["coded_source"],
                        get_runs_and_ref_ids(seg["coded_brace_pattern"],
                        json.loads(seg["coded_ids_sequence"])))
                    )

                if target_get == False:
                    seg['target'] = ""
                    seg['temp_target'] = ""
                    status_id = None
                else:
                    if seg["random_tag_ids"] == []:tags = str(target_tags)
                    else:tags = remove_random_tags(str(target_tags),json.loads(seg["random_tag_ids"]))
                    seg['target'],seg['temp_target'],status_id = self.pre_flow(user,seg['source'],document,mt_engine,tags)


                seg_params.extend([str(seg["source"]), seg['target'], seg['temp_target'], str(seg["coded_source"]), str(tagged_source), \
                    str(seg["coded_brace_pattern"]), str(seg["coded_ids_sequence"]), str(target_tags), str(text_unit["okapi_ref_translation_unit_id"]), \
                        timezone.now(), status_id , text_unit_id, str(seg["random_tag_ids"])])

        segment_sql = 'INSERT INTO ai_workspace_okapi_segment (source, target, temp_target, coded_source, tagged_source, \
                       coded_brace_pattern, coded_ids_sequence, target_tags, okapi_ref_segment_id, updated_at, status_id, text_unit_id, random_tag_ids) VALUES {}'.format(
                           ', '.join(['(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'] * seg_count))
        with closing(connection.cursor()) as cursor:
            cursor.execute(segment_sql, seg_params)


        if target_get == True:
            mt_params = []
            count = 0
            segments = Segment.objects.filter(text_unit__document=document) #####Need to check this##########
            for i in segments:
                if i.target != "":
                    count += 1
                    mt_params.extend([self.remove_tags(i.target),mt_engine,mt_engine,i.id])

            mt_raw_sql = "INSERT INTO ai_workspace_okapi_mt_rawtranslation (mt_raw, mt_engine_id, task_mt_engine_id,segment_id)\
            VALUES {}".format(','.join(['(%s, %s, %s, %s)'] * count))
            if mt_params:
                with closing(connection.cursor()) as cursor:
                    cursor.execute(mt_raw_sql, mt_params)
        return document

class DocumentSerializerV2(DocumentSerializer):
    document_id = serializers.IntegerField(source="id", read_only=True)
    filename = serializers.CharField(source="file.filename", read_only=True)

    def to_internal_value(self, data):
        job_id=data["job"]
        job = Job.objects.get(id=job_id)
        data["text_unit_ser"] = [
            {key:value} for key, value in data.pop("text", {}).items()
        ]
        data["created_by"] = (job.project.ai_user_id)
        return super(DocumentSerializer, self).to_internal_value(data=data)

    class Meta(DocumentSerializer.Meta):
        fields = ("text_unit_ser", "file", "job", "project", "filename",
                  "total_word_count", "total_char_count",
                  "total_segment_count", "created_by", "document_id",
                  "source_language", "target_language", "source_language_id",
                  "target_language_id", "source_language_code", "target_language_code", "doc_credit_check_open_alert",
                  'assign_detail','show_mt','project_type_sub_category',
                  "target_language_script",'download_audio_output_file','converted_audio_file_exists',
                  )

class DocumentSerializerV3(DocumentSerializerV2):
    text = TextUnitSerializerV2(many=True,  read_only=True, source="document_text_unit_set")
    filename = serializers.CharField(read_only=True, source="file.filename")
    class Meta(DocumentSerializerV2.Meta):
        model = Document
        fields = (
            "text",  'total_word_count', 'total_char_count', 'total_segment_count', "filename"
        )

    def to_representation(self, instance):
        ret = super().to_representation(instance=instance)
        coll = {}
        for itr in ret.pop("text", []):
            coll.update(itr)
        ret["text"] = coll
        return ret

from .models import SelflearningAsset,ChoiceLists,ChoiceListSelected
class SelflearningAssetSerializer (serializers.ModelSerializer):
    class Meta():
        model=SelflearningAsset
        fields="__all__"

    def create(self,validated_data):
        choicelist = validated_data.get('choice_list',None)
        edited = validated_data.get('edited_word',None)
        source = validated_data.get('source_word',None)
        # user = validated_data.get('user',None)
        print(choicelist,"++++++++++++++++")

        slf_lrn_list=SelflearningAsset.objects.filter(choice_list=choicelist,source_word=source)
        print(slf_lrn_list)
        if  slf_lrn_list.filter(edited_word=edited):
            ins = slf_lrn_list.filter(edited_word=edited).last()
            ins.occurance +=1
            ins.save()         
        else:
            if slf_lrn_list.count() >= 5:
                first_out=slf_lrn_list.first().delete()
            ins=SelflearningAsset.objects.create(choice_list=choicelist,source_word=source,edited_word=edited,occurance=1)  
        return ins


class ChoiceListsSerializer (serializers.ModelSerializer):

    class Meta:
        model = ChoiceLists
        fields = "__all__"

class ChoiceListSelectedSerializer (serializers.ModelSerializer):
    language=serializers.SerializerMethodField()
    class Meta:
        model = ChoiceListSelected
        fields = ("id","project","choice_list","language")
    
    def get_language(self,obj):
        return obj.choice_list.language.id


class MT_RawSerializer(serializers.ModelSerializer):
    mt_engine_name = serializers.CharField(source="mt_engine.engine_name", read_only=True)

    class Meta:
        model = MT_RawTranslation
        fields = (
            "segment", 'mt_engine', 'mt_raw', "task_mt_engine", "mt_engine_name",
            "target_language"
        )

        extra_kwargs = {
            "mt_raw": {"required": False},
        }

    def to_internal_value(self, data):

        segment_id = data.get("segment")

        # Getting the MT engine of Project
        obj = Project.objects.filter(project_jobs_set__file_job_set__document_text_unit_set__text_unit_segment_set=segment_id).first()
        proj_mt_engine_id = obj.mt_engine.id if obj.mt_engine else 1

        # Getting the MT engine for task
        task_mt_engine_id = TaskAssign.objects.filter(
            Q(task__document__document_text_unit_set__text_unit_segment_set=segment_id) &
            Q(step_id=1)
        ).first().mt_engine.id


        data["mt_engine"] = proj_mt_engine_id
        data["task_mt_engine"] = task_mt_engine_id if task_mt_engine_id else 1
        return super().to_internal_value(data=data)

    # def slf_learning_word_update(self,instance,doc):
    #     from ai_workspace_okapi.models import SelflearningAsset
    #     slf_lrn_inst=SelflearningAsset.objects.filter(user=doc.owner_pk,target_language=doc.target_language_id)
    #     if slf_lrn_inst:
    #         word_list=list(slf_lrn_inst.values_list('source_word',flat=True))
    #         mt_raw_lists=instance.mt_raw.split(' ')
    #         for mt_raw_list in mt_raw_lists:
    #             if mt_raw_list in word_list:
    #                 edited_word=slf_lrn_inst.filter(source_word=mt_raw_list).last().edited_word
    #                 instance.mt_raw=instance.mt_raw.replace(mt_raw_list,edited_word)
    #                 instance.save()

    def create(self, validated_data):

        segment = validated_data["segment"]
        active_segment = segment.get_active_object()
        mt_engine= validated_data["mt_engine"]
        task_mt_engine = validated_data["task_mt_engine"]

        text_unit_id = segment.text_unit_id
        doc = TextUnit.objects.get(id=text_unit_id).document

        sl_code = doc.source_language_code
        tl_code = doc.target_language_code

        validated_data["mt_raw"] = get_translation(mt_engine.id, active_segment.source, sl_code, tl_code,user_id=doc.owner_pk)
        print("mt_raw------>>",validated_data["mt_raw"])
        print("inside ____mt--------------------------------")
        instance = MT_RawTranslation.objects.create(**validated_data)

        #word update in mt_raw
        #instance=self.slf_learning_word_update(instance,doc)
        return instance

class TM_FetchSerializer(serializers.ModelSerializer):
    pentm_dir_path = serializers.CharField(source=\
            "text_unit.document.job.project.pentm_path", read_only=True)
    search_source_string = serializers.CharField(source="source", read_only=True)

    class Meta:
        model = Segment
        fields = (
            "pentm_dir_path", "search_source_string", "target_language_code",
            "tm_fetch_configs"
        )

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret = {**ret, **ret.pop("tm_fetch_configs")}
        ret.pop("tm_fetch_configs", None)
        return ret

class TranslationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranslationStatus
        fields = "__all__"

class FontSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FontSize
        fields = "__all__"

class SegmentPageSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SegmentPageSize
        fields = "__all__"

class CommentSerializer(serializers.ModelSerializer):
    commented_by_user = serializers.ReadOnlyField(source='commented_by.fullname')
    class Meta:
        model = Comment
        fields = ('id','comment','segment','split_segment','commented_by','commented_by_user','created_at','updated_at',)

class FilterSerializer(serializers.Serializer):
    status_list = serializers.JSONField(
        required=False
    )

    class Meta:
        fields = ( "status_list", )

class PentmUpdateParamSerializer(serializers.ModelSerializer):
    source_text = serializers.CharField(source="source", read_only=True)
    # target_language_code = serializers.CharField(\
    #     source="target_language_code", read_only=True)
    target_text = serializers.CharField(source="target", read_only=True)

    class Meta:
        model = Segment
        fields = ("source_text", "target_language_code", \
                  "target_text")


class PentmUpdateSerializer(serializers.ModelSerializer):

    pentm_params = serializers.SerializerMethodField(read_only=True)
    pentm_update_params = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Segment
        fields = ("pentm_params", "pentm_update_params")

    def get_pentm_params(self, object):
        project = Project.objects.get( \
            id = object.text_unit.document.project)
        return json.dumps(PentmWriteSerializer(project).data)

    def get_pentm_update_params(self, object):
        return json.dumps(PentmUpdateParamSerializer(object).data)


# class MergeSegmentSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = MergeSegment
#         fields = ("segments", "text_unit")
#
#     def validate(self, data):
#         segments = data["segments"] = sorted(data["segments"], key=lambda x: x.id)
#         text_unit = data["text_unit"]
#         if not all( [seg.text_unit.id==text_unit.id for seg  in segments]):
#             raise serializers.ValidationError("all segments should be have same text unit id...")
#         return super().validate(data)

class ListSegmentIntgerationUpdateSerializer(serializers.ListSerializer):
    def create(self, validated_data, text_unit):
        ids = []
        for s_data in validated_data:
            segment = self.child.create(s_data, text_unit=text_unit, ids = ids)
            ids.append(segment.id)

class SegmentIntgerationUpdateSerializer(serializers.ModelSerializer):
    source = serializers.CharField(trim_whitespace=False, allow_blank=True)
    random_tag_ids = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        model = Segment
        list_serializer_class = ListSegmentIntgerationUpdateSerializer

        fields = (
            "source",
            "target",
            "coded_source",
            "coded_brace_pattern",
            "coded_ids_sequence",
            "text_unit",
            #"is_merge_start",
            "random_tag_ids",
        )

        extra_kwargs = {
            #"is_merged": {"required": False, "default": False},
            "text_unit": {"required": False},
        }

    def to_internal_value(self, data):
        print("child internal")
        data["coded_ids_sequence"] = json.dumps(data["coded_ids_sequence"])
        data["random_tag_ids"] = json.dumps(data["random_tag_ids"])
        return super().to_internal_value(data=data)

    def create(self, validated_data, text_unit, ids):
        segment = text_unit.text_unit_segment_set.filter(
           Q (source=validated_data.get("source")) & (~Q(id__in=ids))
            ).first()
        if segment:
            return segment
        segment = Segment.objects.create(**validated_data, text_unit=text_unit)
        return  segment

class ListTextUnitIntgerationUpdateSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        result = []
        for s_data in validated_data:
            result.append(self.child.create(s_data))
        return  result

class TextUnitIntgerationUpdateSerializer(serializers.ModelSerializer):
    text_unit_segment_set = SegmentIntgerationUpdateSerializer(many=True)
    class Meta:
        list_serializer_class = ListTextUnitIntgerationUpdateSerializer
        model = TextUnit
        fields  = ("text_unit_segment_set", "document",
                   "okapi_ref_translation_unit_id")

    def create(self, validated_data):
        segments = validated_data.pop("text_unit_segment_set")
        text_unit, created = TextUnit.objects.get_or_create(
            okapi_ref_translation_unit_id = validated_data.get("okapi_ref_translation_unit_id"),
            document = validated_data.get("document")
        )

        ser = SegmentIntgerationUpdateSerializer(many=True)
        ser.create(segments, text_unit=text_unit)
        return text_unit


# from ai_workspace_okapi.models import SegmentDiff

# class SegmentDiffSerializer(serializers.ModelSerializer):
#     # seg_history= serializers.PrimaryKeyRelatedField(queryset=SegmentHistory.objects.all(),required=False)
#     class Meta:
#         model=SegmentDiff
#         fields=('id','sentense_diff_result','save_type')

# class SegmentHistorySerializer(serializers.ModelSerializer):
#     segment_difference=SegmentDiffSerializer(many=True)
#     step_name=serializers.SerializerMethodField()
#     status_id=serializers.ReadOnlyField(source='status.status_id')
#     user_name=serializers.ReadOnlyField(source='user.fullname')
#     class Meta:
#         model = SegmentHistory
#         fields = ('segment','created_at','user_name','status_id','step_name','segment_difference')
#         # extra_kwargs = {
#         #     "status": {"write_only": True}}


#     def to_representation(self, instance):
#         from ai_workspace_okapi.api_views import segment_difference
#         s=SegmentDiff.objects.filter(seg_history=instance)
#         if not s:
#             seg_diff=segment_difference(sender=None, instance=instance)
#         return super().to_representation(instance)

#     def get_step_name(self,obj):
#         try:
#             step = TaskAssign.objects.filter(
#                 Q(task__document__document_text_unit_set__text_unit_segment_set=obj.segment_id) &
#                 Q(assign_to = obj.user)).first().step
#             return step.name
#         except:
#             return None
        
class VerbSerializer(serializers.Serializer):
    text_string = serializers.CharField()
    synonyms_form =serializers.ListField()




from ai_workspace_okapi.models import SegmentDiff

class SegmentDiffSerializer(serializers.ModelSerializer):
    # seg_history= serializers.PrimaryKeyRelatedField(queryset=SegmentHistory.objects.all(),required=False)
    class Meta:
        model=SegmentDiff
        fields=('id','sentense_diff_result','save_type')

class SegmentHistorySerializer(serializers.ModelSerializer):
    segment_difference=SegmentDiffSerializer(many=True)
    step_name=serializers.SerializerMethodField()
    status_id=serializers.ReadOnlyField(source='status.status_id')
    user_name=serializers.ReadOnlyField(source='user.fullname')
    class Meta:
        model = SegmentHistory
        fields = ('segment','created_at','user_name','status_id','step_name','segment_difference')
        # extra_kwargs = {
        #     "status": {"write_only": True}}


    # def to_representation(self, instance):
    #     from ai_workspace_okapi.api_views import segment_difference
    #     s=SegmentDiff.objects.filter(seg_history=instance)
    #     if not s:
    #         seg_diff=segment_difference(sender=None, instance=instance)
    #     return super().to_representation(instance)

    def get_step_name(self,obj):
        try:
            step = TaskAssign.objects.filter(
                Q(task__document__document_text_unit_set__text_unit_segment_set=obj.segment_id) &
                Q(assign_to = obj.user)).first().step
            return step.name
        except:
            return None


from ai_workspace_okapi.models import SelflearningAsset
class SelflearningAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model=SelflearningAsset



#For copy_from command

# okapi Execution time----------------> 48.274311780929565
# Command Execution: 0.3987123966217041 seconds
# Execution time: 44.15513563156128 seconds
# postman: 1 m 34.44 s


# CSV Writer Execution time 43.151642084121704 seconds
# Command Execution: 0.0005958080291748047 seconds
# Execution time: 43.4935302734375 seconds
# Postman: 1 m 2.82 s

# CSV Writer Execution time 43.607571840286255 seconds
# Command Execution: 0.0005240440368652344 seconds
# Execution time: 43.95321273803711 seconds



# For insert_into command

# okapi Execution time----------------> 48.53391695022583
# Command Execution time: 0.9105117321014404 seconds
# Execution time: 44.53358769416809 seconds
# Postman: 1 m 35.04 s

# okapi Execution time----------------> 49.68941617012024
# Command Execution time: 0.9043436050415039 seconds
# Execution time: 44.367270708084106 seconds
# Postman: 1 m 36.06 s

# class SegmentSerializerNew(serializers.ModelSerializer):# For Read only
#     target = serializers.CharField(read_only=True, source="get_mt_raw_target_if_have",
#         trim_whitespace=False)
#     merge_segment_count = serializers.IntegerField(read_only=True,
#         source="get_merge_segment_count", )

#     class Meta:
#         # pass
#         model = Segment
#         fields = ['id','source', 'target', 'coded_source', 'coded_brace_pattern',
#             'coded_ids_sequence', "random_tag_ids", 'merge_segment_count']
#         read_only_fields = ['source', 'target', 'coded_source', 'coded_brace_pattern',
#             'coded_ids_sequence']
#     def to_representation(self, instance):
#         ret = super().to_representation(instance)
#         ret['random_tag_ids'] = json.loads(ret['random_tag_ids'])
#         ret['coded_ids_sequence'] = json.loads(ret['coded_ids_sequence'])
#         return ret


# class TextUnitSerializerNew(serializers.ModelSerializer):
#     segment_ser = SegmentSerializerNew(many=True ,read_only=True, source="text_unit_segment_set")

#     class Meta:
#         model = TextUnit
#         fields = (
#             "segment_ser","okapi_ref_translation_unit_id"
#         )

#     def to_representation(self, instance):
#         ret = super(TextUnitSerializerNew, self).to_representation(instance=instance)
#         ret[ret.pop("okapi_ref_translation_unit_id")] = (
#             ret.pop("segment_ser")
#         )
#         return ret


# class DocumentSerializerNew(DocumentSerializerV2):
#     text = TextUnitSerializerNew(many=True,  read_only=True, source="document_text_unit_set")
#     filename = serializers.CharField(read_only=True, source="file.filename")
#     class Meta(DocumentSerializerV2.Meta):
#         model = Document
#         fields = (
#             "text",  'total_word_count', 'total_char_count', 'total_segment_count', "filename"
#         )

#     def to_representation(self, instance):
#         ret = super().to_representation(instance=instance)
#         coll = {}
#         for itr in ret.pop("text", []):
#             coll.update(itr)
#         ret["text"] = coll
#         return ret


