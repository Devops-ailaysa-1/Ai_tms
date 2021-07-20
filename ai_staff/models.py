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
    native_script = models.CharField(max_length=200, null=True, blank=True)
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
