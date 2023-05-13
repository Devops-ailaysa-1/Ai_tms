from django.contrib import admin

# Register your models here.
from .models import VendorsInfo,VendorLanguagePair,VendorServiceInfo,VendorServiceTypes

admin.site.register(VendorsInfo)


admin.site.register(VendorLanguagePair)
admin.site.register(VendorServiceInfo)
admin.site.register(VendorServiceTypes)