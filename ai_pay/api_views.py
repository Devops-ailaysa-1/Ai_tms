import decimal
from locale import currency
from ai_auth.models import AiUser, BillingAddress
from ai_pay.models import AiInvoicePO, AilaysaGeneratedInvoice, PurchaseOrder,POTaskDetails,POAssignment, StripeSupportedCountries
from ai_pay.signals import update_po_status
from ai_staff.models import IndianStates
from ai_workspace.models import Project, TaskAssignInfo,AiRoleandStep
from rest_framework.views import APIView
from rest_framework import viewsets
from django.conf import settings
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
import stripe
from django.http import JsonResponse
from djstripe.models import Account,Customer,Invoice
from weasyprint import HTML, CSS
from django.template.loader import render_to_string
from decimal import Decimal
from django.db.models import Count
import logging
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from rest_framework.decorators import api_view,permission_classes
from rest_framework import generics
from ai_pay.models import POTaskDetails,POAssignment,PurchaseOrder
from ai_pay.serializers import (InvoiceListSerializer, POTaskSerializer,POAssignmentSerializer, PoAssignDetailsSerializer, 
                PurchaseOrderListSerializer,PurchaseOrderSerializer,AilaysaGeneratedInvoiceSerializer, PurchaseOrderTaskListSerializer)

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter,OrderingFilter
from django.db.models import Q
from django.conf import settings
import time
from django.http import Http404
from ai_auth.api_views import resync_instances
from notifications.signals import notify
from ai_auth.utils import get_assignment_role

logger = logging.getLogger('django')

try:
    default_djstripe_owner=Account.get_default_account()
except BaseException as e:
    print(f"Error : {str(e)}")

def get_stripe_key():
    '''gets stripe api key for current environment'''
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY
    return api_key

def get_connect_account(user):
    '''get connected account details'''
    ##(True,False) -->
    ##(False,False) -->

    try:
        acc= Account.objects.get(email=user.email)
        return acc
    except Account.MultipleObjectsReturned:
        logger.warning(f"{user.uid} has more thn one connect account.")
        return None
    except Account.DoesNotExist:
        return None



def conn_account_create(user):
    '''creating stripe connect account'''
    ##(acc_created_flag,acc_linl_object) -->

    stripe.api_key=get_stripe_key()
    acc= get_connect_account(user)
    if acc:
        # if acc.payouts_enabled:
        #     return True,None            
        # else:
        #     link_type = "account_update"
        pass
    else:
        try:
            StripeSupportedCountries.objects.get(country=user.country)
        except StripeSupportedCountries.DoesNotExist:
            logger.warning("user connect country not found",user.uid)
            raise ValueError("user_country_not_supported")
        
        acc=stripe.Account.create(
            type="standard",
            country=user.country.sortname,
            email=user.email,
            metadata={'uid':user.uid}
            #business_type = 'individual',
            #settings={"payouts": {"schedule": {"delay_days": 31}}},
            )
        Account.sync_from_stripe_data(acc, api_key=get_stripe_key())
    
    # print(acc_create)
    if acc:
        acc_link = stripe.AccountLink.create(
            account=acc.id,
            refresh_url=settings.USERPORTAL_URL,
            return_url=settings.USERPORTAL_URL,
            type= link_type if 'link_type' in locals() else "account_onboarding"
            )
        return True,acc_link
    else:
        logger.error("Account_creation_failed for uid:",user.uid)
        return False,None


class AiConnectOnboarding(viewsets.ViewSet):
    #permission_classes = [IsAuthenticated]
    def create(self,request):
        try:
            acc_link = conn_account_create(request.user)[1]
        except ValueError as e:
            return Response({'msg':str(e)},status=400)
        if acc_link:
            return Response({'msg':'Connect Account Link Generated','url':acc_link.url,'expiry':acc_link.expires_at},status=200)
        else:
            return Response({'msg':'Connect Account Link Generation Failed'},status=404)
    
    def update(self,request,pk):
        pass



def create_payment_page_conn(ven_acc_id,cust_id): 
    session = stripe.checkout.Session.create(
    customer =cust_id ,
    line_items=[{
        'name': 'project 71',
        'amount': 1000,
        'currency': 'inr',
        'quantity' : 1
    }],
    payment_intent_data={
        'application_fee_amount': 100,
    },
    mode='payment',
    success_url='https://example.com/success',
    cancel_url='https://example.com/cancel',
    stripe_account=ven_acc_id,
    )

    return session

