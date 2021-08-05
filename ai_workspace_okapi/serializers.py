from rest_framework import serializers
from .models import Document, Segment, TextUnit, MT_RawTranslation, MT_Engine, TranslationStatus, FontSize, Comment
import json
from google.cloud import translate_v2 as translate

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
    temp_target = serializers.CharField()
    status = serializers.PrimaryKeyRelatedField(required=False, queryset=TranslationStatus.objects.all())
    class Meta(SegmentSerializer.Meta):
        fields = ("target", "id", "temp_target", "status")
        #

    def to_internal_value(self, data):
        return super(SegmentSerializer, self).to_internal_value(data=data)

    def update(self, instance, validated_data):
        print(validated_data)
        if "target" in validated_data:
            instance.temp_target = instance.target
        # print(instance.target)
        return super().update(instance, validated_data)

class SegmentSerializerV3(serializers.ModelSerializer):# For Read only
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
                  "total_segment_count", "created_by", "id")

        extra_kwargs = {
            "file": {"write_only": True},
            "job": {"write_only": True},
            "created_by": {"write_only": True},
            "id": {"read_only": True, "source": "get_user_email"},
            # "text_unit_ser": dict(source="document_text_unit_set", write_only=True)
        }

    def to_internal_value(self, data):
        # print(""data)
        data["text_unit_ser"] = [
            {key:value} for key, value in data.pop("text", {}).items()
        ]
        data["created_by"] = 8
        # data["total_word_count"] = data["total_char_count"] = 0; #data["total_segment_count"] = 0
        return super().to_internal_value(data=data)


    def create(self, validated_data, **kwargs):
        text_unit_ser_data  = validated_data.pop("text_unit_ser", [])
        document = Document.objects.create(**validated_data)
        for text_unit in text_unit_ser_data:
            segs = text_unit.pop("segment_ser", [])
            text_unit = TextUnit.objects.create(**text_unit, document=document)
            print("text unit data--->", text_unit)
            for seg  in segs:
                print("seg data---->", seg)
                seg = Segment.objects.create(**seg, text_unit=text_unit)
        return document

class DocumentSerializerV2(DocumentSerializer):
    document_id = serializers.IntegerField(source="id", read_only=True)

    def to_internal_value(self, data):
        data["text_unit_ser"] = [
            {key:value} for key, value in data.pop("text", {}).items()
        ]
        data["created_by"] = (self.context.get("request").user.id \
                              if self.context.get("request", None)\
                              else None)
        return super(DocumentSerializer, self).to_internal_value(data=data)

    class Meta(DocumentSerializer.Meta):
        fields = ("text_unit_ser", "file", "job", "project",
                  "total_word_count", "total_char_count",
                  "total_segment_count", "created_by", "document_id",
                  "source_language", "target_language", "source_language_id",
                  "target_language_id", "source_language_code", "target_language_code"
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
                                    target_language=segment.target_language_code)\
                                    .get("translatedText")
        instance = MT_RawTranslation.objects.create(**validated_data)
        return instance

class TM_FetchSerializer(serializers.ModelSerializer):
    pentm_dir_path = serializers.CharField(source="text_unit.document.job.project.pentm_path", read_only=True)
    search_source_string = serializers.CharField(source="source", read_only=True)

    class Meta:
        model = Segment
        fields = (
            "pentm_dir_path", "search_source_string", "target_language_code"
        )

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

# //////////////////////////////////// References  \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\



# DocumentSerializer(<Document: Document object (19)>):
#     text_unit_ser = TextUnitSerializer(many=True, source='document_text_unit_set'):
#         okapi_ref_translation_unit_id = CharField(style={'base_template': 'textarea.html'})
#         document = PrimaryKeyRelatedField(queryset=Document.objects.all(), required=False, write_only=True)
#         segment_ser = SegmentSerializer(many=True, write_only=True):
#             source = CharField(style={'base_template': 'textarea.html'}, write_only=True)
#             target = CharField(allow_blank=True, allow_null=True, required=False, style={'base_template': 'textarea.html'})
#             coded_source = CharField(allow_blank=True, allow_null=True, required=False, style={'base_template': 'textarea.html'}, write_only=True)
#             coded_brace_pattern = CharField(allow_blank=True, allow_null=True, required=False, style={'base_template': 'textarea.html'}, write_only=True)
#             coded_ids_sequence = CharField(allow_blank=True, allow_null=True, required=False, style={'base_template': 'textarea.html'}, write_only=True)
#             tagged_source = CharField(read_only=True, style={'base_template': 'textarea.html'})
#             target_tags = CharField(read_only=True, style={'base_template': 'textarea.html'})
#             segment_id = IntegerField(read_only=True, source='id')
#     file = PrimaryKeyRelatedField(queryset=File.objects.all(), write_only=True)
#     job = PrimaryKeyRelatedField(queryset=Job.objects.all(), write_only=True)
#     total_word_count = IntegerField()
#     total_char_count = IntegerField()
#     total_segment_count = IntegerField()
#     created_by = PrimaryKeyRelatedField(allow_null=True, queryset=AiUser.objects.all(), required=False, write_only=True)
#     id = IntegerField(label='ID', read_only=True)


# \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\ ////////////////////////////////////////////////////////
#
# DocumentSerializer(<Document: Document object (19)>):
#     text_unit_ser = TextUnitSerializer(many=True, source='document_text_unit_set', write_only=True):
#         okapi_ref_translation_unit_id = CharField(style={'base_template': 'textarea.html'})
#         document = PrimaryKeyRelatedField(queryset=Document.objects.all(), required=False, write_only=True)
#         segment_ser = SegmentSerializer(many=True, write_only=True):
#             source = CharField(style={'base_template': 'textarea.html'}, write_only=True)
#             target = CharField(allow_blank=True, allow_null=True, required=False, style={'base_template': 'textarea.html'})
#             coded_source = CharField(allow_blank=True, allow_null=True, required=False, style={'base_template': 'textarea.html'}, write_only=True)
#             coded_brace_pattern = CharField(allow_blank=True, allow_null=True, required=False, style={'base_template': 'textarea.html'}, write_only=True)
#             coded_ids_sequence = CharField(allow_blank=True, allow_null=True, required=False, style={'base_template': 'textarea.html'}, write_only=True)
#             tagged_source = CharField(read_only=True, style={'base_template': 'textarea.html'})
#             target_tags = CharField(read_only=True, style={'base_template': 'textarea.html'})
#             segment_id = IntegerField(read_only=True, source='id')
#     file = PrimaryKeyRelatedField(queryset=File.objects.all(), write_only=True)
#     job = PrimaryKeyRelatedField(queryset=Job.objects.all(), write_only=True)
#     total_word_count = IntegerField()
#     total_char_count = IntegerField()
#     total_segment_count = IntegerField()
#     created_by = PrimaryKeyRelatedField(allow_null=True, queryset=AiUser.objects.all(), required=False, write_only=True)
#     id = IntegerField(label='ID', read_only=True)


