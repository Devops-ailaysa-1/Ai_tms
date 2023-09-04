from random import choices
from django.db import models
from django.contrib.auth.models import User
from ai_auth.managers import CustomUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from ai_staff.models import AiUserType, ProjectRoleLevel, StripeTaxId, SubjectFields,Countries,\
                            TaskRoleLevel,Timezones,SupportType,JobPositions,\
                            SupportTopics,Role,Currencies,ApiServiceList,SuggestionType,Suggestion
from django.db.models.signals import post_save, pre_save, pre_delete
from ai_auth.signals import proz_connect, create_allocated_dirs, updated_user_taxid, update_internal_member_status, vendor_status_send_email, get_currency_based_on_country#,vendorsinfo_update
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from ai_auth.utils import get_unique_uid
from djstripe.models import Customer,Subscription,PaymentIntent,Invoice,Price,Product,Charge
from ai_auth import Aiwebhooks
from ai_auth.utils import get_plan_name
# from djstripe import webhooks
from django.db.models import Q
from datetime import datetime,date,timedelta
from django.db.models.constraints import UniqueConstraint
from simple_history.models import HistoricalRecords
from ai_openai.signals import text_gen_credit_deduct
from django.conf import settings
from ai_workspace.signals import invalidate_cache_on_save,invalidate_cache_on_delete
from django.core.exceptions import ValidationError

