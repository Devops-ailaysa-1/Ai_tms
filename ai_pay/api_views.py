from locale import currency
from ai_auth.models import AiUser
from ai_pay.models import AiInvoicePO, AilaysaGeneratedInvoice, PurchaseOrder,POTaskDetails,POAssignment
from rest_framework.views import APIView
from rest_framework import viewsets
from django.conf import settings
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
import stripe
from django.http import JsonResponse
from djstripe.models import Account,Customer
from weasyprint import HTML
from django.template.loader import render_to_string

from django.db.models import Count
import logging

from django.db import transaction


def get_stripe_key():
    '''gets stripe api key for current environment'''
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY
    return api_key


def conn_account_create(user):
    '''creating stripe connect account'''
    stripe.api_key=get_stripe_key()
    acc_create=stripe.Account.create(
        type="standard",
        country=user.country.sortname,
        email=user.email,
        #business_type = 'individual',
        #settings={"payouts": {"schedule": {"delay_days": 31}}},
        )
    print(acc_create)
    if acc_create:
        acc_link = stripe.AccountLink.create(
        account=acc_create.id,
        refresh_url="https://staticstaging.ailaysa.com/benefits",
        return_url="https://staticstaging.ailaysa.com/pricing",
        type="account_onboarding",
        )
        return acc_link

class AiConnectOnboarding(viewsets.ViewSet):
    #permission_classes = [IsAuthenticated]
    def create(self,request):
        acc_link = conn_account_create(request.user)
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


def customer_create_conn_account(user,vendor):
    cust =Customer.objects.get(subscriber=user)
    if cust:
        conn_cust_create = stripe.Customer.create(
        email=cust.email,
        metadata=cust.metadata,
        address=cust.address,
        stripe_account=vendor.id
        )

def create_invoice_conn_direct(cust,vendor,amount,currency,finalize=True):
    stripe.api_key=get_stripe_key()
    percent=3
    app_fee_amount=percent/100*amount
    invoice_it= stripe.InvoiceItem.create( # You can create an invoice item after the invoice
                customer=cust.id,amount =amount,currency=currency)

    invo = stripe.Invoice.create(
        customer=cust.id,
        application_fee_amount=app_fee_amount,
        stripe_account=vendor.id,)
    if finalize:
        stripe.Invoice.finalize_invoice(invo.id,stripe_account=vendor.id)


# payment_intent = stripe.PaymentIntent.create(
#   amount=1000,
#   currency='usd',
#   transfer_data={
#     'destination': '{{CONNECTED_STRIPE_ACCOUNT_ID}}',
#   }
# )




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
    html_string = render_to_string('pdf_template_po.html', {'cust': po.client,'ven':po.seller,'status':po.po_status,'tasks':tasks})

    html = HTML(string=html_string)

    html.write_pdf(target='mypdf.pdf');
    #po_generate()

    # fs = FileSystemStorage('/tmp')
    # with fs.open('mypdf.pdf') as pdf:
    #     response = HttpResponse(pdf, content_type='application/pdf')
    #     response['Content-Disposition'] = 'attachment; filename="Ailaysa_invoice.pdf"'
    #     return response



def download_pdf():
    pass


def generate_invoice_offline(po_li):
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
                invo = AilaysaGeneratedInvoice.objects.create(client=pos.last().client,seller=pos.last().seller,invo_status='draft')
                for po in pos:
                    AiInvoicePO.objects.create(invoice=invo,po=po)
        except:
            logging.error("Invoice Generration Failed")
     

def generate_client_po(task_assign_info):
    #pos.values('currency').annotate(dcount=Count('currency')).order_by()
    try:
       with transaction.atomic():
        for instance in task_assign_info:
            assign=POAssignment.objects.get_or_create(assignment_id=instance.assignment_id)[0]
            insert={'task_id':instance.task.id,'assignment':assign,'project_name':instance.task.job.project.project_name,
                    'word_count':instance.total_word_count,'char_count':instance.task.task_details.last().task_char_count,'price':instance.mtpe_rate,
                    'unit_type':instance.mtpe_count_unit,'source_language':instance.task.job.source_language,'target_language':instance.task.job.target_language}
            po_task=POTaskDetails.objects.create(**insert)
        insert2={'client':instance.assigned_by,'seller':instance.task.assign_to,
                'assignment':assign,'currency':instance.currency,
                'po_status':'issued'}
        po=PurchaseOrder.objects.create(**insert2)
    except:
       print("PO Not generated")
       logging.error("PO Generations Failed For assignment:{0}".format(instance.assignment_id))


def generate_invoice_pdf(invo):
    pos=invo.ai_invo_po.all()
    pos_ls=[po_i.po for po_i in pos]
    # for po in pos:
    #     tasks = po.assignment.assignment_po.all()
    #     qs=tasks.union(tasks)
    tasks =  POTaskDetails.objects.filter(assignment__po_assign__in=pos_ls)
    print("tasks invo",tasks)
    context= {'cust': invo.client,'ven':invo.seller,'pos_ids':pos_ls,'status':invo.invo_status,'tasks':tasks}
    html_string = render_to_string('pdf_template_invoice.html',context)
    html = HTML(string=html_string)
    html.write_pdf(target='myinvo.pdf');