from rest_framework import serializers
from ai_auth.models import AiUser
from ai_bi.models import BiUser


class AiUserSerializer(serializers.ModelSerializer):

    class Meta:
        model  = AiUser
        # fields ="__all__"
        exclude = ('password', )

class BiUserSerializer(serializers.ModelSerializer):
    name=serializers.SerializerMethodField()
    email=serializers.SerializerMethodField()
    # role=serializers.SerializerMethodField()
    class Meta:
        model  = BiUser
        fields =("id","bi_user","bi_role","name","email")
        read_only_fields = ("name","email")

    def get_name(self,obj):
        return obj.bi_user.fullname

    # def get_role(self,obj):
    #     return obj.get_bi_role_display()

    def get_email(self,obj):
        return obj.bi_user.email