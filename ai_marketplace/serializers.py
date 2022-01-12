from rest_framework import serializers
from .models import (AvailableVendors,ProjectboardDetails,ProjectPostJobDetails,
                    AvailableJobs,BidChat,BidPropasalDetails,BidProposalServicesRates,
                    Thread,ProjectPostContentType,ProjectPostSubjectField,ChatMessage)
from ai_auth.models import AiUser,AiUserProfile,HiredEditors
from ai_staff.models import Languages
from django.db.models import Q
from ai_workspace.models import Project,Job
from drf_writable_nested import WritableNestedModelSerializer
import json
from itertools import groupby
from rest_framework.response import Response
from dj_rest_auth.serializers import UserDetailsSerializer
from ai_auth.serializers import ProfessionalidentitySerializer
from ai_vendor.serializers import VendorLanguagePairSerializer,VendorSubjectFieldSerializer,VendorContentTypeSerializer,VendorServiceInfoSerializer,VendorLanguagePairCloneSerializer
from ai_vendor.models import VendorLanguagePair,VendorServiceInfo,VendorsInfo,VendorSubjectFields

class AvailableJobSerializer(serializers.ModelSerializer):
    class Meta:
        model=AvailableJobs
        fields="__all__"

class AvailableVendorSerializer(serializers.ModelSerializer):
    class Meta:
        model= AvailableVendors
        fields="__all__"

    def run_validation(self, data):
        vendor = data.get('vendor')
        customer = data.get('customer')
        if vendor == customer:
            raise serializers.ValidationError({"msg":"Both vendor and customer are same"})
        lookup = Q(customer_id=customer) & Q(vendor_id=vendor)
        qs = AvailableVendors.objects.filter(lookup)
        print(qs)
        if qs.exists():
            raise serializers.ValidationError({"msg":"This vendor is already assigned to customer" })
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
    projectpostjob_id  = serializers.PrimaryKeyRelatedField(queryset=ProjectPostJobDetails.objects.all().values_list('pk', flat=True))
    projectpost_id  = serializers.PrimaryKeyRelatedField(queryset=ProjectboardDetails.objects.all().values_list('pk', flat=True))
    vendor_id = serializers.PrimaryKeyRelatedField(queryset=AiUser.objects.all().values_list('pk', flat=True))
    class Meta:
        model = BidPropasalDetails
        fields = ('id','projectpostjob_id','projectpost_id','vendor_id','service_and_rates','proposed_completion_date','description','sample_file_upload','status',)

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
        if first_person == second_person:
            raise serializers.ValidationError({"msg":"Thread between same person cannot be created"})
        lookup1 = Q(first_person=first_person) & Q(second_person=second_person) & Q(bid=bid)
        lookup2 = Q(first_person=second_person) & Q(second_person=first_person) & Q(bid=bid)
        lookup = Q(lookup1 | lookup2)
        qs = Thread.objects.filter(lookup)
        print(qs)
        if qs.exists():
            raise serializers.ValidationError({"msg":f'Thread between {first_person} and {second_person} already exists.','thread_id':qs[0].id})# for this {bid}.'})
        return super().run_validation(data)


# class VendorSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = VendorsInfo
#         fields = ('type','currency','native_lang','year_of_experience',)

# class OfficialInfoSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = AiUserProfile
#         fields = ('organisation_name',)


# class VendorSubjectSerializer(serializers.ModelSerializer):
#     subject = serializers.ReadOnlyField(source='subject.name')
#     class Meta:
#         model=VendorSubjectFields
#         fields=('subject',)



