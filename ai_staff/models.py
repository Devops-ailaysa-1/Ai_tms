from django import db
from django.utils import timezone
from django.db import models
from django.db.models.query import QuerySet

# Create your models here.

class ParanoidQuerySet(QuerySet):

    def delete(self):
        for obj in self:
            obj.deleted_at=timezone.now()
            obj.save()


class ParanoidManager(models.Manager):

    def get_queryset(self):
        return ParanoidQuerySet(self.model, using=self._db).filter(
            deleted_at__isnull=True)


class ParanoidModel(models.Model):
    class Meta:
        abstract = True

    deleted_at = models.DateTimeField(null=True, blank=True)
    objects = ParanoidManager()
    original_objects = models.Manager()

    def delete(self):
        self.deleted_at=timezone.now()
        self.save()

    def undelete(self):
        self.deleted_at=None
        self.save()


### SYSTEM VALUES TABLES ###

class SubjectFields(ParanoidModel):
    name = models.CharField(max_length=191)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    #deleted_at = models.DateTimeField(blank=True, null=True)
    is_active=models.BooleanField(default=True)

    class Meta:
        db_table = 'subject_fields'


class Currencies(ParanoidModel):
    currency = models.CharField(max_length=191)
    currency_code = models.CharField(max_length=191)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    #deleted_at = models.DateTimeField(blank=True, null=True)
    is_active=models.BooleanField(default=True)

    class Meta:
        db_table = 'currencies'



class Countries(ParanoidModel):
    sortname = models.CharField(max_length=191)
    name = models.CharField(max_length=191)
    phonecode = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    #deleted_at = models.DateTimeField(blank=True, null=True)
    is_active=models.BooleanField(default=True)

    class Meta:
        db_table = 'countries'


class ContentTypes(ParanoidModel):
    name = models.CharField(max_length=191)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    is_active=models.BooleanField(default=True)

    class Meta:
        db_table = 'content_types'

class Languages(ParanoidModel):
    #lang_code = models.CharField(max_length=191)
    language = models.CharField(max_length=191)
    #native_script = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    #deleted_at = models.DateTimeField(blank=True, null=True)
    #is_active=models.BooleanField(default=True)

    def __str__(self):
        return self.language

    __repr__ = __str__

    class Meta:
        db_table = 'languages'

