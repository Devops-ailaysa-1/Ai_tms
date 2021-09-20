
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import settings
from django.utils.text import slugify
#from ai_auth.api_views import update_billing_address
import os
import random
from djstripe.models import Customer
import stripe

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


def updated_billingaddress(sender, instance, *args, **kwargs):
    res=update_billing_address(address=instance)
    print("updated customer address")




def update_billing_address(address):
    if settings.STRIPE_LIVE_MODE == True :
        api_key = settings.STRIPE_LIVE_SECRET_KEY
    else:
        api_key = settings.STRIPE_TEST_SECRET_KEY    
    try:
        customer = Customer.objects.get(subscriber=address.user)
    except Customer.DoesNotExist:
        customer = Customer.objects.get(subscriber=address.user)

    stripe.api_key = api_key
    response =stripe.Customer.modify(
    customer.id,
    name = address.name if address.name is not None else address.user.fullname, 
    address={
    "city": address.city,
    "line1": address.line1,
    "line2": address.line2,
    "state": address.state,
    "country": address.country.sortname,
    "postal_code": address.zipcode
    },

    )
    return response