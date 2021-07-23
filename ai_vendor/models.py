from ai_auth.models import AiUser, user_directory_path
from ai_staff.models import (Billingunits, CATSoftwares, ContentTypes,
                             Currencies, Languages, MtpeEngines, ParanoidModel,
                             ServiceTypes, SubjectFields,
                             VendorLegalCategories, VendorMemberships)
from django.db import models
from django.db.models.constraints import UniqueConstraint
from ai_auth.models import AiUser,user_directory_path
from ai_staff.models import ContentTypes, Currencies, ParanoidModel, SubjectFields,Languages, VendorLegalCategories,VendorMemberships,MtpeEngines,Billingunits,ServiceTypes,CATSoftwares,ServiceTypeunits

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
    cv_file = models.FileField(upload_to=user_directory_path, blank=True, null=True)
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

    # class Meta:
    #     unique_together = ("user", "source_lang","target_lang")

class VendorServiceInfo(ParanoidModel):
     lang_pair=models.ForeignKey(VendorLanguagePair,related_name='service', on_delete=models.CASCADE)
     mtpe_rate= models.DecimalField(max_digits=5,decimal_places=2 , blank=True, null=True)
     mtpe_hourly_rate=models.DecimalField(max_digits=5,decimal_places=2 , blank=True, null=True)
     mtpe_count_unit=models.ForeignKey(ServiceTypeunits,related_name='unit_type', on_delete=models.CASCADE)
     created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
     updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
     # currency = models.ForeignKey(Currencies,related_name='vendorservice_currency', on_delete=models.CASCADE, blank=True, null=True)

class VendorServiceTypes(ParanoidModel):
    lang_pair=models.ForeignKey(VendorLanguagePair,related_name='servicetype', on_delete=models.CASCADE)
    services=models.ForeignKey(ServiceTypes,related_name='services', on_delete=models.CASCADE)
    unit_type=models.ForeignKey(ServiceTypeunits, on_delete=models.CASCADE , blank=True, null=True)
    unit_rate=models.DecimalField(max_digits=5,decimal_places=2 , blank=True, null=True)
    hourly_rate=models.DecimalField(max_digits=5,decimal_places=2 , blank=True, null=True)
    minute_rate=models.DecimalField(max_digits=5,decimal_places=2,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

class TranslationSamples(ParanoidModel):
    lang_pair=models.ForeignKey(VendorLanguagePair,related_name='translationfile', on_delete=models.CASCADE)
    translation_file = models.FileField(upload_to=user_directory_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    # deleted_at = models.DateTimeField(auto_now=True,blank=True, null=True)


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT / user_<id>/<filename>
    return '{0}/{1}/{2}'.format(lang_pair.instance.user.uid, "TranslationSamples",filename)

class MtpeSamples(ParanoidModel):
    lang_pair=models.ForeignKey(VendorLanguagePair,related_name='mtpesamples',on_delete=models.CASCADE)
    sample_file = models.FileField(upload_to=user_directory_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    # deleted_at = models.DateTimeField(auto_now=True,blank=True, null=True)
