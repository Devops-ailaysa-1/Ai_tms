
from django.db import models
from django.contrib.auth.models import User
from ai_auth.managers import CustomUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from ai_staff.models import AiUserType, SubjectFields,Countries,Timezones


from django.contrib.auth.models import AbstractUser


class AiUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    fullname=models.CharField(max_length=191)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    from_mysql = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class UserAttribute(models.Model):
    user = models.OneToOneField(AiUser, on_delete=models.CASCADE)
    user_type=models.ForeignKey(AiUserType,related_name='user_attribute', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    class Meta:
        db_table='user_attribute'

class PersonalInformation(models.Model):
    user = models.OneToOneField(AiUser, on_delete=models.CASCADE)
    address = models.CharField(max_length=255, blank=True, null=True)
    country= models.ForeignKey(Countries,related_name='personal_info', on_delete=models.CASCADE,blank=True, null=True)
    timezone=models.ForeignKey(Timezones,related_name='personal_info', on_delete=models.CASCADE,blank=True, null=True)
    phonenumber=models.CharField(max_length=255, blank=True, null=True)
    mobilenumber=models.CharField(max_length=255, blank=True, null=True)
    linkedin=models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    class Meta:
        db_table = 'personal_info'


class OfficialInformation(models.Model):
    user = models.OneToOneField(AiUser, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    designation = models.CharField(max_length=255, blank=True, null=True)
    industry=models.ForeignKey(SubjectFields,related_name='official_info', on_delete=models.CASCADE)
    country= models.ForeignKey(Countries,related_name='official_info', on_delete=models.CASCADE)
    timezone=models.ForeignKey(Timezones,related_name='official_info', on_delete=models.CASCADE)
    website=models.CharField(max_length=255, blank=True, null=True)
    linkedin=models.CharField(max_length=255, blank=True, null=True)
    billing_email=models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    class Meta:
        db_table = 'official_info'


def user_directory_path(instance, filename):
  
    # file will be uploaded to MEDIA_ROOT / user_<id>/<filename>
    return 'user_{0}/{1}'.format(instance.user.id, filename)

class Professionalidentity(models.Model):
    user = models.OneToOneField(AiUser, on_delete=models.CASCADE)
    avatar=models.ImageField(upload_to=user_directory_path,blank=True,null=True)
    logo=models.ImageField(upload_to=user_directory_path,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    class Meta:
        db_table = 'professional_identity'