
from django.db import models
from django.contrib.auth.models import User
from ai_auth.managers import CustomUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from ai_staff.models import AiUserType, SubjectFields,Countries,Timezones,SupportType
from django.db.models.signals import post_save, pre_save
from .signals import create_allocated_dirs,updated_billingaddress
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from ai_auth.utils import get_unique_uid
from djstripe.models import Customer,Subscription,PaymentIntent,Invoice,Price,Product,Charge
from ai_auth import Aiwebhooks 
# from djstripe import webhooks

class AiUser(AbstractBaseUser, PermissionsMixin):
    uid = models.CharField(max_length=25, null=False, blank=True)
    email = models.EmailField(_('email address'), unique=True)
    fullname=models.CharField(max_length=191)
    country= models.ForeignKey(Countries,related_name='aiuser_country', on_delete=models.CASCADE,blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
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
    user_type=models.ForeignKey(AiUserType, related_name='user_attribute', on_delete=models.CASCADE)
    allocated_dir = models.URLField(default=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
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

class PersonalInformation(models.Model):
    user = models.OneToOneField(AiUser, on_delete=models.CASCADE,null=True,related_name='personal_info')
    #address = models.CharField(max_length=255, blank=True, null=True)
    
    #country= models.ForeignKey(Countries,related_name='personal_info', on_delete=models.CASCADE,blank=True, null=True)
    timezone=models.ForeignKey(Timezones,related_name='personal_info', on_delete=models.CASCADE,blank=True, null=True)
    phonenumber=models.CharField(max_length=255, blank=True, null=True)
    mobilenumber=models.CharField(max_length=255, blank=True, null=True)
    linkedin=models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    # created_at = models.CharField(max_length=200,blank=True, null=True)
    # updated_at = models.CharField(max_length=200,blank=True, null=True)
    class Meta:
        db_table = 'personal_info'


class OfficialInformation(models.Model):
    user = models.OneToOneField(AiUser, on_delete=models.CASCADE,null=True,related_name='official_info')
    company_name = models.CharField(max_length=255, blank=True, null=True)
   # address = models.CharField(max_length=255, blank=True, null=True)
    designation = models.CharField(max_length=255, blank=True, null=True)
    industry=models.ForeignKey(SubjectFields,related_name='official_info', on_delete=models.CASCADE,blank=True, null=True)
    #country= models.ForeignKey(Countries,related_name='official_info', on_delete=models.CASCADE,blank=True, null=True)
    timezone=models.ForeignKey(Timezones,related_name='official_info', on_delete=models.CASCADE,blank=True, null=True)
    website=models.CharField(max_length=255, blank=True, null=True)
    linkedin=models.CharField(max_length=255, blank=True, null=True)
    billing_email=models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    class Meta:
        db_table = 'official_info'


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
    description = models.TextField(max_length=1000, blank=True, null=True)
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
    Buyed_credits = models.IntegerField()
    credits_left =models.IntegerField()
    expiry = models.DateTimeField(blank=True, null=True)
    invoice = models.CharField(max_length=200,blank=True, null=True)
    paymentintent = models.CharField(max_length=200,blank=True, null=True)
    


class CreditPack(models.Model):
    name = models.CharField(max_length=200)
    #product = models.OneToOneField(Product, on_delete=models.CASCADE)
    #price = models.OneToOneField(Price, on_delete=models.CASCADE)
    product =models.OneToOneField(Product,on_delete=models.CASCADE)
    type = models.CharField(max_length=200)
    credits = models.IntegerField(default=0)

class BillingAddress(BaseAddress):
    user = models.OneToOneField(AiUser, on_delete=models.CASCADE,related_name='billing_addr_user')
    name = models.CharField(max_length=255, blank=True, null=True)
    country= models.ForeignKey(Countries,related_name='billing_country', on_delete=models.CASCADE,blank=True, null=True)

#post_save.connect(updated_billingaddress, sender=BillingAddress)

class UserTaxInfo(models.Model):
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE,related_name='tax_info_user')
    country = models.ForeignKey(Countries,on_delete=models.CASCADE) 
    tax_id = models.CharField(max_length=250)

class UserAppPreference(models.Model):
    email = models.EmailField()
    country = models.ForeignKey(Countries,related_name='app_pre_country',on_delete=models.CASCADE) 

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