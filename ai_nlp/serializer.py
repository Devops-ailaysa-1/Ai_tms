from rest_framework import serializers
from ai_nlp.models import PdffileUpload,PdffileChatHistory
from ai_nlp.utils import loader #,thumbnail_create


class PdffileChatHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PdffileChatHistory
        fields ='__all__'

class PdffileShowDetailsSerializer(serializers.ModelSerializer):
    pdf_file_chat=PdffileChatHistorySerializer(many=True)
    class Meta:
        model = PdffileUpload
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        pdf_file_chat = instance.pdf_file_chat.order_by('-id')
        representation['pdf_file_chat'] = PdffileChatHistorySerializer(pdf_file_chat, many=True).data
        return representation

class PdffileUploadSerializer(serializers.ModelSerializer):
    # website = serializers.CharField(required=False)
    class Meta:
        model = PdffileUpload
        fields =('id','file_name','created_at','updated_at','celery_id','status','user','file')


    def create(self, validated_data):
        instance = PdffileUpload.objects.create(**validated_data)
        instance.file_name = instance.file.name.split("/")[-1]#.split(".")[0] ###not a file
        instance.status="PENDING"
        # if instance.file.name.endswith(".epub"):
        #     text_scrap = epub_processing(instance.file.path)
        #     instance.text_file =text_scrap
        #     instance.save()
        celery_id = loader.apply_async(args=(instance.id,),) #loader(instance.id)#
        print(celery_id)
        print("vector chromadb created")
        instance.celery_id=celery_id
        instance.is_train=False
         
        # if instance.file.name.endswith(".pdf"):
        #     instance.pdf_thumbnail = thumbnail_create(instance.file.path)
        instance.save()
        return instance