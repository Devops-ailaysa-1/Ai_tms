# from django.db import transaction
from djstripe import webhooks
from djstripe.models import Customer,Price,Invoice,PaymentIntent
from djstripe.models.billing import Subscription
from ai_auth import models
from django.db.models import Q
from django.utils import timezone

# def add_credits(user,price,data):
#     pass


def update_user_credits(user,cust,price,quants,invoice,payment,pack,subscription=None):
    if pack.type=="Subscription":
        expiry = subscription.current_period_end
        creditsls= models.UserCredits.objects.filter(user=user,credit_pack_type='Subscription').filter(~Q(invoice=invoice.id))
        for credit in creditsls:
            credit.ended_at=timezone.now()
            credit.save()

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
    customer=data.get('object').get('customer',None)
    cust_obj = Customer.objects.get(id=customer)
    user=cust_obj.subscriber
    invoice=data.get('object').get('id') 
    invoice_obj=Invoice.objects.get(id=invoice)
    sub=data['object']['lines']['data'][0]['subscription']
    subscription = Subscription.objects.get(id=sub)
    #meta = data['object']['metadata']
    price_obj= Price.objects.get(id=price)
    if price_obj.id != subscription.plan.id:
        print("Subscription not updated yet")
    cp = models.CreditPack.objects.get(product=price_obj.product)
    #print(data['object']['metadata'])
    #quants= int(meta.get('quantity'))
    update_user_credits(user=user,cust=cust_obj,price=price_obj,
                        quants=quants,invoice=invoice_obj,payment=payment_obj,pack=cp,subscription=subscription)
    # kwarg = {
    #     'user':user,
    #     'stripe_cust_id':cust_obj,
    #     'price_id':price,
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
