# from django.db import transaction
from django.conf import settings
import stripe
from ai_staff.models import IndianStates,Countries
from djstripe import webhooks
from djstripe.models import Customer,Price,Invoice,PaymentIntent
from djstripe.models.billing import Subscription, TaxRate
from ai_auth import models
from django.db.models import Q
from django.utils import timezone

# def add_credits(user,price,data):
#     pass


def update_user_credits(user,cust,price,quants,invoice,payment,pack,subscription=None,trial=None):
    if pack.type=="Subscription":
        if subscription.plan.interval=='year':
            expiry = subscription.current_period_end
        else:
            expiry = subscription.current_period_end
        creditsls= models.UserCredits.objects.filter(user=user).filter(Q(credit_pack_type='Subscription')|Q(credit_pack_type='Subscription_Trial')).filter(~Q(invoice=invoice.id))
        for credit in creditsls:
            credit.ended_at=timezone.now()
            credit.save()

    if pack.type=="Subscription_Trial":
         expiry = subscription.trial_end

    if pack.type=="Addon":
        expiry = None
    kwarg = {
    'user':user,
    'stripe_cust_id':cust,
    'price_id':price.id,
    'buyed_credits':pack.credits*quants,
    'credits_left':pack.credits*quants,
    'expiry': expiry,
    'paymentintent':payment.id if payment else None,
    'invoice':invoice.id if invoice else None,
    'credit_pack_type': pack.type,
    'ended_at': None
    }
    us = models.UserCredits.objects.create(**kwarg)
    print(us)



@webhooks.handler("payment_intent.succeeded")
def my_handler(event, **kwargs):
    print(event)
    data =event.data
    invoice=data.get('object').get('invoice',None)
    if invoice == None:
        customer=data.get('object').get('customer',None)
        cust_obj = Customer.objects.get(id=customer)
        user=cust_obj.subscriber
        paymentintent=data.get('object').get('id',None)
        
        if paymentintent:
            payment_obj=PaymentIntent.objects.get(id=paymentintent)
        else :
            payment_obj=None
            
        if invoice:
            invoice_obj=Invoice.objects.get(id=invoice)
        else :
            invoice_obj=None

        meta = data['object']['metadata']
        price_obj= Price.objects.get(id=meta['price'])
        cp = models.CreditPack.objects.get(product=price_obj.product)
        print(data['object']['metadata'])
        quants= int(meta.get('quantity',1))
        update_user_credits(user=user,cust=cust_obj,price=price_obj,
                        quants=quants,invoice=invoice_obj,payment=payment_obj,pack=cp)
        # kwarg = {
        #     'user':user,
        #     'stripe_cust_id':cust_obj,
        #     'price_id':price_obj.id,
        #     'Buyed_credits':cp.credits*quants,
        #     'credits_left':cp.credits*quants,
        #     'expiry': None,
        #     'paymentintent':payment_obj.id,
        #     'invoice':invoice_obj.id
        #     }
        # us = models.UserCredits.objects.create(**kwarg)
        # print(us)
        # print(event.data.object)


# @webhooks.handler("customer.subscription.created")
# def my_handler(event, **kwargs):
#     print(event.data)
#     print("customer subscribed")
#     print(event.data.object)

# @webhooks.handler("charge.succeeded")
# def my_handler(event, **kwargs):
#     print(event)
#     print("charge paid")

def remove_trial_sub(customer,subscription):
    trials = customer.subscriptions.filter(status='trialing').filter(~Q(id=subscription.id))
    for trial in trials:
        trial.cancel(at_period_end=False)


