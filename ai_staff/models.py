from django import db
from django.db.models.fields import NullBooleanField
from django.utils import timezone
from django.db import models
from django.db.models.query import QuerySet
from django.apps import apps



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

    def __str__(self):
        return self.name

class ContentTypes(ParanoidModel):
    name = models.CharField(max_length=191)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    is_active=models.BooleanField(default=True)

    class Meta:
        db_table = 'content_types'
        verbose_name_plural = "Content_types"

    def __str__(self):
        return self.name

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

    def __str__(self):
        return self.use_type

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
    ime = models.BooleanField(null=True, blank=True, default=False)

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
    set_id = models.IntegerField()
    sequence_id = models.IntegerField()
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
    expiry =  models.CharField(max_length=200,null=True,blank=True)
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


class SuggestionType(ParanoidModel):
    type_of_suggestion = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)


class Suggestion(ParanoidModel):
    suggestion = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    
class ModelGPTName(models.Model):
    model_name = models.CharField(max_length=40, null=True, blank=True)
    model_code = models.CharField(max_length=40, null=True, blank=True)
    model_ability =models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self) -> str:
        return self.model_name
    
class PromptCategories(models.Model):
    category = models.CharField(max_length=1000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    
    def __str__(self) -> str:
        return self.category 


class PromptTones(models.Model):
    tone = models.CharField(max_length=1000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    
    def __str__(self) -> str:
        return self.tone 

class PromptSubCategories(models.Model):
    category = models.ForeignKey(PromptCategories,related_name='prompt_category',on_delete = models.CASCADE,blank=True, null=True)
    sub_category = models.CharField(max_length=1000, null=True, blank=True)
    # fields = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    
    def __str__(self) -> str:
        return self.sub_category    
    
class PromptFields(models.Model):
    prompt_sub_categories = models.ForeignKey(PromptSubCategories,related_name='sub_category_fields',
                                 on_delete = models.CASCADE,blank=True, null=True)
    fields = models.CharField(max_length=100, null=True, blank=True)
    # optional_field =  models.BooleanField()
    help_text = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    
    def __str__(self) -> str:
        return self.fields 


class ImageGeneratorResolution(models.Model):
    image_resolution = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    
    def __str__(self) -> str:
        return self.image_resolution 
 
class PromptStartPhrases(models.Model):
    sub_category = models.ForeignKey(PromptSubCategories,related_name='prompt_sub_category',
                                 on_delete = models.CASCADE,blank=True, null=True)
    start_phrase =  models.TextField(null=True, blank=True)   
    punctuation = models.CharField(max_length=5 , null=True,blank=True)
    max_token = models.CharField(max_length=10 , null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    
    def __str__(self) -> str:
        return self.start_phrase

class DocumentType(models.Model):
    type = models.CharField(max_length=30, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    def __str__(self) -> str:
        return  self.type

 

class AiCustomize(models.Model):
    # user = models.ForeignKey(AiUser, on_delete=models.CASCADE)
    customize = models.CharField(max_length =200, null=True, blank=True)  
    prompt =   models.CharField(max_length =200, null=True, blank=True)
    instruct = models.CharField(max_length =300, null=True, blank=True)
    grouping = models.CharField(max_length =200, null=True, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    
    def __str__(self) -> str:
        return self.customize
    

class Role(ParanoidModel):
    name = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    def __str__(self):
        return self.name

class OldVendorPasswords(models.Model):
    email = models.EmailField(max_length=100, null=True, blank=True)
    password = models.CharField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.email

class CurrencyBasedOnCountry(models.Model):
    country = models.ForeignKey(Countries,related_name='user_country',
        on_delete=models.CASCADE,blank=True, null=True)
    currency = models.ForeignKey(Currencies,related_name='user_currency',
        on_delete=models.CASCADE,blank=True, null=True)


class ProjectType(models.Model):
    type = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    def __str__(self):
        return self.type

class ProjectTypeDetail(models.Model):
    projecttype = models.ForeignKey(ProjectType,related_name='project_type_detail',on_delete=models.CASCADE,blank=True, null=True)
    sub_category_name = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    def __str__(self):
        return self.sub_category_name


class MTLanguageSupport(models.Model):
    language = models.ForeignKey(Languages,related_name='supported_lang', on_delete=models.CASCADE)
    mtpe_engines = models.ForeignKey(AilaysaSupportedMtpeEngines,related_name='supported_mt',on_delete=models.CASCADE)
    speech_to_text = models.BooleanField(default=False)
    text_to_speech = models.BooleanField(default=False)
    translate = models.BooleanField(default=True)
    # has_female = models.BooleanField(default=False)
    # has_male = models.BooleanField(default=False)


class MTLanguageLocaleVoiceSupport(models.Model):
    GENDER =(('MALE','MALE'),('FEMALE','FEMALE'))
    language = models.ForeignKey(Languages,related_name='supported_language', on_delete=models.CASCADE)
    language_locale = models.ForeignKey(LanguagesLocale,related_name='supported_locale', on_delete=models.CASCADE)
    mtpe_engines = models.ForeignKey(AilaysaSupportedMtpeEngines,related_name='support_mt',on_delete=models.CASCADE)
    # has_female = models.BooleanField(default=False)
    # has_male = models.BooleanField(default=False)
    gender=models.CharField(max_length=50,choices=GENDER)
    voice_name = models.CharField(max_length=300, null=True, blank=True)
    voice_type = models.CharField(max_length=100, null=True, blank=True)#wavenet,standard,neural


class TranscribeSupportedPunctuation(models.Model):
    language_locale = models.ForeignKey(LanguagesLocale,related_name='punctuation_locale', on_delete=models.CASCADE)
    mtpe_engines = models.ForeignKey(AilaysaSupportedMtpeEngines,related_name='punc_supported_mt',on_delete=models.CASCADE)

# class MTLanguageLocaleVoiceSupport(models.Model):
#     language = models.ForeignKey(Languages,related_name='supported_language', on_delete=models.CASCADE)
#     language_locale = models.ForeignKey(LanguagesLocale,related_name='supported_locale', on_delete=models.CASCADE)
#     mtpe_engines = models.ForeignKey(AilaysaSupportedMtpeEngines,related_name='support_mt',on_delete=models.CASCADE)
#     has_female = models.BooleanField(default=False)
#     has_male = models.BooleanField(default=False)
#     voice_name = models.CharField(max_length=300, null=True, blank=True)
#     voice_type = models.CharField(max_length=100, null=True, blank=True)#wavenet,standard,neural


class AiRoles(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    def __str__(self):
        return self.name

class TaskRoleLevel(models.Model):
    # from ai_workspace.models import Steps
    role = models.ForeignKey(AiRoles,related_name='task_roles_level',
        on_delete=models.CASCADE,blank=True, null=True)
    step = models.CharField(max_length=300)

class ProjectRoleLevel(models.Model):
    role = models.ForeignKey(AiRoles,related_name='project_roles_level',
        on_delete=models.CASCADE,blank=True, null=True)

class TeamRoleLevel(models.Model):
    role = models.ForeignKey(AiRoles,related_name='team_roles_level',
        on_delete=models.CASCADE,blank=True, null=True)

class OrganizationRoleLevel(models.Model):
    role = models.ForeignKey(AiRoles,related_name='org_roles_level',
        on_delete=models.CASCADE,blank=True, null=True)

class ApiProvider(models.Model):
    name = models.CharField(max_length=300)

    def __str__(self):
        return self.name

class ApiService(models.Model):
    name = models.CharField(max_length=500)

    def __str__(self):
        return self.name

class ApiServiceList(models.Model):
    provider = models.ForeignKey(ApiProvider,related_name ='provider_list', on_delete=models.CASCADE)
    service = models.ForeignKey(ApiService,related_name = 'service_list', on_delete=models.CASCADE)


class FontLanguage(models.Model):
    name = models.CharField(max_length=100 ,null=True,blank=True)
    language  =  models.CharField(max_length=100 ,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)


class FontCatagoryList(models.Model):
    catagory_name=models.CharField(max_length=200)
    def __str__(self) -> str:
        return self.catagory_name

class FontFamily(models.Model):
    catagory=models.ForeignKey(FontCatagoryList,on_delete=models.CASCADE,related_name='font_catagory_family')
    font_family_name = models.CharField(max_length=100 ,null=True , blank=True)
    name = models.CharField(max_length=100,null=True , blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)


class FontData(models.Model):
    font_lang = models.ForeignKey(FontLanguage,related_name='font_data_language', on_delete=models.CASCADE)
    font_family = models.ForeignKey(FontFamily,related_name='font_data_family', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)

 


class SocialMediaSize(models.Model):
    social_media_name=models.CharField(max_length=200,blank=True ,null=True)
    width=models.CharField(max_length=200,blank=True ,null=True)
    height=models.CharField(max_length=200,blank=True ,null=True)
    src=models.FileField(upload_to='socialmediasize',blank=True ,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    

    def __str__(self) -> str:
        return self.social_media_name
    
class ImageCategories(models.Model):
    category= models.CharField(max_length=50,blank=True ,null=True)

    def __str__(self):
        return self.category


class DesignShape(models.Model):
    types = (
        (1, "Outline"),
        (2, "Filled"),
        (3, "Line"))
    shape_name=models.CharField(max_length=200,blank=True ,null=True)
    shape=models.FileField(upload_to='design_shape',blank=True ,null=True)
    types=models.CharField(max_length=300,null=True,blank=True,choices=types)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    def __str__(self) -> str:
        return self.shape_name

 