# payment_intent = stripe.PaymentIntent.create(
#   amount=1000,
#   currency='inr',
#   application_fee_amount=123,
#   stripe_account='{{CONNECTED_STRIPE_ACCOUNT_ID}}',
# )



class CreateChargeVendor(viewsets.ViewSet):
    #permission_classes = [IsAuthenticated]
    def create(self,request):
        cust_id = request.POST.get("customer_id")
        cust_ai = AiUser.objects.get(id=cust_id)
        cust = Customer.objects.get(subscriber=cust_ai)
        acc = Account.objects.get(email=request.user)
        chk_session = create_payment_page_conn(acc.id,cust.id)
        if chk_session:
            return Response({'msg':'Checkout link Generated','url':chk_session.url},status=200)
        else:
            return Response({'msg':'Checkout link generation failed'},status=404)
    
    def update(self,request,pk):
        pass


def void_stripe_invoice(vendor,id):
    stripe.api_key=get_stripe_key()
    try:
        voided = stripe.Invoice.void_invoice(
        stripe_account=vendor.id,
        sid=id,
        )   
    except BaseException as e:
        logger.error(f"invoice voiding failed: {id}")
        return False
    return True


def create_invoice_conn(cust,vendor):
    stripe.api_key=get_stripe_key()
    stripe.InvoiceItem.create( # You can create an invoice item after the invoice
    customer=cust.id,
    amount =10000
    )
    invoice = stripe.Invoice.create(
    customer=cust.id,
    #on_behalf_of=
    application_fee_amount=10,
    transfer_data={
        "destination": vendor.id,
    },
    )


def customer_create_conn_account(client,seller):
    stripe.api_key=get_stripe_key()
    cust =Customer.objects.get(subscriber=client,djstripe_owner_account=default_djstripe_owner)
    vendor = Account.objects.get(email=seller.email)
    if cust:
        conn_cust_create = stripe.Customer.create(
        email=cust.email,
        metadata=cust.metadata,
        address=cust.address,
        stripe_account=vendor.id,
        name=cust.subscriber.fullname
        )

    return conn_cust_create.get('id')

def webhook_wait(invo_id):
    print("inside webhook wait")
    try:
        Invoice.objects.get(id=invo_id)
    except:
        time.sleep(1)
        return webhook_wait(invo_id)
    return True

def create_invoice_conn_direct(cust,vendor,currency):  
    api_key = get_stripe_key()
    stripe.api_key=api_key
    #percent=3
    #app_fee_amount=percent/100*amount
    # invoice_it= stripe.InvoiceItem.create( # You can create an invoice item after the invoice
    #             customer=cust.id,amount =amount,currency=currency)

    invo = stripe.Invoice.create(
        customer=cust.id,
        #application_fee_amount=app_fee_amount,
        stripe_account=vendor.id,
        currency=currency,
        pending_invoice_items_behavior='exclude')
    if invo:
        Invoice.sync_from_stripe_data(invo, api_key=api_key)
        logger.info(f"invoice created : {invo.id}")
    else:
        logger.error(f"invoice creation failed: {invo.id}")  
        return None

    # invoice_it= stripe.InvoiceItem.create( # You can create an invoice item after the invoice
    #         customer=cust.id,amount =amount,currency=currency)

    return invo.id

def stripe_invoice_finalize(invoice_id,vendor) -> bool:
        stripe.api_key=get_stripe_key()
        try:
            res=stripe.Invoice.finalize_invoice(invoice_id,stripe_account=vendor.id)
        except BaseException as e:
            logger.error(f"invoice finalize failed - {invoice_id} :{str(e)}")
            return False
        return True


# payment_intent = stripe.PaymentIntent.create(
#   amount=1000,
#   currency='usd',
#   transfer_data={
#     'destination': '{{CONNECTED_STRIPE_ACCOUNT_ID}}',
#   }
# )


