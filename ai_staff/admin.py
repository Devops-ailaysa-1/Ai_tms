from django.contrib import admin

from .models import (AiUserType, Languages,AssetUsageTypes,AilaysaSupportedMtpeEngines, ProjectRoleLevel, Spellcheckers,
                    SpellcheckerLanguages,SubscriptionPricing,Currencies,SubscriptionPricingPrices,SubscriptionFeatures,
                    CreditsAddons,CreditAddonPrice,IndianStates,StripeTaxId,JobPositions, LanguagesLocale, LanguageScripts,
                    LanguageMetaDetails, Countries,Role, SubjectFields, Billingunits, ContentTypes, ServiceTypes, VendorLegalCategories,
                    ServiceTypeunits,ProjectType,ProjectTypeDetail,MTLanguageSupport,MTLanguageLocaleVoiceSupport,AiRoles,
                    TaskRoleLevel,ModelGPTName,PromptCategories,PromptTones,PromptSubCategories,PromptStartPhrases,AiCustomize,PromptFields,ApiServiceList,
                    ApiProvider,ApiService ,ImageGeneratorResolution,DocumentType,ImageCategories,FontData,FontFamily,FontLanguage,
                    SocialMediaSize,DesignShape,Suggestion,SuggestionType,DesignShapeCategory ,DesignerOrientation,
                    Levels,Genre,BodyMatter,FrontMatter,BackMatter,)
# Register your models here.

class LanguagesAdmin(admin.ModelAdmin):
    list_display = ('language',)

class CountriesAdmin(admin.ModelAdmin):
    list_display = ('sortname','name','phonecode')

@admin.register(LanguagesLocale)
class LanguagesLocaleAdmin(admin.ModelAdmin):
   list_display = ('language','language_locale_name','locale_code')

@admin.register(StripeTaxId)
class StripeTaxIdAdmin(admin.ModelAdmin):
   list_display = ('country','tax_code','name')

@admin.register(IndianStates)
class IndianStatesAdmin(admin.ModelAdmin):
   list_display = ('state_name','state_code','tin_num')

@admin.register(SpellcheckerLanguages)
class SpellcheckerLanguagesAdmin(admin.ModelAdmin):
   list_display = ('language','spellchecker')

@admin.register(Spellcheckers)
class SpellcheckersAdmin(admin.ModelAdmin):
   list_display = ('spellchecker_name',)

@admin.register(Currencies)
class CurrenciesAdmin(admin.ModelAdmin):
   list_display = ('currency','currency_code')

@admin.register(AilaysaSupportedMtpeEngines)
class AilaysaSupportedMtpeEnginesAdmin(admin.ModelAdmin):
   list_display = ('name',)


@admin.register(SubscriptionPricing)
class SubscriptionPricingAdmin(admin.ModelAdmin):
   list_display = ('stripe_product_id','plan')

@admin.register(SubscriptionPricingPrices)
class SubscriptionPricingPricesAdmin(admin.ModelAdmin):
   list_display = ('subscriptionplan','monthly_price','montly_price_id','annual_price','annual_price_id','currency')

@admin.register(SubscriptionFeatures)
class SubscriptionPricingAdmin(admin.ModelAdmin):
   list_display = ('subscriptionplan','features','description','set_id','sequence_id')

@admin.register(ApiServiceList)
class ApiServiceListAdmin(admin.ModelAdmin):
    list_display = ("provider","service")

admin.site.register(AiUserType)
admin.site.register(Languages,LanguagesAdmin)
admin.site.register(AssetUsageTypes)
admin.site.register(ProjectType)
admin.site.register(ProjectTypeDetail)
admin.site.register(MTLanguageSupport)
admin.site.register(MTLanguageLocaleVoiceSupport)
# admin.site.register(AilaysaSupportedMtpeEngines)
# admin.site.register(SpellcheckerLanguages)
# admin.site.register(Spellcheckers)
# admin.site.register(SubscriptionPricing)
# admin.site.register(Currencies)
# admin.site.register(SubscriptionPricingPrices)
# admin.site.register(SubscriptionFeatures)
admin.site.register(CreditsAddons)
admin.site.register(CreditAddonPrice)
admin.site.register(Suggestion) 
admin.site.register(SuggestionType)
#admin.site.register(IndianStates)
# admin.site.register(StripeTaxId)
admin.site.register(JobPositions)
# admin.site.register(LanguagesLocale)
admin.site.register(LanguageScripts)
admin.site.register(LanguageMetaDetails)
admin.site.register(Levels)
admin.site.register(Genre)
admin.site.register(BodyMatter)
admin.site.register(FrontMatter)
admin.site.register(BackMatter)
# admin.site.register(Countries)
admin.site.register(Role)

admin.site.register(Countries,CountriesAdmin)

admin.site.register(SubjectFields)
admin.site.register(Billingunits)
admin.site.register(ContentTypes)
admin.site.register(ServiceTypes)
admin.site.register(VendorLegalCategories)
admin.site.register(ServiceTypeunits)
admin.site.register(AiRoles)
admin.site.register(TaskRoleLevel)
admin.site.register(ProjectRoleLevel)

admin.site.register(ApiProvider)
admin.site.register(ApiService)

admin.site.register(ModelGPTName)
admin.site.register(PromptCategories)
admin.site.register(PromptTones)
admin.site.register(PromptSubCategories)
admin.site.register(PromptStartPhrases)
admin.site.register(AiCustomize)
admin.site.register(PromptFields)
admin.site.register(ImageGeneratorResolution)
admin.site.register(DocumentType)
admin.site.register(FontData)
admin.site.register(FontFamily)
admin.site.register(FontLanguage)
admin.site.register(ImageCategories)
admin.site.register(SocialMediaSize)
admin.site.register(DesignShape)
admin.site.register(DesignShapeCategory) 
admin.site.register(DesignerOrientation)
