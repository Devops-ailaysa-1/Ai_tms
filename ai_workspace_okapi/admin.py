from django.contrib import admin
from .models import MT_Engine,TranslationStatus,Segment,SelflearningAsset,Document,Segment,MT_RawTranslation
# from reversion.admin import VersionAdmin

# Register your models here.
admin.site.register(MT_Engine)
admin.site.register(TranslationStatus)

admin.site.register(Document)

admin.site.register(MT_RawTranslation)
admin.site.register(Segment)

# @admin.register(Segment)
# class SegmentModelAdmin(VersionAdmin):
#     pass
class self_learnig_list(admin.ModelAdmin):
    list_display=['source_word',"edited_word","occurance","target_language"]




admin.site.register(SelflearningAsset,self_learnig_list)

