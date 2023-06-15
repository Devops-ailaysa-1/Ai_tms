from django.db.models.fields import IntegerField
from rest_framework import serializers
from .models import (AilaysaSupportedMtpeEngines, ContentTypes, Countries, IndianStates,
                    Languages, LanguagesLocale, MtpeEngines, ServiceTypes,Currencies, StripeTaxId,
                    SubjectFields, SupportFiles, Timezones,Billingunits,
                    AiUserType,ServiceTypeunits,SupportType,SubscriptionPricing,
                    SubscriptionFeatures,CreditsAddons,SubscriptionPricingPrices,
                    CreditAddonPrice,SupportTopics,JobPositions,Role,MTLanguageSupport,
                    ProjectTypeDetail,ProjectType , PromptCategories ,PromptSubCategories ,
                    PromptStartPhrases,PromptTones,AiCustomize,PromptFields,FontLanguage,FontFamily,FontData,SocialMediaSize,ImageGeneratorResolution,DesignShape)
import json
from itertools import groupby
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
    locale_code = serializers.SerializerMethodField()

    class Meta:
        model = Languages

        fields = ('id', 'language','locale_code','created_at','updated_at')
        read_only_fields = ('id','created_at','updated_at')

    def get_locale_code(self,obj):
        return obj.locale.first().locale_code

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

# class AiSupportedMtpeEnginesSerializer(serializers.ModelSerializer):
#     project = serializers.IntegerField(required=False, source="project_id")
#     class Meta:
#         model = AilaysaSupportedMtpeEngines
#         fields = ("id","name",'created_at','updated_at')
#         read_only_fields = ('id','created_at','updated_at')

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

# class subscriptionPricingGroup(serializers.ModelSerializer):
#     events = serializers.SerializerMethodField(method_name='get_events')
#     class Meta:


class SubscriptionFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionFeatures
        fields = ('id','features','subscriptionplan','description','set_id','sequence_id')
        extra_kwargs = {
		 	"subscriptionplan": {"write_only": True},
            'set_id':{'write_only': True},
            'sequence_id':{'write_only': True},

            }

    # def to_representation(self, value):
    #     data = super().to_representation(value)
    #     user_type_serializer = AiUserTypeSerializer(value.user_type)
    #     data['user_type'] = user_type_serializer.data
    #     return data


class CreditAddonPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditAddonPrice
        fields = ('id','pack','price','currency','stripe_price_id',)

class CreditsAddonSerializer(serializers.ModelSerializer):
    addon_price = CreditAddonPriceSerializer(many=True,read_only=True,source='credit_addon_price')
    class Meta:
        model = CreditsAddons
        fields = ('id','pack','credits','description','expiry','discount','stripe_product_id','addon_price')



class  SubscriptionPricingPageSerializer(serializers.Serializer):
    #subscriptionplan=SubscriptionPricingSerializer(read_only=True,many=True)
    id = serializers.IntegerField()
    plan = serializers.CharField(max_length=200)
    stripe_product_id = serializers.CharField(max_length=200)
    subscription_price=SubscriptionPricingPriceSerializer(many=True,read_only=True)
    subscription_feature = serializers.SerializerMethodField()

    def get_subscription_feature(self, obj):
        features = obj.subscription_feature.all().order_by('sequence_id')
        print('features',features)
        features_grouped_by_set = groupby(features.iterator(), lambda m: m.set_id)
        dict_val = {}
        print("dict_value",dict_val)
        for set_id, group_of_features in features_grouped_by_set:
            dict_key = 'set_'+str(set_id)
            print("dict_key",dict_key)
            #dict_val[dict_key] = SubscriptionFeatureSerializer(group_of_features,many=True).data
            dict_val.setdefault(dict_key,[]).extend(SubscriptionFeatureSerializer(group_of_features,many=True).data)
        #print("final==",dict_val)
        return dict_val



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


class SupportTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTopics
        fields = "__all__"

class JobPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPositions
        fields = "__all__"

class TeamRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = "__all__"


class MTLanguageSupportSerializer(serializers.ModelSerializer):
    class Meta:
        model = MTLanguageSupport
        fields = "__all__"


class GetLanguagesSerializer(serializers.Serializer):
    language = serializers.ReadOnlyField(source = 'language.language')
    language_id = serializers.ReadOnlyField(source = 'language.id')


class AiSupportedMtpeEnginesSerializer(serializers.ModelSerializer):
    # project = serializers.IntegerField(required=False, source="project_id")Edited
    class Meta:
        model = AilaysaSupportedMtpeEngines
        fields = ("id","name",'created_at','updated_at')
        read_only_fields = ('id','created_at','updated_at')


class ProjectTypeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectTypeDetail
        fields = "__all__"

class ProjectTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectType
        fields = "__all__"



class LanguagesSerializerNew(serializers.ModelSerializer):
    locale_code = serializers.SerializerMethodField()

    class Meta:
        model = Languages
        fields = ('id', 'language','locale_code')

    def get_locale_code(self,obj):
        return obj.locale.first().locale_code


class PromptStartPhrasesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptStartPhrases
        fields = '__all__'

class PromptFieldsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptFields
        fields = '__all__'

class PromptSubCategoriesSerializer(serializers.ModelSerializer):
    sub_category_fields = PromptFieldsSerializer(many=True)
    class Meta:
        model = PromptSubCategories
        fields = ('id','category','sub_category','sub_category_fields',)

class PromptCategoriesSerializer(serializers.ModelSerializer):
    prompt_category = PromptSubCategoriesSerializer(many=True )
    class Meta:
        model = PromptCategories
        fields = ('id','category','prompt_category',)
        
        
class PromptTonesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptTones
        fields = ('id','tone')
    
class AiCustomizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiCustomize
        fields = ('id' , 'customize',)

class AiCustomizeGroupingSerializer(serializers.ModelSerializer):
    results = serializers.SerializerMethodField()

    class Meta:
        model = AiCustomize
        fields = ('results',)

    def get_results(self,obj):
        result_dict ={}
        #queryset = AiCustomize.objects.all().distinct('grouping')
        results =['Edit','Explore','Convert']
        for i in results:
            rr = AiCustomize.objects.filter(grouping=i).exclude(customize='Text completion').order_by('id')
            result_dict[i] = AiCustomizeSerializer(rr,many=True).data
        return result_dict
        

class FontLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model =  FontLanguage
        fields = ("id",'name')


class FontLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model =  FontLanguage
        fields = ("id",'name')

class FontFamilySerializer(serializers.ModelSerializer):
    is_custom=serializers.SerializerMethodField()
    class Meta:
        model = FontFamily
        fields = ('font_family_name','is_custom')
    
    
    def get_is_custom(self,instance):
        if type(instance) is FontFamily or type(instance) is FontData:
            return False
        else:
            return True
    
class FontDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FontData
        fields = ('id','font_family')#,'font_data_family' )
        depth = 1


class SocialMediaSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model=SocialMediaSize
        fields='__all__'

    def to_representation(self, instance):
        data=super().to_representation(instance)
        if 'src' in data.keys() and instance.src:
            if instance.src:
                data['src'] = instance.src.url
        return data

    def create(self, validated_data):
        instance= SocialMediaSize.objects.create(**validated_data)
        return instance
    
    def update(self, instance, validated_data):
        src=validated_data.get('src',None)
        if src:
            instance.src = src
        instance.social_media_name=validated_data.get('social_media_name',instance.social_media_name)
        instance.width=validated_data.get('width',instance.width)
        instance.height=validated_data.get('height',instance.height)
        instance.save()
        return instance

class ImageGeneratorResolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model=ImageGeneratorResolution
        fields=('id','image_resolution')



class DesignShapeSerializer(serializers.ModelSerializer):
    class Meta:
        model=DesignShape
        fields='__all__'