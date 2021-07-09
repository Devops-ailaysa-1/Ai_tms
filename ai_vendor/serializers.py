from rest_framework import serializers
from .models import VendorsInfo,VendorLanguagePair,VendorServiceTypes,VendorServiceInfo,TranslationSamples,MtpeSamples


class VendorsInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = VendorsInfo
        fields = (
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


    def save(self, user_id):
        user = VendorsInfo.objects.create(**self.validated_data, user_id=user_id)
        return user

    def save_update(self):
        return super().save()



class VendorLanguagePairSerializers(serializers.ModelSerializer):
     class Meta:
        model = VendorLanguagePair

class VendorServiceTypeSerializer(serializers.ModelSerializer):
    class Meta:
       model = VendorServiceTypes

class TranslationSamplesSerializer(serializers.ModelSerializer):
    class Meta:
        model=TranslationSamples

class MtpeSamplesSerializer(serializers.ModelSerializer):
    class Meta:
        model=MtpeSamples

class VendorServiceInfoSerializers(serializers.ModelSerializer):
    class Meta:
       model = VendorServiceInfo
