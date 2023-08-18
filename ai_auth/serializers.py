from django.db.models import query
from ai_auth.forms import SendInviteForm
from django.core.validators import FileExtensionValidator
from ai_staff.models import AiUserType, Countries, SubjectFields, Timezones,SupportType,IndianStates
from rest_framework import serializers, status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from ai_auth.models import (AiUser, AilaysaCampaigns, BillingAddress,UserAttribute,
                            Professionalidentity,UserProfile,CustomerSupport,ContactPricing,
                            TempPricingPreference, UserTaxInfo,AiUserProfile,CarrierSupport,
                            VendorOnboarding,GeneralSupport,Team,HiredEditors,InternalMember,
                            CampaignUsers,CoCreateForm,CoCreateFiles)
from rest_framework import status
from ai_staff.serializer import AiUserTypeSerializer,TeamRoleSerializer,Languages
from dj_rest_auth.serializers import PasswordResetSerializer,PasswordChangeSerializer,LoginSerializer
from django.contrib.auth import get_user_model
from django.conf import settings
from allauth.account.signals import password_changed
UserModel = get_user_model()
from .validators import file_size
import logging
from rest_framework.validators import UniqueValidator
from ai_auth.utils import create_user
from ai_auth.forms import campaign_user_invite_email

logger = logging.getLogger('django')
try:
    from django.utils.translation import gettext_lazy as _
except ImportError:
    from django.utils.translation import gettext_lazy as _
import django.contrib.auth.password_validation as validators
from django.core import exceptions
from ai_auth.signals import update_billing_address2
from allauth.socialaccount.models import SocialAccount

def is_campaign_exist(value):
    try:
        AilaysaCampaigns.objects.get(campaign_name=value)
    except AilaysaCampaigns.DoesNotExist:
        raise serializers.ValidationError('Invalid Input')

# def subscribe_campaign_users(campaign,user):
#     CampaignUsers.objects.create(user=user,campaign_name=campaign)
#     pass

class UserRegistrationSerializer(serializers.ModelSerializer):
    # email=serializers.EmailField()
    # fullname= serializers.CharField(required=True)
    # password = serializers.CharField(style={'input_type':'password'}, write_only=True,required= True)
    campaign = serializers.CharField(required=False,validators=[is_campaign_exist])
    source_language = serializers.PrimaryKeyRelatedField(queryset=Languages.objects.all(),many=False,required=False)
    target_language = serializers.PrimaryKeyRelatedField(queryset=Languages.objects.all(),many=False,required=False)
    cv_file = serializers.FileField(required=False,validators=[file_size,FileExtensionValidator(allowed_extensions=['txt','pdf','docx'])])
    is_agency = serializers.CharField(required=False,allow_null=True)

    class Meta:
        model = AiUser
        fields = ['email','fullname','password','country','campaign','source_language','target_language','cv_file','is_agency']
        extra_kwargs = {
            'password': {'write_only':True},
            'campaign': {'write_only':True}
        }

    def run_validation(self,data):
        password = data['password']
        try:
            validators.validate_password(password=password)
        except exceptions.ValidationError as e:
            print("Errors---->",list(e))
            raise serializers.ValidationError({"error":list(e)})
        return super().run_validation(data)

    def vendor_signup():
        pass


    def save(self, request):
        from ai_vendor.models import VendorLanguagePair,VendorOnboardingInfo,VendorsInfo
        from ai_auth.api_views import subscribe_vendor,check_campaign,subscribe_lsp
        user = AiUser(
            email=self.validated_data['email'],
            fullname=self.validated_data['fullname'],
            country = self.validated_data['country']

        )

        password = self.validated_data['password']
        print("valid",self.validated_data)
       # password2 = self.validated_data['password2']

        # if password != password2:
        #     raise serializers.ValidationError({'password':'Passwords must match.'})
        user.set_password(password)
        user.save()
        UserAttribute.objects.create(user=user)
        campaign = self.validated_data.get('campaign',None)
        source_language = self.validated_data.get('source_language',None)
        target_language = self.validated_data.get('target_language',None)
        cv_file = self.validated_data.get('cv_file',None)
        is_agency = self.validated_data.get('is_agency',None)

        print("Agency----->",is_agency)

        if 'is_agency' in self.validated_data:
            if is_agency == 'True':
                sub = subscribe_lsp(user)
                user.is_agency = True
            elif is_agency == 'False':
                sub = subscribe_vendor(user)
            user.is_vendor = True
            user.save() 
            VendorOnboardingInfo.objects.create(user=user,onboarded_as_vendor=True)

        # if source_language and target_language:
        #     VendorLanguagePair.objects.create(user=user,source_lang = source_language,target_lang=target_language,primary_pair=True)
        #     user.is_vendor = True
        #     user.save()
        #     if is_agency:    
        #         sub = subscribe_lsp(user)
        #         user.is_agency = True
        #         user.save()
        #     else:
        #         sub = subscribe_vendor(user)
        #     if not cv_file:
        #         VendorOnboardingInfo.objects.create(user=user,onboarded_as_vendor=True)
        #     else:
        #         VendorsInfo.objects.create(user=user,cv_file = cv_file)
        #         VendorOnboardingInfo.objects.create(user=user,onboarded_as_vendor=True)
        #         VendorOnboarding.objects.create(name=user.fullname,email=user.email,cv_file=cv_file,status=1)
            
        if campaign:
            ## users from campaign pages
            #AilaysaCampaigns.objects.get(campaign_name=campaign)
            print("campaign",campaign)
            ai_camp = AilaysaCampaigns.objects.get(campaign_name=campaign)
            CampaignUsers.objects.create(user=user,campaign_name=ai_camp)
            if user.is_vendor:
                if check_campaign(user):
                    pass
                else:
                    logger.error("campaign updation failed",user.uid)

        return user

    # def create(self, validated_data):
    #     pass


