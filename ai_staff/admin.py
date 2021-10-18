from django.contrib import admin

from .models import (AiUserType, Languages,AssetUsageTypes,AilaysaSupportedMtpeEngines, Spellcheckers,
                    SpellcheckerLanguages,SubscriptionPricing,Currencies,SubscriptionPricingPrices,SubscriptionFeatures,
                    CreditsAddons,CreditAddonPrice,IndianStates,StripeTaxId,JobPositions, LanguagesLocale)
# Register your models here.

admin.site.register(AiUserType)
admin.site.register(Languages)
admin.site.register(AssetUsageTypes)
admin.site.register(AilaysaSupportedMtpeEngines)
admin.site.register(SpellcheckerLanguages)
admin.site.register(Spellcheckers)
admin.site.register(SubscriptionPricing)
admin.site.register(Currencies)
admin.site.register(SubscriptionPricingPrices)
admin.site.register(SubscriptionFeatures)
admin.site.register(CreditsAddons)
admin.site.register(CreditAddonPrice)
admin.site.register(IndianStates)
admin.site.register(StripeTaxId)
admin.site.register(JobPositions)
admin.site.register(LanguagesLocale)
