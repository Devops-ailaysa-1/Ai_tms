from rest_framework import serializers
from .models import UploadedTMinfo
from ai_staff.models import SubjectFields


class UploadedTMinfoListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        return  [ self.child.create(data) for data in validated_data]


class UploadedTMinfoSerializer(serializers.ModelSerializer):

    class Meta:
        list_serializer_class = UploadedTMinfoListSerializer
        model  = UploadedTMinfo
        fields = ("tm_file", "source_language", "target_languages",
                  "subject_fields")

class TMUploadRequestDataResolveSerializer(serializers.
        Serializer):
    tm_files = serializers.ListField()
    subject_fields = serializers.ListField()
    target_languages = serializers.ListField()
    source_language = serializers.IntegerField()

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret = [{"tm_file": tm_file, "source_language": ret["source_language"],
                "target_languages": ret["target_languages"], "subject_fields":
                ret["subject_fields"]} for tm_file in ret.pop("tm_files")]
        return ret



