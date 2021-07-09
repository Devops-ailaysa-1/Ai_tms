from django.db import models
from django.db.models.constraints import UniqueConstraint
from ai_auth.models import AiUser,user_directory_path
from ai_staff.models import ContentTypes, Currencies, ParanoidManager, SubjectFields,Languages, VendorLegalCategories,VendorMemberships

# Create your models here.
class VendorsInfo(models.Model):
    user = models.OneToOneField(AiUser, on_delete=models.CASCADE)
    vendor_unique_id = models.CharField(max_length=191, blank=True, null=True)
    type = models.ForeignKey(VendorLegalCategories,related_name='vendor_legal_type', on_delete=models.CASCADE)
    currency = models.ForeignKey(Currencies,related_name='vendor_currency', on_delete=models.CASCADE)
    vm_status = models.IntegerField(blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)
    token = models.CharField(max_length=191, blank=True, null=True)
    skype = models.CharField(max_length=191, blank=True, null=True)
    proz_link = models.CharField(max_length=191, blank=True, null=True)
    cv_file = models.FileField(upload_to=user_directory_path, blank=True, null=True)
    native_lang = models.ForeignKey(Languages,related_name='native_lang', on_delete=models.CASCADE)
    year_of_experience = models.DecimalField(max_length=5,decimal_places=1 , blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True)
    # memberships = models.CharField(max_length=191, blank=True, null=True)
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


class VendorSubjectFields(ParanoidManager):
    user = models.ForeignKey(AiUser,related_name='vendor_subject', on_delete=models.CASCADE)
    subject = models.ForeignKey(SubjectFields,related_name='vendor_subject', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    class Meta:
        unique_together = ("user", "subject")

class VendorMemberships(ParanoidManager):
    user = models.ForeignKey(AiUser,related_name='vendor_membership', on_delete=models.CASCADE)
    membership = models.ForeignKey(VendorMemberships,related_name='vendor_membership', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    class Meta:
        unique_together = ("user", "membership")

class VendorContentTypes(ParanoidManager):
    user = models.ForeignKey(AiUser,related_name='vendor_contentype', on_delete=models.CASCADE)
    contenttype = models.ForeignKey(ContentTypes,related_name='vendor_contentype', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    class Meta:
        unique_together = ("user", "contenttype")



