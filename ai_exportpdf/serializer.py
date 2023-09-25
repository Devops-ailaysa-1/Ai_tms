from statistics import mode
from rest_framework import serializers
from .models import Ai_PdfUpload # AiImageGeneration
from ai_auth.models import UserCredits
from itertools import groupby
from django_celery_results.models import TaskResult
import json

class PdfFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ai_PdfUpload
        fields = "__all__"


    def to_representation(self, instance):
        data=super().to_representation(instance)
        if instance.pdf_task_id:
            task_id=instance.pdf_task_id
            tsk_ins=TaskResult.objects.filter(task_id=task_id)
            if tsk_ins:
                data['progress']=json.loads(tsk_ins.last().result)  
                data['info']=tsk_ins.last().status 
        return data
    
    def create(self,validated_data):
        validated_data['pdf_file_name']=str(validated_data['pdf_file'])
        validated_data['file_name']=str(validated_data['pdf_file'])
        instance=Ai_PdfUpload.objects.create(**validated_data)
        return instance
            
# class PdfFileDownloadLinkSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Ai_PdfUpload
#         fields = ('id' , 'docx_file_urls')

class PdfFileStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ai_PdfUpload
        fields = ('id' ,'pdf_language','counter','pdf_no_of_page' ,'pdf_task_id',
                  'docx_url_field','status' ,'docx_file_name','file_name', 'pdf_file_name')
 

