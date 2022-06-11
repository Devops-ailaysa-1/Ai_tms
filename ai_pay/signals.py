from django.db import transaction
from ai_pay.models import POAssignment,POTaskDetails,PurchaseOrder
import logging
from django.dispatch import receiver,Signal

# generate_client_po= Signal()

# def generate_client_po(sender, instance, created, *args, **kwargs):
#     print("inside generate_client_po signal")
#     try:
#        with transaction.atomic():
#         assign=POAssignment.objects.get_or_create(assignment_id=instance.assignment_id)[0]
#         insert={'task_id':instance.task.id,'assignment':assign,'project_name':instance.task.job.project.project_name,
#                 'word_count':instance.total_word_count,'price':instance.mtpe_rate,
#                 'unit_type':instance.mtpe_count_unit,'source_language':instance.task.job.source_language,'target_language':instance.task.job.target_language}
#         po_task=POTaskDetails.objects.create(**insert)
#         insert2={'client':instance.assigned_by,'seller':instance.task.assign_to,
#                 'assignment':assign,'currency':instance.currency,
#                 'po_status':'issued'}
#         po=PurchaseOrder.objects.create(**insert2)
#     except:
#        print("PO Not generated")
#        logging.error("PO Generations Failed For assignment:{0}".format(instance.assignment_id))
