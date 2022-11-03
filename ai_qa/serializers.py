from .models import Forbidden,Untranslatable
from rest_framework import serializers




class ForbiddenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Forbidden
        fields = "__all__"


class UntranslatableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Untranslatable
        fields = "__all__"