class AiUser(AbstractBaseUser, PermissionsMixin):####need to migrate and add value for field 'currency_based_on_country' for existing users#####
    uid = models.CharField(max_length=25, null=False, blank=True)
    email = models.EmailField(_('email address'), unique=True)
    fullname=models.CharField(max_length=191)
    country= models.ForeignKey(Countries,related_name='aiuser_country',
        on_delete=models.CASCADE,blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    deactivation_date = models.DateTimeField(null=True,blank=True)
    date_joined = models.DateTimeField(default=timezone.now)
    from_mysql = models.BooleanField(default=False)
    deactivate = models.BooleanField(default=False)
    is_vendor = models.BooleanField(default=False)
    is_agency = models.BooleanField(default=False)
    is_internal_member = models.BooleanField(default=False)
    first_login = models.BooleanField(default=False)
    currency_based_on_country = models.ForeignKey(Currencies,related_name='aiuser_country_based_currency',
        on_delete=models.CASCADE,blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def remove_anonymous_user():
        user = AiUser.objects.filter(email="AnonymousUser").first()
        if user:
            user.delete()

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):

        if not self.uid:
            self.uid = get_unique_uid(AiUser)
        return super().save(*args, **kwargs)


    @property
    def agency(self):
        if self.is_agency == True:
            return True
        else:
            if self.team and self.team.owner.is_agency == True and self in self.team.get_project_manager:
                return True
            else:
                return False               


    @property
    def internal_member_team_detail(self):
        if self.is_internal_member == True:
            obj = InternalMember.objects.get(internal_member_id = self.id)
            # return {'team_name':obj.team.name,'team_id':obj.team.id,"role":obj.role.name}
            plan = get_plan_name(obj.team.owner)
            if plan in settings.TEAM_PLANS:
                return {'team_name':obj.team.name,'team_id':obj.team.id,"role":obj.role.name,"team_active":"True"}
            else:
                return {'team_name':obj.team.name,'team_id':obj.team.id,"role":obj.role.name,"team_active":"False"}


    @property
    def team(self):
        if self.is_internal_member == True:
            obj = InternalMember.objects.get(internal_member_id = self.id)
            plan = get_plan_name(obj.team.owner)
            return obj.team if plan in settings.TEAM_PLANS else None
        else:
            try:
                team = Team.objects.get(owner_id = self.id)
                plan = get_plan_name(self)
                return team if plan in settings.TEAM_PLANS else None
            except:
                return None

    @property
    def get_hired_editors(self):
        return [i.hired_editor for i in self.user_info.all()]

    @property
    def get_team_members(self):
        if self.team:
            return [i.internal_member for i in self.team.internal_member_team_info.all()]

    @property
    def credit_balance(self):
        # total_credit_left = 0
        addons = subscription = subscription_total= addon_buyed_credits= 0
        present = datetime.now()

        try:
            addon_credits = UserCredits.objects.filter(Q(user=self) & Q(credit_pack_type="Addon")).\
                    filter(Q(expiry__isnull=True) | Q(expiry__gte=timezone.now())).order_by('expiry')
            for addon in addon_credits:
                addons += addon.credits_left
                # addon credits doesn't have expiry so we are excluding record with zero credits_left
                if addon.credits_left != 0:
                    # Need to update if addon expiry is added
                    addon_buyed_credits += addon.buyed_credits

        except Exception as e:
            print("NO ADD-ONS AVAILABLE")

        try:
            sub_credits = UserCredits.objects.get(Q(user=self) & Q(credit_pack_type__icontains="Subscription") \
                                                & Q(ended_at=None))
            if present.strftime('%Y-%m-%d %H:%M:%S') <= sub_credits.expiry.strftime('%Y-%m-%d %H:%M:%S'):
                subscription += sub_credits.credits_left

                sub_buyed_credits = sub_credits.buyed_credits
                if sub_credits.carried_credits ==None:
                    carryed_credits = abs(sub_buyed_credits - subscription)
                    sub_credits.carried_credits=carryed_credits
                    sub_credits.save()
                sub_carryed_credits = sub_credits.carried_credits
                subscription_total = sub_buyed_credits + sub_carryed_credits


            # carry_on_credits = UserCredits.objects.filter(Q(user=self) & Q(credit_pack_type__icontains="Subscription") & \
            #     Q(ended_at__isnull=False)).last()

            # if sub_credits.created_at.strftime('%Y-%m-%d %H:%M:%S') <= carry_on_credits.expiry.strftime('%Y-%m-%d %H:%M:%S'):
            #     total_credit_left += carry_on_credits.credits_left

        except:
            print("No active subscription")
            # return total_credit_left
            return {"addon": addons, "subscription": subscription, "total_left": addons + subscription}

        # return total_credit_left
        return {"addon": addons, "subscription": subscription, "total_left": addons + subscription ,"total_buyed": subscription_total + addon_buyed_credits}

    @property
    def buyed_credits(self):
        addons = subscription = 0
        present = datetime.now()
        try:
            addon_credits = UserCredits.objects.filter(Q(user=self) & Q(credit_pack_type="Addon"))
            for addon in addon_credits:
                addons += addon.buyed_credits
        except Exception as e:
            print("NO ADD-ONS AVAILABLE")
        try:
            #sub_credits = UserCredits.objects.get(Q(user=self) & Q(credit_pack_type__icontains="Subscription") & Q(ended_at=None))
            # if present.strftime('%Y-%m-%d %H:%M:%S') <= sub_credits.expiry.strftime('%Y-%m-%d %H:%M:%S'):
            #     subscription += sub_credits.buyed_credits

            #carry_on_credits = UserCredits.objects.filter(Q(user=self) & Q(credit_pack_type__icontains="Subscription") & \
            #    Q(ended_at__isnull=False)).last()
            carry_credits = UserCredits.objects.filter(Q(user=self) & Q(credit_pack_type__icontains="Subscription")).order_by('-id')
            avai_cp= 0
            for credits in carry_credits:
                if credits.ended_at == None:
                    enddate = credits.expiry
                    startdate = credits.created_at
                    print("inside if")
                    avai_cp = credits.buyed_credits
                else:
                    print("else")
                    if startdate.strftime('%Y-%m-%d %H:%M:%S') <= credits.expiry.strftime('%Y-%m-%d %H:%M:%S') \
                                    <= enddate.strftime('%Y-%m-%d %H:%M:%S'):
                    # if startdate.strftime('%Y-%m-%d %H:%M:%S') <= credits.expiry.strftime('%Y-%m-%d %H:%M:%S') <= enddate.strftime('%Y-%m-%d %H:%M:%S'):
                        startdate = credits.created_at
                        enddate = credits.expiry
                        print("inside else")
                        avai_cp += credits.buyed_credits


            # if sub_credits.created_at.strftime('%Y-%m-%d %H:%M:%S') <= carry_on_credits.expiry.strftime('%Y-%m-%d %H:%M:%S'):
            #     subscription += carry_on_credits.credits_left
        except:
            print("No active subscription")
            return {"addon":addons, "subscription":avai_cp, "total": addons + avai_cp}

        return {"addon":addons, "subscription":avai_cp, "total": addons + avai_cp}

    @property
    def username(self):
        print("username field not available.so it is returning fullname")
        return self.fullname

    @property
    def owner_pk(self):
        return self.id


post_save.connect(update_internal_member_status, sender=AiUser)
post_save.connect(get_currency_based_on_country, sender=AiUser)
post_save.connect(proz_connect, sender=AiUser)



class BaseAddress(models.Model):
    line1 = models.CharField(max_length=200,blank=True, null=True)
    line2 = models.CharField(max_length=200,blank=True, null=True)
    state = models.CharField(max_length=200,blank=True, null=True)
    city = models.CharField(max_length=200,blank=True, null=True)
    zipcode= models.CharField(max_length=200,blank=True, null=True)
    class Meta:
        abstract=True


class UserAttribute(models.Model):
    user = models.OneToOneField(AiUser, on_delete=models.CASCADE,null=True)
    user_type=models.ForeignKey(AiUserType, related_name='user_attribute', on_delete=models.CASCADE,default=1)
    allocated_dir = models.URLField(default=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        managed = True
        db_table='user_attribute'
        permissions = (
                ("user-attribute-exist", "user attribute exist"),
            )

    def save(self, *args, **kwargs):
        content_type = ContentType.objects.get_for_model(UserAttribute)
        try:
            permission = Permission.objects.get(codename="user-attribute-exist",
                                content_type=content_type)
            self.user.user_permissions.add(permission)
        except Exception as e :
            print(e)
        return super().save(*args, **kwargs)

    @property
    def owner_pk(self):
        return self.user.id

pre_save.connect(create_allocated_dirs, sender=UserAttribute)

# class PersonalInformation(models.Model):
#     user = models.OneToOneField(AiUser, on_delete=models.CASCADE,null=True,related_name='personal_info')
#     #address = models.CharField(max_length=255, blank=True, null=True)
#
#     #country= models.ForeignKey(Countries,related_name='personal_info', on_delete=models.CASCADE,blank=True, null=True)
#     timezone=models.ForeignKey(Timezones,related_name='personal_info', on_delete=models.CASCADE,blank=True, null=True)
#     phonenumber=models.CharField(max_length=255, blank=True, null=True)
#     mobilenumber=models.CharField(max_length=255, blank=True, null=True)
#     linkedin=models.CharField(max_length=255, blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
#     updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
#     # created_at = models.CharField(max_length=200,blank=True, null=True)
#     # updated_at = models.CharField(max_length=200,blank=True, null=True)
#     class Meta:
#         managed=False
#         db_table = 'personal_info'


# class OfficialInformation(models.Model):
#     user = models.OneToOneField(AiUser, on_delete=models.CASCADE,null=True,related_name='official_info')
#     company_name = models.CharField(max_length=255, blank=True, null=True)
#    # address = models.CharField(max_length=255, blank=True, null=True)
#     designation = models.CharField(max_length=255, blank=True, null=True)
#     industry=models.ForeignKey(SubjectFields,related_name='official_info', on_delete=models.CASCADE,blank=True, null=True)
#     #country= models.ForeignKey(Countries,related_name='official_info', on_delete=models.CASCADE,blank=True, null=True)
#     timezone=models.ForeignKey(Timezones,related_name='official_info', on_delete=models.CASCADE,blank=True, null=True)
#     website=models.CharField(max_length=255, blank=True, null=True)
#     linkedin=models.CharField(max_length=255, blank=True, null=True)
#     billing_email=models.EmailField(blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
#     updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
#     class Meta:
#         managed=False
#         db_table = 'official_info'


def user_directory_path(instance, filename):

    # file will be uploaded to MEDIA_ROOT / user_<id>/<filename>
    return '{0}/{1}/{2}'.format(instance.user.uid, "profile",filename)

class Professionalidentity(models.Model):
    user = models.OneToOneField(AiUser, on_delete=models.CASCADE,related_name="professional_identity_info")
    avatar=models.ImageField(upload_to=user_directory_path,blank=True,null=True)
    logo=models.ImageField(upload_to=user_directory_path,blank=True,null=True)
    header=models.ImageField(upload_to=user_directory_path,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    class Meta:
        # managed=False
        db_table = 'professional_identity'
#pre_save.connect(create_allocated_dirs, sender=UserAttribute)

    @property
    def avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url

    @property
    def owner_pk(self):
        return self.user.id

class UserProfile(models.Model):
    user = models.OneToOneField(AiUser, on_delete=models.CASCADE)
    description = models.TextField(max_length=1000, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    @property
    def owner_pk(self):
        return self.user.id

class CustomerSupport(models.Model):
    user = models.ForeignKey(AiUser,on_delete=models.CASCADE)
    support_type = models.ForeignKey(SupportType,on_delete=models.CASCADE)
    description = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)

class ContactPricing(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    business_email = models.EmailField()
    country = models.ForeignKey(Countries,on_delete=models.CASCADE,blank=True,null=True)
    description = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)

class TempPricingPreference(models.Model):
    product_id = models.CharField(max_length=200)
    price_id = models.CharField(max_length=200)
    email = models.EmailField()
    is_subscribed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)


class UserCredits(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    stripe_cust_id=  models.ForeignKey(Customer, on_delete=models.CASCADE)
    price_id = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    buyed_credits = models.IntegerField()
    credits_left =models.IntegerField()
    carried_credits =models.IntegerField(blank=True, null=True)
    expiry = models.DateTimeField(blank=True, null=True)
    invoice = models.CharField(max_length=200,blank=True, null=True)
    paymentintent = models.CharField(max_length=200,blank=True, null=True)
    credit_pack_type = models.CharField(max_length=200, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    @property
    def owner_pk(self):
        return self.user.id

post_save.connect(text_gen_credit_deduct, sender=UserCredits)

class CreditPack(models.Model):
    name = models.CharField(max_length=200)
    #product = models.OneToOneField(Product, on_delete=models.CASCADE)
    #price = models.OneToOneField(Price, on_delete=models.CASCADE)
    product =models.ForeignKey(Product,on_delete=models.CASCADE)
    type = models.CharField(max_length=200)
    credits = models.IntegerField(default=0)
    expires_at = models.IntegerField(null=True,blank=True,help_text = "no of months")

class BillingAddress(BaseAddress):
    user = models.OneToOneField(AiUser, on_delete=models.CASCADE,related_name='billing_addr_user')
    name = models.CharField(max_length=255, blank=True, null=True)
    country= models.ForeignKey(Countries,related_name='billing_country', on_delete=models.CASCADE,blank=True, null=True)

    @property
    def owner_pk(self):
        return self.user.id


class UserTaxInfo(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE,related_name='tax_info_user')
    stripe_tax_id = models.ForeignKey(StripeTaxId,on_delete=models.CASCADE,related_name='stripe_taxid_user')
    tax_id = models.CharField(max_length=250)
    #tax_uid= models.CharField(max_length=250)

    @property
    def owner_pk(self):
        return self.user.id

pre_save.connect(updated_user_taxid, sender=UserTaxInfo)

# class UserAppPreference(models.Model):
#     email = models.EmailField()
#     country = models.ForeignKey(Countries,related_name='app_pre_country',on_delete=models.CASCADE)

class AiUserProfile(models.Model):
    user = models.OneToOneField(AiUser, on_delete=models.CASCADE,null=True,related_name='ai_profile_info')
    organisation_name = models.CharField(max_length=255, blank=True, null=True)
    timezone=models.ForeignKey(Timezones,related_name='profile_info', on_delete=models.CASCADE,blank=True, null=True)
    phonenumber=models.CharField(max_length=255, blank=True, null=True)
    linkedin=models.CharField(max_length=255, blank=True, null=True)
    website=models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    # created_at = models.CharField(max_length=200,blank=True, null=True)
    # updated_at = models.CharField(max_length=200,blank=True, null=True)
    class Meta:
        db_table = 'ai_user_profile'

    @property
    def owner_pk(self):
        return self.user.id

def file_path(instance, filename):
    return '{0}/{1}/{2}'.format(instance.email,"cv_file",filename)

class CarrierSupport(models.Model):
    name = models.CharField(max_length=250,blank=True,null=True)
    email = models.EmailField()
    phonenumber = models.CharField(max_length=255, blank=True, null=True)
    job_position = models.ForeignKey(JobPositions,on_delete=models.CASCADE)
    message = models.TextField(max_length=1000)
    cv_file = models.FileField(upload_to=file_path)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

def file_path_vendor(instance, filename):
    user = AiUser.objects.get(email = instance.email)
    return '{0}/{1}/{2}'.format(user.uid,"vendor_cv_file",filename)

class VendorOnboarding(models.Model):
    REQUEST_SENT = 1
    ACCEPTED = 2
    HOLD = 3
    WAITLISTED = 4
    STATUS_CHOICES = [
        (REQUEST_SENT,'Request Sent'),
        (ACCEPTED, 'Accepted'),
        (HOLD, 'Hold'),
        (WAITLISTED, 'Waitlisted'),
    ]
    name = models.CharField(max_length=250)
    email = models.EmailField(_('email address'), unique=True)
    # user = models.OneToOneField(AiUser, on_delete=models.CASCADE)
    cv_file = models.FileField(upload_to=file_path_vendor)
    message = models.TextField(max_length=1000,blank=True, null=True)
    status = models.IntegerField(choices=STATUS_CHOICES)
    # rejected_count = models.IntegerField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

post_save.connect(vendor_status_send_email, sender=VendorOnboarding)
# post_save.connect(vendorsinfo_update, sender=VendorOnboarding)

def support_file_path(instance, filename):
    return '{0}/{1}/{2}'.format(instance.email,"support_file",filename)

class GeneralSupport(models.Model):
    name = models.CharField(max_length=250,blank=True,null=True)
    email = models.EmailField()
    phonenumber = models.CharField(max_length=255, blank=True, null=True)
    topic = models.ForeignKey(SupportTopics,on_delete=models.CASCADE)
    message = models.TextField(max_length=1000)
    support_file = models.FileField(upload_to=support_file_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

def cocreate_file_path(instance, filename):
    return '{0}/{1}/{2}'.format(instance.co_create.email,"app_suggestion_file",filename)


class CoCreateForm(models.Model):
    name = models.CharField(max_length=250,blank=True,null=True)
    email = models.EmailField()
    suggestion_type = models.ForeignKey(SuggestionType,on_delete=models.CASCADE)
    suggestion = models.ForeignKey(Suggestion,on_delete=models.CASCADE)
    description = models.TextField(max_length=5000)
    #app_suggestion_file = models.FileField(upload_to=cocreate_file_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

class CoCreateFiles(models.Model):
    co_create = models.ForeignKey(CoCreateForm,on_delete=models.CASCADE,blank=True, null=True, related_name='cocreate_file')
    app_suggestion_file = models.FileField(upload_to=cocreate_file_path, blank=True, null=True)



class Team(models.Model):
    name = models.CharField(max_length=50)#,unique=True)
    owner = models.OneToOneField(AiUser, on_delete=models.CASCADE,related_name='team_owner')
    description = models.TextField(max_length=1000,blank=True,null=True)

    def __str__(self):
        return self.name

    @property
    def get_project_manager(self):
        return [i.internal_member for i in self.internal_member_team_info.filter(role_id=1)]

    @property
    def get_team_members(self):
        return [i.internal_member for i in self.internal_member_team_info.all()]

    @property
    def owner_pk(self):
        return self.owner.id


class InternalMember(models.Model):
    CRDENTIALS_SENT = 1
    LOGGED_IN = 2
    STATUS_CHOICES = [
        (CRDENTIALS_SENT,'Credentials Sent'),
        (LOGGED_IN, 'Logged In'),
    ]
    team = models.ForeignKey(Team,on_delete=models.CASCADE,related_name='internal_member_team_info')
    internal_member = models.ForeignKey(AiUser, on_delete=models.CASCADE,related_name='internal_member')
    role = models.ForeignKey(Role,on_delete=models.CASCADE,related_name='member_role')
    functional_identity = models.CharField(max_length=255, blank=True, null=True)
    added_by = models.ForeignKey(AiUser,on_delete=models.SET_NULL,related_name='internal_team_manager',blank=True, null=True)
    status = models.IntegerField(choices=STATUS_CHOICES)

    @property
    def owner_pk(self):
        return self.team.owner_pk

    def __str__(self):
        return self.internal_member.email
    
    def generate_cache_keys(self):
        cache_keys = [
            f'check_role_{self.team.owner.id}_*',
        ]
        return cache_keys

post_save.connect(invalidate_cache_on_save, sender=InternalMember)
pre_delete.connect(invalidate_cache_on_delete, sender=InternalMember) 


def default_date_hired_editor_expiry():
    return date.today() + timedelta(days=7)

class HiredEditors(models.Model):
    INVITE_SENT = 1
    INVITE_ACCEPTED = 2
    # INVITE_DECLINED = 3
    STATUS_CHOICES = [
        (INVITE_SENT,'Invite Sent'),
        (INVITE_ACCEPTED, 'Invite Accepted'),
        # (INVITE_DECLINED, 'Invite Declined'),
    ]
    status = models.IntegerField(choices=STATUS_CHOICES)
    user = models.ForeignKey(AiUser,on_delete=models.CASCADE,related_name='user_info')
    hired_editor = models.ForeignKey(AiUser, on_delete=models.CASCADE,related_name='hired_editor')
    date_of_link_sent = models.DateField(blank= True, default=timezone.now)
    date_of_expiry = models.DateField(blank= True, default=default_date_hired_editor_expiry)
    added_by = models.ForeignKey(AiUser,on_delete=models.SET_NULL,related_name='external_team_manager',blank=True, null=True)
    role = models.ForeignKey(Role,on_delete=models.CASCADE)
    class Meta:
        unique_together = ['user', 'hired_editor','role']

    @property
    def owner_pk(self):
        return self.user.id

    def generate_cache_keys(self):
        cache_keys = [
            f'check_role_{self.user.id}_*',
        ]
        return cache_keys

post_save.connect(invalidate_cache_on_save, sender=HiredEditors)
pre_delete.connect(invalidate_cache_on_delete, sender=HiredEditors) 

class ReferredUsers(models.Model):
    email = models.EmailField()

class AilaysaCampaigns(models.Model):
    DURATION =(
    ("month","month"),
    ("year", "year"),
    )
    campaign_name = models.CharField(max_length=100,unique=True)
    subscription_name = models.CharField(max_length=100, blank=True, null=True)
    subscription_duration = models.CharField(choices=DURATION, max_length=100,blank=True, null=True)
    subscription_intervals = models.IntegerField(default=1)
    subscription_credits=models.IntegerField()
    Addon_name = models.CharField(max_length=100, blank=True, null=True)
    Addon_quantity =models.IntegerField(default=1)
    coupon = models.CharField(max_length=60, blank=True, null=True)

    @property
    def owner_pk(self):
        return self.user.id

class CampaignUsers(models.Model):
    user = models.ForeignKey(AiUser,on_delete=models.CASCADE,related_name='user_campaign')
    campaign_name =  models.ForeignKey(AilaysaCampaigns,on_delete=models.CASCADE,related_name='ai_campaigns')
    subscribed = models.BooleanField(default=False)
    coupon_used = models.BooleanField(null=True)

    @property
    def owner_pk(self):
        return self.user.id

class ExistingVendorOnboardingCheck(models.Model):
    user = models.ForeignKey(AiUser,on_delete=models.CASCADE,related_name='existing_vendor_info')
    gen_password = models.CharField(max_length=255)
    mail_sent = models.BooleanField(default=False)
    mail_sent_time = models.DateTimeField(blank=True, null=True)

    @property
    def owner_pk(self):
        return self.user.id

class SocStates(models.Model):
    state = models.CharField(max_length=150,unique=True)
    data = models.CharField(max_length=255, blank=True, null=True)


class ProjectRoles(models.Model):
    role = models.ForeignKey(ProjectRoleLevel,related_name='project_roles',
        on_delete=models.CASCADE,blank=True, null=True)
    user = models.ForeignKey(AiUser,related_name='user_project_roles',
        on_delete=models.CASCADE,blank=True, null=True)
    proj_pk = models.CharField(_('Project ID'), max_length=255)

    class Meta:
       constraints = [
            UniqueConstraint(fields=['role', 'user', 'proj_pk'], name='unique_project_roles')
        ]
    @property
    def role_name(self):
        return self.role.role.name


class TaskRoles(models.Model):
    role = models.ForeignKey(TaskRoleLevel,related_name='task_roles',
        on_delete=models.CASCADE,blank=True, null=True)
    user = models.ForeignKey(AiUser,related_name='user_task_roles',
        on_delete=models.CASCADE,blank=True, null=True)
    task_pk = models.CharField(_('Task ID'), max_length=255)
    proj_pk = models.CharField(_('Project ID'), max_length=255)

    class Meta:
       constraints = [
            UniqueConstraint(fields=['role', 'user', 'task_pk'], name='unique_task_roles')
        ]
    @property
    def role_name(self):
        return self.role.role.name

class ApiUsage(models.Model):
    uid = models.CharField(max_length = 200)
    email = models.CharField(max_length = 200)
    service = models.ForeignKey(ApiServiceList,related_name='usage_service_list', on_delete=models.CASCADE)
    usage =models.IntegerField(default=0)
    history = HistoricalRecords()

    class Meta:
       constraints = [
            UniqueConstraint(fields=['uid', 'email', 'service'], name='unique_user_usage')
        ]


class SubscriptionOrder(models.Model):
    plan =models.ForeignKey(Product,related_name='sub_order_product',on_delete=models.CASCADE)
    lower_plan = models.ForeignKey(Product,related_name='sub_order_product_lw',null=True,blank=True,on_delete=models.CASCADE)
    higher_plan = models.ForeignKey(Product,related_name='sub_order_product_up',null=True,blank=True,on_delete=models.CASCADE)

    class Meta:
        # Create a unique constraint across all three fields
        constraints = [
            models.UniqueConstraint(fields=['plan', 'lower_plan','higher_plan'], name='subscriptins_order')
        ]

    def clean(self):
        # Custom validation logic to check for blank values
        if self.higher_plan!=None and self.lower_plan!=None:
            raise ValidationError("Either 'higher_plan' or 'lower_plan' must have a value.")
        elif self.higher_plan!=None and self.lower_plan==None:
            self.lower_plan = None  # Ensure lower_plan is blank if higher_plan is blank
        elif self.higher_plan==None and self.lower_plan!=None:
            self.higher_plan = None  # Ensure higher_plan is blank if lower_plan is blank

    def save(self, *args, **kwargs):
        self.full_clean()  # Run clean() before saving
        super().save(*args, **kwargs)