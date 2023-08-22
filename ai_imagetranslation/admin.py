from django.contrib import admin

# Register your models here.
from ai_imagetranslation.models import CustomImageGenerationStyle ,ImageStyleCategories,ImageModificationTechnique,GeneralPromptList,ImageStyleSD
admin.site.register(CustomImageGenerationStyle)
admin.site.register(ImageStyleCategories)
admin.site.register(ImageModificationTechnique)
admin.site.register(GeneralPromptList)

admin.site.register(ImageStyleSD)

