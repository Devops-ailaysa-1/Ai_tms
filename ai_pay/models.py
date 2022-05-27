import random,string
from django.db import models
from ai_auth.models import AiUser
from ai_staff.models import Billingunits, Currencies, Languages, ServiceTypeunits


class POAssignment(models.Model):
    #task_assign =  models.CharField(max_length=191, blank=True, null=True)
    assignment_id =  models.CharField(max_length=191, blank=True, null=True)

class POTaskDetails(models.Model):
    task_id = models.CharField(max_length=191)
    assignment = models.ForeignKey(POAssignment,related_name='assignment_po',on_delete=models.PROTECT)
    #step = models.ForeignKey(Steps,on_delete=models.PROTECT, null=False, blank=False,
    #        related_name="po_step")
    project_name = models.CharField(max_length=223, blank=True, null=True)
    word_count=models.IntegerField(null=True,blank=True)
    char_count=models.IntegerField(null=True,blank=True)
    price =models.DecimalField(max_digits=12, decimal_places=2)
    unit_type = models.ForeignKey(ServiceTypeunits,related_name="po_unit",on_delete=models.PROTECT)

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

class POLangpair(models.Model):
    task_po=models.ForeignKey(POTaskDetails,related_name='task_po_langpair',on_delete=models.CASCADE)
    source_language = models.ForeignKey(Languages, null=False, blank=False, on_delete=models.PROTECT,\
        related_name="po_source_lang")
    target_language = models.ForeignKey(Languages, null=False, blank=False, on_delete=models.PROTECT,\
        related_name="po_target_lang")



def po_dir_path(instance, filename):
    return '{0}/{1}/{2}/{3}'.format(instance.user.uid, "Reports","PO",filename)

class PurchaseOrder(models.Model):
    status =(
    ("draft","draft"),
    ("issued", "issued"),
    ("open","open"),
    ("closed","closed"),
    ("void","void")
    )

    
    def generate_po_id():
        return "PO-{0}".format(id_generator())

    poid=models.CharField(max_length=50,default=generate_po_id,unique=True)
    client=models.ForeignKey(AiUser,related_name='user_client',on_delete=models.PROTECT)
    seller=models.ForeignKey(AiUser,related_name='user_seller',on_delete=models.PROTECT)
    assignment = models.ForeignKey(POAssignment,related_name='user_seller',on_delete=models.PROTECT)  
    currency = models.ForeignKey(Currencies,related_name='po_currency', on_delete=models.PROTECT,blank=True, null=True)
    po_status =models.CharField(max_length=50,choices=status,default='draft')
    po_file = models.FileField(upload_to=po_dir_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)




class AilaysaGeneratedInvoice(models.Model):
    '''Invoice generate by Ailaysa'''
    STATUS =(
    ("draft","draft"),
    ("paid", "paid"),
    ("open","open"),
    ("void","void")
    )
    def generate_invo_id():
        return "{0}".format(id_generator())
    invo_id=models.CharField(max_length=50,default=generate_invo_id,unique=True)
    invo_status=models.CharField(max_length=50,choices=STATUS)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

class AiInvoicePO(models.Model):
    invoice=models.ForeignKey(AilaysaGeneratedInvoice,related_name='ai_invo_po',on_delete=models.CASCADE)
    po=models.ForeignKey(PurchaseOrder,related_name='ai_po',on_delete=models.CASCADE)



