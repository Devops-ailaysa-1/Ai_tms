from django.db.models.fields import IntegerField
from rest_framework import serializers
from .models import (AilaysaSupportedMtpeEngines, ContentTypes, Countries, IndianStates,
                    Languages, LanguagesLocale, MtpeEngines, ServiceTypes,Currencies, StripeTaxId,
                    SubjectFields, SupportFiles, Timezones,Billingunits,
                    AiUserType,ServiceTypeunits,SupportType,SubscriptionPricing,
                    SubscriptionFeatures,CreditsAddons,SubscriptionPricingPrices,CreditAddonPrice)
import json
from drf_writable_nested import WritableNestedModelSerializer

class ServiceTypesSerializer(serializers.ModelSerializer):

    class Meta:
        model = ServiceTypes
        fields = ( 'id', 'name', 'is_active','created_at','updated_at')
        read_only_fields = ('id','created_at','updated_at')

    def create(self, validated_data):
        ServiceType = ServiceTypes.objects.create(**validated_data)
        return ServiceType



class CurrenciesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Currencies

        fields = ( 'id', 'currency','currency_code','is_active','created_at','updated_at')
        read_only_fields = ('id','created_at','updated_at')

    def create(self, validated_data):
        request = self.context['request']
        Currency = Currencies.objects.create(**validated_data)
        return Currency



class CountriesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Countries

        fields = ( 'id','sortname', 'name','phonecode','is_active','created_at','updated_at')
        read_only_fields = ('id','created_at','updated_at')

    def create(self, validated_data):
        request = self.context['request']
        Country = Countries.objects.create(**validated_data)
        return Country

    # def update(self, instance, validated_data):
    #     instance.sortname = validated_data.get('sortname', instance.sortname)
    #     instance.name = validated_data.get('name', instance.name)
    #     instance.phonecode = validated_data.get('phonecode', instance.phonecode)
    #     instance.is_active = validated_data.get('is_active', instance.is_active)
    #     return instance

class SubjectFieldsSerializer(serializers.ModelSerializer):

    class Meta:
        model = SubjectFields

        fields = ( 'id','name','is_active','created_at','updated_at')
        read_only_fields = ('id','created_at','updated_at')

    def create(self, validated_data):
        request = self.context['request']
        subject = SubjectFields.objects.create(**validated_data)
        return subject

class ContentTypesSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContentTypes

        fields = ( 'id', 'name','is_active','created_at','updated_at')
        read_only_fields = ('id','created_at','updated_at')

    def create(self, validated_data):
        request = self.context['request']
        content = ContentTypes.objects.create(**validated_data)
        return content

class MtpeEnginesSerializer(serializers.ModelSerializer):

    class Meta:
        model = MtpeEngines

        fields = ( 'id', 'name','is_active','created_at','updated_at')
        read_only_fields = ('id','created_at','updated_at')

    def create(self, validated_data):
        request = self.context['request']
        engine = MtpeEngines.objects.create(**validated_data)
        return engine

class SupportFilesSerializer(serializers.ModelSerializer):

    class Meta:
        model = SupportFiles

        fields = ( 'id', 'format','is_active','created_at','updated_at')
        read_only_fields = ('id','created_at','updated_at')

    def create(self, validated_data):
        request = self.context['request']
        extension = SupportFiles.objects.create(**validated_data)
        return extension

class TimezonesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Timezones

        fields = ('id', 'timezoneid','name','utc_offset','is_active','created_at','updated_at')
        read_only_fields = ('id','created_at','updated_at')

    def create(self, validated_data):
        request = self.context['request']
        t_zone = Timezones.objects.create(**validated_data)
        return t_zone

class LanguagesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Languages

        fields = ('id', 'language','created_at','updated_at')
        read_only_fields = ('id','created_at','updated_at')

    def create(self, validated_data):
        request = self.context['request']
        lang = Languages.objects.create(**validated_data)
        return lang

class LocaleSerializer(serializers.ModelSerializer):
    # language_detail=LanguagesSerializer(read_only=True)

    class Meta:
        model = LanguagesLocale

        fields = ('id','language_id','language_locale_name','locale_code','is_active','created_at','updated_at')
        read_only_fields = ('id','created_at','updated_at')
        # extra_kwargs = {
        #     'language_id': {'write_only': True},
        #     #'language': {'read_only': True}
        #     }

    def create(self, validated_data):
        request = self.context['request']
        print(request.data.get("language_id"))
        print("validated DAT>>>",validated_data)
        lang = LanguagesLocale.objects.create(**validated_data,language_id=request.data.get("language_id"))
        return lang

class BillingunitsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Billingunits

        fields = ( 'id', 'unit','is_active','created_at','updated_at')
        read_only_fields = ('id','created_at','updated_at')

    def create(self, validated_data):
        request = self.context['request']
        unit = Billingunits.objects.create(**validated_data)
        return unit

class ServiceTypeUnitsSerializer(serializers.ModelSerializer):

    class Meta:
        model = ServiceTypeunits

        fields = ( 'id', 'unit','is_active','created_at','updated_at')
        read_only_fields = ('id','created_at','updated_at')

class SupportTypeSerializer(serializers.ModelSerializer):

        class Meta:
            model = SupportType
            fields = ('id', 'support_type','created_at','updated_at')
            read_only_fields = ('id','created_at','updated_at')

class AiUserTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = AiUserType

        fields = "__all__"
        read_only_fields = ('id','created_at','updated_at')

class AiSupportedMtpeEnginesSerializer(serializers.ModelSerializer):
    project = serializers.IntegerField(required=False, source="project_id")
    class Meta:
        model = AilaysaSupportedMtpeEngines
        fields = ("id","name",'created_at','updated_at')
        read_only_fields = ('id','created_at','updated_at')

class SubscriptionPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPricing
        fields = ('id','stripe_product_id',)


class SubscriptionPricingPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPricingPrices
        fields = ('id','subscriptionplan','monthly_price','montly_price_id','annual_price','annual_price_id','currency',)
        extra_kwargs = {
        "subscriptionplan": {"write_only": True}
        }


class SubscriptionFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionFeatures
        fields = ('id','features','subscriptionplan','description')
        extra_kwargs = {
		 	"subscriptionplan": {"write_only": True}
            }


class CreditAddonPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditAddonPrice
        fields = ('id','pack','price','currency','stripe_price_id',)

class CreditsAddonSerializer(serializers.ModelSerializer):
    addon_price = CreditAddonPriceSerializer(many=True,read_only=True,source='credit_addon_price')
    class Meta:
        model = CreditsAddons
        fields = ('id','pack','credits','description','discount','stripe_product_id','addon_price')



class SubscriptionPricingPageSerializer(serializers.Serializer):
    #subscriptionplan=SubscriptionPricingSerializer(read_only=True,many=True)
    id = serializers.IntegerField()
    plan = serializers.CharField(max_length=200)
    stripe_product_id = serializers.CharField(max_length=200)
    subscription_price=SubscriptionPricingPriceSerializer(many=True,read_only=True)
    subscription_feature=SubscriptionFeatureSerializer(many=True,read_only=True)
    # class Meta:
    #     fields = ('subscriptionplan','prices','features')



class IndianStatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndianStates
        fields = ("id","state_name",'state_code','tin_num','created_at','updated_at')
        read_only_fields = ('id','created_at','updated_at')



class StripeTaxIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = StripeTaxId
        fields = ("id","tax_code",'name','country','created_at','updated_at')
        read_only_fields = ('id','created_at','updated_at')