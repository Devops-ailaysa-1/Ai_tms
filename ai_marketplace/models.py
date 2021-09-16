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
from django.contrib.auth import get_user_model
# Create your models here.
class AvailableVendors(ParanoidModel):
    customer= models.ForeignKey(AiUser,related_name='customer',on_delete=models.CASCADE)
    vendor =  models.ForeignKey(AiUser,related_name='vendor',on_delete=models.CASCADE)


class ProjectboardDetails(models.Model):
    project=models.ForeignKey(Project, on_delete=models.CASCADE,related_name="proj_detail")
    customer = models.ForeignKey(AiUser,on_delete=models.CASCADE, null=True, blank=True)
    service = models.CharField(max_length=191,blank=True, null=True)
    steps = models.CharField(max_length=191,blank=True, null=True)
    # sub_field = models.ForeignKey(SubjectFields,blank=True, null=True, related_name='project_sub_field', on_delete=models.CASCADE)
    # content_type = models.ForeignKey(ContentTypes,blank=True, null=True, related_name='project_content_type', on_delete=models.CASCADE)
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


class ProjectPostContentType(models.Model):
    project = models.ForeignKey(ProjectboardDetails, on_delete=models.CASCADE,
                        related_name="projectpost_content_type")
    content_type = models.ForeignKey(ContentTypes, on_delete=models.CASCADE,
                        related_name="projectpost_content_type")

class ProjectPostSubjectField(models.Model):
    project = models.ForeignKey(ProjectboardDetails, on_delete=models.CASCADE,
                        related_name="projectpost_subject")
    subject = models.ForeignKey(SubjectFields, on_delete=models.CASCADE,
                        related_name="projectpost_subject")



class BidChat(models.Model):
    message = models.TextField()
    sender = models.ForeignKey(AiUser,related_name='message_creator',on_delete=models.CASCADE,blank=True, null=True)
    # receiver = models.ForeignKey(AiUser,related_name='receiver',on_delete=models.CASCADE,blank=True, null=True)
    projectpost_jobs = models.ForeignKey(ProjectPostJobDetails,related_name='bidding_job',on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('timestamp',)

class AvailableJobs(models.Model):
    projectpostjob=models.ForeignKey(ProjectPostJobDetails, on_delete=models.CASCADE,related_name="projpostjob_details")
    vendor=models.ForeignKey(AiUser, on_delete=models.CASCADE)
    projectpost=models.ForeignKey(ProjectboardDetails,on_delete=models.CASCADE,related_name='projectpost')

def user_directory_path(instance, filename):
    return '{0}/{1}/{2}/{3}'.format(instance.vendor.uid,"BidDetails","Samplefiles",filename)


class BidPropasalDetails(models.Model):
    projectpostjob =  models.ForeignKey(ProjectPostJobDetails, on_delete=models.CASCADE,related_name="bidjob_details")
    projectpost = models.ForeignKey(ProjectboardDetails, on_delete=models.CASCADE,related_name="bidproject_details")
    vendor = models.ForeignKey(AiUser, on_delete=models.CASCADE,related_name="bid_sent_vendor")
    proposed_completion_date = models.DateTimeField(blank=True,null=True)
    description = models.TextField(blank=True,null=True)
    sample_file_upload = models.FileField(upload_to=user_directory_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)

class BidProposalServicesRates(models.Model):
    bid =  models.ForeignKey(BidPropasalDetails, on_delete=models.CASCADE,related_name="service_and_rates")
    mtpe_rate= models.DecimalField(max_digits=5,decimal_places=2,blank=True, null=True)
    mtpe_hourly_rate=models.DecimalField(max_digits=5,decimal_places=2,blank=True, null=True)
    mtpe_count_unit=models.ForeignKey(ServiceTypeunits,on_delete=models.CASCADE,related_name='bid_job_mtpe_unit_type',blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)


User = get_user_model()

class ThreadManager(models.Manager):
    def by_user(self, **kwargs):
        user = kwargs.get('user')
        lookup = Q(first_person=user) | Q(second_person=user)
        qs = self.get_queryset().filter(lookup).distinct()
        return qs


class Thread(models.Model):
    first_person = models.ForeignKey(AiUser, on_delete=models.CASCADE, null=True, blank=True, related_name='thread_first_person')
    second_person = models.ForeignKey(AiUser, on_delete=models.CASCADE, null=True, blank=True,
                                     related_name='thread_second_person')
    bid = models.ForeignKey(BidPropasalDetails,on_delete=models.CASCADE, null=True, blank=True,related_name='thread_bid')
    updated = models.DateTimeField(auto_now=True,null=True,blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = ThreadManager()
    class Meta:
        unique_together = ['first_person', 'second_person','bid']


class ChatMessage(models.Model):
    thread = models.ForeignKey(Thread, null=True, blank=True, on_delete=models.CASCADE, related_name='chatmessage_thread')
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
