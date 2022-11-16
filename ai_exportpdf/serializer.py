from statistics import mode
from rest_framework import serializers
from .models import Ai_PdfUpload



class PdfFileSerializer(serializers.ModelSerializer):
 
    class Meta:
        model = Ai_PdfUpload
        # fields = ('id','pdf_file_name' ,'counter','pdf_no_of_page' ,'pdf_task_id' ,'docx_file_urls' )
        fields = "__all__"


# class PdfFileDownloadLinkSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Ai_PdfUpload
#         fields = ('id' , 'docx_file_urls')

class PdfFileStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ai_PdfUpload
        fields = ('id' ,'pdf_language','counter','pdf_no_of_page' ,'pdf_task_id' ,'docx_url_field','status' ,'docx_file_name','file_name', 'pdf_file_name')
 
    