def update_invoice_items_stripe(cust,vendor,amount,currency,invo_id,po_id):
    stripe.api_key=get_stripe_key()
    invoice_it= stripe.InvoiceItem.create( # You can create an invoice item after the invoice
    stripe_account=vendor.id,
    customer=cust.id,
    amount =amount,
    description=f"{po_id}",
    currency=currency,
    metadata={"poid":po_id},
    invoice=invo_id
    )
    return invoice_it.get('id')


class CreateInvoiceVendor(viewsets.ViewSet):
    def create(self,request):
        cust_id = request.POST.get("customer_id")
        cust = AiUser.objects.get(id=cust_id)
        acc = Account.objects.get(email=request.user)
        inv = create_invoice_conn_direct(cust=cust,vendor=acc)
        if inv:
            return Response({'msg':'Invoice Generated','url':inv.id},status=200)
        else:
            return Response({'msg':'Invoice Generation failed'},status=404)


def po_generate_pdf(po):
    #paragraphs = ['first paragraph', 'second paragraph', 'third paragraph']
    tasks = po.po_task.all()
    print("inside gen po",po.poid)
    ## Need to remove added for old po support
    if tasks.count() <1:
        pos = PurchaseOrder.objects.filter(assignment=po.assignment,po_status='void')
        if not pos.count() > 0:
            tasks = po.assignment.assignment_po.all()
            if tasks.count() == 0:
                logger.warning(f"no tasks were found for po :{po.poid}")
                return False
    project_id=tasks.last().projectid
    project_name=tasks.last().project_name
    step = po.assignment.step.name
    context={'client': po.client,'seller':po.seller,'poid':po.poid,
     'created_at':po.created_at,'project_name':project_name ,'project_id':project_id,'currency':po.currency.currency_code,'po_total_amount':po.po_total_amount,'tasks':tasks,'step':step}
    html_string = render_to_string('po_pdf.html', context)

    html = HTML(string=html_string)
    po_res = html.write_pdf()
    # print('po_res',po_res)
    po.po_file = SimpleUploadedFile( po.poid +'.pdf', po_res, content_type='application/pdf')
    po.save()
    return True
    #po_generate()

    # fs = FileSystemStorage('/tmp')
    # with fs.open('mypdf.pdf') as pdf:
    #     response = HttpResponse(pdf, content_type='application/pdf')
    #     response['Content-Disposition'] = 'attachment; filename="Ailaysa_invoice.pdf"'
    #     return response



def download_pdf():
    pass

def get_gst(client,seller):
    if client.country.sortname == seller.country.sortname == 'IN':
        return  2
        # addr_client=BillingAddress.objects.get(user=client)
        # addr_seller=BillingAddress.objects.get(user=seller)
        # print(addr.state)
        # state_client = IndianStates.objects.filter(state_name__icontains=addr_client.state)
        # state_seller = IndianStates.objects.filter(state_name__icontains=addr_seller.state)
        # if state_client.exists() and state_client.first().state_code == 'TN':
        #     tax_rate=[TaxRate.objects.filter(display_name = 'CGST').last().id,TaxRate.objects.filter(display_name = 'SGST').last().id]
        # elif state.exists():
        #     tax_rate=[TaxRate.objects.filter(display_name = 'IGST').last().id,]
        #tax_rate=[TaxRate.objects.get(display_name = 'GST',description='IN GST').id,]
        
    else:
        return 0



def generate_invoice_offline(po_li,gst=None,user=None):
    #same currency po
    pos = PurchaseOrder.objects.filter(poid__in=po_li)
    res  = pos.values('currency').annotate(dcount=Count('currency')).order_by().count()
    res2 = pos.values('seller_id').annotate(dcount=Count('seller_id')).order_by().count()
    res3 = pos.values('client_id').annotate(dcount=Count('client_id')).order_by().count()
    if res&res2&res3 >1:
        logger.error("Invoice creation Failed More Than on currency or users")
        return None
    else:
        try:
            with transaction.atomic():
                # if gst: 
                #     gst_tax =get_gst(pos.last().client,pos.last().seller)
                #     pass
                total_amount=0
                tax_amount =0
                currency = pos.last().currency
                for po in pos:
                    total_amount+=float(po.po_total_amount)
                grand_total = tax_amount + total_amount
                invo = AilaysaGeneratedInvoice.objects.create(client=pos.last().client,
                            seller=pos.last().seller,invo_status='open',tax_amount=tax_amount,total_amount=total_amount,gst="NOGST",grand_total=grand_total,currency=currency)
                # print("invo")
                for po in pos:
                    AiInvoicePO.objects.create(invoice=invo,po=po)
                return invo
        except:
            logger.error("Invoice Generration Failed")
            return None

