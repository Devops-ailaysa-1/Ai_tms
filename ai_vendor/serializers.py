from rest_framework import serializers
from ai_vendor.models import (VendorsInfo,VendorLanguagePair,VendorServiceTypes,
                                VendorServiceInfo,VendorMtpeEngines,VendorMembership,
                                VendorSubjectFields,VendorContentTypes,VendorBankDetails,
                                TranslationSamples,MtpeSamples,VendorCATsoftware,
                                SavedVendor)
from ai_auth.models import AiUser
from drf_writable_nested import WritableNestedModelSerializer
import json
from rest_framework.response import Response


class VendorsInfoSerializer(serializers.ModelSerializer):
    cv_file = serializers.FileField(required=False, allow_empty_file=True, allow_null=True)
    class Meta:
        model = VendorsInfo
        fields = ('id','vendor_unique_id','type','currency','vm_status','status','token','skype',
                'proz_link','cv_file','cv_file_display','native_lang','year_of_experience','rating','location','bio',)
        extra_kwargs = {'id':{"read_only":True},}

    def save(self, user_id):
        user = VendorsInfo.objects.create(**self.validated_data, user_id=user_id)
        return user

    def save_update(self):
        return super().save()

class VendorServiceTypeSerializer(serializers.ModelSerializer):
    class Meta:
       model = VendorServiceTypes
       fields=('id','services','unit_rate','unit_type','hourly_rate',)

class VendorServiceInfoSerializer(serializers.ModelSerializer):
    # mtpe_rate = serializers.DecimalField(max_digits=12, decimal_places=2)
    class Meta:
        model=VendorServiceInfo
        # fields = ('id','mtpe_rate','mtpe_hourly_rate','mtpe_count_unit',)
        exclude=('lang_pair','created_at','updated_at','deleted_at')

class VendorCATsoftwareSerializer(serializers.ModelSerializer):
    class Meta:
        model=VendorCATsoftware
        fields=('software',)

class SavedVendorSerializer(serializers.ModelSerializer):
    class Meta:
        model=SavedVendor
        fields='__all__'

    def run_validation(self, data):
        customer = data.get('customer')
        vendor = json.loads(data.get('vendor'))
        print('customer--------->',customer,type(customer))
        print('vendor----------->',vendor,type(vendor))
        if customer == vendor:
            print("Inside")
            raise serializers.ValidationError({"msg":"save-vendor cannot happen between same person"})
        return super().run_validation(data) 
    

class VendorSubjectFieldSerializer(serializers.ModelSerializer):
    subject_name = serializers.ReadOnlyField(source='subject.name')
    class Meta:
        model=VendorSubjectFields
        fields=('subject','subject_name')

class VendorMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model=VendorMembership
        fields=('membership',)

class VendorMtpeEngineSerializer(serializers.ModelSerializer):
    class Meta:
        model=VendorMtpeEngines
        fields=('mtpe_engines',)

class VendorContentTypeSerializer(serializers.ModelSerializer):
    contenttype_name = serializers.ReadOnlyField(source='contenttype.name')
    class Meta:
        model=VendorContentTypes
        fields=('contenttype','contenttype_name')

class TranslationSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model=TranslationSamples
        fields=('translation_file',)

class MtpeSampleSerializer(serializers.ModelSerializer):
    class Meta:
        model=MtpeSamples
        fields=('sample_file',)

class VendorLanguagePairCloneSerializer(serializers.ModelSerializer):
    Currency = serializers.ReadOnlyField(source='currency.currency_code')
    service=VendorServiceInfoSerializer(many=True,required=False)
    servicetype=VendorServiceTypeSerializer(many=True,required=False)
    source_lang = serializers.ReadOnlyField(source='source_lang.language')
    target_lang = serializers.ReadOnlyField(source='target_lang.language')
    class Meta:
        model = VendorLanguagePair
        fields=('source_lang','target_lang','Currency','service','servicetype')

class VendorLanguagePairSerializer(WritableNestedModelSerializer,serializers.ModelSerializer):#WritableNestedModelSerializer,
     service=VendorServiceInfoSerializer(many=True,required=False)
     servicetype=VendorServiceTypeSerializer(many=True,required=False)
     translationfile=TranslationSampleSerializer(many=True,required=False)
     mtpesamples=MtpeSampleSerializer(many=True,required=False)
     existing_lang_pair_id=serializers.PrimaryKeyRelatedField(queryset=VendorLanguagePair.objects.all().values_list('pk', flat=True),required=False,write_only=True)
     apply_for_reverse=serializers.IntegerField(write_only=True,required=False)
     user_id=serializers.IntegerField()
     currency_code =  serializers.ReadOnlyField(source ='currency.currency_code')
     source_lang_name = serializers.ReadOnlyField(source ='source_lang.language')
     target_lang_name = serializers.ReadOnlyField(source ='target_lang.language')

     class Meta:
         model = VendorLanguagePair
         fields=('id','user_id','source_lang','target_lang','currency','currency_code','source_lang_name','target_lang_name','service','servicetype','translationfile','mtpesamples','existing_lang_pair_id','apply_for_reverse',)
         extra_kwargs = {
            'translationfile':{'read_only':True},
            'MtpeSamples':{'read_only':True},
            "source_lang": {"required": False},
            "target_lang": {"required": False},
            "currency":{"required":False}
         }


     def run_validation(self, data):
         print("Data--->",data)
         data["user_id"] = self.context.get("request").user.id
         # if self.context['request']._request.method == 'POST':
         #     if "source_lang" in data and "target_lang" in data:
         #         tt = VendorLanguagePair.objects.filter(source_lang_id=data.get('source_lang'),target_lang_id=data.get('target_lang'),user_id=data['user_id'])
         #         if len(tt) == 1:
         #             if tt.first().service.exists():pass
         #             elif tt.first().servicetype.exists():pass
         #             else:tt.delete()
         # # if not (("service" in data and ((("source_lang") in data) and(("target_lang") in data)) )\
         # #    or ((("existing_lang_pair_id") in data) and (((("source_lang") in data) and(("target_lang") in data))\
         # #    or("apply_for_reverse") in data))):
         # # if self.context['request']._request.method == 'POST':
         # #     if not (("service" in data and ((("source_lang") in data) and(("target_lang") in data)) )\
         # #        or ((("existing_lang_pair_id") in data) and (("apply_for_reverse") in data))):
         # #         raise serializers.ValidationError({"message":"Given data is not sufficient to create lang_pair"})
        #   ##
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
             print("lang====>",lang)
         else:
             lang = VendorLanguagePair.objects.get(id=existing_lang_pair_id)

         if apply_for_reverse:
             reverse_data={"source_lang_id":lang.target_lang_id,"target_lang_id":lang.source_lang_id,"currency":lang.currency,"user_id":user_id}
             print("reverse_data--->",reverse_data)
             try:lang_reverse = VendorLanguagePair.objects.create(**reverse_data)
             except BaseException as e:
                 print(f"Error : {str(e)}")

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
        print('Data---->',data)
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
        return super().run_validation(data)

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
