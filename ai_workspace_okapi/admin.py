from django.contrib import admin
from .models import MT_Engine,TranslationStatus,Segment,SelflearningAsset
# from reversion.admin import VersionAdmin

# Register your models here.
admin.site.register(MT_Engine)
admin.site.register(TranslationStatus)

admin.site.register(SelflearningAsset)

# @admin.register(Segment)
# class SegmentModelAdmin(VersionAdmin):
#     pass
