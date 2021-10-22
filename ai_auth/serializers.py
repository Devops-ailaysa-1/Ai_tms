from django.db.models import query
from ai_auth.forms import SendInviteForm
from django.core.validators import FileExtensionValidator
from ai_staff.models import AiUserType, Countries, SubjectFields, Timezones,SupportType
from rest_framework import serializers, status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from ai_auth.models import (AiUser, BillingAddress,UserAttribute,
                            Professionalidentity,UserProfile,CustomerSupport,ContactPricing,
                            TempPricingPreference, UserTaxInfo,AiUserProfile,CarrierSupport,VendorOnboarding,GeneralSupport)
from rest_framework import status
from ai_staff.serializer import AiUserTypeSerializer
from dj_rest_auth.serializers import PasswordResetSerializer,PasswordChangeSerializer
from django.contrib.auth import get_user_model
from django.conf import settings
from allauth.account.signals import password_changed
UserModel = get_user_model()
from .validators import file_size
import django.contrib.auth.password_validation as validators
from django.core import exceptions
from ai_auth.signals import update_billing_address2

class UserRegistrationSerializer(serializers.ModelSerializer):
    # email=serializers.EmailField()
    # fullname= serializers.CharField(required=True)
    # password = serializers.CharField(style={'input_type':'password'}, write_only=True,required= True)

    class Meta:
        model = AiUser
        fields = ['email','fullname','password','country']
        extra_kwargs = {
            'password': {'write_only':True}
        }

    def run_validation(self,data):
        password = data['password']
        try:
            validators.validate_password(password=password)
        except exceptions.ValidationError as e:
            print("Errors---->",list(e))
            raise serializers.ValidationError({"error":list(e)})
        return super().run_validation(data)


    def save(self, request):
        user = AiUser(
            email=self.validated_data['email'],
            fullname=self.validated_data['fullname'],
            country = self.validated_data['country']

        )

        password = self.validated_data['password']
       # password2 = self.validated_data['password2']

        # if password != password2:
        #     raise serializers.ValidationError({'password':'Passwords must match.'})
        user.set_password(password)
        user.save()
        UserAttribute.objects.create(user=user)
        return user


class AiPasswordResetSerializer(PasswordResetSerializer):

    password_reset_form_class = SendInviteForm


class AiPasswordChangeSerializer(PasswordChangeSerializer):
       def save(self):
        self.set_password_form.save()
        password_changed.send(
            sender=self.request.user.__class__,
            request=self.request,
            user=self.request.user,
        )
        if not self.logout_on_password_change:
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(self.request, self.user)






# class MyTokenObtainPairSerializer(TokenObtainPairSerializer):

#     @classmethod
#     def get_token(cls, user):
#         token = super(MyTokenObtainPairSerializer, cls).get_token(user)

#         # Add custom claims
#         token['username'] = user.email
#         return token



# class RegisterSerializer(serializers.ModelSerializer):
#     email = serializers.EmailField(
#             required=True,
#             validators=[UniqueValidator(queryset=AiUser.objects.all())]
#             )

#     password = serializers.CharField(write_only=True, required=True)

#     class Meta:
#         model = AiUser
#         fields = ('password', 'email', 'fullname')
#         extra_kwargs = {
#             'fullname': {'required': True}
#         }


#     def create(self, validated_data):

#         user = AiUser.objects.create(
#             email=validated_data['email'],
#             fullname=validated_data['fullname'],
#         )


#         user.set_password(validated_data['password'])
#         user.save()

#         return user



class UserAttributeSerializer(serializers.ModelSerializer):
    user_type = serializers.PrimaryKeyRelatedField(queryset=AiUserType.objects.all(),many=False,required=False)

    class Meta:
        model = UserAttribute
        fields = ( 'user_type',)
        #read_only_fields = ('id',)
        depth = 2

    def create(self, validated_data):
        print("validated data",validated_data)
        request = self.context['request']
        user_attr = UserAttribute.objects.create(user_id=request.user.id,**validated_data)
        return user_attr


    def to_representation(self, value):
        data = super().to_representation(value)
        user_type_serializer = AiUserTypeSerializer(value.user_type)
        data['user_type'] = user_type_serializer.data
        return data

# class PersonalInformationSerializer(serializers.ModelSerializer):
#    # country = serializers.PrimaryKeyRelatedField(queryset=Countries.objects.all(),many=False,required=False)
#     timezone = serializers.PrimaryKeyRelatedField(queryset=Timezones.objects.all(),many=False,required=False)

#     class Meta:
#         model = PersonalInformation
#         fields = ( 'timezone','mobilenumber','phonenumber','linkedin','created_at','updated_at')
#         read_only_fields = ('created_at','updated_at')

#     def create(self, validated_data):
#         print("validated==>",validated_data)
#         request = self.context['request']
#         personal_info = PersonalInformation.objects.create(**validated_data,user_id=request.user.id)
#         return  personal_info

# class OfficialInformationSerializer(serializers.ModelSerializer):
#     #country = serializers.PrimaryKeyRelatedField(queryset=Countries.objects.all(),many=False,required=False)
#     timezone = serializers.PrimaryKeyRelatedField(queryset=Timezones.objects.all(),many=False,required=False)
#     industry = serializers.PrimaryKeyRelatedField(queryset=SubjectFields.objects.all(),many=False,required=False)
#     class Meta:
#         model = OfficialInformation
#         fields = ( 'id','company_name','designation','industry','timezone','website','linkedin','billing_email','created_at','updated_at')
#         read_only_fields = ('id','created_at','updated_at')

