from django.contrib import admin

# Register your models here.
from ai_imagetranslation.models import CustomImageGenerationStyle ,ImageStyleCategories,ImageModificationTechnique
admin.site.register(CustomImageGenerationStyle)
admin.site.register(ImageStyleCategories)
admin.site.register(ImageModificationTechnique)