class AiPasswordResetSerializer(PasswordResetSerializer):

    password_reset_form_class = SendInviteForm

class AiLoginSerializer(LoginSerializer):
    def validate(self, attrs):
        # username = attrs.get('username')
        # email = attrs.get('email')
        # password = attrs.get('password')
        # user = self.get_auth_user(username, email, password)

        # if user:
        #     if user.deactivate == True:
        #         msg = _('User is deactivated.')
        #         raise exceptions.ValidationError(msg)

        # if not user:
        #     msg = _('Unable to log in with provided credentials.')
        #     raise exceptions.ValidationError(msg)

        # # Did we get back an active user?
        # self.validate_auth_user_status(user)

        # # If required, is the email verified?
        # if 'dj_rest_auth.registration' in settings.INSTALLED_APPS:
        #     self.validate_email_verification_status(user)

        # attrs['user'] = user
        attrs = super().validate(attrs)
        user = attrs['user']
        if user:
            if user.last_login==None:
                user.first_login = True
            elif user.first_login==True:
                user.first_login=False
            user.save()

        return attrs

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
        fields = "__all__"
        # fields = ( 'id','avatar','logo','header')
        #read_only_fields = ('id','created_at','updated_at')


    # def create(self, validated_data):
    #     request = self.context['request']
    #     print("validated data ",validated_data)
    #     identity = Professionalidentity.objects.create(**validated_data,user=request.user)
    #     return identity

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

    is_social = serializers.SerializerMethodField(source="get_is_social",read_only=True)
    is_campaign =  serializers.SerializerMethodField(source="get_is_campaign",read_only=True)
    
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
        fields = ('pk','deactivate','is_internal_member','internal_member_team_detail','is_vendor', 'agency','first_login','is_social','is_campaign',*extra_fields)
        read_only_fields = ('email',)

    def get_is_social(self,obj):
        if SocialAccount.objects.filter(user=obj).count()!=0:
            return True
        else :
            return False
    
    def get_is_campaign(self,obj):
        if CampaignUsers.objects.filter(user=obj).count()!=0:
            return True
        else :
            return False

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
    # country = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    class Meta:
        model = BillingAddress
        #fields  = "__all__"
        #read_only_fields = ('id','created_at','updated_at')
        exclude = ['user']


    def validate(self, data):
        print("validated data",data)
        print("request context ",self.context.get('request').method)

        if self.context.get('request').method == 'POST':
            if data.get('line1',None) == '' or data.get('line1',None) == None:
                raise serializers.ValidationError("address line 1 required")
            
            if data.get('line2',None) == '' or data.get('line2',None) == None:
                raise serializers.ValidationError("address line 2 required")

            # if data['city'] == None:
            #     raise serializers.ValidationError("address city required")
            
            if data['country'].id == 101:
                try:
                    IndianStates.objects.get(state_name=data['state'])              
                except:
                    raise serializers.ValidationError("state not found")
        return data



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
    current_status = serializers.ReadOnlyField(source='get_status_display')
    cv_file = serializers.FileField(validators=[file_size,FileExtensionValidator(allowed_extensions=['txt','pdf','docx'])])
    class Meta:
        model = VendorOnboarding
        fields  = ('id','name','email','cv_file','message','status','current_status',)
        extra_kwargs = {
            'status':{'write_only':True},
            }