def get_task_total_amt(instance):
    tot_amount = 0
    if instance.mtpe_count_unit.unit=='Word':
        if instance.total_word_count:
            if instance.account_raw_count and instance.billable_word_count==None:   
                tot_amount =instance.total_word_count * instance.mtpe_rate
            elif instance.billable_word_count!=None:
                tot_amount =instance.billable_word_count * instance.mtpe_rate
        else:
            tot_amount = 0
    elif instance.mtpe_count_unit.unit =='Char':
        if instance.task_assign.task.task_char_count:
            if instance.account_raw_count and instance.billable_char_count==None:
                tot_amount = instance.task_assign.task.task_char_count* instance.mtpe_rate
            elif instance.billable_char_count!=None:
                tot_amount = instance.billable_char_count* instance.mtpe_rate

        else:
                tot_amount = 0
    elif instance.mtpe_count_unit.unit =='Fixed':
        tot_amount = instance.mtpe_rate
    elif instance.mtpe_count_unit.unit =='Hour':
        if instance.estimated_hours:
            tot_amount = instance.estimated_hours * instance.mtpe_rate
        else:
            tot_amount = 0
    else:
        # rasie error on invalid price should be rised
        logger.error("Invalid unit type for Po Assignment:{0}".format(instance.assignment_id))
        tot_amount=0
    return tot_amount

def update_task_po(task_assign,po_task):
    tot_amount = get_task_total_amt(task_assign)
    insert={'word_count':task_assign.billable_word_count,'char_count':task_assign.billable_char_count,'unit_price':task_assign.mtpe_rate,'unit_type':task_assign.mtpe_count_unit,
    'estimated_hours':task_assign.estimated_hours,'total_amount':tot_amount,'tsk_accepted':False,'assign_status':None}
    task_po_res=POTaskDetails.objects.filter(id=po_task.id).update(**insert)
    po = po_task.po
    po.po_file=None
    # po.po_total_amount=tot_amount
    po.save()
    # po_generate_pdf(po)

    

def generate_client_po(task_assign_info):
    #pos.values('currency').annotate(dcount=Count('currency')).order_by()
    if len(task_assign_info) == 0:
        return None
    with transaction.atomic():
        po_total_amt=0.0
        instance = TaskAssignInfo.objects.get(id=task_assign_info[-1])
        assign=POAssignment.objects.get_or_create(assignment_id=instance.assignment_id,step=instance.task_assign.step)[0]
        if instance.task_assign.reassigned:
            if instance.assigned_by.team:
                client = instance.assigned_by.team.owner
            else:
                client = instance.assigned_by

        else:
            client = instance.task_assign.task.job.project.ai_user


        insert2={'client':client,'seller':instance.task_assign.assign_to,
                'assignment':assign,'currency':instance.currency,
                'po_status':'issued','po_total_amount':0}
        # print("insert2",insert2)

        old_po = PurchaseOrder.objects.filter(Q(assignment=assign)&~Q(po_status="void")&Q(po_status="issued"))
        if  old_po.count() != 0 :
            if old_po.count() == 1:
                po = old_po.last()
            else:
                logger.error("too many open po found")
        else:
            po = PurchaseOrder.objects.create(**insert2)
            
               
        for obj_id in task_assign_info:
            instance = TaskAssignInfo.objects.get(id=obj_id)
            assign=POAssignment.objects.get_or_create(assignment_id=instance.assignment_id,step=instance.task_assign.step)[0]

            
            if instance.task_ven_status == 'task_accepted':
                tsk_accepted = True
            else:
                tsk_accepted = False

            if instance.task_assign.task.job.target_language == None and instance.task_assign.task.job.project.project_type.id==4:
                task_tar_lang = instance.task_assign.task.job.source_language
            else:
                task_tar_lang = instance.task_assign.task.job.target_language

            tot_amount = get_task_total_amt(instance)
            insert={'task_id':instance.task_assign.task.id,'po':po,'assignment':assign,'project_name':instance.task_assign.task.job.project.project_name,'projectid':instance.task_assign.task.job.project.ai_project_id,
                    'word_count':instance.billable_word_count,'char_count':instance.billable_char_count,'unit_price':instance.mtpe_rate,'tsk_accepted':tsk_accepted,'assign_status':instance.task_ven_status,
                    'unit_type':instance.mtpe_count_unit,'estimated_hours':instance.estimated_hours,'source_language':instance.task_assign.task.job.source_language,'target_language':task_tar_lang,'total_amount':tot_amount,'reassigned':instance.task_assign.reassigned}
            # print("insert1",insert)
            po_task=POTaskDetails.objects.create(**insert)
            # print("po_task",po_task)
            po_total_amt+=float(tot_amount)
            po.po_total_amount=po_total_amt
            po.save()
            po_generate_pdf(po)
            msg_send_po(po,"po_created")
        # print("po2",po)
    return po


