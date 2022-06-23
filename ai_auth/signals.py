from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver,Signal
from django.contrib.auth import settings
from django.utils.text import slugify
#from ai_auth.api_views import update_billing_address
from ai_auth import models as auth_model
from ai_staff import models as staff_model
import os
import random
from djstripe.models import Customer
import stripe
from allauth.account.signals import email_confirmed, password_changed
from ai_auth import forms as auth_forms
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import Group





def create_dirs_if_not_exists(path):
	if not os.path.isdir(path):
		os.makedirs(path)
		return  path
	return create_dirs_if_not_exists(path+random.choice(["-", "_","@", "!"])+str(random.randint(1,100)))

def create_allocated_dirs(sender, instance, *args, **kwargs):
    '''
    Allocating a specific directory to a user.
    '''
    if instance.allocated_dir == None:
        instance.allocated_dir = os.path.join(settings.MEDIA_ROOT, str(instance.user.uid))
        instance.allocated_dir = create_dirs_if_not_exists(instance.allocated_dir)



def  vendor_status_send_email(sender, instance, *args, **kwargs):
    from ai_auth.api_views import subscribe_vendor
    print("status----->",instance.get_status_display())
    if instance.get_status_display() == "Accepted":
       user = auth_model.AiUser.objects.get(email = instance.email)
       # user.is_vendor = True
       # user.save()
       # sub = subscribe_vendor(user)
       email = instance.email
       auth_forms.vendor_status_mail(email,instance.get_status_display())
    elif (instance.get_status_display() == "Waitlisted"):
       email = instance.email
       status = instance.get_status_display() #if instance.get_status_display() =="Rejected" else "Held"
       auth_forms.vendor_status_mail(email,status)
    elif instance.get_status_display() == "Request Sent":
       auth_forms.vendor_request_admin_mail(instance)


def shortlisted_vendor_list_send_email_new(sender, instance, created, *args, **kwargs):
    from ai_vendor.models import VendorLanguagePair
    from ai_auth import forms as auth_forms
    if created:
        jobs = instance.get_postedjobs
        lang_pair = VendorLanguagePair.objects.none()
        for obj in jobs:
            if obj.src_lang_id == obj.tar_lang_id:
                query = VendorLanguagePair.objects.filter(Q(source_lang_id=obj.src_lang_id) | Q(target_lang_id=obj.tar_lang_id) & Q(deleted_at=None)).distinct('user')
            else:
                query = VendorLanguagePair.objects.filter(Q(source_lang_id=obj.src_lang_id) & Q(target_lang_id=obj.tar_lang_id) & Q(deleted_at=None)).distinct('user')
            lang_pair = lang_pair.union(query)
        res={}
        for object in lang_pair:
            tt = object.source_lang.language if object.source_lang_id == object.target_lang_id else object.source_lang.language
            print(object.user.fullname)
            if object.user_id in res:
                res[object.user_id].get('lang').append({'source':object.source_lang.language,'target':tt})
            else:
                res[object.user_id]={'name':object.user.fullname,'user_email':object.user.email,'lang':[{'source':object.source_lang.language,'target':tt}],'project_deadline':projectpost.proj_deadline,'bid_deadline':projectpost.bid_deadline}
        auth_forms.vendor_notify_post_jobs(res)
        print("mailsent")
# def updated_billingaddress(sender, instance, *args, **kwargs):
#     '''Updating user billing address to stripe'''
#     res=update_billing_address(address=instance)
#     print("-----------updated customer address-------")

# def vendorsinfo_update(sender, instance, created, *args, **kwargs):
# 	from ai_vendor.models import VendorsInfo
# 	if created:
# 		try:
# 			user = AiUser.objects.get(email = instance.email)
# 			query = VendorsInfo.objects.filter(user=user)
# 			tt = query.update(cv_file=instance.cv_file)
# 			print("@@@@",tt)
# 		except:
# 			pass


# def update_billing_address(address):
#     if settings.STRIPE_LIVE_MODE == True :
#         api_key = settings.STRIPE_LIVE_SECRET_KEY
#     else:
#         api_key = settings.STRIPE_TEST_SECRET_KEY
#     try:
#         customer = Customer.objects.get(subscriber=address.user)
#     except Customer.DoesNotExist:
#         cust = Customer.get_or_create(subscriber=address.user)
#         customer = cust[0]
#     stripe.api_key = api_key
#     coun=None
#     # addr=auth_model.BillingAddress.filter(user=customer.subscriber)
#     response = stripe.Customer.retrieve(customer.id)
#     kwarg=dict()
#     stipe_addr=response['address']
#     if stipe_addr != None:
#         if stipe_addr['line1'] != None and address.line1 != stipe_addr['line1']:
#             kwarg['line1']=address.line1
#         if stipe_addr['line2'] != None and address.line2 != stipe_addr['line2']:
#             kwarg['line2']= address.line2
#         if stipe_addr['state'] != None and address.state != stipe_addr['state']:
#             kwarg['state']= address.state
#         if stipe_addr['city'] != None and address.city != stipe_addr['city']:
#             kwarg['city']=address.city
#         if stipe_addr['postal_code'] != None and address.zipcode != stipe_addr['postal_code']:
#             kwarg['postal_code']=address.zipcode
#         if stipe_addr['country'] != None :
#             if address.country != None:
#                 if address.country.sortname != stipe_addr['country']:
#                     coun=staff_model.Countries.objects.get(sortname= stipe_addr['country'])
#                     kwarg['country']=coun
#             else:
#                 coun=staff_model.Countries.objects.get(sortname= stipe_addr['country'])
#                 kwarg['country']=coun


