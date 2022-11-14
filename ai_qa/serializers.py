from .models import Forbidden,Untranslatable
from rest_framework import serializers




class ForbiddenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Forbidden
        fields = ('id','forbidden_file','project','job','name','created_at',)
        #fields = "__all__"


class UntranslatableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Untranslatable
        fields = ('id','untranslatable_file','project','job','name','created_at',)
        #fields = "__all__"
