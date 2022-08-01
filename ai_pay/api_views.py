from asyncio.log import logger
import decimal
from locale import currency
from ai_auth.models import AiUser, BillingAddress
from ai_pay.models import AiInvoicePO, AilaysaGeneratedInvoice, PurchaseOrder,POTaskDetails,POAssignment
from ai_staff.models import IndianStates
from rest_framework.views import APIView
from rest_framework import viewsets
from django.conf import settings
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
import stripe
from django.http import JsonResponse
from djstripe.models import Account,Customer,Invoice
from weasyprint import HTML
from django.template.loader import render_to_string
from decimal import Decimal
from django.db.models import Count
import logging
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from rest_framework.decorators import api_view,permission_classes
from rest_framework import generics
from ai_pay.models import POTaskDetails,POAssignment,PurchaseOrder
from ai_pay.serializers import (InvoiceListSerializer, POTaskSerializer,POAssignmentSerializer, 
                PurchaseOrderListSerializer,PurchaseOrderSerializer,AilaysaGeneratedInvoiceSerializer)

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter,OrderingFilter
from django.db.models import Q
from django.conf import settings
import time

default_djstripe_owner=Account.get_default_account()

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
        if acc.payouts_enabled:
            return True,None            
        else:
            link_type = "account_update"
    else:
        acc=stripe.Account.create(
            type="standard",
            country=user.country.sortname,
            email=user.email,
            metadata={'uid':user.uid}
            #business_type = 'individual',
            #settings={"payouts": {"schedule": {"delay_days": 31}}},
            )
    
    # print(acc_create)
    if acc:
        acc_link = stripe.AccountLink.create(
            account=acc.id,
            refresh_url=settings.USERPORTAL_URL,
            return_url=settings.USERPORTAL_URL,
            type= link_type if not 'link_type' in locals() else "account_onboarding"
            )
        return True,acc_link
    else:
        logging.error("Account_creation_failed for uid:",user.uid)
        return False,None


class AiConnectOnboarding(viewsets.ViewSet):
    #permission_classes = [IsAuthenticated]
    def create(self,request):
        acc_link = conn_account_create(request.user)[1]
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
        logging.error(f"invoice voiding failed: {id}")
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
    stripe.api_key=get_stripe_key()
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

    # invoice_it= stripe.InvoiceItem.create( # You can create an invoice item after the invoice
    #         customer=cust.id,amount =amount,currency=currency)
    print("invo__id",invo.id)
    if webhook_wait(invo.id):
        logging.info(f"invoice created : {invo.id}")
    else:
        logging.error(f"invoice creation failed: {invo.id}")  
        return None
    return invo.id

def stripe_invoice_finalize(invoice_id,vendor) -> bool:
        stripe.api_key=get_stripe_key()
        try:
            res=stripe.Invoice.finalize_invoice(invoice_id,stripe_account=vendor.id)
        except BaseException as e:
            logging.error(f"invoice finalize failed - {invoice_id} :{str(e)}")
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
    tasks = po.assignment.assignment_po.all()
    project_id=tasks.last().projectid
    project_name=tasks.last().project_name
    context={'client': po.client,'seller':po.seller,'poid':po.poid,
     'created_at':po.created_at,'project_name':project_name ,'project_id':project_id,'currency':po.currency.currency_code,'po_total_amount':po.po_total_amount,'tasks':tasks}
    html_string = render_to_string('po_pdf.html', context)

    html = HTML(string=html_string)
    po_res = html.write_pdf()
    # print('po_res',po_res)
    po.po_file = SimpleUploadedFile( po.poid +'.pdf', po_res, content_type='application/pdf')
    po.save()
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
        logging.error("Invoice creation Failed More Than on currency or users")
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
            logging.error("Invoice Generration Failed")
            return None
     

