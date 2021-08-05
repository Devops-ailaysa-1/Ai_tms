from ai_auth.models import AiUser, user_directory_path
from ai_staff.models import (Billingunits, CATSoftwares, ContentTypes,
                             Currencies, Languages, MtpeEngines, ParanoidModel,
                             ServiceTypes, SubjectFields,
                             VendorLegalCategories, VendorMemberships,Countries)
from django.db import models
from django.db.models.constraints import UniqueConstraint
from ai_auth.models import AiUser,user_directory_path
from ai_workspace.models import Job
from ai_staff.models import ContentTypes, Currencies, ParanoidModel, SubjectFields,Languages, VendorLegalCategories,VendorMemberships,MtpeEngines,Billingunits,ServiceTypes,CATSoftwares,ServiceTypeunits
from django.db.models import Q


def vendor_directory_path(instance, filename):
    return '{0}/{1}/{2}/{3}'.format(instance.user.uid, "vendor","cv_file",filename)


class VendorsInfo(models.Model):
    user = models.OneToOneField(AiUser, on_delete=models.CASCADE)
    vendor_unique_id = models.CharField(max_length=191, blank=True, null=True)
    type = models.ForeignKey(VendorLegalCategories,related_name='vendor_legal_type', on_delete=models.CASCADE)
    currency = models.ForeignKey(Currencies,related_name='vendor_currency', on_delete=models.CASCADE)
    vm_status = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True)
    token = models.CharField(max_length=191, blank=True, null=True)
    skype = models.CharField(max_length=191, blank=True, null=True)
    proz_link = models.CharField(max_length=191, blank=True, null=True)
    cv_file = models.FileField(upload_to=vendor_directory_path, blank=True, null=True)
    native_lang = models.ForeignKey(Languages,blank=True, null=True, related_name='native_lang', on_delete=models.CASCADE)
    year_of_experience = models.DecimalField(max_digits=5,decimal_places=1 , blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)


class VendorBankDetails(models.Model):
    user = models.OneToOneField(AiUser, on_delete=models.CASCADE)
    paypal_email = models.EmailField(max_length=191, blank=True, null=True)
    bank_name = models.CharField(max_length=191, blank=True, null=True)
    bank_address = models.TextField(blank=True, null=True)
    bank_account_name = models.CharField(max_length=191, blank=True, null=True)
    bank_account_number = models.CharField(max_length=191, blank=True, null=True)
    iban = models.CharField(max_length=191, blank=True, null=True)
    bank_swift_code = models.CharField(max_length=191, blank=True, null=True)
    bank_ifsc = models.CharField(max_length=191, blank=True, null=True)
    gst_number = models.CharField(max_length=191, blank=True, null=True)
    pan_number = models.CharField(max_length=191, blank=True, null=True)
    other_bank_details = models.CharField(max_length=191,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)