class GetVendorDetailSerializer(serializers.Serializer):
    uid = serializers.CharField(read_only=True)
    fullname = serializers.CharField(read_only=True)
    organisation_name = serializers.ReadOnlyField(source='ai_profile_info.organisation_name')
    legal_category = serializers.ReadOnlyField(source='vendor_info.type.name')
    currency = serializers.ReadOnlyField(source='vendor_info.currency.currency_code')
    country = serializers.ReadOnlyField(source = 'country.name')
    location = serializers.ReadOnlyField(source = 'vendor_info.location')
    native_lang = serializers.ReadOnlyField(source = 'vendor_info.native_lang.language')
    year_of_experience = serializers.ReadOnlyField(source = 'vendor_info.year_of_experience')
    professional_identity= serializers.ReadOnlyField(source='professional_identity_info.avatar_url')
    vendor_subject = VendorSubjectFieldSerializer(read_only=True,many=True)
    vendor_contentype = VendorContentTypeSerializer(read_only=True,many=True)
    vendor_lang_pair = serializers.SerializerMethodField(source='get_vendor_lang_pair')
    status = serializers.SerializerMethodField()

    def get_vendor_lang_pair(self, obj):
        request = self.context['request']
        job_id= request.query_params.get('job')
        source_lang = request.query_params.get('source_lang')
        target_lang = request.query_params.get('target_lang')
        if job_id:
            source_lang=Job.objects.get(id=job_id).source_language_id
            target_lang=Job.objects.get(id=job_id).target_language_id
        return VendorLanguagePairCloneSerializer(obj.vendor_lang_pair.filter(Q(source_lang_id=source_lang)&Q(target_lang_id=target_lang)), many=True, read_only=True).data

    def get_status(self,obj):
        request_user = self.context['request'].user
        user = request_user.team.owner if request_user.is_internal_member == True else request_user
        editor = AiUser.objects.get(uid = obj.uid)
        if editor in user.get_hired_editors:
            hired = HiredEditors.objects.get(Q(hired_editor = editor)&Q(user = user))
            return hired.get_status_display()
        else:
            return None


class ProjectPostJobDetailSerializer(serializers.ModelSerializer):
    bid_count = serializers.SerializerMethodField()
    bidjob_details = BidPropasalDetailSerializer(many=True,read_only=True)
    class Meta:
        model=ProjectPostJobDetails
        fields=('id','src_lang','tar_lang','bid_count','bidjob_details',)

    def get_bid_count(self, obj):
        return obj.bidjob_details.count()

class ProjectPostContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPostContentType
        fields = ('content_type',)

class ProjectPostSubjectFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPostSubjectField
        fields = ('subject',)



