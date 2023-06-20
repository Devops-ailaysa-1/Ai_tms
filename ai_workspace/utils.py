import os
import random
from django.core.files.uploadedfile import InMemoryUploadedFile
from io import StringIO, BytesIO
import sys
import string


class DjRestUtils:

    def get_a_inmemoryuploaded_file():
        io = BytesIO()
        with open("/home/langscape/Documents/translate_status_api.txt", "rb") as f:
            io.write(f.read())
        io.seek(0)
        im = InMemoryUploadedFile(io, None, "text.txt", "text/plain",
                sys.getsizeof(io), None)
        return im

    def convert_content_to_inmemoryfile(filecontent, file_name):
        # text/plain hardcoded may be needs to be change as generic...
        io = BytesIO()
        io.write(filecontent)
        io.seek(0)
        im = InMemoryUploadedFile(io, None, file_name,
                                  "text/plain", sys.getsizeof(io), None)
        return im

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
	chars=string.ascii_uppercase + string.digits
	size=6
	rand_id = "AS-"+''.join(random.choice(chars) for _ in range(size))
	pr = TaskAssignInfo.objects.filter(assignment_id = rand_id)
	if not pr:
		return  rand_id
	return create_assignment_id()



def create_task_id():
	from ai_workspace.models import Task
	chars=string.ascii_uppercase + string.digits
	size=6
	rand_id = "TK-"+''.join(random.choice(chars) for _ in range(size))
	pr = Task.objects.filter(ai_taskid = rand_id)
	if not pr:
		return  rand_id
	return create_task_id()


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
import math

def roundup(x):
    return int(math.ceil(x / 15.0)) * 15



def get_consumable_credits_for_text_to_speech(total_chars):
    return round(total_chars/20)

def get_consumable_credits_for_speech_to_text(total_seconds):#######Minimum billable 15 seconds##########
    return round(roundup(total_seconds)/3)

def task_assing_role_ls(task_assign_info_ls):
	from ai_auth.signals import assign_object
	from ai_auth.utils import get_assignment_role
	from ai_workspace.models import TaskAssignInfo
	from ai_workspace.models import AiRoleandStep
	objs = TaskAssignInfo.objects.filter(id__in=task_assign_info_ls)
	for instance in objs:
		role = get_assignment_role(instance.task_assign.step,instance.task_assign.reassigned)
		# role= AiRoleandStep.objects.get(step=instance.task_assign.step).role.name
		assign_object.send(
			sender=TaskAssignInfo,
			instance = instance,
			user=instance.task_assign.assign_to,
			role = role
		)