class VendorSubjectFields(ParanoidModel):
    user = models.ForeignKey(AiUser,related_name='vendor_subject', on_delete=models.CASCADE)
    subject = models.ForeignKey(SubjectFields,blank=True, null=True, related_name='vendor_subject', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    # class Meta:
    #     unique_together = ("user", "subject")

class VendorCATsoftware(ParanoidModel):
    user = models.ForeignKey(AiUser,related_name='vendor_software', on_delete=models.CASCADE)
    software = models.ForeignKey(CATSoftwares,blank=True, null=True, related_name='vendor_software', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)



class VendorMembership(ParanoidModel):
    user = models.ForeignKey(AiUser,related_name='vendor_membership', on_delete=models.CASCADE)
    membership = models.ForeignKey(VendorMemberships,blank=True, null=True, related_name='vendor_membership', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    # class Meta:
    #     unique_together = ("user", "membership")

class VendorContentTypes(ParanoidModel):
    user = models.ForeignKey(AiUser,related_name='vendor_contentype', on_delete=models.CASCADE)
    contenttype = models.ForeignKey(ContentTypes, blank=True, null=True, related_name='vendor_contentype', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    # deleted_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    # class Meta:
    #     unique_together = ("user", "contenttype")

class VendorMtpeEngines(ParanoidModel):
    user = models.ForeignKey(AiUser,related_name='vendor_mtpe_engines', on_delete=models.CASCADE)
    mtpe_engines = models.ForeignKey(MtpeEngines,blank=True, null=True, related_name='vendor_mtpe_engines', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    # class Meta:
    #     unique_together = ("user", "mtpe_engines")


class VendorLanguagePair(ParanoidModel):
    user = models.ForeignKey(AiUser,related_name='vendor_lang_pair', on_delete=models.CASCADE)
    source_lang=models.ForeignKey(Languages,blank=True, null=True, related_name='vendor_source_lang', on_delete=models.CASCADE)
    target_lang=models.ForeignKey(Languages,blank=True, null=True, related_name='vendor_target_lang', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    # created_at = models.CharField(max_length=100)
    # updated_at = models.CharField(max_length=100)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['user', 'source_lang', 'target_lang'], condition=Q(deleted_at=None), name='unique_if_not_deleted')
        ]
    # class Meta:
    #    unique_together = ("user", "source_lang","target_lang","deleted_at")


class VendorServiceInfo(ParanoidModel):
     lang_pair=models.ForeignKey(VendorLanguagePair,related_name='service', on_delete=models.CASCADE)
     mtpe_rate= models.DecimalField(max_digits=5,decimal_places=2 , blank=True, null=True)
     mtpe_hourly_rate=models.DecimalField(max_digits=5,decimal_places=2 , blank=True, null=True)
     mtpe_count_unit=models.ForeignKey(ServiceTypeunits,related_name='unit_type', on_delete=models.CASCADE, blank=True, null=True)
     created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
     updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

class VendorServiceTypes(ParanoidModel):
    lang_pair=models.ForeignKey(VendorLanguagePair,related_name='servicetype', on_delete=models.CASCADE)
    services=models.ForeignKey(ServiceTypes,related_name='services', on_delete=models.CASCADE)
    unit_type=models.ForeignKey(ServiceTypeunits, on_delete=models.CASCADE , blank=True, null=True)
    unit_rate=models.DecimalField(max_digits=5,decimal_places=2 , blank=True, null=True)
    hourly_rate=models.DecimalField(max_digits=5,decimal_places=2 , blank=True, null=True)
    minute_rate=models.DecimalField(max_digits=5,decimal_places=2,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    class Meta:
        managed = False


def user_directory_path(instance, filename):
    return '{0}/{1}/{2}/{3}'.format(lang_pair.instance.user.uid, "vendor","TranslationSamples",filename)

class TranslationSamples(ParanoidModel):
    lang_pair=models.ForeignKey(VendorLanguagePair,related_name='translationfile', on_delete=models.CASCADE)
    translation_file = models.FileField(upload_to=user_directory_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    # deleted_at = models.DateTimeField(auto_now=True,blank=True, null=True)

def user_directory_path_1(instance, filename):
    return '{0}/{1}/{2}/{3}'.format(lang_pair.instance.user.uid, "vendor","MtpeSamples",filename)

class MtpeSamples(ParanoidModel):
    lang_pair=models.ForeignKey(VendorLanguagePair,related_name='mtpesamples',on_delete=models.CASCADE)
    sample_file = models.FileField(upload_to=user_directory_path_1, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    # deleted_at = models.DateTimeField(auto_now=True,blank=True, null=True)

class AssignedVendors(ParanoidModel):
    customer= models.ForeignKey(AiUser,related_name='customer',on_delete=models.CASCADE)
    vendor =  models.ForeignKey(AiUser,related_name='vendor',on_delete=models.CASCADE)



class jobboard_details(models.Model):
    job=models.ForeignKey(Job, on_delete=models.CASCADE,related_name="job_detail")
    service = models.CharField(max_length=191,blank=True, null=True)
    steps = models.CharField(max_length=191,blank=True, null=True)
    # src_lang = models.CharField(max_length=191,blank=True, null=True)
    # tar_lang = models.CharField(max_length=191,blank=True, null=True)
    sub_field = models.CharField(max_length=191,blank=True, null=True)
    content_type = models.CharField(max_length=191,blank=True, null=True)
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

# class vendor_bid_details(models.Model):
#     proj_id=models.ForeignKey(jobboard_projdetails, on_delete=models.CASCADE)
#     bid_amount=models.DecimalField(
#                          max_digits = 5,
#                          decimal_places = 2,blank=True, null=True)
#     vendor= models.ForeignKey(User, on_delete=models.CASCADE)
#     created = models.DateTimeField(auto_now_add=True)
#     ven_bid_msg = models.CharField(max_length=1000,blank=True, null=True)
