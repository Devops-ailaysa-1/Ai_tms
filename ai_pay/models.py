import random,string
from django.db import models
from ai_auth.models import AiUser
from ai_staff.models import Billingunits, Currencies, Languages, ServiceTypeunits,Countries
from ai_workspace.models import Steps
from ai_pay.signals import change_po_status,_create_po_file
from django.db.models.signals import post_save, pre_save

class POAssignment(models.Model):
    #task_assign =  models.CharField(max_length=191, blank=True, null=True)
    assignment_id =  models.CharField(max_length=191, blank=True, null=True)
    step = models.ForeignKey(Steps,on_delete=models.CASCADE, null=False, blank=False,
            related_name="po_assignment_step")

    def __unicode__(self):
        return self.assignment_id
    def __str__(self):
        return self.assignment_id



def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

# class POLangpair(models.Model):
#     task_po=models.ForeignKey(POTaskDetails,related_name='task_po_langpair',on_delete=models.CASCADE)
#     source_language = models.ForeignKey(Languages, null=False, blank=False, on_delete=models.PROTECT,\
#         related_name="po_source_lang")
#     target_language = models.ForeignKey(Languages, null=False, blank=False, on_delete=models.PROTECT,\
#         related_name="po_target_lang")



def po_dir_path(instance, filename):
    #return '{0}/{1}/{2}/{3}'.format(instance.user.uid, "Reports","PO",filename)
    return '{0}/{1}/{2}'.format("ai_reports","PO",filename)

class PurchaseOrder(models.Model):
    '''Purchase Order Created During Assignment'''
    status =(
    ("draft","draft"),
    ("issued", "issued"),
    ("open","open"),
    ("closed","closed"),
    ("void","void"),
    ("generated","generated")
    )


    def generate_po_id():
        return "PO-{0}".format(id_generator())

    poid=models.CharField(max_length=50,default=generate_po_id,unique=True)
    client=models.ForeignKey(AiUser,related_name='user_client',on_delete=models.PROTECT)
    seller=models.ForeignKey(AiUser,related_name='user_seller',on_delete=models.PROTECT)
    assignment = models.ForeignKey(POAssignment,related_name='po_assign',on_delete=models.PROTECT)
    currency = models.ForeignKey(Currencies,related_name='po_currency', on_delete=models.PROTECT,blank=True, null=True)
    po_status =models.CharField(max_length=50,choices=status,default='draft')
    po_file = models.FileField(upload_to=po_dir_path, blank=True, null=True)
    po_total_amount = models.DecimalField(max_digits=12,decimal_places=4)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    @property
    def get_pdf(self):
        return self.po_file.url
    
post_save.connect(_create_po_file, sender=PurchaseOrder)

class POTaskDetails(models.Model):
    ACCEPT_STATUS =[("task_accepted","task_accepted"),
                    ("change_request","change_request")]
    
    task_id = models.CharField(max_length=191)
    po = models.ForeignKey(PurchaseOrder,related_name="po_task",on_delete=models.CASCADE,null=True)
    assignment = models.ForeignKey(POAssignment,related_name='assignment_po',on_delete=models.PROTECT)
    # step = models.ForeignKey(Steps,on_delete=models.PROTECT, null=False, blank=False,
    #        related_name="po_step")
    source_language = models.ForeignKey(Languages, null=False, blank=False, on_delete=models.PROTECT,\
        related_name="po_source_lang")
    target_language = models.ForeignKey(Languages, null=False, blank=False, on_delete=models.PROTECT,\
        related_name="po_target_lang")
    project_name = models.CharField(max_length=223, blank=True, null=True)
    projectid= models.CharField(max_length=223, blank=True, null=True)
    word_count=models.IntegerField(null=True,blank=True)
    char_count=models.IntegerField(null=True,blank=True)
    estimated_hours=models.IntegerField(null=True,blank=True)
    unit_price =models.DecimalField(max_digits=12, decimal_places=4)
    unit_type = models.ForeignKey(Billingunits,related_name="po_unit",on_delete=models.PROTECT)
    total_amount = models.DecimalField(max_digits=12, decimal_places=4)
    tsk_accepted = models.BooleanField(default=False)
    assign_status = models.CharField(max_length=20,choices=ACCEPT_STATUS,null=True,blank=True)
    reassigned = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.total_amount:
            if self.unit_type.unit=='Char' and self.char_count!=None:
                self.total_amount = self.unit_price * self.char_count
            elif self.unit_type.unit=='Word' and self.word_count!=None:
                self.total_amount = self.unit_price * self.word_count
            #self.assignment_id = self.task.job.project.ai_project_id+"t"+str(TaskAssignInfo.objects.filter(task=self.task).count()+1)
        super().save()

    @property
    def unit_price_float_format(self):
        formatNumber = lambda n: n if n%1 else int(n)
        return formatNumber(self.unit_price)

post_save.connect(change_po_status, sender=POTaskDetails)
# post_save.connect(update_po_file, sender=POTaskDetails)

def invoice_dir_path(instance, filename):
    #return '{0}/{1}/{2}/{3}'.format(instance.user.uid, "Reports","PO",filename)
    return '{0}/{1}/{2}'.format("ai_reports","Invoice",filename)

class AilaysaGeneratedInvoice(models.Model):
    '''Invoice generate by Ailaysa'''
    STATUS =(
    ("draft","draft"),
    ("paid", "paid"),
    ("open","open"),
    ("void","void")
    )
    GST_CAT =(("NOGST","NOGST"),("SGST,CGST","SGST,CGST"),("IGST","IGST"))
    def generate_invo_id():
        return "{0}".format(id_generator())
    invoid=models.CharField(max_length=50,default=generate_invo_id,unique=True)
    invo_status=models.CharField(max_length=50,choices=STATUS)
    client=models.ForeignKey(AiUser,related_name='user_client_invo',on_delete=models.PROTECT)
    seller=models.ForeignKey(AiUser,related_name='user_seller_invo',on_delete=models.PROTECT)
    invo_file = models.FileField(upload_to=invoice_dir_path, blank=True, null=True)
    gst = models.CharField(max_length=50,choices=GST_CAT)
    tax_amount = models.DecimalField(max_digits=12,decimal_places=4)
    total_amount = models.DecimalField(max_digits=12,decimal_places=4)
    grand_total = models.DecimalField(max_digits=12,decimal_places=4)
    currency = models.ForeignKey(Currencies,related_name='ai_invo_currency', on_delete=models.PROTECT,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    @property
    def get_pdf(self):
        return self.invo_file.url

class AiInvoicePO(models.Model):
    invoice=models.ForeignKey(AilaysaGeneratedInvoice,related_name='ai_invo_po',on_delete=models.CASCADE)
    po=models.ForeignKey(PurchaseOrder,related_name='ai_po',on_delete=models.CASCADE)

class StripeSupportedCountries(models.Model):
    country = models.ForeignKey(Countries,related_name='stripe_countries',on_delete=models.CASCADE)
