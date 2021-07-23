from rest_framework import serializers
from .models import VendorsInfo,VendorLanguagePair,VendorServiceTypes,VendorServiceInfo,VendorMtpeEngines,VendorMembership,VendorSubjectFields,VendorContentTypes,VendorBankDetails,TranslationSamples,MtpeSamples,VendorCATsoftware
from ai_auth.models import AiUser
from drf_writable_nested import WritableNestedModelSerializer
import json

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
     class Meta:
         model = VendorLanguagePair
         fields=('id','user_id','source_lang_id','target_lang_id','service','servicetype','translationfile','mtpesamples',)
         extra_kwargs = {'translationfile':{'read_only':True},'MtpeSamples':{'read_only':True},
         }#'source_lang':{"read_only":True},'target_lang':{"read_only":True},'user_id':{"read_only":True},


     def run_validation(self, data):
         if data.get("source_lang_id"):
             data["source_lang_id"]=json.loads(data["source_lang_id"])
         if data.get("apply_for_reverse"):
             data["apply_for_reverse"]=json.loads(data["apply_for_reverse"])
         if data.get("existing_lang_pair_id"):
             data["existing_lang_pair_id"]=json.loads(data["existing_lang_pair_id"])
         if data.get("target_lang_id"):
             data["target_lang_id"]=json.loads(data["target_lang_id"])
         if data.get('service'):
             data["service"] = json.loads(data["service"])
         if data.get("servicetype"):
             data["servicetype"] = json.loads(data["servicetype"])
         print("validated data----->",data)
         return data
        # data["translationfile"] = [{'translation_file': file} for file in data["translation_files"]]
        # data["MtpeSamples"] = [{"sample_file":file} for file in data["mtpe_samples"]]


     def create(self,validated_data):
         user_id=self.context["request"].user.id
         print("user_id---->",user_id)
         data_new=validated_data
         if validated_data.get("existing_lang_pair_id"):
             existing_lang_pair_id=validated_data.pop('existing_lang_pair_id')
         if validated_data.get('servicetype'):
             service_type_data=validated_data.pop('servicetype')
         if validated_data.get("service"):
             service_data =validated_data.pop('service')
         if validated_data.get("apply_for_reverse"):
             reverse =validated_data.pop('apply_for_reverse')
         print("NEW---->",validated_data)
         try:
             if bool(int(reverse)):
                 source_new=validated_data.get("target_lang_id")
                 target_new=validated_data.get("source_lang_id")
                 data_new={"source_lang_id":source_new,"target_lang_id":target_new,"user_id":user_id}
                 lang_reverse = VendorLanguagePair.objects.create(**data_new)
                 lang= VendorLanguagePair.objects.create(**validated_data)
         except:
             lang = VendorLanguagePair.objects.create(**validated_data)
         print("langId---->",lang.id)
         try:
             if service_type_data:
                     for j in service_type_data:
                         VendorServiceTypes.objects.create(lang_pair_id=lang.id,**j)
                         if lang_reverse:
                             VendorServiceTypes.objects.create(lang_pair_id=lang_reverse.id,**j)
         except:
              servicetype_datas=VendorServiceTypes.objects.filter(lang_pair_id=existing_lang_pair_id)
              print(servicetype_datas)
              for data in servicetype_datas:
                  data.pk=None
                  data.lang_pair_id=lang.id
                  data.save()
         try:
             if service_data:
                 for i in service_data:
                     VendorServiceInfo.objects.create(lang_pair_id=lang.id,**i)
                     if lang_reverse:
                         VendorServiceInfo.objects.create(lang_pair_id=lang_reverse.id,**i)
         except:
             service_datas=VendorServiceInfo.objects.filter(lang_pair_id=existing_lang_pair_id)
             print(service_datas)
             for i in service_datas:
                 i.pk=None
                 i.lang_pair_id=lang.id
                 i.save()
         return data_new



    # def create(self,validated_data):
    #     user_id=self.context["request"].user.id
    #     print(user_id)
    #     data_new=validated_data
    #     service_data = validated_data.pop('service')
    # def save(self,user_id):
    #     data_new=self.validated_data
    #     service_data = self.validated_data.pop('service')
    #     print("service--->",service_data)
    #     service_type_data=self.validated_data.pop('servicetype')
    #     lang = VendorLanguagePair.objects.create(**self.validated_data,user_id=user_id)
    #     for i in service_data:
    #         VendorServiceInfo.objects.create(lang_pair=lang,**i)
    #     for j in service_type_data:
    #         VendorServiceTypes.objects.create(lang_pair=lang,**j)
    #     return data_new
    #
    # def update(self, instance, validated_data):
    #     print(instance)
    #     services=instance.service
    #     # print(service.id)
    #     for item, service in zip(validated_data['service'], services.all()):
    #         VendorServiceInfo.objects.update_or_create(**item)


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
        if data.get("vendor_subject"):
            data["vendor_subject"]=json.loads(data["vendor_subject"])
        if data.get("vendor_membership"):
            data["vendor_membership"]=json.loads(data["vendor_membership"])
        if data.get('vendor_contentype'):
            data["vendor_contentype"] = json.loads(data["vendor_contentype"])
        if data.get("vendor_mtpe_engines"):
            data["vendor_mtpe_engines"] = json.loads(data["vendor_mtpe_engines"])
        if data.get("vendor_software"):
            data["vendor_software"] = json.loads(data["vendor_software"])
        print("validated data----->",data)
        return data

class VendorBankDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model=VendorBankDetails
        fields=('user','paypal_email','bank_name','bank_address','bank_account_name','bank_account_number','iban','bank_swift_code','bank_ifsc','gst_number','pan_number','other_bank_details')
        extra_kwargs = {'user':{"read_only":True},
        }


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
