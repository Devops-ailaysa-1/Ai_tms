import random 

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