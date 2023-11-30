from django.contrib import admin

# Register your models here.
from .models import VendorsInfo,VendorLanguagePair
from ai_auth.admin import staff_admin_site

admin.site.register(VendorsInfo)


@admin.register(VendorLanguagePair, site=staff_admin_site)
class VendorLangpairAdmin(admin.ModelAdmin):
    list_display = ("user","source_lang","target_lang")
    list_filter = ("user",)