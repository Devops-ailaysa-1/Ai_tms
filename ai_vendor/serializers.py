from rest_framework import serializers
from .models import VendorsInfo,VendorLanguagePair,VendorServiceTypes,VendorServiceInfo,VendorMtpeEngines,VendorMembership,VendorSubjectFields,VendorContentTypes,VendorBankDetails,TranslationSamples,MtpeSamples,VendorCATsoftware,AvailableVendors,ProjectboardDetails,ProjectPostJobDetails
from ai_auth.models import AiUser
from drf_writable_nested import WritableNestedModelSerializer
import json
from rest_framework.response import Response


class VendorsInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = VendorsInfo
        fields = (
            'id',
            'vendor_unique_id',
            'type',
            'currency',
            'vm_status',
            'status',
            'token',
            'skype',
            'proz_link',
            'cv_file',
            'native_lang',
            'year_of_experience',
            'rating',
        )
        extra_kwargs = {'id':{"read_only":True},}

    def save(self, user_id):
        user = VendorsInfo.objects.create(**self.validated_data, user_id=user_id)
        return user

    def save_update(self):
        return super().save()

class VendorLanguagePairSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorLanguagePair
        fields='__all__'

class VendorServiceTypeSerializer(serializers.ModelSerializer):
    class Meta:
       model = VendorServiceTypes
       fields=('id','services','unit_rate','unit_type','hourly_rate',)

class VendorServiceInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model=VendorServiceInfo
        exclude=('lang_pair',)

class VendorCATsoftwareSerializer(serializers.ModelSerializer):
    class Meta:
        model=VendorCATsoftware
        fields=('software',)

class VendorSubjectFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model=VendorSubjectFields
        fields=('subject',)

class VendorMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model=VendorMembership
        fields=('membership',)

class VendorMtpeEngineSerializer(serializers.ModelSerializer):
    class Meta:
        model=VendorMtpeEngines
        fields=('mtpe_engines',)

class VendorContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model=VendorContentTypes
        fields=('contenttype',)

class TranslationSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model=TranslationSamples
        fields=('translation_file',)

class MtpeSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model=MtpeSamples
        fields=('sample_file',)



class VendorLanguagePairSerializer(WritableNestedModelSerializer,serializers.ModelSerializer):#WritableNestedModelSerializer,
     service=VendorServiceInfoSerializer(many=True,required=False)
     servicetype=VendorServiceTypeSerializer(many=True,required=False)
     translationfile=TranslationSampleSerializer(many=True,required=False)
     mtpesamples=MtpeSampleSerializer(many=True,required=False)
     existing_lang_pair_id=serializers.PrimaryKeyRelatedField(queryset=VendorLanguagePair.objects.all().values_list('pk', flat=True),required=False,write_only=True)
     apply_for_reverse=serializers.IntegerField(write_only=True,required=False)
     user_id=serializers.IntegerField()
     class Meta:
         model = VendorLanguagePair
         fields=('id','user_id','source_lang','target_lang','service','servicetype','translationfile','mtpesamples','existing_lang_pair_id','apply_for_reverse',)
         extra_kwargs = {
            'translationfile':{'read_only':True},
            'MtpeSamples':{'read_only':True},
            "source_lang": {"required": False},
            "target_lang": {"required": False}
         }

     def run_validation(self, data):
         if not (("service" in data and ((("source_lang") in data) and(("target_lang") in data)) )\
            or ((("existing_lang_pair_id") in data) and (((("source_lang") in data) and(("target_lang") in data))\
            or("apply_for_reverse") in data))):
             raise serializers.ValidationError({"msg":"any one field is required"})
         if "source_lang" in data:
             if data.get('source_lang')==data.get('target_lang'):
                 raise serializers.ValidationError({"message":"source and target language should not be same"})
         data["user_id"] = self.context.get("request").user.id
         if data.get('service'):
             data["service"] = json.loads(data["service"])
         if data.get("servicetype"):
             data["servicetype"] = json.loads(data["servicetype"])
         print("validated data----->",data)
         return super().run_validation(data)
     def create(self, data):
         user_id = data.get("user_id")
         service_data = data.pop('service', [])
         service_type_data=data.pop('servicetype', [])
         existing_lang_pair_id = data.pop("existing_lang_pair_id", None)
         apply_for_reverse = data.pop("apply_for_reverse", None)
         print("Reverse--->",apply_for_reverse)
         lang_reverse = None
         if data.get("source_lang"):
             lang = VendorLanguagePair.objects.create(**data)
         else:
             lang = VendorLanguagePair.objects.get(id=existing_lang_pair_id)

         if apply_for_reverse:
             reverse_data={"source_lang_id":lang.target_lang_id,"target_lang_id":lang.source_lang_id,"user_id":user_id}
             print("reverse_data--->",reverse_data)
             lang_reverse = VendorLanguagePair.objects.create(**reverse_data)

         if service_data:
             for i in service_data:
                 VendorServiceInfo.objects.create(lang_pair=lang,**i)
                 VendorServiceInfo.objects.create(lang_pair=lang_reverse,**i) if lang_reverse else None
         else:
            service_data=VendorServiceInfo.objects.filter(lang_pair_id=existing_lang_pair_id)
            for k in service_data:
                k.pk=None
                k.lang_pair_id=lang_reverse.id
                k.save()

         if service_type_data:
             for j in service_type_data:
                 VendorServiceTypes.objects.create(lang_pair=lang,**j)
                 VendorServiceTypes.objects.create(lang_pair=lang_reverse,**j) if lang_reverse else None
         else:
             service_type_data=VendorServiceTypes.objects.filter(lang_pair_id=existing_lang_pair_id)
             for m in service_type_data:
                 m.pk=None
                 m.lang_pair_id=lang_reverse.id
                 m.save()

         return lang

