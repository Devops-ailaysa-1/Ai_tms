from rest_framework import serializers
from ai_nlp.models import PdffileUpload,PdffileChatHistory
from ai_nlp.utils import loader,thumbnail_create


class PdffileChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PdffileChatHistory
        fields ='__all__'

class PdffileShowDetailsSerializer(serializers.ModelSerializer):
    pdf_file_chat=PdffileChatHistorySerializer(many=True)
    class Meta:
        model = PdffileUpload
        fields = '__all__'




class PdffileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PdffileUpload
        fields ='__all__'


    def create(self, validated_data):
        print("validated_data",validated_data)
        # request = self.context['request']
        # user = request.user.team.owner  if request.user.team  else request.user
        # created_by = request.user
        print("this is instance to create")
        instance = PdffileUpload.objects.create(**validated_data)
        instance.file_name = instance.file.name.split("/")[-1].split(".")[0]
        loader(instance)
        print("vector chromadb created")
        instance.is_train=True
        if instance.file.name.endswith(".pdf"):
            instance.pdf_thumbnail = thumbnail_create(instance.file.path)
        instance.save()
        return instance