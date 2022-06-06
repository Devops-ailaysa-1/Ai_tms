import os
import random

def create_dirs_if_not_exists(path):
	if not os.path.isdir(path):
		os.makedirs(path)
		return  path
	return create_dirs_if_not_exists(path+random.choice(["-", "_","@", "!"])+str(random.randint(1,100)))

def print_key_value(keys, values):
	for i, j in zip(keys, values):
		print(f'{i}--->{j}')


def create_assignment_id():
	from ai_workspace.models import TaskAssignInfo
	rand_id = "AssId-"+str(random.randint(1,10000))
	pr = TaskAssignInfo.objects.filter(assignment_id = rand_id)
	if not pr:
		return  rand_id
	return create_assignment_id()
# //////////////// References \\\\\\\\\\\\\\\\\\\\

# random.choice([1,2,3])  ---> 2
# random.choice([1,2,3])  ---> 2
# random.choices([1,2,3])  ---> [2]
