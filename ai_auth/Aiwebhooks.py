# from django.db import transaction
from django.conf import settings
import stripe
from ai_staff.models import IndianStates,Countries
from djstripe import webhooks
from djstripe.models import Customer,Price,Invoice,PaymentIntent,Account
from djstripe.models.billing import Plan, Subscription, TaxRate
from ai_auth import models
from ai_auth import forms as auth_forms
from ai_auth.utils import add_months
from django.db.models import Q
from django.utils import timezone
from django.db import transaction
import logging
from ai_auth.signals import send_campaign_email
import os

logger = logging.getLogger('django')
try:
    default_djstripe_owner=Account.get_default_account()
except BaseException as e:
    print(f"Error : {str(e)}")

def check_referred(user):
    try:
        models.ReferredUsers.objects.get(email=user.email)
        ref_cred= 18000
    except models.ReferredUsers.DoesNotExist:
        ref_cred =0
    return ref_cred

def check_campaign(user):
    camp = models.CampaignUsers.objects.filter(user=user,subscribed=False)
    if camp.count() == 1:
        logger.info(f"new campaign user {user.uid} ")
        camp = camp.last()
        camp.subscribed =True
        camp.save()
        send_campaign_email.send(
        sender=camp.__class__,
        instance = camp,
        user=user,
        )
        return camp.campaign_name.subscription_credits
    elif camp.count() > 1:
        logger.error(f"more than one campaign found open {user.uid}")
    else:
        return None


def calculate_addon_expiry(start_date,pack):
    if pack.expires_at == None:
        return None
    else:
        return add_months(start_date,pack.expires_at)

def update_user_credits(user,cust,price,quants,invoice,payment,pack,subscription=None,trial=None):
    carry = 0
    referral_credits = 0
    payg_credits = 0

    if pack.unit_type != "credits":
        update_purchaseunits(user,cust,price,quants,invoice,payment,pack)
        return 'created'


    if pack.type=="Subscription" and pack.name != os.environ.get("PLAN_PAYG"):
        if subscription.plan.interval=='year':
            expiry = expiry_yearly_sub(subscription)
        else:
            expiry = subscription.current_period_end
        # if pack.name != os.environ.get("PLAN_PAYG"):
        
        creditsls= models.UserCredits.objects.filter(user=user).filter(Q(credit_pack_type='Subscription')|Q(credit_pack_type='Subscription_Trial')).filter(~Q(invoice=invoice.id))
        for credit in creditsls:
            #check the previous subscription record has unused credits before expiry
            if credit.ended_at==None and (credit.expiry > timezone.now()):
                carry = credit.credits_left
            credit.ended_at=timezone.now()
            credit.save()

    elif pack.type=="Subscription" and pack.name == os.environ.get("PLAN_PAYG"): 
        user_credits = models.UserCredits.objects.filter(user=user).filter(Q(credit_pack_type='Subscription')|Q(credit_pack_type='Subscription_Trial'))
        if user_credits.count() == 0: 
            expiry = subscription.current_period_end
            camp = models.CampaignUsers.objects.filter(user=user,subscribed=False)
            if camp.count() > 0:
                camp_obj = camp.last()
                payg_credits = camp_obj.campaign_name.subscription_credits
                camp_obj.subscribed = True
                camp_obj.save()
            else:
                payg_credits = pack.credits
        else:
            expiry = subscription.current_period_end
            creditsls= user_credits.filter(~Q(invoice=invoice.id))
            for credit in creditsls:
                if credit.ended_at==None and (credit.expiry > timezone.now()):
                    carry = credit.credits_left
                    credit.ended_at=timezone.now()
                    credit.save()
                


    if pack.type=="Subscription_Trial":
        expiry = subscription.trial_end
        referral_credits = check_referred(user)
        creditsls= models.UserCredits.objects.filter(user=user).filter(Q(credit_pack_type='Subscription_Trial')).filter(~Q(invoice=invoice.id))
        for credit in creditsls:
            #check the previous subscription record has unused credits before expiry
            if credit.ended_at==None and (credit.expiry > timezone.now()):
                carry = credit.credits_left
            credit.ended_at=timezone.now()
            credit.save()

    if pack.type=="Addon":
        expiry = calculate_addon_expiry(timezone.now(),pack)
        
    if pack.product.name == 'Pro - V':
        camp_credits= check_campaign(user)
    else:
        camp_credits = None

    if camp_credits != None:
        buyed_credits = camp_credits
    elif pack.name == os.environ.get("PLAN_PAYG"):
        buyed_credits =  payg_credits
    else:
        buyed_credits = ((pack.credits*quants)+referral_credits)
    
    logger.info(f"user:{user.uid}, buyed:{buyed_credits}, credits_pack:{pack.credits}, quantity :{quants}, carry:{carry}")
    kwarg = {
    'user':user,
    'stripe_cust_id':cust,
    'price_id':price.id,
    'buyed_credits':buyed_credits,
    'credits_left':buyed_credits+carry,
    'expiry': expiry,
    'paymentintent':payment.id if payment else None,
    'invoice':invoice.id if invoice else None,
    'credit_pack_type': pack.type,
    'ended_at': None
    }

    us = models.UserCredits.objects.create(**kwarg)
    print(us)
    return 'created'

