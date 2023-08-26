from django.contrib import admin

# Register your models here.
from ai_imagetranslation.models import (CustomImageGenerationStyle ,ImageStyleCategories,ImageModificationTechnique,GeneralPromptList,
                                        ImageStyleSD,Color,Lighting ,Composition,AspectRatio,SDImageResolution,StableDiffusionVersion)



admin.site.register(CustomImageGenerationStyle)
admin.site.register(ImageStyleCategories)
admin.site.register(ImageModificationTechnique)
admin.site.register(GeneralPromptList)
admin.site.register(ImageStyleSD)
admin.site.register(Color)
admin.site.register(Lighting)
admin.site.register(Composition)
admin.site.register(AspectRatio)
admin.site.register(SDImageResolution)
admin.site.register(StableDiffusionVersion)