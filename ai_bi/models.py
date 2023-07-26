from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save, pre_save

# Create your models here.
from ai_auth.models import AiUser
from ai_bi.signals import _bi_user_details

class BiUser(models.Model):
    # TECHNICAL=1
    # FINANCE=2
    # ADMIN=3
    ROLE_CHOICES = (
        ("TECHNICAL", 'TECHNICAL'),
        ("FINANCE", 'FINANCE'),
        ("ADMIN","ADMIN"),
    )
    bi_user=models.OneToOneField(AiUser,related_name="bi_user", on_delete=models.CASCADE)
    bi_role = models.CharField(max_length=250, choices=ROLE_CHOICES)


class AiUserDetails(models.Model):
    email = models.EmailField(unique=True)
    fullname=models.CharField(max_length=191,null=True,blank=True)
    country= models.CharField(max_length=100,null=True,blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    deactivation_date = models.DateTimeField(null=True,blank=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(default=timezone.now,null=True,blank=True)
    deactivate = models.BooleanField(default=False)
    is_vendor = models.BooleanField(default=False)
    is_agency = models.BooleanField(default=False)
    is_internal_member = models.BooleanField(default=False)
    first_login = models.BooleanField(default=False)
    currency_based_on_country = models.CharField(max_length=100,null=True,blank=True)
    subscription_name = models.CharField(max_length=100,null=True,blank=True)
    subscription_status = models.CharField(max_length=100,null=True,blank=True)
    subscription_start = models.DateTimeField(null=True,blank=True)
    subscription_end =models.DateTimeField(null=True,blank=True)
    intial_credits = models.IntegerField(default=0)
    credits_left = models.IntegerField(default=0)
    credits_consumed = models.IntegerField(default=0)
    projects_created = models.IntegerField(default=0)
    documents_created = models.IntegerField(default=0)
    pdf_conversion = models.IntegerField(default=0)
    blogs_created = models.IntegerField(default=0)
    signup_age = models.IntegerField(default=0)
    project_types = models.CharField(max_length=100,null=True,blank=True)
    language_pairs_used = models.TextField(null=True,blank=True)

    class Meta:
        managed=False


# post_save.connect(_bi_user_details, sender=AiUserDetails)