from rest_framework import serializers
from .models import Document, Segment, TextUnit, MT_RawTranslation, MT_Engine
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
        )

        read_only_fields = (
            "tagged_source",
            "target_tags",
            # "id",
        )

        extra_kwargs = {
            "source": {"write_only": True},
            "coded_source": {"write_only": True},
            "coded_brace_pattern": {"write_only": True},
            "coded_ids_sequence": {"write_only": True},
        }

    def to_internal_value(self, data):
        # print(self)
        data["coded_ids_sequence"] = json.dumps(data["coded_ids_sequence"])
        return super().to_internal_value(data=data)

class SegmentSerializerV2(SegmentSerializer):
    class Meta(SegmentSerializer.Meta):
        fields = ("target", "id")

    def to_internal_value(self, data):
        return super(SegmentSerializer, self).to_internal_value(data=data)


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
            "id": {"read_only": True}
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
        fields = ("text_unit_ser", "file", "job",
                  "total_word_count", "total_char_count",
                  "total_segment_count", "created_by", "document_id")

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

