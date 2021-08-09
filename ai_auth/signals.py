from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import settings
from django.utils.text import slugify
import os
import random

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
