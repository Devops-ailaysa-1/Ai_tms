from django.db import models
from ai_auth.models import AiUser, user_directory_path
from ai_staff.models import (Billingunits, CATSoftwares, ContentTypes,
                             Currencies, Languages, MtpeEngines, ParanoidModel,
                             ServiceTypes, SubjectFields,
                             VendorLegalCategories, VendorMemberships,Countries)
from django.db.models.constraints import UniqueConstraint
from ai_auth.models import AiUser,user_directory_path
from ai_workspace.models import Job,Project
from ai_staff.models import ContentTypes, Currencies, ParanoidModel, SubjectFields,Languages, VendorLegalCategories,VendorMemberships,MtpeEngines,Billingunits,ServiceTypes,CATSoftwares,ServiceTypeunits
from django.db.models import Q

# Create your models here.
class AvailableVendors(ParanoidModel):
    customer= models.ForeignKey(AiUser,related_name='customer',on_delete=models.CASCADE)
    vendor =  models.ForeignKey(AiUser,related_name='vendor',on_delete=models.CASCADE)


class ProjectboardDetails(models.Model):
    project=models.ForeignKey(Project, on_delete=models.CASCADE,related_name="proj_detail")
    service = models.CharField(max_length=191,blank=True, null=True)
    steps = models.CharField(max_length=191,blank=True, null=True)
    sub_field = models.ForeignKey(SubjectFields,blank=True, null=True, related_name='project_sub_field', on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentTypes,blank=True, null=True, related_name='project_content_type', on_delete=models.CASCADE)
    proj_name = models.CharField(max_length=191,blank=True, null=True)
    proj_desc = models.CharField(max_length=1000,blank=True, null=True)
    bid_deadline = models.DateTimeField(blank=True, null=True)
    proj_deadline = models.DateTimeField(blank=True, null=True)
    ven_native_lang = models.ForeignKey(Languages,blank=True, null=True, related_name='vendor_native_lang', on_delete=models.CASCADE)
    ven_res_country = models.ForeignKey(Countries,blank=True, null=True, related_name='res_country', on_delete=models.CASCADE)
    ven_special_req = models.CharField(max_length=1000,blank=True, null=True)
    cust_pc_name = models.CharField(max_length=191,blank=True, null=True)
    cust_pc_email = models.CharField(max_length=191,blank=True, null=True)
    rate_range_min = models.DecimalField(
                         max_digits = 5,
                         decimal_places = 2,blank=True, null=True)
    rate_range_max = models.DecimalField(
                         max_digits = 5,
                         decimal_places = 2,blank=True, null=True)
    currency = models.ForeignKey(Currencies,blank=True, null=True, related_name='ven_currency', on_delete=models.CASCADE)
    unit = models.ForeignKey(Billingunits,blank=True, null=True, related_name='bill_unit', on_delete=models.CASCADE)
    milestone = models.CharField(max_length=191,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)


class ProjectPostJobDetails(models.Model):
     src_lang = models.ForeignKey(Languages,related_name='projectpost_source_lang', on_delete=models.CASCADE)
     tar_lang = models.ForeignKey(Languages,related_name='projectpost_target_lang', on_delete=models.CASCADE)
     projectpost=models.ForeignKey(ProjectboardDetails,on_delete=models.CASCADE,related_name='projectpost_jobs')


class BidChat(models.Model):
    message = models.TextField()
    sender = models.ForeignKey(AiUser,related_name='message_creator',on_delete=models.CASCADE,blank=True, null=True)
    # receiver = models.ForeignKey(AiUser,related_name='receiver',on_delete=models.CASCADE,blank=True, null=True)
    projectpost_jobs = models.ForeignKey(ProjectPostJobDetails,related_name='bidding_job',on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('timestamp',)

class AvailableBids(models.Model):
    projectpostjob=models.ForeignKey(ProjectPostJobDetails, on_delete=models.CASCADE,related_name="projpostjob_details")
    vendor=models.ForeignKey(AiUser, on_delete=models.CASCADE)
