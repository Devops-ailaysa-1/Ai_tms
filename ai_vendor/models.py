from django.db import models
from ai_auth.models import AiUser,user_directory_path
from ai_staff.models import ContentTypes, Currencies, ParanoidModel, SubjectFields,Languages, VendorLegalCategories,VendorMemberships,MtpeEngines,Billingunits,ServiceTypes

# Create your models here.
class VendorsInfo(models.Model):
    user = models.OneToOneField(AiUser, on_delete=models.CASCADE, blank=True, null=True)
    vendor_unique_id = models.CharField(max_length=191, blank=True, null=True)
    type = models.ForeignKey(VendorLegalCategories,related_name='vendor_legal_type', on_delete=models.CASCADE)
    currency = models.ForeignKey(Currencies,related_name='vendor_currency', on_delete=models.CASCADE, blank=True, null=True)
    vm_status = models.IntegerField( blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)
    token = models.CharField(max_length=191, blank=True, null=True)
    skype = models.CharField(max_length=191, blank=True, null=True)
    proz_link = models.CharField(max_length=191, blank=True, null=True)
    cv_file = models.FileField(upload_to=user_directory_path, blank=True, null=True)
    native_lang = models.ForeignKey(Languages,related_name='native_lang', on_delete=models.CASCADE,blank=True, null=True)
    year_of_experience = models.DecimalField(max_digits=5,decimal_places=1 , blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)
    # memberships = models.CharField(max_length=191, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

class VendorBankDetails(models.Model):
    user = models.OneToOneField(AiUser, on_delete=models.CASCADE, blank=True, null=True)
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
    subject = models.ForeignKey(SubjectFields,related_name='vendor_subject', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    # class Meta:
    #     unique_together = ("user", "subject")

# class VendorCATsoftware(ParanoidModel):
#     user = models.ForeignKey(AiUser,related_name='vendor_software', on_delete=models.CASCADE)
#     software = models.ForeignKey(CATsoftware,related_name='vendor_software', on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
#     updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)


class VendorMemberships(ParanoidModel):
    user = models.ForeignKey(AiUser,related_name='vendor_membership', on_delete=models.CASCADE)
    membership = models.ForeignKey(VendorMemberships,related_name='vendor_membership', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    # class Meta:
    #     unique_together = ("user", "membership")

class VendorContentTypes(ParanoidModel):
    user = models.ForeignKey(AiUser,related_name='vendor_contentype', on_delete=models.CASCADE)
    contenttype = models.ForeignKey(ContentTypes,related_name='vendor_contentype', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    # class Meta:
    #     unique_together = ("user", "contenttype")

class VendorMtpeEngines(ParanoidModel):
    user = models.ForeignKey(AiUser,related_name='vendor_mtpe_engines', on_delete=models.CASCADE)
    mtpe_engines = models.ForeignKey(MtpeEngines,related_name='vendor_mtpe_engines', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    # class Meta:
    #     unique_together = ("user", "mtpe_engines")


class VendorLanguagePair(ParanoidModel):
    user = models.ForeignKey(AiUser,related_name='vendor_lang_pair', on_delete=models.CASCADE)
    source_lang=models.ForeignKey(Languages,related_name='source_lang', on_delete=models.CASCADE)
    target_lang=models.ForeignKey(Languages,related_name='target_lang', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    class Meta:
        unique_together = ("user", "source_lang","target_lang")

class VendorServiceInfo(ParanoidModel):
     lang_pair=models.ForeignKey(VendorLanguagePair,related_name='service', on_delete=models.CASCADE)
     mtpe_rate= models.DecimalField(max_digits=5,decimal_places=2 , blank=True, null=True)
     mtpe_hourly_rate=models.DecimalField(max_digits=5,decimal_places=2 , blank=True, null=True)
     mtpe_count_unit=models.ForeignKey(Billingunits,related_name='unit_type', on_delete=models.CASCADE)
     translation_file = models.FileField(upload_to=user_directory_path, blank=True, null=True)
     sample_file = models.FileField(upload_to=user_directory_path, blank=True, null=True)
     created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
     updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
     currency = models.ForeignKey(Currencies,related_name='vendorservice_currency', on_delete=models.CASCADE, blank=True, null=True)

class VendorServiceTypes(ParanoidModel):
    lang_pair=models.ForeignKey(VendorLanguagePair,related_name='servicetype', on_delete=models.CASCADE)
    services=models.ForeignKey(ServiceTypes,related_name='services', on_delete=models.CASCADE)
    unit_type=models.ForeignKey(Billingunits, on_delete=models.CASCADE , blank=True, null=True)
    unit_rate=models.DecimalField(max_digits=5,decimal_places=2 , blank=True, null=True)
    hourly_rate=models.DecimalField(max_digits=5,decimal_places=2 , blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

# class TranslationSamples(ParanoidModel):
#     lang_pair=models.ForeignKey(VendorLanguagePair, on_delete=models.CASCADE)
#     translation_file = models.FileField(upload_to=user_directory_path, blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
#     updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
#
# class MtpeSamples(ParanoidModel):
#     lang_pair=models.ForeignKey(VendorLanguagePair,on_delete=models.CASCADE)
#     sample_file = models.FileField(upload_to=user_directory_path, blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
#     updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
