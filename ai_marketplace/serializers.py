from rest_framework import serializers
from .models import (AvailableVendors,ProjectboardDetails,ProjectPostJobDetails,
                    AvailableBids,BidChat,BidPropasalDetails,BidProposalServicesRates,
                    Thread)
from ai_auth.models import AiUser,OfficialInformation
from django.db.models import Q
from ai_workspace.models import Project
from drf_writable_nested import WritableNestedModelSerializer
import json
from rest_framework.response import Response
from dj_rest_auth.serializers import UserDetailsSerializer
from ai_auth.serializers import ProfessionalidentitySerializer,OfficialInformationSerializer
from ai_vendor.serializers import VendorLanguagePairSerializer,VendorSubjectFieldSerializer,VendorContentTypeSerializer,VendorServiceInfoSerializer
from ai_vendor.models import VendorLanguagePair,VendorServiceInfo,VendorsInfo

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
    customer_id = serializers.PrimaryKeyRelatedField(queryset=AiUser.objects.all().values_list('pk', flat=True),write_only=True)
    class Meta:
        model=ProjectboardDetails
        fields=('id','project_id','customer_id','service','steps','sub_field','content_type','proj_name','proj_desc',
                 'bid_deadline','proj_deadline','ven_native_lang','ven_res_country','ven_special_req',
                 'cust_pc_name','cust_pc_email','rate_range_min','rate_range_max','currency',
                 'unit','milestone','projectpost_jobs')

    def run_validation(self, data):
        if data.get("projectpost_jobs") and isinstance( data.get("projectpost_jobs"), str):
            data["projectpost_jobs"]=json.loads(data["projectpost_jobs"])
        return super().run_validation(data)


class BidChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = BidChat
        fields = "__all__"

    def save(self):
        message = BidChat.objects.create(**self.validated_data)
        return message

    def save_update(self):
        return super().save()


class BidPropasalServicesRatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = BidProposalServicesRates
        fields = ('mtpe_rate','mtpe_hourly_rate','mtpe_count_unit',)


class BidPropasalDetailSerializer(WritableNestedModelSerializer,serializers.ModelSerializer):
    service_and_rates = BidPropasalServicesRatesSerializer(many=True,required=False)
    projectpostjob_id  = serializers.PrimaryKeyRelatedField(queryset=ProjectPostJobDetails.objects.all().values_list('pk', flat=True),write_only=True)
    vendor_id = serializers.PrimaryKeyRelatedField(queryset=AiUser.objects.all().values_list('pk', flat=True),write_only=True)
    class Meta:
        model = BidPropasalDetails
        fields = ('id','projectpostjob_id','vendor_id','service_and_rates','proposed_completion_date','description','sample_file_upload',)

    def run_validation(self, data):
        if data.get("service_and_rates") and isinstance( data.get("service_and_rates"), str):
            data["service_and_rates"]=json.loads(data["service_and_rates"])
        return super().run_validation(data)



class ThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Thread
        fields = "__all__"

    def run_validation(self, data):
        first_person = data.get('first_person')
        second_person = data.get('second_person')
        bid = data.get('bid')
        lookup1 = Q(first_person=first_person) & Q(second_person=second_person) & Q(bid=bid)
        lookup2 = Q(first_person=second_person) & Q(second_person=first_person) & Q(bid=bid)
        lookup = Q(lookup1 | lookup2)
        qs = Thread.objects.filter(lookup)
        print(qs)
        if qs.exists():
            raise serializers.ValidationError({"msg":f'Thread between {first_person} and {second_person} already exists for this {bid}.'})
        return super().run_validation(data)


class VendorServiceSerializer(serializers.ModelSerializer):
    service = VendorServiceInfoSerializer(many=True,read_only=True,required=False)
    class Meta:
        model = VendorLanguagePair
        fields = ('service',)

class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorsInfo
        fields = ('type','currency','proz_link','native_lang','year_of_experience',)

class OfficialInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfficialInformation
        fields = ('company_name',)

class GetVendorDetailSerializer(serializers.Serializer):
    fullname = serializers.CharField(read_only=True)
    official_info = OfficialInfoSerializer(read_only=True,required=False)
    vendor_subject = VendorSubjectFieldSerializer(read_only=True,many=True)
    vendor_contentype = VendorContentTypeSerializer(read_only=True,many=True)
    vendor_info = VendorSerializer(read_only=True)
