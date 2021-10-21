
from django.db import models
from django.contrib.auth.models import User
from ai_auth.managers import CustomUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from ai_staff.models import AiUserType, StripeTaxId, SubjectFields,Countries,Timezones,SupportType,JobPositions,SupportTopics
from django.db.models.signals import post_save, pre_save
from ai_auth.signals import create_allocated_dirs,updated_billingaddress,updated_user_taxid
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from ai_auth.utils import get_unique_uid
from djstripe.models import Customer,Subscription,PaymentIntent,Invoice,Price,Product,Charge
from ai_auth import Aiwebhooks
# from djstripe import webhooks
from django.db.models import Q
from datetime import datetime



class AiUser(AbstractBaseUser, PermissionsMixin):
    uid = models.CharField(max_length=25, null=False, blank=True)
    email = models.EmailField(_('email address'), unique=True)
    fullname=models.CharField(max_length=191)
    country= models.ForeignKey(Countries,related_name='aiuser_country', on_delete=models.CASCADE,blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    deactivation_date = models.DateTimeField(null=True, blank=True)
    deactive = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    from_mysql = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.uid:
            self.uid = get_unique_uid(AiUser)
        return super().save(*args, **kwargs)

    @property
    def credit_balance(self):
        print("**** inside AiUser credit balance  ****")
        total_credit_left = 0
        present = datetime.now()
        sub_credits = UserCredits.objects.get(Q(user=self) & Q(credit_pack_type__icontains="Subscription") \
                                             & Q(ended_at=None))
        if present.strftime('%Y-%m-%d %H:%M:%S') <= sub_credits.expiry.strftime('%Y-%m-%d %H:%M:%S'):
            total_credit_left += sub_credits.credits_left

        try:
            addon_credits = UserCredits.objects.filter(Q(user=self) & Q(credit_pack_type="Addon"))
            for addon in addon_credits:
                total_credit_left += addon.credits_left
        except Exception as e:
            print("NO ADD-ONS AVAILABLE")

        return total_credit_left

    @property
    def buyed_credits(self):
        print("**** inside AiUser buyed credits  ****")
        total_buyed_credits = 0
        present = datetime.now()
        sub_credits = UserCredits.objects.get(Q(user=self) & Q(credit_pack_type__icontains="Subscription") & Q(ended_at=None))
        if present.strftime('%Y-%m-%d %H:%M:%S') <= sub_credits.expiry.strftime('%Y-%m-%d %H:%M:%S'):
            total_buyed_credits += sub_credits.buyed_credits
        try:
            addon_credits = UserCredits.objects.filter(Q(user=self) & Q(credit_pack_type="Addon"))
            for addon in addon_credits:
                total_buyed_credits += addon.buyed_credits
        except Exception as e:
            print("NO ADD-ONS AVAILABLE")

        return total_buyed_credits


class BaseAddress(models.Model):
    line1 = models.CharField(max_length=200,blank=True, null=True)
    line2 = models.CharField(max_length=200,blank=True, null=True)
    state = models.CharField(max_length=200,blank=True, null=True)
    city = models.CharField(max_length=200,blank=True, null=True)
    zipcode= models.IntegerField(default=0,blank=True, null=True)
    class Meta:
        abstract=True


class UserAttribute(models.Model):
    user = models.OneToOneField(AiUser, on_delete=models.CASCADE,null=True)
    user_type=models.ForeignKey(AiUserType, related_name='user_attribute', on_delete=models.CASCADE,default=1)
    allocated_dir = models.URLField(default=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        # managed=False
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

pre_save.connect(create_allocated_dirs, sender=UserAttribute)

# class PersonalInformation(models.Model):
#     user = models.OneToOneField(AiUser, on_delete=models.CASCADE,null=True,related_name='personal_info')
#     #address = models.CharField(max_length=255, blank=True, null=True)

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
#         #managed=False
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
#         #managed=False
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

class UserProfile(models.Model):
    user = models.OneToOneField(AiUser, on_delete=models.CASCADE)
    description = models.TextField(max_length=1000, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

class CustomerSupport(models.Model):
    user = models.ForeignKey(AiUser,on_delete=models.CASCADE)
    support_type = models.ForeignKey(SupportType,on_delete=models.CASCADE)
    description = models.TextField(max_length=1000, blank=True, null=True)
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
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)


class UserCredits(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    stripe_cust_id=  models.ForeignKey(Customer, on_delete=models.CASCADE)
    price_id = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    buyed_credits = models.IntegerField()
    credits_left =models.IntegerField()
    expiry = models.DateTimeField(blank=True, null=True)
    invoice = models.CharField(max_length=200,blank=True, null=True)
    paymentintent = models.CharField(max_length=200,blank=True, null=True)
    credit_pack_type = models.CharField(max_length=200, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    ended_at = models.DateTimeField(null=True, blank=True)

class CreditPack(models.Model):
    name = models.CharField(max_length=200)
    #product = models.OneToOneField(Product, on_delete=models.CASCADE)
    #price = models.OneToOneField(Price, on_delete=models.CASCADE)
    product =models.ForeignKey(Product,on_delete=models.CASCADE)
    type = models.CharField(max_length=200)
    credits = models.IntegerField(default=0)

class BillingAddress(BaseAddress):
    user = models.OneToOneField(AiUser, on_delete=models.CASCADE,related_name='billing_addr_user')
    name = models.CharField(max_length=255, blank=True, null=True)
    country= models.ForeignKey(Countries,related_name='billing_country', on_delete=models.CASCADE,blank=True, null=True)

post_save.connect(updated_billingaddress, sender=BillingAddress)

class UserTaxInfo(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE,related_name='tax_info_user')
    stripe_tax_id = models.ForeignKey(StripeTaxId,on_delete=models.CASCADE,related_name='stripe_taxid_user')
    tax_id = models.CharField(max_length=250)
    #tax_uid= models.CharField(max_length=250)

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
    return '{0}/{1}/{2}'.format(instance.email,"vendor_cv_file",filename)

class VendorOnboarding(models.Model):
    name = models.CharField(max_length=250)
    email = models.EmailField()
    cv_file = models.FileField(upload_to=file_path_vendor)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)


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