class GeneralSupportSerializer(serializers.ModelSerializer):
    support_file = serializers.FileField(allow_null=True,validators=[file_size,FileExtensionValidator(allowed_extensions=['txt','pdf','docx','jpg','png','jpeg'])])
    class Meta:
        model = GeneralSupport
        fields = "__all__"


class CoCreateFilesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoCreateFiles
        fields = "__all__"



class CoCreateFormSerializer(serializers.ModelSerializer):
    cocreate_file = CoCreateFilesSerializer(many=True,required=False)
    #app_suggestion_file = serializers.FileField(allow_null=True,validators=[file_size,FileExtensionValidator(allowed_extensions=['txt','pdf','docx','jpg','png','jpeg'])])
    class Meta:
        model = CoCreateForm
        fields = ('id','name','email','suggestion_type','suggestion','description','cocreate_file','created_at','updated_at')


    def run_validation(self, data):
        if data.get('cocreate_file'):
           data['cocreate_file'] = [{'app_suggestion_file':file} for file in data['cocreate_file']]
        return super().run_validation(data)

    def create(self,data):
        files = data.pop("cocreate_file",[])
        ins = CoCreateForm.objects.create(**data)
        if files:
            tt = [CoCreateFiles.objects.create(**sug_file,co_create = ins ) for sug_file in files]
        return ins

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = "__all__"

class InternalMemberSerializer(serializers.ModelSerializer):
    internal_member_detail = serializers.SerializerMethodField(source='get_internal_member_detail')
    team_name = serializers.ReadOnlyField(source='team.name')
    current_status = serializers.ReadOnlyField(source='get_status_display')
    professional_identity= serializers.ReadOnlyField(source='internal_member.professional_identity_info.avatar_url')
    class Meta:
        model = InternalMember
        fields = ('id','team','team_name','added_by','role','functional_identity','professional_identity',
                'status','current_status','internal_member','internal_member_detail',)
        extra_kwargs = {
            'internal_member':{'write_only':True},
            'added_by':{'write_only':True},
            'status':{'write_only':True},
            }

    def get_internal_member_detail(self, obj):
        return {'name':obj.internal_member.fullname,'email':obj.internal_member.email}


class HiredEditorSerializer(serializers.ModelSerializer):
    hired_editor_detail = serializers.SerializerMethodField(source='get_hired_editor_detail')
    current_status = serializers.ReadOnlyField(source='get_status_display')
    professional_identity= serializers.ReadOnlyField(source='hired_editor.professional_identity_info.avatar_url')
    class Meta:
        model = HiredEditors
        fields = ('id','role','user','professional_identity',\
                'status','current_status','hired_editor','hired_editor_detail','added_by',)
        extra_kwargs = {
            'hired_editor':{'write_only':True},
            'user':{'write_only':True},
            'status':{'write_only':True},
            'added_by':{'write_only':True},
            }
    def get_hired_editor_detail(self, obj):
        return {'name':obj.hired_editor.fullname,'email':obj.hired_editor.email}


class CampaignRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(allow_blank=False)
    campaign = serializers.CharField()

    def create(self, validated_data):
        from ai_auth.api_views import check_campaign
        email = validated_data.get('email')
        campaign = validated_data.get('campaign')
        # print("email-->",email)
        # print("email-->",campaign)
        res = create_user(email=email,country=101)
        if res==None:
            raise ValueError('email already registerd')

        user,password = res
        ai_camp = AilaysaCampaigns.objects.get(campaign_name=campaign)
        if ai_camp.coupon != None:
            coupon = False
        else:
            coupon = None
        CampaignUsers.objects.create(user=user,campaign_name=ai_camp,coupon_used=coupon)
        campaign_user_invite_email(user=user,gen_password=password)
        camp = check_campaign(user)
        return user