def update_purchaseunits(user,cust,price,quants,invoice,payment,pack,purchased=True):

    buyed_units = pack.credits   
    expiry = calculate_addon_expiry(timezone.now(),pack)
    if payment != None:
        if payment.amount_received > 0:
            purchased = True
    else:
        purchased = False

    kwarg = {
    'user':user,
    'stripe_cust_id':cust,
    'dj_stripe_price_id':price.id if price!=None else None,
    'purchase_pack_type':pack.type,
    'purchase_pack':pack,
    'units_buyed':buyed_units,
    # 'units_left':buyed_units,
    'expiry': expiry,
    'paymentintent':payment.id if payment else None,
    'invoice':invoice.id if invoice else None,
    'purchased': purchased,
    'buyed_at':payment.created if payment!=None else timezone.now(),
    'ended_at': None
    }

    PC = models.PurchasedUnits.objects.create(**kwarg)
    logger.info(f"user:{user.uid}, buyed:{buyed_units}, credits_pack:{pack.credits}, quantity :{quants}, carry:{0}")
    print(PC)
    # if pack.secondary_unit_type =! None:



@webhooks.handler("payment_intent.succeeded")
def my_handler(event, **kwargs):
    print(event)
    data =event.data
    invoice=data.get('object').get('invoice',None)
    if invoice == None:
        customer=data.get('object').get('customer',None)
        cust_obj = Customer.objects.get(id=customer,djstripe_owner_account=default_djstripe_owner)
        user=cust_obj.subscriber
        paymentintent=data.get('object').get('id',None)
        
        if paymentintent:
            payment_obj=PaymentIntent.objects.get(id=paymentintent,djstripe_owner_account=default_djstripe_owner)
        else :
            payment_obj=None
            
        if invoice:
            invoice_obj=Invoice.objects.get(id=invoice,djstripe_owner_account=default_djstripe_owner)
        else :
            invoice_obj=None

        meta = data['object']['metadata']
        price_obj= Price.objects.get(id=meta['price'],djstripe_owner_account=default_djstripe_owner)
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
    free_plans = customer.subscriptions.filter(plan__product__name=os.environ.get("PLAN_PAYG")).filter(~Q(id=subscription.id))
    for plan in free_plans:
        plan.cancel(at_period_end=False)

        
def remove_pro_v_sub(customer,subscription):
    subs = customer.subscriptions.filter(status='active').filter(plan__product__name='Pro - V').filter(~Q(id=subscription.id))
    for sub in subs:
        sub.cancel(at_period_end=False)

@webhooks.handler("invoice.paid")
def my_handler(event, **kwargs):
    print(event.data)
    data =event.data
    paymentintent=data.get('object').get('payment_intent',None)
    if paymentintent:
        payment_obj=PaymentIntent.objects.get(id=paymentintent,djstripe_owner_account=default_djstripe_owner)
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
    cust_obj = Customer.objects.get(id=customer,djstripe_owner_account=default_djstripe_owner)
    user=cust_obj.subscriber
    if user == None:
        raise ValueError("No user Found")
    print("----user-------",user)
    invoice=data.get('object').get('id') 
    invoice_obj=Invoice.objects.get(id=invoice,djstripe_owner_account=default_djstripe_owner)
    sub=data['object']['lines']['data'][0]['subscription']
    subscription = Subscription.objects.get(id=sub,djstripe_owner_account=default_djstripe_owner)
    bill_reason = data['object']['billing_reason'] 
    amount_paid=data['object']['amount_paid']
    if bill_reason != 'subscription_create' and amount_paid != 0:
        modify_subscription_data(subscription)

    remove_trial_sub(cust_obj,subscription)
    #meta = data['object']['metadata']
    price_obj= Price.objects.get(id=price,djstripe_owner_account=default_djstripe_owner)
    if price_obj.id != subscription.plan.id:
        print("Subscription not updated yet")
    #sub_type=data['object']['lines']['data'][0]['metadata']['type']
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
    print("**** customer subscription updated *****")
    print(event.data)
    data = event.data
    print("**** customer subscription updated   End *****")
    # subscription_prices = data.get('object').get('items').get('data')[0].get('price')
    # subscription_id = data.get('object').get('id')
    # print("subscription prices",subscription_prices)
    # print("subscription_id",subscription_id)
    # # customer_id = data.get('object').get('customer')
    # #price_id = data.get('object').get('items').get('data')[0].get('price').get('id')
    # try:
    #     price_id = data.get('object').get('pending_update').get("subscription_items")[0].get("price").get("id")

    # except AttributeError:
    #     price_id = None

    # sub = Subscription.objects.get(id=subscription_id)

    # if price_id:
    #     plan=Plan.objects.get(id=price_id)
    #     print("upcoming_plan",plan.interval)
    #     if sub.plan.interval == "month" and plan.interval == "year": 
    #         response = schedule_downgrading_subscription(subscription_id,price_id)
    #         print("***schedule interval start***")
    #         print(response)
    #         print("***schedule interval end***")
    # # stripe.Subscription.modify(
    # # "sub_C6Am1ELc0KQvPV",
    # #  metadata={"order_id": "6735"},
    # # )


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
    data = event.data
    print(event.data)
    print("**** customer trial_end   End *****")
    sub = Subscription.objects.get(id=data.get('object').get('id'),djstripe_owner_account=default_djstripe_owner)
    user = sub.customer.subscriber
    auth_forms.user_trial_end(user=user,sub=sub)
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
    customer = Customer.objects.get(id=custid,djstripe_owner_account=default_djstripe_owner)
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