class ProjectPostSerializer(WritableNestedModelSerializer,serializers.ModelSerializer):
    bid_count = serializers.SerializerMethodField()
    # bidproject_details = BidPropasalDetailSerializer(many=True,read_only=True)
    projectpost_jobs=ProjectPostJobDetailSerializer(many=True,required=False)
    projectpost_content_type=ProjectPostContentTypeSerializer(many=True,required=False)
    projectpost_subject=ProjectPostSubjectFieldSerializer(many=True,required=False)
    project_id=serializers.PrimaryKeyRelatedField(queryset=Project.objects.all().values_list('pk', flat=True),write_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(queryset=AiUser.objects.all().values_list('pk', flat=True),write_only=True)
    class Meta:
        model=ProjectboardDetails
        fields=('id','project_id','customer_id','service','steps','proj_name','proj_desc',
                 'bid_deadline','proj_deadline','ven_native_lang','ven_res_country','ven_special_req',
                 'cust_pc_name','cust_pc_email','rate_range_min','rate_range_max','currency',
                 'unit','milestone','bid_count','projectpost_jobs','projectpost_content_type','projectpost_subject',)

    def get_bid_count(self, obj):
        bidproject_details = BidPropasalDetailSerializer(many=True,read_only=True)
        print(obj.bidproject_details.count())
        return obj.bidproject_details.count()


    def run_validation(self, data):
        if data.get('contents') and isinstance( data.get("contents"), str):
            data["projectpost_content_type"] = json.loads(data['contents'])

        if data.get('subjects') and isinstance( data.get("subjects"), str):
            data["projectpost_subject"] = json.loads(data['subjects'])

        if data.get("jobs") and isinstance( data.get("jobs"), str):
            jobs=json.loads(data["jobs"])
            source_language = jobs[0].get("src_lang")
            target_languages = jobs[0].get("tar_lang")
            if source_language and target_languages:
                data["projectpost_jobs"] = [{"src_lang": source_language, "tar_lang": target_language}
                                            for target_language in target_languages]
        print("data---->",data["projectpost_jobs"])
        return super().run_validation(data)

class VendorInfoListSerializer(serializers.ModelSerializer):
    legal_category = serializers.ReadOnlyField(source='type.name')
    currency = serializers.ReadOnlyField(source='currency.currency_code')
    class Meta:
        model = VendorsInfo
        fields = ('legal_category','currency')


class VendorServiceSerializer(serializers.ModelSerializer):
    service = VendorServiceInfoSerializer(many=True,read_only=True)
    class Meta:
        model = VendorLanguagePair
        fields = ('service',)


class GetVendorListSerializer(serializers.ModelSerializer):
    vendor_lang_pair = serializers.SerializerMethodField(source='get_vendor_lang_pair')
    legal_category = serializers.ReadOnlyField(source='vendor_info.type.name')
    currency = serializers.ReadOnlyField(source='vendor_info.currency.currency_code')
    country = serializers.ReadOnlyField(source = 'country.sortname')
    professional_identity= serializers.ReadOnlyField(source='professional_identity_info.avatar_url')
    status = serializers.SerializerMethodField()
    class Meta:
        model = AiUser
        fields = ('id','uid','fullname','legal_category','country','currency','professional_identity','vendor_lang_pair','status',)


    def get_status(self,obj):
        request_user = self.context['request'].user
        user = request_user.team.owner if request_user.is_internal_member == True else request_user
        editor = AiUser.objects.get(uid = obj.uid)
        if editor in user.get_hired_editors:
            hired = HiredEditors.objects.get(Q(hired_editor = editor)&Q(user = user))
            return hired.get_status_display()
        else:
            return None



    def get_vendor_lang_pair(self, obj):
        request = self.context['request']
        job_id= request.query_params.get('job')
        source_lang = request.query_params.get('source_lang')
        target_lang = request.query_params.get('target_lang')
        if job_id:
            source_lang=Job.objects.get(id=job_id).source_language_id
            target_lang=Job.objects.get(id=job_id).target_language_id
        return VendorServiceSerializer(obj.vendor_lang_pair.filter(Q(source_lang_id=source_lang)&Q(target_lang_id=target_lang)&Q(deleted_at=None)), many=True, read_only=True).data

class ChatMessageSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.fullname')
    # user_avatar = serializers.ReadOnlyField(source='user.professional_identity_info.avatar_url')
    class Meta:
        model = ChatMessage
        fields = ('id','thread','user','user_name','message','timestamp',)
        # extra_kwargs = {
        #     'user':{'write_only':True},
        #      }

    def run_validation(self,data):
        if self.context['request']._request.method == 'POST':
            user = int(data.get('user'))
            thread = data.get('thread')
            user1 = Thread.objects.get(id = thread).first_person_id
            user2 = Thread.objects.get(id = thread).second_person_id
            if (user!=user1) and (user!=user2):
                raise serializers.ValidationError({"msg":'This person is not in this thread,he cannot send messages here'})
        return super().run_validation(data)


class ChatMessageByDateSerializer(serializers.ModelSerializer):
    logged_in_user = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    message = serializers.SerializerMethodField()
    organisation_name = serializers.SerializerMethodField()
    class Meta:
        model = Thread
        fields = ('logged_in_user','user_name','avatar','organisation_name','message',)

    def get_logged_in_user(self,obj):
        user = self.context['request'].user
        return user.id

    def get_user_name(self,obj):
        user = obj.first_person if obj.second_person == self.context['request'].user else obj.second_person
        # user = self.context['request'].user
        return user.fullname

    def get_avatar(self,obj):
        user = obj.first_person if obj.second_person == self.context['request'].user else obj.second_person
        try: return user.professional_identity_info.avatar_url
        except: return None

    def get_organisation_name(self,obj):
        user = obj.first_person if obj.second_person == self.context['request'].user else obj.second_person
        try: return user.ai_profile_info.organisation_name
        except: return None

    def get_message(self, obj):
        message = self.context['request'].query_params.get('message')
        if message:
            messages = ChatMessage.objects.filter(Q(thread_id = obj.id) & Q(message__icontains=message))
        else:
            messages = ChatMessage.objects.filter(thread_id = obj.id)
        messages_grouped_by_date = groupby(messages.iterator(), lambda m: m.timestamp.date())
        messages_dict = {}
        for date, group_of_messages in messages_grouped_by_date:
            dict_key = date.strftime('%Y-%m-%d')
            messages_dict[dict_key] = ChatMessageSerializer(group_of_messages,many=True).data
        return messages_dict
