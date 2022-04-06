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


def create_ai_project_id_if_not_exists(user):
	from ai_workspace.models import Project
	rand_id = user.uid+"p"+str(random.randint(1,10000))
	pr = Project.objects.filter(ai_project_id = rand_id)
	if not pr:
		return  rand_id
	return create_ai_project_id_if_not_exists(user)

# //////////////// References \\\\\\\\\\\\\\\\\\\\

# random.choice([1,2,3])  ---> 2
# random.choice([1,2,3])  ---> 2
# random.choices([1,2,3])  ---> [2]