class LanguagesLocale(ParanoidModel):
    language = models.ForeignKey(Languages,related_name='locale', on_delete=models.CASCADE)
    language_locale_name=models.CharField(max_length=191, blank=True, null=True)
    locale_code = models.CharField(max_length=191, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    #deleted_at = models.DateTimeField(blank=True, null=True)
    is_active=models.BooleanField(default=True)

    class Meta:
        db_table = 'languages_locale'


class ServiceTypes(ParanoidModel):
    name = models.CharField(max_length=191)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    #deleted_at = models.DateTimeField(blank=True, null=True)
    is_active=models.BooleanField(default=True)

    class Meta:
        db_table = 'service_types'

class MtpeEngines(ParanoidModel):
    name = models.CharField(max_length=191)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    #deleted_at = models.DateTimeField(blank=True, null=True)
    is_active=models.BooleanField(default=True)

    class Meta:
        db_table = 'mtpe_engines'

class SupportFiles(ParanoidModel):
    format = models.CharField(max_length=191)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    #deleted_at = models.DateTimeField(blank=True, null=True)
    is_active=models.BooleanField(default=True)

    class Meta:
        db_table = 'support_files'


class Timezones(ParanoidModel):
    timezoneid = models.CharField(max_length=191)
    name = models.CharField(max_length=191)
    utc_offset = models.CharField(max_length=191)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    #deleted_at = models.DateTimeField(blank=True, null=True)
    is_active=models.BooleanField(default=True)

    class Meta:
        db_table = 'timezones'

class Billingunits(ParanoidModel):
    unit =models.CharField(max_length=191)
    #unit_code= models.CharField(max_length=191, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    #deleted_at = models.DateTimeField(blank=True, null=True)
    is_active=models.BooleanField(default=True)
    class Meta:
        db_table = 'billing_units'

class ServiceTypeunits(ParanoidModel):
    unit =models.CharField(max_length=191)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    is_active=models.BooleanField(default=True)
    class Meta:
        db_table = 'service_type_units'


class AiUserType(models.Model):
    type =models.CharField(max_length=191)
    #unit_code= models.CharField(max_length=191, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    #deleted_at = models.DateTimeField(blank=True, null=True))

    class Meta:
        db_table = 'ai_usertype'


class VendorMemberships(ParanoidModel):
    membership =models.CharField(max_length=191)
    #unit_code= models.CharField(max_length=191, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    #deleted_at = models.DateTimeField(blank=True, null=True))
    is_active=models.BooleanField(default=True)
    class Meta:
        db_table = 'vendor_membership'

class VendorLegalCategories(ParanoidModel):
    name =models.CharField(max_length=191)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    is_active=models.BooleanField(default=True)
    class Meta:
        db_table = 'vendor_legal_categories'

class CATSoftwares(ParanoidModel):
    name =models.CharField(max_length=191)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    is_active=models.BooleanField(default=True)
    class Meta:
        db_table = 'cat_softwares'


class AilaysaSupportedMtpeEngines(ParanoidModel):
    name = models.CharField(max_length=191)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    #deleted_at = models.DateTimeField(blank=True, null=True)
    is_active=models.BooleanField(default=True)

    class Meta:
        db_table = 'ailaysa_mtpe_engines'


class AssetUsageTypes(ParanoidModel):
    use_type = models.CharField(max_length=190)
    type_path = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    #deleted_at = models.DateTimeField(blank=True, null=True)
    is_active=models.BooleanField(default=True)

    class Meta:
        db_table = 'asset_usage_types'

class Spellcheckers(ParanoidModel):
    spellchecker_name = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    is_active=models.BooleanField(default=True)

    class Meta:
        db_table = 'spellcheckers'

class SpellcheckerLanguages(ParanoidModel):
    language = models.ForeignKey(Languages, related_name="spellcheck_language", on_delete=models.CASCADE)
    spellchecker = models.ForeignKey(Spellcheckers, related_name='spellcheck_name', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    is_active=models.BooleanField(default=True)
    class Meta:
        db_table = 'spellchecker_languages'

class LanguageScripts(models.Model):
    # Currently scripts listed are used for filtering 
    # IME icon will be displayed for languages that are not available in this model
    script_name = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        db_table = "language_scripts"

    def __str__(self):
        return self.script_name

class LanguageMetaDetails(models.Model):
    language = models.ForeignKey(Languages, related_name="language_meta_details", on_delete=models.CASCADE, null=True, blank=True)
    lang_name_in_script = models.CharField(max_length=200, null=True, blank=True)
    script = models.ForeignKey(LanguageScripts, related_name="language_meta_details", on_delete=models.SET_NULL, null=True, blank=True)
    # ner = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return self.language.language
    
    class Meta:
        db_table = "language_meta_details"

class SupportType(ParanoidModel):
    support_type = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

class SubscriptionPricing(ParanoidModel):
    stripe_product_id =  models.CharField(max_length=200,blank=True, null=True)
    plan = models.CharField(max_length=100, null=True, blank=True)
    #currency = models.ForeignKey(Currencies,on_delete=models.CASCADE,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

class SubscriptionPricingPrices(ParanoidModel):
    subscriptionplan = models.ForeignKey(SubscriptionPricing,on_delete = models.CASCADE,related_name='subscription_price')
    monthly_price = models.IntegerField(blank=True, null=True)
    montly_price_id=models.CharField(max_length=200,null=True,blank=True)
    annual_price = models.IntegerField(blank=True, null=True)
    annual_price_id=models.CharField(max_length=200,null=True,blank=True)
    currency = models.ForeignKey(Currencies,on_delete=models.CASCADE,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

class SubscriptionFeatures(ParanoidModel):
    features = models.TextField(max_length=1000)
    description = models.TextField(max_length=1000,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    subscriptionplan = models.ForeignKey(SubscriptionPricing,on_delete = models.CASCADE,related_name='subscription_feature')

class CreditsAddons(ParanoidModel):
    stripe_product_id = models.CharField(max_length=200,null=True,blank=True)
    pack = models.CharField(max_length=200,null=True,blank=True)
    description = models.TextField(max_length=1000, blank=True, null=True)
    credits = models.IntegerField(null=True,blank=True)
    discount = models.CharField(max_length=100,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

class CreditAddonPrice(ParanoidModel):
    pack = models.ForeignKey(CreditsAddons,on_delete = models.CASCADE,related_name='credit_addon_price')
    price =  models.IntegerField(blank=True, null=True)
    currency = models.ForeignKey(Currencies,on_delete=models.CASCADE)
    stripe_price_id = models.CharField(max_length=200,null=True,blank=True)

class IndianStates(ParanoidModel):
    state_name = models.CharField(max_length=200,null=True,blank=True)
    state_code=models.CharField(max_length=200,null=True,blank=True)
    tin_num= models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    is_active=models.BooleanField(default=True)
    class Meta:
        db_table = 'indian_states'


class AilaysaFinancialValues(ParanoidModel):
    state = models.ForeignKey(IndianStates,on_delete = models.CASCADE,related_name='ai_fin_values_states')
    finance_address = models.CharField(max_length=200,null=True,blank=True)
    finance_email = models.EmailField()
    finance_phone =models.IntegerField()
    finance_gst = models.CharField(max_length=200,null=True,blank=True)
    finance_pan =models.CharField(max_length=200,null=True,blank=True)
    langscape_account_name = models.CharField(max_length=200,null=True,blank=True)
    langscape_account_number = models.CharField(max_length=200,null=True,blank=True)
    bank_branch = models.CharField(max_length=200,null=True,blank=True)
    ifsc_code = models.CharField(max_length=200,null=True,blank=True)
    swift_code = models.CharField(max_length=200,null=True,blank=True)
    paypal_id = models.CharField(max_length=200,null=True,blank=True)
    payoneer_id = models.CharField(max_length=200,null=True,blank=True)
    bank_name = models.CharField(max_length=200,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    class Meta:
        db_table = 'ailaysa_finance_values'

class IndianGSTSACList(ParanoidModel):
    sac_code = models.CharField(max_length=200,null=True,blank=True)
    business_category = models.CharField(max_length=200,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    class Meta:
        db_table = 'indian_gst_sac_list'


class StripeTaxId(ParanoidModel):
    country = models.ForeignKey(Countries,on_delete=models.CASCADE,blank=True,null=True,related_name='stripe_tax_coun')
    tax_code = models.CharField(max_length=200,null=True,blank=True)
    name = models.CharField(max_length=200,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    class Meta:
        db_table = 'stripe_tax_id'


class JobPositions(ParanoidModel):
    job_name = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)


class SupportTopics(ParanoidModel):
    topic = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