def po_modify_weigted_count(task_assign_info_ls):
    if len(task_assign_info_ls)!= 0:
        assignment = POAssignment.objects.filter(assignment_id=task_assign_info_ls[0].assignment_id).last()       
        pos = PurchaseOrder.objects.filter(Q(assignment=assignment)&~Q(po_status="void"))
        if pos.count()==1:
            po =pos.last()
        elif pos.count()==0:
            return True
        else:
            logger.error('returned more than one po for same assignment')
            return False
    for assign_obj in task_assign_info_ls:
        taskpo = POTaskDetails.objects.filter(task_id=assign_obj.task_assign.task.id,po=po)       
        tot_amount = get_task_total_amt(assign_obj)
        insert = {'word_count':assign_obj.billable_word_count,'char_count':assign_obj.billable_char_count,
                'total_amount':tot_amount}
        taskpo.update(**insert)
    po_total =0
    for tasks in po.po_task.all():
        po_total += tasks.total_amount
    po.po_total_amount=po_total
    po.po_file=None
    po.save()
    # msg_send_po(po,"po_updated") 


def po_modify(task_assign_info_id,po_update):
    from ai_auth.signals import assign_object

    instance= TaskAssignInfo.objects.get(id=task_assign_info_id)
    assignment_id= instance.assignment_id
    task =instance.task_assign.task.id

    if 'accepted' in po_update:
        #if instance.owner != instance.task_assign.task.job.project.project_manager:
        #role= AiRoleandStep.objects.get(step=instance.task_assign.step).role.name

        assign_object.send(
            sender=TaskAssignInfo,
            instance = instance,
            user=instance.task_assign.assign_to,
            role = get_assignment_role(instance.task_assign.step,instance.task_assign.reassigned )
        )
        try:
            po_task_obj = POTaskDetails.objects.get(Q(assignment__assignment_id=assignment_id,task_id=task)&~Q(po__po_status='void'))
            po_task_obj.tsk_accepted=True
            po_task_obj.assign_status="task_accepted"
            po_task_obj.save()
            return True
        except BaseException as e:
            logger.error(f"error while updating po task status for {task_assign_info_id},ERROR:{str(e)}")
            
    if 'change_request' in po_update:
        try:
            po_task_obj = POTaskDetails.objects.get(Q(assignment__assignment_id=assignment_id,task_id=task)&~Q(po__po_status='void'))
            po_task_obj.assign_status="change_request"
            po_task_obj.save()
            return True
        except BaseException as e:
            logger.error(f"error while updating po task status for {task_assign_info_id},ERROR:{str(e)}")

    if ('accepted_rate' in po_update or 'accepted_rate_by_owner' in po_update) and ('assign_to' not in po_update):
        try:
            with transaction.atomic():
                po_task_obj = POTaskDetails.objects.get(Q(assignment__assignment_id=assignment_id,task_id=task)&~Q(po__po_status='void'))
                try:
                    update_task_po(instance,po_task_obj)
                except:
                    raise ValueError("updating task po failed")
            # return True
            # if 'currency_change' in po_update:
            #     pass
            # else:
            #     return True

        except BaseException as e:
            logger.error(f"error while updating po task status for {task_assign_info_id} for accepted_rate_by_owner,ERROR:{str(e)}")

    po_new =None
    with transaction.atomic():
        task_assign_info_ids = [tsk.id for tsk in TaskAssignInfo.objects.filter(assignment_id=assignment_id)]
        if 'unassigned' in po_update:
            # if task is unassigned
            task_assign_info_ids.remove(instance.id)
        pos = PurchaseOrder.objects.filter(Q(assignment__assignment_id=assignment_id)&~Q(po_status="void"))
        if pos.count()==1:
            po =pos.last()
        else:
            raise ValueError('returned more than one po for same assignment')
        po.po_status="void"
        po.save()
        if len(task_assign_info_ids)==0:
            return True
        po_new = generate_client_po(task_assign_info_ids) 
        print("new po",po_new) 
    if po_new:
        po_tsk = po_new.po_task.last()
        update_po_status.send(
            sender=po_tsk.__class__,
            instance = po_tsk,
            created = False
        )
        msg_send_po(po,"po_updated")   
        return True
    else:
        return False


