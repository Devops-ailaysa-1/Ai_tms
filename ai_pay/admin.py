from django.contrib import admin
from ai_pay.models import PurchaseOrder,POTaskDetails,POAssignment,AilaysaGeneratedInvoice,AiInvoicePO

# Register your models here.



admin.site.register(POAssignment)
admin.site.register(AilaysaGeneratedInvoice)
admin.site.register(AiInvoicePO)

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('poid','client','seller','assignment_id','get_curreny')

    def get_curreny(self, obj):
        return obj.currency.currency_code


@admin.register(POTaskDetails)
class POTaskDetailsAdmin(admin.ModelAdmin):
    list_display = ('task_id','assignment','source_language','target_language',
                'project_name','unit_price','unit_type','word_count','char_count','total_amount')
