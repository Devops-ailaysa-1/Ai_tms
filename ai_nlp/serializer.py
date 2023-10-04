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
    # website = serializers.CharField(required=False)
    class Meta:
        model = PdffileUpload
        fields ='__all__'


    def create(self, validated_data):
        instance = PdffileUpload.objects.create(**validated_data)
        instance.file_name = instance.file.name.split("/")[-1]#.split(".")[0] ###not a file
        instance.status="PENDING"
        celery_id = loader.apply_async(args=(instance.id,),) #loader(instance.id)#
        print(celery_id)
        print("vector chromadb created")
        instance.celery_id=celery_id
        instance.is_train=False
        # if instance.file.name.endswith(".pdf"):
        #     instance.pdf_thumbnail = thumbnail_create(instance.file.path)
        instance.save()
        return instance