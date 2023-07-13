from rest_framework import serializers
from ai_auth.models import AiUser


class AiUserSerializer(serializers.ModelSerializer):

    class Meta:
        model  = AiUser
        # fields ="__all__"
        exclude = ('password', )