def extend_po() :
    pass



def generate_invoice_pdf(invo):
    pos=invo.ai_invo_po.all()
    pos_ls=[po_i.po for po_i in pos]
    # for po in pos:
    #     tasks = po.assignment.assignment_po.all()
    #     qs=tasks.union(tasks)
    # tasks =  POTaskDetails.objects.filter(assignment__po_assign__in=pos_ls)
    tasks =   POTaskDetails.objects.filter(po__in=pos_ls)
    # print("tasks invo",tasks)
    context= {'client': invo.client,'seller':invo.seller,'pos_ids':pos_ls,'invo':invo,'tasks':tasks}
    html_string = render_to_string('invoice_pdf.html',context)
    html = HTML(string=html_string)
    invo_res = html.write_pdf()
    invo.invo_file = SimpleUploadedFile(invo.invoid +'.pdf', invo_res, content_type='application/pdf')
    invo.save()


class POViewSet(viewsets.ViewSet):
    def list(self, request):
        queryset = POAssignment.objects.all()
        serializer = POAssignmentSerializer(queryset, many=True)
        return Response(serializer.data)


class POListView(generics.ListAPIView):
    #permission_classes=[IsAuthenticated]
    serializer_class = PurchaseOrderListSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    #search_fields = ['']

    def get_queryset(self):
        user = self.request.user
        queryset = PurchaseOrder.objects.filter(Q(client=user)|Q(seller=user))
        return queryset

    def list(self, request):
        # Note the use of `get_queryset()` instead of `self.queryset`
        queryset = self.get_queryset()
        serializer = PurchaseOrderListSerializer(queryset,context=request)
        return Response(serializer.data)

def converttocent(amount,currency_code=None):
    return int(amount*100)

def generate_invoice_by_stripe(po_li,user,gst=None):
    print("user>.",user)
    pos = PurchaseOrder.objects.filter(poid__in=po_li)
    res  = pos.values('currency').annotate(dcount=Count('currency')).order_by().count()
    res2 = pos.values('seller_id').annotate(dcount=Count('seller_id')).order_by().count()
    res3 = pos.values('client_id').annotate(dcount=Count('client_id')).order_by().count()
    if user.id != pos.last().seller.id: # validate seller
        print("given user is not po owner")
    elif res&res2&res3 >1:
        logger.error("Invoice creation Failed More Than on currency or clients")
        return None
    else:
        seller  = pos.last().seller
        client = pos.last().client
        currency = pos.last().currency.currency_code
        try:
            vendor = Account.objects.get(email=seller.email)
            cust =Customer.objects.get(subscriber=client,djstripe_owner_account=vendor)
        except Account.DoesNotExist:
            logger.error("{user.uid} has no stripe connect account")
            return False
        except Customer.DoesNotExist:
            cust_id = customer_create_conn_account(client,seller)
            try:
                cust =Customer.objects.get(id=cust_id,djstripe_owner_account=vendor)
            except Customer.DoesNotExist:
                resync_instances(user.djstripe_customers.all())
                cust =Customer.objects.get(id=cust_id,djstripe_owner_account=vendor)
        invo_id = create_invoice_conn_direct(cust,vendor,currency)
        for po in pos:
            try:
                po_amount=converttocent(po.po_total_amount,po.currency.currency_code)
                update_invoice_items_stripe(cust,vendor,po_amount,po.currency.currency_code,invo_id,po.poid)
            except BaseException as e:
                logger.error(f"invoice item error {po.poid} : {str(e)}")
                return False

        return stripe_invoice_finalize(invo_id,vendor)