#     if len(kwarg)>0:
#         if coun!= None:
#             coun_name=coun.sortname
#         else:
#              coun_name= None

#         response =stripe.Customer.modify(
#         customer.id,
#         name = address.name if address.name is not None else address.user.fullname,

#         address={
#         "city": address.city,
#         "line1": address.line1,
#         "line2": address.line2,
#         "state": address.state,
#         "country":coun_name ,
#         "postal_code": address.zipcode
#         },

#         )
#     return response
# def team_create(sender, instance,created, *args, **kwargs):
#     if created:
#         teamname = instance.fullname + "'s team"
#         team =auth_model.Team.objects.get_or_create(name=teamname,owner_id=instance.id)
#         print("Team Created")

def updated_user_taxid(sender, instance, *args, **kwargs):
    # ss=auth_model.UserTaxInfo.objects.get(id=instance.id)
    # print('args',args)
    # print('kwargs',kwargs)
    # if instance.stripe_tax_id==ss.stripe_tax_id and instance.tax_id==ss.tax_id:
    #     print("Already updated customer address")
    #     pass
    res=update_user_tax_id(taxid=instance)
    print("updated customer tax id")


def update_user_tax_id(taxid):
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY

    customer = Customer.objects.get(subscriber=taxid.user)
    stripe.api_key = api_key
    try:
        response= stripe.Customer.create_tax_id(
        customer.id,
        type=taxid.stripe_tax_id.tax_code,
        value=taxid.tax_id,
        )
    except stripe.error.InvalidRequestError as e:
        raise ValueError('Invalid Tax Id')
    return response


@receiver(email_confirmed)
def email_confirmed_(request, email_address, **kwargs):
    user = auth_model.AiUser.objects.get(email=email_address)
    current_site = get_current_site(request)
    auth_forms.send_welcome_mail(current_site,user)

@receiver(password_changed)
def password_changed_handler(request, user, **kwargs):
    current_site = get_current_site(request)
    auth_forms.send_password_change_mail(current_site, user)



update_billing_address2= Signal()

@receiver(update_billing_address2)
def password_changed_handler(request, user,instance, **kwargs):
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY
    try:
        customer = Customer.objects.get(subscriber=user)
    except Customer.DoesNotExist:
        cust = Customer.get_or_create(subscriber=user)
        customer = cust[0]
    stripe.api_key = api_key
    # addr=auth_model.BillingAddress.filter(user=customer.subscriber)
    #response = stripe.Customer.retrieve(customer.id)

    response =stripe.Customer.modify(
    customer.id,
    name = instance.name if instance.name is not None else instance.user.fullname,

    address={
    "city": instance.city,
    "line1": instance.line1,
    "line2": instance.line2,
    "state": instance.state,
    "country":instance.country.sortname ,
    "postal_code": instance.zipcode
    },

    )

def add_internal_member_group(user) -> bool:
    # add a user into member group
    internal_group = Group.objects.get_or_create(name = 'internal_members')[0]
    internal_group.user_set.add(user)
    return True

def update_internal_member_status(sender, instance, *args, **kwargs):
    if instance.is_internal_member:
        if instance.last_login:
            obj = auth_model.InternalMember.objects.get(internal_member = instance)
            obj.status = 2
            obj.save()
            # add_internal_member_group(user=instance.internal_member)
            print("status updated")


def get_currency_based_on_country(sender, instance, created, *args, **kwargs):
	if created:
		if instance.is_internal_member == True:
			instance.currency_based_on_country_id = 144
			instance.save()
		else:
			queryset = staff_model.CurrencyBasedOnCountry.objects.filter(country_id = instance.country_id)
			if queryset:
				instance.currency_based_on_country_id = queryset.first().currency_id
				instance.save()
			else:
				instance.currency_based_on_country_id = 144
				instance.save()




# def updated_user_taxid(sender, instance, *args, **kwargs):
def create_postjob_id(sender, instance, *args, **kwargs):
    if instance.postjob_id == None:
        instance.postjob_id = str(random.randint(1,10000))+"j"+str(instance.id)
        instance.save()