@webhooks.handler("invoice.paid")
def my_handler(event, **kwargs):
    print(event.data)
    data =event.data
    paymentintent=data.get('object').get('payment_intent',None)
    if paymentintent:
        payment_obj=PaymentIntent.objects.get(id=paymentintent)
    else :
        payment_obj=None


        #pay_id=data.get('object').get('id',None)
        # if pay_id != None:
        #     paymentintent = PaymentIntent.objects.get(id=pay_id)
        # else:
        #     paymentintent = None

    price=data['object']['lines']['data'][0]['price']['id']
    quants= data['object']['lines']['data'][0]['quantity']
    customer=data.get('object').get('customer')
    cust_obj = Customer.objects.get(id=customer)
    user=cust_obj.subscriber
    if user == None:
        raise ValueError("No user Found")
    print("----user-------",user)
    invoice=data.get('object').get('id') 
    invoice_obj=Invoice.objects.get(id=invoice)
    sub=data['object']['lines']['data'][0]['subscription']
    subscription = Subscription.objects.get(id=sub)
    bill_reason = data['object']['billing_reason'] 
    amount_paid=data['object']['amount_paid']
    if bill_reason != 'subscription_create' and amount_paid != 0:
        modify_subscription_data(subscription)

    remove_trial_sub(cust_obj,subscription)
    #meta = data['object']['metadata']
    price_obj= Price.objects.get(id=price)
    if price_obj.id != subscription.plan.id:
        print("Subscription not updated yet")
    sub_type=data['object']['lines']['data'][0]['metadata']['type']
    if subscription.status == 'trialing':
        trial = True
        cp = models.CreditPack.objects.get(product=price_obj.product,type='Subscription_Trial')
    else:
        cp = models.CreditPack.objects.get(product=price_obj.product,type='Subscription')
        trial=False
    #print(data['object']['metadata'])
    #quants= int(meta.get('quantity'))
    update_user_credits(user=user,cust=cust_obj,price=price_obj,
                        quants=quants,invoice=invoice_obj,payment=payment_obj,pack=cp,subscription=subscription,trial=trial)
    # kwarg = {
    #     'user':user,
    #     'stripe_cust_id':cust_obj,
    #     'price_id':price,Subscription_Trial
    #     'Buyed_credits':cp.credits*quants,
    #     'credits_left':cp.credits*quants,
    #     'expiry': expiry,
    #     'invoice':invoice_obj,
    #     'paymentintent':
    #     }
    # print(kwarg)
    # us = models.UserCredits.objects.create(**kwarg)
    # print(us)
    #print(event.data.object)


# @webhooks.handler("customer.tax_id.created")
# def my_handler(event, **kwargs):
#     print(event.data)


# def modify_invoice(invoice_id,tax_rate):
#     if settings.STRIPE_LIVE_MODE == True :
#         api_key = settings.STRIPE_LIVE_SECRET_KEY
#     else:
#         api_key = settings.STRIPE_TEST_SECRET_KEY

#     stripe.api_key = api_key

#     stripe.Invoice.modify(
#     invoice_id,
#     default_tax_rates=taxrate
#     )

# @webhooks.handler("invoice.created")
# def my_handler(event, **kwargs):
#     print("**** invoice Created *****")
#     print(event.data)
#     print("**** invoice  End *****")
    
#     if event.data.object.billing_reason == 'subscription_update':
#         customer=event.data.get('object').get('customer',None)
#         invoice_id=event.data.get('object').get('id',None)
#         cust_obj=Customer.objects.get(id=customer)
#         user=cust_obj.subscriber
#         if user.country.sortname == 'IN':
#             try:
#                 addr=models.BillingAddress.objects.get(user=user)
#             except models.BillingAddress.DoesNotExist:
#                 print("Billing Address Not Found")
#             state = IndianStates.objects.filter(state_name__icontains=addr.state)
#             if state.exists() and state.first().state_code == 'TN':
#                 tax_rate=[TaxRate.objects.get(display_name = 'CGST').id,TaxRate.objects.get(display_name = 'SGST').id]
#             elif state.exists():
#                 tax_rate=[TaxRate.objects.get(display_name = 'IGST').id,]
#         else:            
#             tax_rate=None

#         modify_invoice(invoice_id=invoice_id,tax_rate=tax_rate)


# def subscriptin_modify_default_tax_rate(sub_id,tax_rates):
#     if settings.STRIPE_LIVE_MODE == True :
#         api_key = settings.STRIPE_LIVE_SECRET_KEY
#     else:
#         api_key = settings.STRIPE_TEST_SECRET_KEY

#     stripe.api_key = api_key
#     if tax_rates != None:
#         response = stripe.Subscription.modify(
#         sub_id,
#         default_tax_rates=tax_rates
#         )
#         print(response)

# @webhooks.handler("customer.subscription.created")
# def my_handler(event, **kwargs):

