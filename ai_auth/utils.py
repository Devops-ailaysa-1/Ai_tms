import random
from djstripe.models import Customer,Subscription
from django.db.models import Q

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
	customer = Customer.objects.get(subscriber=user)
	#subscriptions = Subscription.objects.filter(customer=customer).last()
	sub = customer.subscriptions.filter(Q(status='active')|Q(status='trialing')|Q(status='past_due')).last()
	if sub:
		name = sub.plan.product.name
		return name
	else: return None


def get_currency_based_on_country(user):
	pass
