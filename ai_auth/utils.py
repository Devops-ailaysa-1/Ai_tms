import random
from djstripe.models import Customer,Subscription,Account
from django.db.models import Q
import time

try:
    default_djstripe_owner=Account.get_default_account()
except BaseException as e:
    print(f"Error : {str(e)}")

max_iter = ((10**6)/3)

def get_unique_uid(klass, iter_count=1):
	# Aiuser is the klass
	if iter_count == max_iter:
		# Should be logged properly if max iteration reached
		return  None
	uid = random.randint(1, 10**6)
	if not klass.objects.filter(uid=uid):
		return "u"+ str(uid)
	return get_unique_uid(klass, iter_count+1)



def get_unique_pid(klass, iter_count=1):
	if iter_count == max_iter:
		# Should be logged properly if max iteration reached
		return  None
	temp_proj_id = random.randint(1, 10**6)
	if not klass.objects.filter(temp_proj_id=temp_proj_id):
		return "tp"+ str(temp_proj_id)
	return get_unique_uid(klass, iter_count+1)

# ////////////////////// References \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

# import random  ---> None
# random.randint(1,100)  ---> 58
# random.randint(1000,10000)  ---> 4579


def get_plan_name(user):
	try:
		customer = Customer.objects.get(subscriber=user,djstripe_owner_account=default_djstripe_owner)
	except Customer.DoesNotExist:
		time.sleep(4)
		try:
			customer = Customer.objects.get(subscriber=user,djstripe_owner_account=default_djstripe_owner)
		except Customer.DoesNotExist:
			time.sleep(4)
			customer = Customer.objects.get(subscriber=user,djstripe_owner_account=default_djstripe_owner)
	#subscriptions = Subscription.objects.filter(customer=customer).last()
	sub = customer.subscriptions.filter(Q(status='active')|Q(status='trialing')|Q(status='past_due')).last()
	if sub:
		name = sub.plan.product.name
		return name
	else: return None


def get_currency_based_on_country(user):
	pass