@webhooks.handler("customer.subscription.deleted")
def my_handler(event, **kwargs):
    print("**** customer deleted start *****")
    print(event.data)
    data=event.data
    print("**** customer deleted end *****")
    custid=data.get('object').get('customer')
    cust_obj = Customer.objects.get(id=custid,djstripe_owner_account=default_djstripe_owner)
    user=cust_obj.subscriber
    subid=data.get('object').get('id')
    #invoice_obj = Invoice.objects.get(subscription_id=subid)
    #creditsls= models.UserCredits.objects.filter(user=user).filter(Q(invoice=invoice_obj.id))
    #for credit in creditsls:
    #    credit.ended_at=timezone.now()
    #    credit.save()
    # invoice=data.get('object').get('id') 
    # invoice_obj=Invoice.objects.get(id=invoice)
    #sub=data['object']['lines']['data'][0]['subscription']

def expiry_yearly_sub(sub):
    '''Montly renewal of Credits for Yearly Subscription'''
    start=sub.billing_cycle_anchor
    end=timezone.now()
    if start.day != end.day:
        print("This is Not bill date")

    print("no of months",abs(((start.year - end.year)*12)+start.month-end.month)+1)
    expiry= add_months(start,abs(((start.year - end.year)*12)+start.month-end.month)+1)
    return expiry



def subscription_credit_carry(user,invoice):

    pass


# def schedule_downgrading_subscription(subscription_id,price_id):
#     if settings.STRIPE_LIVE_MODE == True :
#         api_key = settings.STRIPE_LIVE_SECRET_KEY
#     else:
#         api_key = settings.STRIPE_TEST_SECRET_KEY

#     stripe.api_key = api_key
#     sub = Subscription.objects.get(id=subscription_id)
    

#     schedule_res = stripe.SubscriptionSchedule.create(
#     from_subscription=sub.id,
#     )
 

#     # stripe.SubscriptionSchedule.retrieve(
#     # schedule_res.id,
#     # )


#     response = stripe.SubscriptionSchedule.modify(
#     schedule_res.id,
#     end_behavior= "release",
#     proration_behavior = None,
#     phases=[
#         {
#         'items': [
#             {'price':  sub.plan.id },
#         ],
#         'start_date':int(sub.current_period_start.timestamp()),
#         'end_date': int(sub.current_period_end.timestamp()),
#         },
#         {
#         'items': [
#             {'price': price_id},
#         ],
#         },
#     ],
#     )

#     return response
 
def renew_user_credits_yearly(subscription):
    try:
        pack = models.CreditPack.objects.get(product=subscription.plan.product,type='Subscription')
        prev_cp = models.UserCredits.objects.filter(user=subscription.customer.subscriber,credit_pack_type='Subscription',price_id=subscription.plan.id,ended_at=None).last()
        expiry = expiry_yearly_sub(subscription)
        creditsls= models.UserCredits.objects.filter(user=subscription.customer.subscriber).filter(Q(credit_pack_type='Subscription')|Q(credit_pack_type='Subscription_Trial'))
        with transaction.atomic():
            for credit in creditsls:
                credit.ended_at=timezone.now()
                credit.save()
            kwarg = {
            'user':subscription.customer.subscriber,
            'stripe_cust_id':subscription.customer,
            'price_id':subscription.plan.id,
            'buyed_credits':pack.credits,
            'credits_left':pack.credits,
            'expiry': expiry,
            'credit_pack_type': pack.type,
            'ended_at': None
            }
            if prev_cp==None:
                logger.warning("user has no intial year subscription credits")
                kwarg['paymentintent']=None
                kwarg['invoice']=None
            else:
                kwarg['paymentintent']=prev_cp.paymentintent
                kwarg['invoice']=prev_cp.invoice
            us = models.UserCredits.objects.create(**kwarg)
    except Exception as e:
        logger.error('Failed to do something: ' + str(e))
