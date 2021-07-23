from rest_framework import serializers
from .models import Document, Segment, TextUnit
import json

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
            "id"
        )

        read_only_fields = (
            "tagged_source",
            "target_tags",
            "id"
        )

        extra_kwargs = {
            "source": {"write_only": True},
            "coded_source": {"write_only": True},
            "coded_brace_pattern": {"write_only": True},
            "coded_ids_sequence": {"write_only": True},
        }

    def to_internal_value(self, data):
        data["coded_ids_sequence"] = json.dumps(data["coded_ids_sequence"])
        return super().to_internal_value(data=data)

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

class DocumentSerializer(serializers.ModelSerializer):
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
        data["total_word_count"] = data["total_char_count"] = data["total_segment_count"] = 0
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