def generate_client_po(task_assign_info):
    #pos.values('currency').annotate(dcount=Count('currency')).order_by()

    with transaction.atomic():
        po_total_amt=0.0
        for instance in task_assign_info:
            assign=POAssignment.objects.get_or_create(assignment_id=instance.assignment_id)[0]
            if instance.mtpe_count_unit.unit=='Word':
                tot_amount =instance.total_word_count * instance.mtpe_rate
            elif instance.mtpe_count_unit.unit =='Char':
                tot_amount = instance.task.task_details.last().task_char_count * instance.mtpe_rate
            else:
                # rasie error on invalid price should be rised
                logging.error("Invlaid unit type for Po Assignment:{0}".format(instance.assignment_id))
                tot_amount=0
            insert={'task_id':instance.task.id,'assignment':assign,'project_name':instance.task.job.project.project_name,'projectid':instance.task.job.project.ai_project_id,
                    'word_count':instance.total_word_count,'char_count':instance.task.task_char_count,'unit_price':instance.mtpe_rate,
                    'unit_type':instance.mtpe_count_unit,'source_language':instance.task.job.source_language,'target_language':instance.task.job.target_language,'total_amount':tot_amount}
            # print("insert1",insert)
            po_task=POTaskDetails.objects.create(**insert)
            # print("po_task",po_task)
            po_total_amt+=float(tot_amount)
        insert2={'client':instance.assigned_by,'seller':instance.task.assign_to,
                'assignment':assign,'currency':instance.currency,
                'po_status':'issued','po_total_amount':po_total_amt}
        # print("insert2",insert2)
        po=PurchaseOrder.objects.create(**insert2)
        # print("po2",po)



def generate_invoice_pdf(invo):
    pos=invo.ai_invo_po.all()
    pos_ls=[po_i.po for po_i in pos]
    # for po in pos:
    #     tasks = po.assignment.assignment_po.all()
    #     qs=tasks.union(tasks)
    tasks =  POTaskDetails.objects.filter(assignment__po_assign__in=pos_ls)
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
        logging.error("Invoice creation Failed More Than on currency or clients")
        return None
    else:
        seller  = pos.last().seller
        client = pos.last().client
        currency = pos.last().currency.currency_code
        try:
            vendor = Account.objects.get(email=seller.email)
            cust =Customer.objects.get(subscriber=client,djstripe_owner_account=vendor)
        except Account.DoesNotExist:
            logging.error("{user.uid} has no stripe connect account")
            return False
        except Customer.DoesNotExist:
            cust_id = customer_create_conn_account(client,seller)
            try:
                cust =Customer.objects.get(id=cust_id,djstripe_owner_account=vendor)
            except Customer.DoesNotExist:
                time.sleep(1)
                cust =Customer.objects.get(id=cust_id,djstripe_owner_account=vendor)
        invo_id = create_invoice_conn_direct(cust,vendor,currency)
        for po in pos:
            try:
                po_amount=converttocent(po.po_total_amount,po.currency.currency_code)
                update_invoice_items_stripe(cust,vendor,po_amount,po.currency.currency_code,invo_id,po.poid)
            except BaseException as e:
                logging.error(f"invoice item error {po.poid} : {str(e)}")
                return False
        
    return stripe_invoice_finalize(invo_id,vendor)
    

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
        print('user>>',user)
        acc = get_connect_account(user)
        print('acc>',acc)
        if acc == None:
            acc_created,acc_link=conn_account_create(user)
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
            po =PurchaseOrder.objects.get(assignment__assignment_id=assignmentid)
        except PurchaseOrder.MultipleObjectsReturned as e:
            logging.error(f"for assignmentid: {assignmentid} {str(e)}")
    else:
        return JsonResponse({'error':'poid_or_assignmenid_field_is_required'},status=400)
    if not po.po_file:
        po_pdf = po_generate_pdf(po)
    return JsonResponse({'url':po.get_pdf},safe=False,status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def invoice_pdf_get(request):
    id = request.GET.get('id')
    invo =AilaysaGeneratedInvoice.objects.get(id=id)
    if not invo.invo_file:
        invo_pdf = generate_invoice_pdf(invo)
    return JsonResponse({'url':invo.get_pdf},safe=False,status=200)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def cancel_stripe_invoice(request):
    try:
        id = request.GET.get('id')
        vendor = Account.objects.get(email=request.user.email)
        void_stripe_invoice(vendor,id)
    except:
        return JsonResponse({'msg':'invoice_status_updation_failed'},safe=False,status=400)
    return JsonResponse({'msg':'invoice_status_updated'},safe=False,status=200)


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