# from django.db import transaction
from djstripe import webhooks
from djstripe.models import Customer,Price,Invoice,PaymentIntent
from ai_auth import models


# def add_credits(user,price,data):
#     pass





# @webhooks.handler("payment_intent.succeeded")
# def my_handler(event, **kwargs):
#     print(event)
#     data =event.data
#     invoice=data.get('object').get('invoice',None) 
#     if invoice == None:
#         customer=data.get('object').get('customer',None)
#         cust_obj = Customer.objects.get(id=customer)
#         user=cust_obj.subscriber
#         paymentintent=data.get('object').get('id',None)
        
#         if paymentintent:
#             payment_obj=PaymentIntent.objects.get(id=paymentintent)
#         else :
#             payment_obj=None
            
#         if invoice:
#             invoice_obj=Invoice.objects.get(id=invoice)
#         else :
#             invoice_obj=None

#         meta = data['object']['metadata']
#         price_obj= Price.objects.get(id=meta['price'])
#         cp = models.CreditPack.objects.get(price=price_obj)
#         print(data['object']['metadata'])
#         quants= int(meta.get('quantity'))
#         kwarg = {
#             'user':user,
#             'stripe_cust_id':cust_obj,
#             'price_id':meta.get('price'),
#             'Buyed_credits':cp.credits*quants,
#             'credits_left':cp.credits*quants,
#             'expiry': None,
#             'paymentintent':payment_obj,
#             'invoice':invoice_obj
#             }
#         us = models.UserCredits.objects.create(**kwarg)
#         print(us)
#         print("We should probably notify the user at this point")
        #print(event.data.object)


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
    # if paymentintent:
    #     payment_obj=PaymentIntent.objects.get(id=paymentintent)

    #meta = data['object']['metadata']
    price_obj= Price.objects.get(id=price)
    cp = models.CreditPack.objects.get(price=price_obj)
    if price == "price_1JQWziSAQeQ4W2LNzgKUjrIS":
        expiry = invoice_obj.period_end
    else:
        expiry = None
    #print(data['object']['metadata'])
    #quants= int(meta.get('quantity'))
    kwarg = {
        'user':user,
        'stripe_cust_id':cust_obj,
        'price_id':price,
        'Buyed_credits':cp.credits*quants,
        'credits_left':cp.credits*quants,
        'expiry': expiry,
        'invoice':invoice_obj
        }
    print(kwarg)
    us = models.UserCredits.objects.create(**kwarg)
    print(us)
    print("We should probably notify the user at this point")
    #print(event.data.object)