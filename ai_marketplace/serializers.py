from rest_framework import serializers
from .models import AvailableVendors,ProjectboardDetails,ProjectPostJobDetails,AvailableBids,BidChat
from ai_auth.models import AiUser
from ai_workspace.models import Project
from drf_writable_nested import WritableNestedModelSerializer
import json
from rest_framework.response import Response


class AvailableBidSerializer(serializers.ModelSerializer):
    class Meta:
        model=AvailableBids
        fields="__all__"

class AvailableVendorSerializer(serializers.ModelSerializer):
    class Meta:
        model= AvailableVendors
        fields="__all__"

class ProjectPostJobDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model=ProjectPostJobDetails
        fields=('src_lang','tar_lang',)

class ProjectPostSerializer(WritableNestedModelSerializer,serializers.ModelSerializer):
    projectpost_jobs=ProjectPostJobDetailSerializer(many=True)
    project_id=serializers.PrimaryKeyRelatedField(queryset=Project.objects.all().values_list('pk', flat=True),write_only=True)
    class Meta:
        model=ProjectboardDetails
        fields=('id','project_id','service','steps','sub_field','content_type','proj_name','proj_desc',
                 'bid_deadline','proj_deadline','ven_native_lang','ven_res_country','ven_special_req',
                 'cust_pc_name','cust_pc_email','rate_range_min','rate_range_max','currency',
                 'unit','milestone','projectpost_jobs')

    def run_validation(self, data):
        if data.get("projectpost_jobs") and isinstance( data.get("projectpost_jobs"), str):
            data["projectpost_jobs"]=json.loads(data["projectpost_jobs"])
        return super().run_validation(data)


class BidChatSerializer(serializers.ModelSerializer):
    # """For Serializing Message"""
    # sender = serializers.SlugRelatedField(many=False, slug_field='username', queryset=User.objects.all())
    # receiver = serializers.SlugRelatedField(many=False, slug_field='username', queryset=User.objects.all())
    class Meta:
        model = BidChat
        fields = "__all__"

    def save(self):
        message = BidChat.objects.create(**self.validated_data)
        return message

    def save_update(self):
        return super().save()