class ServiceExpertiseSerializer(WritableNestedModelSerializer,serializers.ModelSerializer):
    vendor_subject=VendorSubjectFieldSerializer(many=True,required=False)
    vendor_membership=VendorMembershipSerializer(many=True,required=False)
    vendor_contentype=VendorContentTypeSerializer(many=True,required=False)
    vendor_mtpe_engines=VendorMtpeEngineSerializer(many=True,required=False)
    vendor_software=VendorCATsoftwareSerializer(many=True,required=False)

    class Meta:
        model=AiUser
        fields=('id','vendor_subject','vendor_membership','vendor_contentype','vendor_mtpe_engines','vendor_software')
        extra_kwargs = {'id':{"read_only":True},
        }

    def run_validation(self, data):

        if data.get("vendor_subject") and isinstance( data.get("vendor_subject"), str):
            data["vendor_subject"]=json.loads(data["vendor_subject"])
        if data.get("vendor_membership") and isinstance( data.get("vendor_membership"), str):
            data["vendor_membership"]=json.loads(data["vendor_membership"])
        if data.get('vendor_contentype') and isinstance( data.get("vendor_contentype"), str):
            data["vendor_contentype"] = json.loads(data["vendor_contentype"])
        if data.get("vendor_mtpe_engines") and isinstance( data.get("vendor_mtpe_engines"), str):
            data["vendor_mtpe_engines"] = json.loads(data["vendor_mtpe_engines"])
        if data.get("vendor_software") and isinstance( data.get("vendor_software"), str):
            data["vendor_software"] = json.loads(data["vendor_software"])
        print("validated data----->",data)
        return data

class VendorBankDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model=VendorBankDetails
        fields=('user','paypal_email','bank_name','bank_address','bank_account_name','bank_account_number','iban','bank_swift_code','bank_ifsc','gst_number','pan_number','other_bank_details')
        extra_kwargs = {'user':{"read_only":True},
        }

    # def create(self, validated_data):
    #     user_id=self.context["request"].user.id
    #     vendor = VendorBankDetails.objects.create(**validated_data, user_id=user_id)
    #     return vendor
    #
    # def update(self):
    #     return super().create()

    def save(self, user_id):
        vendor = VendorBankDetails.objects.create(**self.validated_data, user_id=user_id)
        return vendor

    def save_update(self):
        return super().save()

class LanguagePairSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorLanguagePair
        fields=('user','id','source_lang','target_lang',)
        extra_kwargs = {'user':{"read_only":True},'id':{"read_only":True},
        }
    # def save(self, user_id):
    #     vendor = VendorLanguagePair.objects.create(**self.validated_data, user_id=user_id)
    #     return vendor


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
    class Meta:
        model=ProjectboardDetails
        fields=('id','project_id','service','steps','sub_field','content_type','proj_name','proj_desc',
                 'bid_deadline','proj_deadline','ven_native_lang','ven_res_country','ven_special_req',
                 'cust_pc_name','cust_pc_email','rate_range_min','rate_range_max','currency',
                 'unit','milestone','projectpost_jobs')

    def run_validation(self, data):
        if data.get("projectpost_jobs") and isinstance( data.get("projectpost_jobs"), str):
            data["projectpost_jobs"]=json.loads(data["projectpost_jobs"])
        return data


    # def save(self):
    #     project_detail = projectboard_details.objects.create(**self.validated_data)
    #     return project_detail
    #
    # def save_update(self):
    #     return super().save()
