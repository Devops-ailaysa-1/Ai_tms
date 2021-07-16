from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import settings
from django.utils.text import slugify
import os 
import random

from .utils import create_dirs_if_not_exists

def create_allocated_dirs(sender, instance, *args, **kwargs):
    '''
    Allocating a specific directory to a user.
    '''
    if instance.allocated_dir == None:
        # Assumed every email should contains @ symbol,so splitting with @ gives prefix and domain 
        if "@" not in instance.email: # Django Email Validation Class is the reference
            raise ValueError("email should contain @ symbol")
        email_pre, domain = instance.email.split("@")
        instance.allocated_dir = os.path.join(settings.MEDIA_ROOT, slugify(email_pre)) 
        # creating directory and reassigning the dir path if any change in path 
        # see create_dirs_if_not_exists function to get better understanding
        instance.allocated_dir = create_dirs_if_not_exists(instance.allocated_dir)         

def create_project_dir(sender, instance, *args, **kwargs):
    '''
    Creating a project directory to upload files in a specific project...
    '''
    if instance.project_dir_path == None:
        instance.project_dir_path = os.path.join(instance.ai_user.userattribute.allocated_dir, slugify(instance.ai_project_id))
        instance.project_dir_path = create_dirs_if_not_exists(instance.project_dir_path)   

def create_pentm_dir_of_project(sender, instance, created, *args, **kwargs):
    if created:
        instance.penseive_tm_klass.objects.create(project=instance)

def set_pentm_dir_of_project(sender, instance, *args, **kwargs):
    if instance.penseive_tm_dir_path == None:
        instance.penseive_tm_dir_path = os.path.join(instance.project.project_dir_path, ".pentm")
        create_dirs_if_not_exists(instance.penseive_tm_dir_path)