def check_po_invoice_generated(poids):
    invo_po=AiInvoicePO.objects.filter(po__poid__in=poids)
    if invo_po.filter(invoice__invo_status='open').count() > 0:
        logger.warning("Invoice already generated")
    seller = invo_po.last().po.seller
    acc = get_connect_account(seller)
    #seller
    pass

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def po_request_payment(request):
    '''API - Generate Invoice based on user selection'''
    user = request.user
    poids = request.POST.getlist('poids')
    gst=request.POST.get('gst',None)
    stripe_con = request.POST.get('stripe_con',None)
    # print("stripe_con >>",stripe_con)

    # print('request_dict',request.POST.getlist('poids'))
    # print('poid',poids)

    invo_po=AiInvoicePO.objects.filter(po__poid__in=poids)
    if invo_po.filter(invoice__invo_status='open').count() > 0:
        return JsonResponse({"msg":"invoice with po already open"},safe=False,status=409)
    if stripe_con == 'True':
        # invo = generat_invoice_by_stripe(poids,gst,user=request.user)
        logger.info('user requested invoice creation by stripe - UID :{user.uid}')
        acc = get_connect_account(user)
        if acc == None:
            try:
                acc_created,acc_link=conn_account_create(user)
            except ValueError as e:
                    logger.warning(f"user Connect account creation failed. {user.uid}- error:{str(e)}")
                    return Response({'msg':str(e)},status=404)
                
            if acc_created:
                #return JsonResponse({"msg":"redirecting to stripe dashboard","url":f"{settings.STRIPE_DASHBOARD_URL}/invoices/create"},status=302)
                invo = generate_invoice_by_stripe(poids,user=user,gst=gst)
            if acc_link:
                return Response({'msg':'Connect Account Link Generated','url':acc_link.url,'expiry':acc_link.expires_at},status=302)
            else:
                return Response({"msg":"Invoice creation failed"},status=400)
        else:
            invo=generate_invoice_by_stripe(poids,user=user,gst=gst)
        ## need to check uid        
    else:
        invo = generate_invoice_offline(poids,gst,user=user)
    if invo:
        return JsonResponse({"msg":"Successfully created Invoice"},safe=False,status=200)
    else:
        return JsonResponse({"msg":"Invoice creation failed"},status=400)
    #generate_invoice_offline()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def po_pdf_get(request):
    poid = request.GET.get('poid',None)
    assignmentid=request.GET.get('assignment_id',None)
    if poid:
        po =PurchaseOrder.objects.get(poid=poid)
    elif assignmentid:
        try:
            pos =PurchaseOrder.objects.filter(Q(assignment__assignment_id=assignmentid)&~Q(po_status='void'))
            if pos.count()==1:
                po = pos.last()
            else:
                raise ValueError('multiple po returned for assignment')
        except ValueError as e:
            logger.error(f" assignmentid: {assignmentid} {str(e)}")
            return JsonResponse({'error':'multiple po returned for assignment'},status=400)
    else:
        return JsonResponse({'error':'poid_or_assignmenid_field_is_required'},status=400)
    if not po.po_file:
        po_pdf = po_generate_pdf(po)
    return JsonResponse({'url':po.get_pdf},safe=False,status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def invoice_pdf_get(request):
    id = request.GET.get('id',None)
    invo =AilaysaGeneratedInvoice.objects.get(id=id)
    if not invo.invo_file:
        invo_pdf = generate_invoice_pdf(invo)
    return JsonResponse({'url':invo.get_pdf},safe=False,status=200)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def cancel_stripe_invoice(request):
    try:
        id = request.POST.get('id',None)
        print('id',id)
        if not id:
            raise ValueError("id_not_given")
        vendor = Account.objects.get(email=request.user.email)
        voided = void_stripe_invoice(vendor,id)
        if voided:
             return JsonResponse({'msg':'invoice_status_updated'},safe=False,status=200)
        else:
            raise ValueError("invoice_voiding_failed")  
    except:
        return JsonResponse({'msg':'invoice_status_updation_failed'},status=400)
   


class InvoiceListView(generics.ListAPIView):
    #permission_classes=[IsAuthenticated]
    serializer_class = InvoiceListSerializer
    filter_backends = [DjangoFilterBackend,SearchFilter,OrderingFilter]
    #search_fields = ['']

    def get_queryset(self):
        user = self.request.user
        queryset = AilaysaGeneratedInvoice.objects.filter(Q(client=user)|Q(seller=user))
        return queryset

    def list(self, request):
        # Note the use of `get_queryset()` instead of `self.queryset`
        queryset = self.get_queryset()
        serializer = InvoiceListSerializer(queryset,context=request)
        
        return Response(serializer.data)


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def gen_invoice_offline(request):
#     poids = request.POST.getlist('poids')



# @api_view(['PUT'])
# @permission_classes([IsAuthenticated])
# def update_aigen_invoice_status(request):
#     try:
#         id = request.POST.get('id')
#         invo =AilaysaGeneratedInvoice.objects.get(id=id)
#         if invo.invo_status == 'open':
#             invo.invo_status = 'void'
#         else:
#             raise ValueError("invoice status not suitable for voiding")
#     except BaseException as e:
#         pass

class AilaysaGeneratedInvoiceViewset(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    def get_object(self, pk):
        try:
            return AilaysaGeneratedInvoice.objects.get(id=pk)
        except AilaysaGeneratedInvoice.DoesNotExist:
            raise Http404

    def update(self, request, pk=None):
        instance=self.get_object(pk)
        serializer = AilaysaGeneratedInvoiceSerializer(instance,data=request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=200)
        return Response(serializer.errors, status=400)

        
def msg_send_po(po,input):
    url = settings.USERPORTAL_URL+"payments/marketplace-payments"
    from ai_marketplace.serializers import ThreadSerializer
    from ai_marketplace.models import ChatMessage
    sender = po.client
    receiver = po.seller
    thread_ser = ThreadSerializer(data={'first_person':sender.id,'second_person':receiver.id})
    if thread_ser.is_valid():
        thread_ser.save()
        thread_id = thread_ser.data.get('id')
    else:
        thread_id = thread_ser.errors.get('thread_id')
    #print("Thread--->",thread_id)
    if input == 'po_updated':
        message = f'''purchase order {po.poid} has been updated.'''
    elif input == 'po_created':
        message = f'''purchase order {po.poid} has been created.'''

    msg = ChatMessage.objects.create(message=message,user=sender,thread_id=thread_id)
    notify.send(sender, recipient=receiver, verb='Message', description=message,thread_id=int(thread_id))


class PurchaseOrderView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,]


    def get_queryset(self):

        queryset = PurchaseOrder.objects.all()
        participant = self.request.query_params.get('participant')
        task = self.request.query_params.get('task')
        step = self.request.query_params.get('step')
        if participant == "seller":
            queryset = queryset.filter(seller=self.request.user)
        elif participant == "buyer":
            queryset = queryset.filter(client=self.request.user)
        else:
            queryset = queryset.filter(Q(client=self.request.user)|Q(seller=self.request.user))        
        queryset = queryset.filter(po_task__task_id =task)
        # queryset= queryset.filter(assignment__step_id=step)
        queryset = queryset.filter(po_status__in=['issued','open'])

        po_gen = queryset.filter(po_file='')
        for po in po_gen:
            po_generate_pdf(po)
        return queryset
    

    def list(self, request):
        queryset = self.get_queryset()
        serializer = PurchaseOrderTaskListSerializer(queryset,context=request)
        return Response(serializer.data)



class ProjectPOTaskView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated,]


    def get_queryset(self):

        project_id = self.request.query_params.get('project_id')
        proj_queryset = Project.objects.filter(id=project_id)
        
        if self.request.user.is_internal_member:
            req_user = self.request.user.team.owner
        else:
            req_user = self.request.user

        queryset = POTaskDetails.objects.filter(Q(projectid__in=proj_queryset.values_list('ai_project_id',flat=True))&
                                                Q(po__seller=req_user)&~Q(po__po_status="void"))
        
        return queryset
    

    def list(self, request):
        queryset = self.get_queryset()
        serializer = PoAssignDetailsSerializer(queryset, many=True)
        return Response(serializer.data)
    
    # def list(self, request):
    #     queryset = self.get_qu