#     def create(self, validated_data):
#         request = self.context['request']
#         official_info = OfficialInformation.objects.create(**validated_data,user_id=request.user.id)
#         return official_info



class ProfessionalidentitySerializer(serializers.ModelSerializer):

    class Meta:
        model = Professionalidentity
        fields = ( 'id','avatar','logo','header')
        #read_only_fields = ('id','created_at','updated_at')


    def create(self, validated_data):
        request = self.context['request']
        print("validated data ",validated_data)
        identity = Professionalidentity.objects.create(**validated_data,user=request.user)
        return identity

    # def save(self, *args, **kwargs):
    #     if self.instance.avatar:
    #         self.instance.avatar.delete()
    #     return super().save(*args, **kwargs)


class AiUserDetailsSerializer(serializers.ModelSerializer):
    """
    User model w/o password
    """
    @staticmethod
    def validate_username(username):
        if 'allauth.account' not in settings.INSTALLED_APPS:
            # We don't need to call the all-auth
            # username validator unless its installed
            return username
        from allauth.account.adapter import get_adapter
        username = get_adapter().clean_username(username)
        return username
    class Meta:
        extra_fields = []
        # see https://github.com/iMerica/dj-rest-auth/issues/181
        # UserModel.XYZ causing attribute error while importing other
        # classes from `serializers.py`. So, we need to check whether the auth model has
        # the attribute or not
        if hasattr(UserModel, 'USERNAME_FIELD'):
            extra_fields.append(UserModel.USERNAME_FIELD)
        if hasattr(UserModel, 'EMAIL_FIELD'):
            extra_fields.append(UserModel.EMAIL_FIELD)
        if hasattr(UserModel, 'first_name'):
            extra_fields.append('first_name')
        if hasattr(UserModel, 'last_name'):
            extra_fields.append('last_name')
        if hasattr(UserModel, 'last_name'):
            extra_fields.append('last_name')
        if hasattr(UserModel, 'fullname'):
            extra_fields.append('fullname')
        if hasattr(UserModel, 'country'):
            extra_fields.append('country')
        model = UserModel
        fields = ('pk','is_active', *extra_fields)
        read_only_fields = ('email',)



class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = "__all__"


class CustomerSupportSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerSupport
        fields  = "__all__"


class ContactPricingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactPricing
        fields = "__all__"

class TempPricingPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempPricingPreference
        fields = "__all__"

class BillingAddressSerializer(serializers.ModelSerializer):
   # user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    class Meta:
        model = BillingAddress
        #fields  = "__all__"
        #read_only_fields = ('id','created_at','updated_at')
        exclude = ['user']


    def save(self,*args,**kwargs):
        print(self.context.get('request'))
        context_ = self.context.get('request')
        response=super().save(*args,**kwargs)
        update_billing_address2.send(
            sender=context_.user.__class__,
            request=context_,
            user=context_.user,
            instance=response
        )

class UserTaxInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTaxInfo
        #fields  = "__all__"
        exclude = ['user']

# class UserAppPreferenceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = UserAppPreference
#         fields  = "__all__"

class BillingInfoSerializer(serializers.Serializer):
    #subscriptionplan=SubscriptionPricingSerializer(read_only=True,many=True)
    id = serializers.IntegerField()
    #fullname = serializers.CharField(max_length=200)
    address = BillingAddressSerializer(read_only=True,source='billing_addr_user')
    tax = UserTaxInfoSerializer(many=True,read_only=True,source='tax_info_user')
    class Meta:
        fields = ('id','tax','address')



class AiUserProfileSerializer(serializers.ModelSerializer):
    fullname = serializers.CharField(required=False)
    class Meta:
        model = AiUserProfile
        fields = ('id','user_id','fullname','organisation_name','timezone','phonenumber','linkedin','website',)

    def create(self, validated_data):
        request = self.context['request']
        if "fullname" in validated_data:
            fullname = validated_data.pop('fullname')
            print(fullname)
            user = AiUser.objects.get(id=request.user.id)
            user.fullname = fullname
            user.save()
        profile = AiUserProfile.objects.create(**validated_data,user=request.user)
        return profile

    def update(self, instance, validated_data):
        print(validated_data)
        if "fullname" in validated_data:
            res = super().update(instance, validated_data)
            user = AiUser.objects.get(id=instance.user.id)
            user.fullname = instance.fullname
            user.save()
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        print(instance)
        data["fullname"] = instance.user.fullname
        return data

class CarrierSupportSerializer(serializers.ModelSerializer):
    cv_file = serializers.FileField(validators=[file_size,FileExtensionValidator(allowed_extensions=['txt','pdf','docx'])])
    class Meta:
        model = CarrierSupport
        fields  = "__all__"

class VendorOnboardingSerializer(serializers.ModelSerializer):
    cv_file = serializers.FileField(validators=[file_size,FileExtensionValidator(allowed_extensions=['txt','pdf','docx'])])
    class Meta:
        model = VendorOnboarding
        fields  = "__all__"

class GeneralSupportSerializer(serializers.ModelSerializer):
    support_file = serializers.FileField(allow_null=True,validators=[file_size,FileExtensionValidator(allowed_extensions=['txt','pdf','docx','jpg','png'])])
    class Meta:
        model = GeneralSupport
        fields = "__all__"
