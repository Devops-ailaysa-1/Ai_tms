from django.contrib import admin
from .models import AiUser, UserAttribute,TempPricingPreference,CreditPack,UserCredits
from django.contrib.auth.models import Permission

# Register your models here.
admin.site.register(AiUser)
admin.site.register(UserAttribute)
admin.site.register(Permission)
admin.site.register(TempPricingPreference)
admin.site.register(CreditPack)
admin.site.register(UserCredits)
