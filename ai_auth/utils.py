import random
from djstripe.models import Customer,Subscription,Account
from django.db.models import Q
import time
from django.core.exceptions import PermissionDenied
from django_oso.auth import authorize
import django_oso

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
	uid = "u"+ str(random.randint(1, 10**6))
	if not klass.objects.filter(uid=uid):
		return uid
	return get_unique_uid(klass, iter_count+1)



def get_unique_pid(klass, iter_count=1):
	if iter_count == max_iter:
		# Should be logged properly if max iteration reached
		return  None
	temp_proj_id = "tp" + str(random.randint(1, 10**6))
	if not klass.objects.filter(temp_proj_id=temp_proj_id):
		return temp_proj_id
	return get_unique_uid(klass, iter_count+1)

# ////////////////////// References \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\

# import random  ---> None
# random.randint(1,100)  ---> 58
# random.randint(1000,10000)  ---> 4579


def get_plan_name(user):
	try:
		customer = Customer.objects.get(subscriber=user,djstripe_owner_account=default_djstripe_owner)
	except Customer.DoesNotExist:
		resync_instances(user.djstripe_customers.all())
		customer = Customer.objects.get(subscriber=user,djstripe_owner_account=default_djstripe_owner)
	#subscriptions = Subscription.objects.filter(customer=customer).last()
	sub = customer.subscriptions.filter(Q(status='active')|Q(status='trialing')|Q(status='past_due')).last()
	if sub:
		name = sub.plan.product.name
		return name
	else: return None


def get_currency_based_on_country(user):
	pass



def filter_authorize(request,query,action,user):
	auth_ids = [] 
	for instance in query:
		try:
			authorize(request ,resource=instance, actor=user, action=action)
			auth_ids.append(instance.id)
		except PermissionDenied:
			continue
	return query.filter(id__in = auth_ids)

def authorize_list(obj_list,action,user):
	for instance in obj_list:
		if not django_oso.oso.Oso.is_allowed(
			actor=user, resource=instance, action=action):
			obj_list.remove(instance)
	return obj_list
			

	# 	try:
	# 		obj_is_allowed()
	# 		authorize(request ,resource=instance, actor=user, action=action)
	# 		auth_ids.append(instance.id)
	# 	except PermissionDenied:
	# 		continue
	# return query.filter(id__in = auth_ids)

def obj_is_allowed(obj,action,user):
	if not django_oso.oso.Oso.is_allowed(
		actor=user, resource=obj, action=action
	):
		raise PermissionDenied

def objls_is_allowed(obj_ls,action,user):
	for obj in obj_ls:
		if isinstance(obj, tuple):
			obj = obj[0]
		if not django_oso.oso.Oso.is_allowed(
			actor=user, resource=obj, action=action
		):
			raise PermissionDenied