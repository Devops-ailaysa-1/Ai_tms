from django.db import transaction
# from ai_pay.models import POTaskDetails
import logging
from django.dispatch import receiver,Signal
# from ai_pay.models import POTaskDetails
from django.db.models.signals import post_save


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
update_po_status= Signal()

@receiver(update_po_status)
def change_po_status(sender, instance, created, *args, **kwargs):
    from ai_pay.models import POTaskDetails
    from ai_pay.api_views import po_generate_pdf
    if instance.po:
        po_tasks = POTaskDetails.objects.filter(assignment=instance.assignment,po=instance.po)
        po_accepted = po_tasks.filter(tsk_accepted=True)
        if po_tasks.count() == po_accepted.count():
            po =po_accepted.last().po
            po.po_status = "open"
            po.save() 
            po_generate_pdf(po)
            # print("po status",po.po_status)      
    else:
        print(f"instance po is null {instance.id}")


# change_po_file= Signal()

# @receiver(change_po_file)
# def update_po_file(sender, instance, created, *args, **kwargs):
#     from ai_pay.api_views import po_generate_pdf
#     po = instance.po
#     print("inside po file change_po_file")
#     if not created:
#         print("inside po file change_po_file if create")
#         po_generate_pdf(po)


create_po_file= Signal()

@receiver(create_po_file)
def _create_po_file(sender, instance, created, *args, **kwargs):
    from ai_pay.api_views import po_generate_pdf
    if instance.po_file == None:
        po_generate_pdf(instance)