from django.contrib import admin
from .models import MT_Engine,TranslationStatus,Segment,SelflearningAsset,SegmentDiff
# from reversion.admin import VersionAdmin

# Register your models here.
admin.site.register(MT_Engine)
admin.site.register(TranslationStatus)

admin.site.register(SelflearningAsset)
admin.site.register(SegmentDiff)
# @admin.register(Segment)
# class SegmentModelAdmin(VersionAdmin):
#     pass