#     print("**** invoice Created *****")
#     print(event.data)
#     print("**** invoice  End *****") 
#     data = event.data
#     sub_id=data['object']['id']
#     customer=event.data.get('object').get('customer',None)
#     cust_obj=Customer.objects.get(id=customer)
#     user=cust_obj.subscriber
#     try:
#         addr=models.BillingAddress.objects.get(user=user)
#     except models.BillingAddress.DoesNotExist:
#         print("Billing Address Not Found")

#     if user.country.sortname == 'IN' and addr.country.sortname == 'IN':
#         state = IndianStates.objects.filter(state_name__icontains=addr.state)
#         if state.exists() and state.first().state_code == 'TN':
#             tax_rate=[TaxRate.objects.get(display_name = 'CGST').id,TaxRate.objects.get(display_name = 'SGST').id]
#         elif state.exists():
#             tax_rate=[TaxRate.objects.get(display_name = 'IGST').id,]
#     else:            
#         tax_rate=None

#     subscriptin_modify_default_tax_rate(sub_id=sub_id,tax_rates=tax_rate)


@webhooks.handler("customer.subscription.updated")
def my_handler(event, **kwargs):
    print("**** customer updated *****")
    print(event.data)
    print("**** customer updated   End *****")
    # stripe.Subscription.modify(
    # "sub_C6Am1ELc0KQvPV",
    #  metadata={"order_id": "6735"},
    # )


def modify_subscription_data(subscription):
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY
    stripe.api_key = api_key

    stripe.Subscription.modify(
    subscription.id,
    metadata={'type':'subscription'}
    )






@webhooks.handler("customer.subscription.trial_will_end")
def my_handler(event, **kwargs):
    print("**** customer trial_end *****")
    print(event.data)
    print("**** customer trial_end   End *****")
    # stripe.Subscription.modify(
    # "sub_C6Am1ELc0KQvPV",
    #  metadata={"order_id": "6735"},
    # )


def subscription_delete(sub):
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY
    stripe.api_key = api_key
    stripe.Subscription.delete(sub.id)



@webhooks.handler("customer.updated")
def my_handler(event, **kwargs):
    print("**** customer updated start *****")
    print(event.data)
    data=event.data
    print("**** customer updated end *****")
    custid=data['object']['id']
    address = data['object']['address']
    name = data['object']['name']
    update_aiuser_billing(custid,address,name)
    # stripe.Subscription.modify(
    # "sub_C6Am1ELc0KQvPV",
    #  metadata={"order_id": "6735"},
    # )


def update_aiuser_billing(custid,address,name=None):
    customer = Customer.objects.get(id=custid)
    if customer.subscriber!=None:
        addr = models.BillingAddress.objects.filter(user=customer.subscriber).first()
        if addr== None:
            addr=models.BillingAddress(user=customer.subscriber)
        
        print('addr>>>>',addr)

        if settings.STRIPE_LIVE_MODE == True :
            api_key = settings.STRIPE_LIVE_SECRET_KEY
        else:
            api_key = settings.STRIPE_TEST_SECRET_KEY

        stripe.api_key = api_key

        # response = stripe.Customer.retrieve(custid)
        # address=response['address']


        kwarg = dict()
        if address != None:
            if addr.name!= name:
                if name == None:
                    kwarg['name']=customer.subscriber.fullname 
                else:
                    kwarg['name']=name
            if address['line1'] != None and addr.line1!= address['line1']:
                kwarg['line1']=address['line1'] 
            if address['line2'] != None and addr.line2!= address['line2']:
                kwarg['line2']= address['line2']
            if address['state'] != None and addr.state!= address['state']:
                kwarg['state']= address['state']
            if address['city'] != None and addr.city!= address['city']:
                kwarg['city']=address['city']
            if address['postal_code'] != None and addr.zipcode != address['postal_code']:
                kwarg['zipcode']=address['postal_code']
            if address['country'] != None :
                if addr.country != None:
                    if addr.country.sortname != address['country']:
                        coun=Countries.objects.get(sortname= address['country'])
                        kwarg['country']=coun
                else:
                    coun=Countries.objects.get(sortname= address['country'])
                    kwarg['country']=coun

        if len(kwarg)>0:
            addr.__dict__.update(kwarg)
            if kwarg.get('country',None)!= None:
                addr.country=kwarg['country']
            addr.save()
