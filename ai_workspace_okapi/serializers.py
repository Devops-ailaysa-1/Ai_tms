from rest_framework import serializers
from .models import Document, Segment, TextUnit, MT_RawTranslation, MT_Engine, TranslationStatus, FontSize, Comment
import json, copy
from google.cloud import translate_v2 as translate
from ai_workspace.serializers import PentmWriteSerializer
from ai_workspace.models import  Project,Job
from django.db.models import Q
from .utils import set_ref_tags_to_runs, get_runs_and_ref_ids
from contextlib import closing
from django.db import connection
from django.utils import timezone

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
    temp_target = serializers.CharField(read_only=True, source="get_temp_target")
    status = serializers.IntegerField(read_only=True, source="status.status_id")
    source = serializers.CharField(trim_whitespace=False, allow_blank=True)

    class Meta:
        model = Segment
        fields = (
            "source",
            "target",
            "coded_source",
            "coded_brace_pattern",
            "coded_ids_sequence",
            "tagged_source",
            "target_tags",
            "segment_id",
            "temp_target",
            "status",
            "has_comment"
        )

        extra_kwargs = {
            "source": {"write_only": True},
            "coded_source": {"write_only": True},
            "coded_brace_pattern": {"write_only": True},
            "coded_ids_sequence": {"write_only": True},
            "tagged_source": {"read_only": True},
            "target_tags": {"read_only": True},
            # "id",
        }

    def to_internal_value(self, data):
        # print(self)
        data["coded_ids_sequence"] = json.dumps(data["coded_ids_sequence"])
        return super().to_internal_value(data=data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # print("-------------------------> called")
        return representation

class SegmentSerializerV2(SegmentSerializer):
    temp_target = serializers.CharField(trim_whitespace=False)
    target = serializers.CharField(trim_whitespace=False, required=False)
    status = serializers.PrimaryKeyRelatedField(required=False, queryset=TranslationStatus.objects.all())
    class Meta(SegmentSerializer.Meta):
        fields = ("target", "id", "temp_target", "status")
        #

    def to_internal_value(self, data):
        return super(SegmentSerializer, self).to_internal_value(data=data)

    def update(self, instance, validated_data):
        if "target" in validated_data:
            res = super().update(instance, validated_data)
            instance.temp_target = instance.target
            instance.save()
            return res
        return super().update(instance, validated_data)

class SegmentSerializerV3(serializers.ModelSerializer):# For Read only
    target = serializers.CharField(read_only=True, source="coded_target", trim_whitespace=False)
    class Meta:
        # pass
        model = Segment
        fields = ['source', 'target', 'coded_source', 'coded_brace_pattern', 'coded_ids_sequence']
        read_only_fields = ['source', 'target', 'coded_source', 'coded_brace_pattern', 'coded_ids_sequence']
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['coded_ids_sequence'] = json.loads(ret['coded_ids_sequence'])
        return ret

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


    def create(self, validated_data, **kwargs):
        text_unit_ser_data  = validated_data.pop("text_unit_ser", [])
        text_unit_ser_data2 = copy.deepcopy(text_unit_ser_data)

        document = Document.objects.create(**validated_data)

        # USING DJANGO SAVE() METHOD
        # for text_unit in text_unit_ser_data:
        #     segs = text_unit.pop("segment_ser", [])
        #     text_unit = TextUnit.objects.create(**text_unit, document=document)
        #     for seg  in segs:
        #         seg = Segment.objects.create(**seg, text_unit=text_unit)

        # USING BULK CREATE METHOD
        # text_unit_instances = []
        # segment_instances = []

        # for text_unit in text_unit_ser_data:
        #     text_unit.pop("segment_ser", [])
        #     text_unit_instances.append(TextUnit(okapi_ref_translation_unit_id=text_unit["okapi_ref_translation_unit_id"], document=document))

        # TextUnit.objects.bulk_create(text_unit_instances)
        # print("***** Textunits bulk created ******")

        # for text_unit2 in text_unit_ser_data2:
        #     segs = text_unit2.pop("segment_ser", [])
        #     text_unit_instance = TextUnit.objects.get(Q(okapi_ref_translation_unit_id=text_unit2["okapi_ref_translation_unit_id"]) & \
        #                                 Q(document_id=document.id))

        #     for seg in segs:

        #         tagged_source, _ , target_tags = (
        #                 set_ref_tags_to_runs(seg["coded_source"],
        #                 get_runs_and_ref_ids(seg["coded_brace_pattern"],
        #                 json.loads(seg["coded_ids_sequence"])))
        #             )

        #         segment_instances.append(Segment(
        #             source = seg["source"],
        #             target = "",
        #             coded_source = seg["coded_source"],
        #             coded_brace_pattern = seg["coded_brace_pattern"],
        #             coded_ids_sequence = seg["coded_ids_sequence"],
        #             temp_target = "",
        #             text_unit = text_unit_instance,
        #             okapi_ref_segment_id = text_unit2["okapi_ref_translation_unit_id"],
        #             tagged_source = tagged_source,
        #             target_tags = target_tags,
        #             ))

        # Segment.objects.bulk_create(segment_instances)
        # print("********** Created segments **********")

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
                target = "" if seg["target"] == None else seg["target"]
                seg_params.extend([str(seg["source"]), target, "", str(seg["coded_source"]), str(tagged_source), \
                    str(seg["coded_brace_pattern"]), str(seg["coded_ids_sequence"]), str(target_tags), str(text_unit["okapi_ref_translation_unit_id"]), \
                        timezone.now(), text_unit_id])

        segment_sql = 'INSERT INTO ai_workspace_okapi_segment (source, target, temp_target, coded_source, tagged_source, \
                       coded_brace_pattern, coded_ids_sequence, target_tags, okapi_ref_segment_id, updated_at, text_unit_id) VALUES {}'.format(
                           ', '.join(['(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'] * seg_count))

        with closing(connection.cursor()) as cursor:
            cursor.execute(segment_sql, seg_params)

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
                  "is_first_doc_view",
                  "target_language_script",
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

class MT_RawSerializer(serializers.ModelSerializer):
    mt_engine_name = serializers.CharField(source="mt_engine.engine_name", read_only=True)

    class Meta:
        model = MT_RawTranslation
        fields = (
            "segment", 'mt_engine', 'mt_raw', "mt_engine_name", "target_language"
        )

        extra_kwargs = {
            "mt_raw": {"required": False},
        }

    def to_internal_value(self, data):
        # print("data--->", data)
        data["mt_engine"] = data.get("mt_engine", 1)
        return super().to_internal_value(data=data)

    def create(self, validated_data):
        segment = validated_data["segment"]
        validated_data["mt_raw"]= client.translate(segment.source,
                                    target_language=segment.target_language_code, format_="text")\
                                    .get("translatedText")
        instance = MT_RawTranslation.objects.create(**validated_data)
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

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = "__all__"

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
