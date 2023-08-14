from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import settings
from django.utils.text import slugify
import os,shutil
import random
from django.db import IntegrityError

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


def delete_project_dir(sender, instance, *args, **kwargs):
    print(instance.project_dir_path)
    shutil.rmtree(instance.project_dir_path)
    print("<-----------------Deleted------------------>")

def create_pentm_dir_of_project(sender, instance, created, *args, **kwargs):
    if created:
        instance.penseive_tm_klass.objects.create(project=instance)

def set_pentm_dir_of_project(sender, instance, *args, **kwargs):
    if instance.penseive_tm_dir_path == None:
        instance.penseive_tm_dir_path = os.path.join(instance.project.project_dir_path, ".pentm")
        create_dirs_if_not_exists(instance.penseive_tm_dir_path)
        instance.source_tmx_dir_path = os.path.join(instance.project.project_dir_path, "source_tmx")
        create_dirs_if_not_exists(instance.source_tmx_dir_path)

def check_job_file_version_has_same_project(sender, instance, *args, **kwargs):
    if (instance.file!=None) and (instance.job!=None) :
        if not (instance.file.project == instance.job.project):
            raise IntegrityError("Project of a file and job should same!!!")

    # if instance.job.project

# def extract_project_instance(instance):
#     if type(instance) is Project:
#         return instance
#     elif type(instance) is Task:
#         return instance.job.project
#     elif type(instance) is Document:
#         return instance.job.project
#     elif type(instance) is Glossary:
#         return instance.project
#     elif type(instance) is TermsModel:
#         return instance.glossary.project
#     elif type(instance) is Segment:
#         return instance.text_unit.document.job.project   
#     elif type(instance) is ExpressProjectDetail:
#         return instance.task.job.project   
#     elif type(instance) is TaskTranscriptDetails:
#         return instance.task.job.project   
#     return None

# # Signal receiver for cache invalidation

# @receiver(post_save, sender=Glossary)
# @receiver(post_save, sender=TermsModel)
# @receiver(post_save, sender=Project)
# @receiver(post_save, sender=Document)
# @receiver(post_save, sender=Task)
# @receiver(post_save, sender= Segment)
# @receiver(post_save, sender= ExpressProjectDetail)
# @receiver(post_save, sender= TaskTranscriptDetails)
# # @receiver(post_delete, sender=Glossary)
# # @receiver(post_delete, sender=TermsModel)

# def invalidate_project_cache(sender, instance, **kwargs):
#     project = extract_project_instance(instance)
#     if project:
#         print("Inside if")
#         cache_key = f'pr_progress_property_{project.pk}'
#         cache.delete(cache_key)
#         print("Deleted")
from django.core.cache import cache
#from cacheops import invalidate_obj

def invalidate_cache_on_save(sender, instance, **kwargs):
    print("instance----------->",instance)
    #invalidate_obj(instance)
    cache_keys = instance.generate_cache_keys()
    print("Keys on save----------->",cache_keys)
    if cache_keys:
        for cache_key in cache_keys:
            try:
                cache.delete(cache_key)
                cache.delete_pattern(cache_key)
            except:
                print("Not found")
                pass
               
                

def invalidate_cache_on_delete(sender, instance, **kwargs):
    print("instance----------->",instance)
    #invalidate_obj(instance)
    cache_keys = instance.generate_cache_keys()
    print("Keys on delete----------->",cache_keys)
    if cache_keys:
        for cache_key in cache_keys:
            try:
                cache.delete(cache_key)
                cache.delete_pattern(cache_key)
            except:
                print("Not found")
                pass