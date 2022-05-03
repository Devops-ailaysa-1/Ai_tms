from django.db import models
from ai_auth.models import AiUser, user_directory_path
from ai_staff.models import (Billingunits, CATSoftwares, ContentTypes,
                             Currencies, Languages, MtpeEngines, ParanoidModel,
                             ServiceTypes, SubjectFields,
                             VendorLegalCategories, VendorMemberships,Countries)
from django.db.models.constraints import UniqueConstraint
from ai_auth.models import AiUser,user_directory_path
from ai_workspace.models import Job,Project,Steps
from ai_staff.models import ContentTypes, Currencies, ParanoidModel, SubjectFields,Languages, VendorLegalCategories,VendorMemberships,MtpeEngines,Billingunits,ServiceTypes,CATSoftwares,ServiceTypeunits
from django.db.models import Q
import os
from django.contrib.auth import get_user_model
# Create your models here.
class AvailableVendors(ParanoidModel):
    customer= models.ForeignKey(AiUser,related_name='customer',on_delete=models.CASCADE)
    vendor =  models.ForeignKey(AiUser,related_name='vendor',on_delete=models.CASCADE)


class ProjectboardDetails(models.Model):#stephen subburaj
    project=models.ForeignKey(Project, on_delete=models.CASCADE,related_name="proj_detail")
    customer = models.ForeignKey(AiUser,on_delete=models.CASCADE, null=True, blank=True)
    service = models.CharField(max_length=191,blank=True, null=True)
    # steps = models.ForeignKey(Steps,blank=True, null=True,related_name = 'project_post_steps',on_delete=models.SET_NULL)
    # sub_field = models.ForeignKey(SubjectFields,blank=True, null=True, related_name='project_sub_field', on_delete=models.CASCADE)
    # content_type = models.ForeignKey(ContentTypes,blank=True, null=True, related_name='project_content_type', on_delete=models.CASCADE)
    proj_name = models.CharField(max_length=191,blank=True, null=True)
    proj_desc = models.CharField(max_length=1000,blank=True, null=True)
    bid_deadline = models.DateTimeField(blank=True, null=True)
    proj_deadline = models.DateTimeField(blank=True, null=True)
    ven_native_lang = models.ForeignKey(Languages,blank=True, null=True, related_name='vendor_native_lang', on_delete=models.CASCADE)
    ven_res_country = models.ForeignKey(Countries,blank=True, null=True, related_name='res_country', on_delete=models.CASCADE)
    ven_special_req = models.CharField(max_length=1000,blank=True, null=True)
    # cust_pc_name = models.CharField(max_length=191,blank=True, null=True)
    # cust_pc_email = models.CharField(max_length=191,blank=True, null=True)
    rate_range_min = models.DecimalField(
                         max_digits = 5,
                         decimal_places = 2,blank=True, null=True)
    rate_range_max = models.DecimalField(
                         max_digits = 5,
                         decimal_places = 2,blank=True, null=True)
    currency = models.ForeignKey(Currencies,blank=True, null=True, related_name='rate_currency', on_delete=models.CASCADE)
    unit = models.ForeignKey(Billingunits,blank=True, null=True, related_name='bill_unit', on_delete=models.CASCADE)
    milestone = models.CharField(max_length=191,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    @property
    def get_jobs(self):
        return [job for job in self.projectpost_jobs.all()]

    @property
    def get_steps(self):
        return [obj.steps for obj in self.projectpost_steps.all()]

    @property
    def get_steps_name(self):
        return [{'step':obj.steps.name,'id':obj.steps.id} for obj in self.projectpost_steps.all()]

class ProjectPostJobDetails(models.Model):
     src_lang = models.ForeignKey(Languages,related_name='projectpost_source_lang', on_delete=models.CASCADE)
     tar_lang = models.ForeignKey(Languages,related_name='projectpost_target_lang', on_delete=models.CASCADE)
     projectpost=models.ForeignKey(ProjectboardDetails,on_delete=models.CASCADE,related_name='projectpost_jobs')

     @property
     def source_target_pair_names(self):
        return "%s->%s"%(
            self.src_lang.language,
            self.tar_lang.language
        )

class ProjectPostContentType(models.Model):
    project = models.ForeignKey(ProjectboardDetails, on_delete=models.CASCADE,
                        related_name="projectpost_content_type")
    content_type = models.ForeignKey(ContentTypes, on_delete=models.CASCADE,
                        related_name="projectpost_content_type")

class ProjectPostSteps(models.Model):
    project = models.ForeignKey(ProjectboardDetails, on_delete=models.CASCADE,
                        related_name="projectpost_steps")
    steps = models.ForeignKey(Steps, on_delete=models.CASCADE,
                        related_name="projectpost_steps")


class ProjectPostSubjectField(models.Model):
    project = models.ForeignKey(ProjectboardDetails, on_delete=models.CASCADE,
                        related_name="projectpost_subject")
    subject = models.ForeignKey(SubjectFields, on_delete=models.CASCADE,
                        related_name="projectpost_subject")


class ProjectboardTemplateDetails(models.Model):
    template_name = models.CharField(max_length=1000,blank=False, null=False)
    project=models.ForeignKey(Project, on_delete=models.CASCADE,related_name="project_detail")
    customer = models.ForeignKey(AiUser,on_delete=models.CASCADE, null=True, blank=True)
    service = models.CharField(max_length=191,blank=True, null=True)
    # steps = models.ForeignKey(Steps,blank=True, null=True,related_name = 'proj_post_steps',on_delete=models.SET_NULL)
    proj_name = models.CharField(max_length=191,blank=True, null=True)
    proj_desc = models.CharField(max_length=1000,blank=True, null=True)
    bid_deadline = models.DateTimeField(blank=True, null=True)
    proj_deadline = models.DateTimeField(blank=True, null=True)
    ven_native_lang = models.ForeignKey(Languages,blank=True, null=True, related_name='ven_native_lang', on_delete=models.CASCADE)
    ven_res_country = models.ForeignKey(Countries,blank=True, null=True, related_name='ven_country', on_delete=models.CASCADE)
    ven_special_req = models.CharField(max_length=1000,blank=True, null=True)
    rate_range_min = models.DecimalField(
                         max_digits = 5,
                         decimal_places = 2,blank=True, null=True)
    rate_range_max = models.DecimalField(
                         max_digits = 5,
                         decimal_places = 2,blank=True, null=True)
    currency = models.ForeignKey(Currencies,blank=True, null=True, related_name='ven_currency_detail', on_delete=models.CASCADE)
    unit = models.ForeignKey(Billingunits,blank=True, null=True, related_name='billing_unit', on_delete=models.CASCADE)
    milestone = models.CharField(max_length=191,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)


class ProjectPostTemplateJobDetails(models.Model):
     src_lang = models.ForeignKey(Languages,related_name='projectposttemp_source_lang', on_delete=models.CASCADE)
     tar_lang = models.ForeignKey(Languages,related_name='projectposttemp_target_lang', on_delete=models.CASCADE)
     projectpost_template=models.ForeignKey(ProjectboardTemplateDetails,on_delete=models.CASCADE,related_name='projectposttemp_jobs')


class ProjectPostTemplateContentType(models.Model):
    projectpost_template = models.ForeignKey(ProjectboardTemplateDetails, on_delete=models.CASCADE,
                        related_name="projectposttemp_content_type")
    content_type = models.ForeignKey(ContentTypes, on_delete=models.CASCADE,
                        related_name="projectposttemp_content_type")

class ProjectPostTemplateSubjectField(models.Model):##############idea given by stephen###########
    projectpost_template = models.ForeignKey(ProjectboardTemplateDetails, on_delete=models.CASCADE,
                        related_name="projectposttemp_subject")
    subject = models.ForeignKey(SubjectFields, on_delete=models.CASCADE,
                        related_name="projectposttemp_subject")

class ProjectPostTemplateSteps(models.Model):
    projectpost_template = models.ForeignKey(ProjectboardTemplateDetails, on_delete=models.CASCADE,
                        related_name="projectposttemp_steps")
    steps = models.ForeignKey(Steps, on_delete=models.CASCADE,
                        related_name="projectposttemp_steps")

class BidChat(models.Model):
    message = models.TextField()
    sender = models.ForeignKey(AiUser,related_name='message_creator',on_delete=models.CASCADE,blank=True, null=True)
    # receiver = models.ForeignKey(AiUser,related_name='receiver',on_delete=models.CASCADE,blank=True, null=True)
    projectpost_jobs = models.ForeignKey(ProjectPostJobDetails,related_name='bidding_job',on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('timestamp',)

# class AvailableJobs(models.Model):
#     projectpostjob=models.ForeignKey(ProjectPostJobDetails, on_delete=models.CASCADE,related_name="projpostjob_details")
#     vendor=models.ForeignKey(AiUser, on_delete=models.CASCADE)
#     projectpost=models.ForeignKey(ProjectboardDetails,on_delete=models.CASCADE,related_name='projectpost')

def user_directory_path(instance, filename):
    return '{0}/{1}/{2}/{3}'.format(instance.vendor.uid,"BidDetails","Samplefiles",filename)

class BidStatus(models.Model):
    status = models.CharField(max_length=191,blank=True, null=True)


class BidPropasalDetails(models.Model):
    # projectpostjob =  models.ForeignKey(ProjectPostJobDetails, on_delete=models.CASCADE,related_name="bidjob_details")
    projectpost = models.ForeignKey(ProjectboardDetails, on_delete=models.CASCADE,related_name="bidproject_details")
    vendor = models.ForeignKey(AiUser, on_delete=models.CASCADE,related_name="bid_proposal_vendor",null=True,blank=True)
    proposed_completion_date = models.DateTimeField(blank=True,null=True)
    description = models.TextField(blank=True,null=True)
    sample_file = models.FileField(upload_to=user_directory_path, blank=True, null=True)
    #status = models.ForeignKey(BidStatus,on_delete=models.CASCADE,related_name="bid_status",blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    # class Meta:
    #     unique_together = ['projectpostjob', 'vendor']
    @property
    def filename(self):
        if self.sample_file:
            return  os.path.basename(self.sample_file.file.name)
        else:
            return None

class BidProposalServicesRates(models.Model):
    bid_proposal =  models.ForeignKey(BidPropasalDetails, on_delete=models.CASCADE,related_name="service_and_rates")
    bidpostjob =  models.ForeignKey(ProjectPostJobDetails, on_delete=models.CASCADE,related_name="bid_details")
    bid_vendor = models.ForeignKey(AiUser, on_delete=models.CASCADE,related_name="bidsent_vendor")
    mtpe_rate= models.DecimalField(max_digits=5,decimal_places=2,blank=True, null=True)
    mtpe_hourly_rate=models.DecimalField(max_digits=5,decimal_places=2,blank=True, null=True)
    bid_step = models.ForeignKey(Steps, on_delete=models.CASCADE,related_name="bidpost_steps")
    status = models.ForeignKey(BidStatus,on_delete=models.CASCADE,related_name="bid_status",blank=True, null=True,default = 1)
    mtpe_count_unit=models.ForeignKey(ServiceTypeunits,on_delete=models.CASCADE,related_name='bid_job_mtpe_unit_type',blank=True,null=True)
    currency = models.ForeignKey(Currencies,blank=True, null=True, related_name='bidding_currency_detail', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)

    class Meta:
        unique_together = ['bidpostjob', 'bid_vendor','bid_step']

# class BidPropasalStepDetails(models.Model):
#     bid_proposal_service_rate = models.ForeignKey(BidProposalServicesRates, on_delete=models.CASCADE,related_name="bid_step_detail")
#     steps = models.ForeignKey(Steps, on_delete=models.CASCADE,related_name="bidpost_steps")


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
        unique_together = ['first_person', 'second_person']


class ChatMessage(models.Model):
    thread = models.ForeignKey(Thread, null=True, blank=True, on_delete=models.CASCADE, related_name='chatmessage_thread')
    user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    # @property
    # def get_sender_and_receiver(self):
    #     Thread.objects.get()
