from ai_auth.models import AiUser
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


def po_generate(cust,ven):
    #paragraphs = ['first paragraph', 'second paragraph', 'third paragraph']
    html_string = render_to_string('pdf_template_po.html', {'cust': cust,'ven':ven})

    html = HTML(string=html_string)
    html.write_pdf(target='mypdf.pdf');

    # fs = FileSystemStorage('/tmp')
    # with fs.open('mypdf.pdf') as pdf:
    #     response = HttpResponse(pdf, content_type='application/pdf')
    #     response['Content-Disposition'] = 'attachment; filename="Ailaysa_invoice.pdf"'
    #     return response


