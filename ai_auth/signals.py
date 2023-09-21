from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver,Signal
from django.contrib.auth import settings
from django.utils.text import slugify
#from ai_auth.api_views import update_billing_address
from ai_auth import models as auth_model
from ai_staff import models as staff_model
import os, requests
import random
from djstripe.models import Customer,Account
import stripe
from allauth.account.signals import email_confirmed, password_changed,user_signed_up
from ai_auth import forms as auth_forms
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import Group
from django.db.models import Q
from django.db import IntegrityError
import logging
logger = logging.getLogger('django')
import requests

try:
    default_djstripe_owner=Account.get_default_account()
except BaseException as e:
    print(f"Error : {str(e)}")

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


def vendor_status_send_email(sender, instance, *args, **kwargs):
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


def create_lang_details(lang_pairs,instance):
    from ai_vendor.models import VendorLanguagePair
    for i in lang_pairs:
        if i.get('services')[0].get('service_id') == 1:
            pairs = i.get('pair_code')
            src,tar = pairs.split('_')
            print(src,tar)
            source = staff_model.ProzLanguagesCode.objects.filter(language_code = src).first().language.id
            target = staff_model.ProzLanguagesCode.objects.filter(language_code = tar).first().language.id
            try:
                lang,created = VendorLanguagePair.objects.get_or_create(source_lang_id=source,target_lang_id=target,user=instance)
                print(lang, created)
            except:pass

def proz_msg_send(user,msg,vendor):
    from ai_marketplace.serializers import ThreadSerializer
    thread_ser = ThreadSerializer(data={'first_person':user.id,'second_person':vendor.id})
    if thread_ser.is_valid():
        thread_ser.save()
        thread_id = thread_ser.data.get('id')
    else:
        thread_id = thread_ser.errors.get('thread_id')
    print("Thread--->",thread_id)
    msg = ChatMessage.objects.create(message=msg,user=user,thread_id=thread_id)
    notify.send(user, recipient=vendor, verb='Message', description=msg,thread_id=int(thread_id))  

def proz_connect(sender, instance, *args, **kwargs):
    from ai_vendor.models import VendorsInfo
    from ai_vendor.models import VendorSubjectFields
    from ai_marketplace.api_views import get_sub_data
    from ai_marketplace.models import ProzMessage
    
    if instance.socialaccount_set.filter(provider='proz'):
        uuid = instance.socialaccount_set.filter(provider='proz').last().uid
        url = "https://api.proz.com/v2/freelancer/{uuid}".format(uuid = uuid)
        headers = {
        'X-Proz-API-Key': os.getenv("PROZ-KEY"),
        }
        response = requests.request("GET", url, headers=headers)
        res = response.json()
        if res and res.get('success') == 1:
            ven = res.get('data')
            if ven.get('qualifications',False):
                cv_file = ven.get('qualifications').get('cv_url',None)
                native_lang = ven.get('qualifications').get('native_language')[0]
            if ven.get('professional_history',False):
                year_of_experience = ven.get('professional_history').get('years_of_experience')
            location = ven.get('contact_info').get('address',{}).get('region',None)
            if ven.get('about_me_localizations') != []:
                bio = ven.get('about_me_localizations',[{}])[0].get('value', None)
            else:bio = None
            obj,created = VendorsInfo.objects.get_or_create(user=instance)
            obj.cv_file = cv_file
            if native_lang:
                obj.native_lang_id = staff_model.ProzLanguagesCode.objects.filter(language_code = native_lang).first().language.id
            obj.year_of_experience = year_of_experience
            obj.location = location
            obj.bio = bio
            obj.save()
            profile,created = auth_model.AiUserProfile.objects.get_or_create(user=instance)
            profile.organisation_name = ven.get('contact_info').get('company_name',None)
            profile.save()
            subs = get_sub_data(ven.get('skills').get("specific_disciplines"))
            [VendorSubjectFields.objects.create(user=instance,subject_id = i.get('subject')) for i in subs]
            lang_pairs = ven.get('skills').get('language_pairs',None)
            if lang_pairs:
                create_lang_details(lang_pairs,instance)
        queryset = ProzMessage.objects.filter(proz_uuid = uuid)
        for i in queryset:
            proz_msg_send(i.customer,i.message,instance)



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

    customer = Customer.objects.get(subscriber=taxid.user,djstripe_owner_account=default_djstripe_owner)
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
        customer = Customer.objects.get(subscriber=user,djstripe_owner_account=default_djstripe_owner)
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
            print("Inside Signal")
            queryset = staff_model.CurrencyBasedOnCountry.objects.filter(country_id = instance.country_id)
            print("Qr--------->",queryset)
            if queryset:
                print("Ins-------->",instance.id)
                print("inside if------>",queryset.first().currency_id)
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


@receiver(user_signed_up)
def populate_user_details(user, sociallogin=None,**kwargs):

    if sociallogin:
        full_name = None
        if sociallogin.account.provider == 'google':
            user_data = user.socialaccount_set.filter(provider='google')[0].extra_data
            full_name = user_data['name']
        if sociallogin.account.provider == 'proz':
            user_data = user.socialaccount_set.filter(provider='proz')[0].extra_data
            user.is_vendor = True
            if user_data.get('account_type') in ["2",]:
                user.is_agency = True
            if user_data['contact_info']['first_name'] == None:
                full_name = user_data['site_name']
            else:
                full_name = user_data['contact_info']['first_name'] + user_data['contact_info']['last_name']
        user.fullname = full_name
        user.first_login = True
        user.save()
        user_attr = auth_model.UserAttribute.objects.create(user=user,user_type_id=1)
        if user_attr == None:
             raise ValueError('User Attribute Not updated'  )

send_campaign_email= Signal()

@receiver(send_campaign_email)
def campaign_send_email(sender,instance,user, *args, **kwargs):
    if instance.subscribed == True:
        auth_forms.send_campaign_welcome_mail(user)

assign_object= Signal()

@receiver(assign_object)
def assign_object_task(sender, instance,user,role,*args, **kwargs):
    from ai_auth.models import TaskRoles
    from ai_staff.models import TaskRoleLevel
    from django.db import transaction
    # instance.step = 
    # role_name = {1:''Project owner'}  
    # tsk.task_assign.task.job.project.project_manager
    with transaction.atomic():
        ins=taskrole_update(instance,user)
        role = TaskRoleLevel.objects.get(role__name=role)
        try:
            TaskRoles.objects.create(user=user,task_pk=instance.task_assign.task.id,role=role,proj_pk=instance.task_obj.proj_obj.id)
        except IntegrityError as e: 
            logger.warning("task_role already exist {instance.task_assign.task.id},{user.uid}")    
        print("task created")

def taskrole_update(instance,user):
    from ai_workspace.models import AiRoleandStep
    from ai_auth.models import TaskRoles
    tsk_role = AiRoleandStep.objects.filter(Q(step=instance.task_assign.step)&Q(role__name__icontains='Invitee')).last().role
    obj=TaskRoles.objects.filter(task_pk=instance.task_assign.task.id,user=user,role__role=tsk_role).last()
    if obj:
        obj.delete()