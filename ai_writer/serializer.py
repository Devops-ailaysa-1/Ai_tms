from rest_framework.serializers import ModelSerializer  
from rest_framework import serializers
from ai_writer.models import FileDetails
 



class FileSerializer(ModelSerializer):
    class Meta:
        model = FileDetails 
        fields = ('id','file_name','user_name','store_quill_data' ,'store_quill_text')  #,'json_file'
        read_only = ('id')

class VerbSerializer(serializers.Serializer):
    text_string = serializers.CharField()
    synonyms_form =serializers.ListField()


class SpellCheckSerializer(serializers.Serializer):
    word_suggest = serializers.ListField()


 


class ProductDescriptionSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=200)
    keywords = serializers.CharField(max_length=200)
    choices = serializers.JSONField()
     


class FaceBookAdSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=200)
    description = serializers.CharField(max_length = 200)
    choices = serializers.JSONField()
