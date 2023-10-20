import os
import random
import re
import string
from django.db.models import Prefetch
from django.db.models.expressions import F
from ai_staff.serializer import AiSupportedMtpeEnginesSerializer
from ai_auth.utils import get_unique_pid
from django.db import models, IntegrityError
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import User
from django.db.models.base import Model
from django.utils.text import slugify
from datetime import datetime, date
from enum import Enum
from django.db import models, transaction, connection
from django.contrib.auth import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Q, Sum
from django.db.models.fields.files import FileField
from django.db.models.signals import post_save, pre_save, post_delete, pre_delete
from django.shortcuts import reverse
from django.utils.functional import cached_property
from django.db import transaction
from ai_auth.models import AiUser, Team
from ai_auth.utils import get_unique_pid
from ai_staff.models import AilaysaSupportedMtpeEngines, AssetUsageTypes, \
    Currencies, ProjectTypeDetail,AiRoles,AiCustomize
from ai_staff.models import Billingunits, MTLanguageLocaleVoiceSupport
from ai_staff.models import ContentTypes, Languages, SubjectFields, ProjectType,DocumentType
from .manager import AilzaManager
from .utils import create_dirs_if_not_exists, create_task_id
from ai_workspace_okapi.utils import SpacesService
from .signals import (create_allocated_dirs, create_project_dir, \
    create_pentm_dir_of_project,set_pentm_dir_of_project, \
    check_job_file_version_has_same_project,invalidate_cache_on_save,invalidate_cache_on_delete)
from .manager import ProjectManager, FileManager, JobManager,\
    TaskManager,TaskAssignManager,ProjectSubjectFieldManager,ProjectContentTypeManager,ProjectStepsManager
from django.db.models.fields import Field
# from integerations.github_.models import ContentFile
# from integerations.base.utils import DjRestUtils
from ai_workspace.utils import create_ai_project_id_if_not_exists
from ai_workspace_okapi.models import Document, Segment
from ai_workspace_okapi.utils import get_processor_name, get_file_extension
from .manager import ProjectManager, FileManager, JobManager, \
    TaskManager, TaskAssignManager, ProjectSubjectFieldManager, ProjectContentTypeManager, ProjectStepsManager
from .signals import (create_project_dir, delete_project_dir,\
                      create_pentm_dir_of_project, set_pentm_dir_of_project, \
                      check_job_file_version_has_same_project, )
from .utils import create_dirs_if_not_exists, create_task_id

from ai_workspace_okapi.models import SplitSegment
from django.db.models.functions import Cast
from django.db.models import CharField
from django.core.cache import cache
import functools


def set_pentm_dir(instance):
    path = os.path.join(instance.project.project_dir_path, ".pentm")
    create_dirs_if_not_exists(path)
    return path

class TempProject(models.Model):
    temp_proj_id =  models.CharField(max_length=50 , null=False, blank=True)
    mt_engine = models.ForeignKey(AilaysaSupportedMtpeEngines,null=True, blank=True, \
        on_delete=models.CASCADE, related_name="temp_proj_mt_engine")

    def save(self, *args, **kwargs):
        if not self.temp_proj_id:
            self.temp_proj_id = get_unique_pid(TempProject)
        return super().save(*args, **kwargs)

def get_temp_file_upload_path(instance, filename):
    file_path = os.path.join("temp_projects",instance.temp_proj.temp_proj_id,\
            "source")
    return os.path.join(file_path, filename)


class Templangpair(models.Model):
    temp_proj = models.ForeignKey(TempProject, on_delete=models.CASCADE,
                        related_name="temp_proj_langpair")
    source_language = models.ForeignKey(Languages, null=False, blank=False, on_delete=\
        models.CASCADE, related_name="temp_source_lang")
    target_language = models.ForeignKey(Languages, null=False, blank=False, on_delete=\
        models.CASCADE, related_name="temp_target_lang")

class PenseiveTM(models.Model):
    penseive_tm_dir_path = models.FilePathField(max_length=1000, null=True,\
        path=settings.MEDIA_ROOT, blank=True, allow_folders=True, allow_files=False)
    source_tmx_dir_path = models.FilePathField(max_length=1000, null=True, \
        path=settings.MEDIA_ROOT, blank=True, allow_folders=True, allow_files=False)
    project = models.OneToOneField("Project", null=False, blank=False, on_delete=models.\
        CASCADE, related_name="project_penseivetm")

    # class Meta:
    #     managed = False
    @property
    def owner_pk(self):
        return self.project.owner_pk

pre_save.connect(set_pentm_dir_of_project, sender=PenseiveTM)


class Steps(models.Model):
    name = models.CharField(max_length=191)
    short_name = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    def __str__(self):
        return self.name

class Workflows(models.Model):
    name = models.CharField(max_length=191)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    standard = models.BooleanField(default=False)
    user = models.ForeignKey(AiUser,on_delete=models.CASCADE,blank=True,null=True,related_name='user_workflow')

    @property
    def owner_pk(self):
        return self.user.id

    def __str__(self):
        return self.name

def my_docs_upload_path(instance, filename):
    file_path = os.path.join(instance.user.uid,"MyDocuments", filename)
    return file_path

class WriterProject(models.Model):
    proj_name = models.CharField(max_length=1000, null=True, blank=True,)
    ai_user = models.ForeignKey(AiUser, null=False, blank=False,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    def save(self, *args, **kwargs):
      
        if not self.proj_name:
            self.proj_name = 'AiWriter-'+str(WriterProject.objects.filter(ai_user=self.ai_user).count()+1).zfill(3)+'('+str(date.today()) +')'
            
        if self.id:
            proj_exact = WriterProject.objects.filter(proj_name=self.proj_name, \
                            ai_user=self.ai_user).exclude(id=self.id).count()
        else:
            proj_exact = WriterProject.objects.filter(proj_name=self.proj_name, \
                            ai_user=self.ai_user,).count()
        if proj_exact != 0:
            if self.id:
                proj_count = WriterProject.objects.filter(proj_name__icontains=self.proj_name, \
                            ai_user=self.ai_user).exclude(id=self.id).count()
            else:
                proj_count = WriterProject.objects.filter(proj_name__icontains=self.proj_name, \
                            ai_user=self.ai_user,).count()
            self.proj_name = self.proj_name + "(" + str(proj_count) + ")"

        return super().save(*args, **kwargs)

class MyDocuments(models.Model):
    project = models.ForeignKey(WriterProject, null=True, blank=True, on_delete=models.CASCADE,related_name = 'related_docs')
    document_type = models.ForeignKey(DocumentType, null=False, blank=False,on_delete=models.CASCADE,default=1)
    file = models.FileField (upload_to=my_docs_upload_path,blank=True, null=True)
    doc_name = models.CharField(max_length=1000, null=True, blank=True,)
    word_count = models.IntegerField(null=True,blank=True)
    html_data = models.TextField(null=True,blank=True)
    blog_data = models.TextField(null=True,blank=True)
    created_by = models.ForeignKey(AiUser, null=True, blank=True, on_delete=models.SET_NULL,related_name = 'doc_created_by')
    ai_user = models.ForeignKey(AiUser, null=False, blank=False,on_delete=models.CASCADE,related_name = 'credit_debit_user')
    source_language = models.ForeignKey(Languages, null=True, blank=True, on_delete=models.CASCADE, related_name="doc_source_lang")
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    
    
    def save(self, *args, **kwargs):
      
        if not self.doc_name:
            self.doc_name = 'Document-'+str(MyDocuments.objects.filter(ai_user=self.ai_user).count()+1).zfill(3)+'('+str(date.today()) +')'
            
        if self.id:
            doc_exact = MyDocuments.objects.filter(doc_name=self.doc_name, \
                            ai_user=self.ai_user).exclude(id=self.id).count()
        else:
            doc_exact = MyDocuments.objects.filter(doc_name=self.doc_name, \
                            ai_user=self.ai_user,).count()
        if doc_exact != 0:
            if self.id:
                doc_count = MyDocuments.objects.filter(doc_name__icontains=self.doc_name, \
                            ai_user=self.ai_user).exclude(id=self.id).count()
            else:
                doc_count = MyDocuments.objects.filter(doc_name__icontains=self.doc_name, \
                            ai_user=self.ai_user,).count()
            self.doc_name = self.doc_name + "(" + str(doc_count) + ")"

        return super().save(*args, **kwargs)


##########################Need to add project type################################
class Project(models.Model):
    project_type = models.ForeignKey(ProjectType, null=False, blank=False,on_delete=models.CASCADE,default=1)
    # project_type_detail = models.ForeignKey(ProjectTypeDetail,null=True,blank=True,on_delete=models.CASCADE)
    project_name = models.CharField(max_length=1000, null=True, blank=True,)
    project_dir_path = models.FilePathField(max_length=1000, null=True,\
        path=settings.MEDIA_ROOT, blank=True, allow_folders=True,
        allow_files=False)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    ai_user = models.ForeignKey(AiUser, null=False, blank=False,
        on_delete=models.CASCADE)
    ai_project_id = models.TextField()
    mt_engine = models.ForeignKey(AilaysaSupportedMtpeEngines,
        null=True, blank=True, \
        on_delete=models.CASCADE, related_name="proj_mt_engine",default=1)
    threshold = models.IntegerField(default=85)
    max_hits = models.IntegerField(default=5)
    workflow = models.ForeignKey(Workflows,null=True,blank=True,on_delete=models.CASCADE,related_name='proj_workflow')
    team = models.ForeignKey(Team,null=True,blank=True,on_delete=models.CASCADE,related_name='proj_team')
    project_manager = models.ForeignKey(AiUser, null=True, blank=True, on_delete=models.CASCADE, related_name='project_owner')
    created_by = models.ForeignKey(AiUser, null=True, blank=True, on_delete=models.SET_NULL,related_name = 'created_by')
    pre_translate = models.BooleanField(default=False)
    mt_enable = models.BooleanField(default=True)
    project_deadline = models.DateTimeField(blank=True, null=True)
    copy_paste_enable = models.BooleanField(default=True)
    get_mt_by_page = models.BooleanField(default=True) 
    file_translate = models.BooleanField(default=False)


    class Meta:
        unique_together = ("project_name", "ai_user")
        #managed = False

    objects = ProjectManager()

    def __str__(self):
        return self.project_name

    __repr__ = __str__

    penseive_tm_klass = PenseiveTM

    def save(self, *args, **kwargs):
        
        with transaction.atomic():
            #transaction.set_isolation_level(transaction.ISOLATION_SERIALIZABLE)

            queryset = Project.objects.select_for_update().filter(ai_user=self.ai_user)

            if not self.ai_project_id:
                self.ai_project_id = create_ai_project_id_if_not_exists(self.ai_user)

            if not self.project_name:
                count = queryset.count()
                prefix = self.get_prefix()
                self.project_name = prefix +str(count+1).zfill(3)+'('+str(date.today()) +')'

            if self.id:
                project_count = queryset.filter(project_name=self.project_name).exclude(id=self.id).count()
            else:
                project_count = queryset.filter(project_name=self.project_name).count()
            if project_count != 0:
                while True:
                    try:
                        if self.id:
                            count_num = queryset.filter(project_name__icontains=self.project_name).exclude(id=self.id).count()
                        else:
                            count_num = queryset.filter(project_name__icontains=self.project_name).count()
                        self.project_name = self.project_name + "(" + str(count_num) + ")"
                        super().save()
                        break
                    except:
                        count_num = count_num+1
                        self.project_name = self.project_name + "(" + str(count_num) + ")"
            return super().save()


    # def generate_cache_keys(self):
    #     from .utils import get_pr_list_cache_key
    #     cache_keys = [
    #         get_pr_list_cache_key(self.ai_user_id)
    #     ]
    #     return cache_keys

    def get_prefix(self):
        if self.project_type_id == 7:
            prefix = 'Book Project-'
        elif self.project_type_id == 6:
            prefix = 'Designer Project-'
        else:
            prefix = 'Project-'
        return prefix

    @property
    def designer_project_detail(self):
        from ai_canvas.models import CanvasDesign,CanvasSourceJsonFiles
        from ai_imagetranslation.models import ImageTranslate
        des_proj_detail = None
        if self.project_type_id == 6:
            des_obj = CanvasDesign.objects.filter(project = self)
            if des_obj: 
                pages= des_obj.last().canvas_json_src.all().count()
                des_proj_detail = {'des_proj_id':des_obj.last().id,'type':'image_design','pages':pages}
            else:
                img_trans_obj = ImageTranslate.objects.filter(project=self)
                print("IMage------------->",img_trans_obj)
                if img_trans_obj:
                    des_proj_detail = {'des_proj_id':img_trans_obj.last().id,'type': 'image_translate','pages':None}
        return des_proj_detail

    @property
    def ref_files(self):
        return self.project_ref_files_set.all()

    @property
    def files_count(self):
        return self.project_files_set.all().count()

    # @property
    # def get_project_type(self):
    #     return self.project_type.id

  
    def pr_progress(self,tasks):
        from ai_workspace.api_views import voice_project_progress
        if self.project_type_id == 3:
            terms = self.glossary_project.term.all()
            if terms.count() == 0:
                return "Yet to start"
            elif terms.count() == terms.filter(Q(tl_term='') | Q(tl_term__isnull = True)).count():
                return "Yet to start"
            else:
                if terms.count() == terms.filter(tl_term__isnull = False).exclude(tl_term='').count():
                    return "Completed"
                else:
                    return "In Progress"

        elif self.project_type_id == 5:
            count=0
            for i in tasks:
                obj = ExpressProjectDetail.objects.filter(task=i)
                if obj.exists():
                    if obj.first().target_text!=None:
                        count+=1
                else:
                    return "Yet to start"
            if tasks.count() == count:
                return "Completed"
            else:
                return "In Progress"

        elif self.project_type_id == 4:
            rr = voice_project_progress(self,tasks)
            return rr

        elif self.project_type_id == 7 or self.project_type_id == 6:
            return None

        else:
            assigned_jobs = [i.job.id for i in tasks]
            docs = Document.objects.filter(job__in=assigned_jobs).all()
            print("Docs------------------->",docs)
            #docs = Document.objects.filter(job__project_id=self.id).all()
            #tasks = len(tasks)
            total_segments = 0
            if not docs:
                return "Yet to start"
            else:
                if docs.count() == tasks.count():

                    total_seg_count = 0
                    confirm_count  = 0
                    confirm_list = [102, 104, 106, 110, 107]

                    segs = Segment.objects.filter(text_unit__document__job__project_id=self.id)

                    for seg in segs:

                        if (seg.is_merged == True and seg.is_merge_start != True):
                            continue

                        elif seg.is_split == True:
                            total_seg_count += 2

                        else:
                            total_seg_count += 1

                        seg_new = seg.get_active_object()

                        if seg_new.is_split == True:
                            for split_seg in SplitSegment.objects.filter(segment_id=seg_new.id):
                                if split_seg.status_id in confirm_list:
                                    confirm_count += 1

                        elif seg_new.status_id in confirm_list:
                            confirm_count += 1

                else:
                    return "In Progress"

            if total_seg_count == confirm_count:
                return "Completed"
            else:
                return "In Progress"
               


    @property
    def files_and_jobs_set(self):
        return  \
            ( # jobs will not exceed 100nos, and files will not exceed 10nos,
            # so all() functionality used...
            self.project_jobs_set.all(),
            self.project_files_set.all())

    @property
    def _assign_tasks_url(self):
        return reverse("", kwargs={"project_id":self.id})

    @property
    def get_assignable_tasks(self):
        tasks=[]
        for task in self.get_tasks:
            if (task.job.target_language == None):
                if (task.file.get_file_extension == '.mp3'):
                    tasks.append(task)
                else:pass
            else:tasks.append(task)
        return tasks

    @property
    def get_assignable_tasks_exists(self):
        cache_key = f'pr_get_assignable_tasks_exists_{self.pk}'
        cached_value = cache.get(cache_key)
        print("Cached Value in Assignable---------->",cached_value)
        if cached_value is None:
            tasks=[]
            for task in self.get_tasks:
                if (task.job.target_language == None):
                    if (task.file.get_file_extension == '.mp3'):
                        tasks.append(task)
                    else:pass
                else:tasks.append(task)
            cached_value = True if tasks else False
            cache.set(cache_key,cached_value)
        return cached_value

    @property
    def get_mtpe_tasks(self):
        return self.get_tasks.filter(~Q(job__target_language=None))

    @property
    def get_analysis_tasks(self):
        if self.project_type_id in [3,6,7]: #[glossary,designer,book]
            return Task.objects.none()
        if self.project_type_id == 4 and self.voice_proj_detail.project_type_sub_category_id == 2:
            return self.get_tasks
        else:
            tsks = self.get_tasks.filter(~Q(job__target_language=None))
            return tsks if tsks else Task.objects.none()
      

    @property
    def get_tasks(self):
        tasks_list = Task.objects.filter(job__project=self).order_by('id').prefetch_related(
                     Prefetch('job', queryset=Job.objects.select_related('project'))).distinct()
        return tasks_list
        # cache_key = f'pr_get_tasks_{self.pk}'
        # cached_value = cache.get(cache_key)
        # print("Cached Value in get_tasks---------->",cached_value)
        # if cached_value is None:
        #     cached_value = Task.objects.filter(job__project=self).order_by('id').prefetch_related(
        #             Prefetch('job', queryset=Job.objects.select_related('project')))
        #     cache.set(cache_key,cached_value)
        # return cached_value
        

    @property
    def get_source_only_tasks(self):
        tasks_id = self.project_jobs_set.filter(job_tasks_set__job__target_language=None).select_related('job_tasks_set__job').values_list('job_tasks_set', flat=True)
        tasks = Task.objects.filter(id__in = tasks_id)
        return tasks

    @property
    def tasks_count(self):
        #return self.get_tasks.count()
        cache_key = f'pr_tasks_count_{self.pk}'
        cached_value = cache.get(cache_key)
        print("Cached Value in tasks_count---------->",cached_value)
        if cached_value is None:
            cached_value = self.get_tasks.count() 
            cache.set(cache_key,cached_value)
        return cached_value

    @property
    def files_jobs_choice_url(self):
        return reverse("get-files-jobs-by-project_id", kwargs={"project_id": self.id})

    @property
    def source_language(self):
        return self.project_jobs_set.first().source_language_code

    @property
    def _source_language(self):
        lang = self.project_jobs_set.first().source__language
        return {"id": lang.id, "language": lang.language}

    @property
    def _target_languages(self):
        return [{"id":job.target__language.id, "language": job.target__language.language} \
            for job in self.project_jobs_set.all()]

    @property
    def source_language_code(self):
        return self.project_jobs_set.first().source_language_code

    @property
    def target_language_codes(self):
        return [job.target_language_code for job in self.project_jobs_set.all()]

    @property
    def pentm_path(self):
        return self.project_penseivetm.penseive_tm_dir_path

    @property
    def get_jobs(self):
        return [job for job in self.project_jobs_set.all()]

    @property
    def get_steps(self):
        return [obj.steps for obj in self.proj_steps.all()]

    @property#@cached_property
    def get_steps_name(self):
        return [obj.steps.name for obj in self.proj_steps.all()]

    @property#@cached_property #Need to check
    def PR_step_edit(self):
        if self.proj_detail.exists():
            if self.proj_detail.first().projectpost_steps.filter(steps_id=2).exists():
                return False
            else:return True
        else:
            for task in self.get_tasks:
                if task.task_info.filter(task_assign_info__isnull=False).filter(step_id=2):
                    return False
            return True

    @property
    def tmx_files_path(self):
        return [tmx_file.tmx_file.path for tmx_file in self.project_tmx_files.all()]

    @property
    def tmx_files_path_not_processed(self):
        return {tmx_file.id:tmx_file.tmx_file.path for tmx_file in self.project_tmx_files\
            .filter(is_processed=False).all()}

    @property
    def get_target_languages(self):
        return [job.target_language for job in self.project_jobs_set.all()]

    @property#@cached_property
    def get_team(self):
        if self.team == None:
            return False
        else:
            return True

    @property#@cached_property
    def is_all_doc_opened(self):
        docs = self.get_tasks.filter(document__isnull=True)
        if docs:return False
        else: return True
      

    @property
    def text_to_speech_source_download(self):
        if self.project_type_id == 4:
            if self.voice_proj_detail.project_type_sub_category_id == 2:
                if self.get_target_languages[0] == None:
                    return True

    @property
    def is_proj_analysed(self):
        if self.is_all_doc_opened:
            cached_value = True
        elif (self.get_analysis_tasks.count() != 0) and (self.get_analysis_tasks.count() == self.task_project.count()):
            cached_value = True
        else:
            cached_value = False
        return cached_value

    @property
    def show_analysis(self):
        cache_key = f'pr_show_analysis_{self.id}'
        cached_value = cache.get(cache_key)
        if cached_value is None:
            if (self.project_type_id != 3) and (self.get_mtpe_tasks):
                cached_value = True
            else:cached_value = False
            cache.set(cache_key,cached_value)
        return cached_value
        

    @property
    def assigned(self):
        if self.get_tasks:
            cache_key = f'pr_assigned_{self.pk}'
            cached_value = cache.get(cache_key)
            print("Cached Value in assigned---------->",cached_value)
            if cached_value is None:
                cached_value =False # Initialize
                for task in self.get_tasks:
                    if task.task_info.filter(task_assign_info__isnull=False):
                        cached_value = True
                        break
                print("CV in  prop--------->",cached_value)
                cache.set(cache_key,cached_value)
            return cached_value
        else:
            return False
                #     assigned = False
        #     for task in self.get_tasks:
        #         if task.task_info.filter(task_assign_info__isnull=False):
        #             assigned = True
        #             break
        #     return assigned
        # else: return False

    @property
    def get_project_file_create_type(self):
        return self.project_file_create_type.file_create_type

    # @property
    # def clone_available(self):
    #     from ai_glex.models import TermsModel
    #     if self.project_type_id == 3:
    #         if self.get_tasks.count() >1:
    #             jobs = [i.job.id for i in self.get_tasks]
    #             if TermsModel.objects.filter(job_id__in = jobs).count() != 0:
    #                 return True
    #             else:return False
    #         else:return False
    #     else:return None

    @property
    def clone_available(self):
        cache_key = f'pr_clone_available_{self.pk}'
        cached_value = cache.get(cache_key)
        print("Cached Value in clone available---------->",cached_value)
        if cached_value is None:
            from ai_glex.models import TermsModel
            if self.project_type_id == 3:
                cached_value = False
                if self.get_tasks.count() >1:
                    jobs = [i.job.id for i in self.get_tasks]
                    if TermsModel.objects.filter(job_id__in = jobs).count() != 0:
                        cached_value = True
            else:
                cached_value = 'null'
            cache.set(cache_key,cached_value)
        return cached_value
       
    
    @property
    def owner_pk(self):
        return self.ai_user.id
    
    @property
    def proj_obj(self):
        return self

                
    @property
    def get_tasks_pk(self):
        return self.project_jobs_set.values("job_tasks_set__id").annotate(as_char=Cast('job_tasks_set__id', CharField())).values_list("as_char",flat=True)

                            
    def project_analysis(self,tasks):
        from ai_auth.tasks import project_analysis_property
        from .models import MTonlytaskCeleryStatus
        from .models import MTonlytaskCeleryStatus
        from .api_views import analysed_true
        if not tasks or self.project_type_id in [6,7] or self.file_translate == True:
            print("In")
            return {"proj_word_count": 0, "proj_char_count": 0, \
                "proj_seg_count": 0, "task_words":[]} 
        #print("PR_AN------------------->",self.is_proj_analysed)
        if self.is_proj_analysed == True:
            return analysed_true(self,tasks)

        else:
            from .api_views import ProjectAnalysisProperty,analysed_true
            
            try:
                print("Inside Try. Checking celery")
                obj = MTonlytaskCeleryStatus.objects.filter(project_id = self.id).filter(task_name = 'project_analysis_property').last()
                state = project_analysis_property.AsyncResult(obj.celery_task_id).state if obj else None
                print("st------->",state)
                if state == 'STARTED':
                    return {'msg':'project analysis ongoing. Please wait','celery_id':obj.celery_task_id}
                elif state == 'SUCCESS' and self.is_proj_analysed == True:
                    return analysed_true(self,tasks)
                else:
                    celery_task = project_analysis_property.apply_async((self.id,), queue='high-priority')
                    return {'msg':'project analysis ongoing. Please wait','celery_id':celery_task.id}
                #return ProjectAnalysisProperty.get(self.id)
            except:
                print("Inside Except")
                return {"proj_word_count": 0, "proj_char_count": 0, \
                "proj_seg_count": 0, "task_words":[]}


    # def project_analysis(self,tasks):
    #     from .api_views import ProjectAnalysisProperty
    #     from .models import MTonlytaskCeleryStatus
    #     from ai_auth.tasks import project_analysis_property
    #     print("Model---------->",tasks)
    #     print("Proj--------->",self.id)
    #     obj = MTonlytaskCeleryStatus.objects.filter(project_id = self.id).filter(task_name = 'project_analysis_property').last()
    #     print("Obj---------->",obj)
    #     state = project_analysis_property.AsyncResult(obj.celery_task_id).state if obj else None
    #     print("Called in model")
    #     #print("State------------>",state)
    #     if state == 'STARTED':
    #         return {'msg':'project analysis ongoing. Please wait','celery_id':obj.celery_task_id}
    #     # elif state == 'PENDING' or state =='None' or state == 'FAILURE':
    #     #     celery_task = project_analysis_property.apply_async((self.id,), )
    #     #     return {'msg':'project analysis ongoing. Please wait','celery_id':celery_task.id}
    #     elif state == "SUCCESS" or self.is_proj_analysed == True:
    #         print("inside if analyse")
    #         task_words = []
    #         if self.is_all_doc_opened:
    #             print("Doc opened")
    #             [task_words.append({i.id:i.document.total_word_count}) for i in tasks]
    #             out=Document.objects.filter(id__in=[j.document_id for j in tasks]).aggregate(Sum('total_word_count'),\
    #                 Sum('total_char_count'),Sum('total_segment_count'))

    #             return {"proj_word_count": out.get('total_word_count__sum'), "proj_char_count":out.get('total_char_count__sum'), \
    #                 "proj_seg_count":out.get('total_segment_count__sum'),\
    #                               "task_words" : task_words }
    #         else:
    #             print("Not Doc Opened")
    #             out = TaskDetails.objects.filter(task_id__in=[j.id for j in tasks]).aggregate(Sum('task_word_count'),Sum('task_char_count'),Sum('task_seg_count'))
    #             task_words = []
    #             [task_words.append({i.id:i.task_details.first().task_word_count if i.task_details.first() else 0}) for i in tasks]

    #             return {"proj_word_count": out.get('task_word_count__sum'), "proj_char_count":out.get('task_char_count__sum'), \
    #                 "proj_seg_count":out.get('task_seg_count__sum'),
    #                             "task_words":task_words}
    #     else:
            # print("Not Analysed")
            # from .api_views import ProjectAnalysisProperty
            # try:
            #     print("Inside Try")
            #     celery_task = project_analysis_property.apply_async((self.id,), )
            #     return {'msg':'project analysis ongoing. Please wait','celery_id':celery_task.id}
            #     #return ProjectAnalysisProperty.get(self.id)
            # except:
            #     print("Inside Except")
            #     return {"proj_word_count": 0, "proj_char_count": 0, \
            #     "proj_seg_count": 0, "task_words":[]}
             # rr = analysed_true(self,tasks)
            # print("RRRRRRRRRR------------------------>",rr)
            # return rr
            # task_words = []
            # if self.is_all_doc_opened:
            #     [task_words.append({i.id:i.document.total_word_count}) for i in tasks]
            #     out=Document.objects.filter(id__in=[j.document_id for j in tasks]).aggregate(Sum('total_word_count'),\
            #         Sum('total_char_count'),Sum('total_segment_count'))

            #     return {"proj_word_count": out.get('total_word_count__sum'), "proj_char_count":out.get('total_char_count__sum'), \
            #         "proj_seg_count":out.get('total_segment_count__sum'),\
            #                       "task_words" : task_words }
            # else:
            #     out = TaskDetails.objects.filter(task_id__in=[j.id for j in tasks]).aggregate(Sum('task_word_count'),Sum('task_char_count'),Sum('task_seg_count'))
            #     task_words = []
            #     [task_words.append({i.id:i.task_details.first().task_word_count if i.task_details.first() else 0}) for i in tasks]

            #     return {"proj_word_count": out.get('task_word_count__sum'), "proj_char_count":out.get('task_char_count__sum'), \
            #         "proj_seg_count":out.get('task_seg_count__sum'),
            #                     "task_words":task_words}

pre_save.connect(create_project_dir, sender=Project)
post_save.connect(create_pentm_dir_of_project, sender=Project,)
post_delete.connect(delete_project_dir, sender=Project)
# post_save.connect(invalidate_cache_on_save, sender=Project)
# pre_delete.connect(invalidate_cache_on_delete, sender=Project)

class ProjectFilesCreateType(models.Model):
    class FileType(models.TextChoices):
        upload_file = 'upload', "Files from usual upload"
        integeration = "integeration", "Files from integerations"
        from_text   = "From insta text"

    file_create_type = models.TextField(choices=FileType.choices,
        default=FileType.upload_file)
    project = models.OneToOneField(Project, on_delete=models.CASCADE,
        related_name="project_file_create_type")

    @property
    def owner_pk(self):
        return self.project.owner_pk
    @property
    def proj_obj(self):
        return self.project


class ProjectSteps(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE,
                        related_name="proj_steps")
    steps = models.ForeignKey(Steps, on_delete=models.CASCADE,
                        related_name="proj_steps_name")
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    objects = ProjectStepsManager()

    @property
    def owner_pk(self):
        return self.project.owner_pk

    @property
    def proj_obj(self):
        return self.project

def get_audio_file_upload_path(instance, filename):
    file_path = os.path.join(instance.voice_project.project.ai_user.uid,instance.voice_project.project.ai_project_id,\
            "Audio",filename)
    return file_path


class VoiceProjectDetail(models.Model):
    project = models.OneToOneField(Project, on_delete = models.CASCADE,related_name="voice_proj_detail")
    source_language = models.ForeignKey(Languages, null=True, blank=True, on_delete=models.CASCADE,related_name="voice_proj_source_language")
    project_type_sub_category = models.ForeignKey(ProjectTypeDetail,null=True,blank=True,on_delete=models.CASCADE)
    # source_language_locale = models.ForeignKey(LanguagesLocale, null=True, blank=True, on_delete=models.CASCADE,related_name="voice_proj_source_language_locale")
    # has_male = models.BooleanField(blank=True,null=True)
    # has_female = models.BooleanField(blank=True,null=True)

    @property
    def owner_pk(self):
        return self.project.owner_pk


class ProjectContentType(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE,
                        related_name="proj_content_type")
    content_type = models.ForeignKey(ContentTypes, on_delete=models.CASCADE,
                        related_name="proj_content_type_name")

    objects = ProjectContentTypeManager()

    @property
    def owner_pk(self):
        return self.project.owner_pk

    @property
    def proj_obj(self):
        return self.project

class ProjectSubjectField(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE,
                        related_name="proj_subject")
    subject = models.ForeignKey(SubjectFields, on_delete=models.CASCADE,
                        related_name="proj_sub_name")

    objects = ProjectSubjectFieldManager()

    @property
    def owner_pk(self):
        return self.project.owner_pk
    
    @property
    def proj_obj(self):
        return self.project

class Job(models.Model):
    source_language = models.ForeignKey(Languages, null=False, blank=False, on_delete=models.CASCADE,\
        related_name="source_language")
    target_language = models.ForeignKey(Languages, null=True, blank=True, on_delete=models.CASCADE,\
        related_name="target_language")
    project = models.ForeignKey(Project, null=False, blank=False, on_delete=models.CASCADE,\
        related_name="project_jobs_set",)
    
    job_id =models.TextField(null=True, blank=True)
    deleted_at = models.BooleanField(default=False)

    class Meta:
        unique_together = [("project", "source_language", "target_language")]

    objects = JobManager()

    def save(self, *args, **kwargs):
        ''' try except block created for logging the exception '''
        if not self.job_id:
            # self.ai_user shoould be set before save
            self.job_id = self.project.ai_project_id+"j"+str(Job.objects.filter(project=self.project)\
                .count()+1)
        super().save()#*args, **kwargs)

    @property
    def can_delete(self):
        return  self. file_job_set.all().__len__() == 0

    @property################need to work#################
    def assignable(self):
        if self.target_language == None:
            for i in self.job_tasks_set.all():
                if i.file.get_file_extension == '.mp3':
                    return True
                else:return False
        else:return True



    @property
    def source_target_pair(self): # code repr
        if self.target_language != None:
            return "%s-%s"%(self.source_language.locale.first().locale_code,\
                self.target_language.locale.first().locale_code)
        else:
            return "%s-%s"%(self.source_language.locale.first().locale_code,None)

    @property
    def source_target_pair_names(self):
        if self.target_language != None:
            return "%s->%s"%(
                self.source_language.language,
                self.target_language.language)
        else:
            return "%s->%s"%(
                self.source_language.language,None)

    @property
    def source_language_code(self):
        return self.source_language.locale.first().locale_code

    @property
    def target_language_code(self):
        return self.target_language.locale.first().locale_code

    @property
    def source__language(self):  #used in task serilaizer
        #print("called first time!!!")
        # return self.source_language.locale.first().language
        return self.source_language_code

    @property
    def type_of_job(self):
        if self.project.project_type_id == 4:
            if self.project.voice_proj_detail.project_type_sub_category_id == 1:
                if self.target_language == None:
                    return "Transcibe post editing"
                else:return "MTPE"
            else:return "MTPE"
        elif self.project.project_type_id == 3:
            if self.source_language == self.target_language:
                return "Glossary Term Addition"
            else: return "Glossary Translation"
        else:return "MTPE"


    @property
    def target__language(self):
        #print("called every time!!!")
        # return self.target_language.locale.first().language
        return  self.target_language_code

    @property
    def owner_pk(self):
        return self.project.owner_pk
   
    @property
    def proj_obj(self):
        return self.project

    def __str__(self):
        try:
            return self.source_language.language+"->"+self.target_language.language
        except:
            return self.source_language.language

# class ProjectTeamInfo(models.Model):
#     project = models.ForeignKey(Project, null=False, blank=False, on_delete=models.\
#                 CASCADE, related_name="team_project_info")
#     team = models.ForeignKey(Team, null=False, blank=False, on_delete=models.\
#                 CASCADE, related_name="project_team_info")

class FileTypes(models.Model):
    TERMBASE = "termbase"
    QA_UNTRANSLATABLE = "untranslatable"
    QA_BLOCKEDTEXT= "blockedtext"
    TRANSLATION_MEMORY="translation_memory"
    SOURCE = "source"
    REFERENCE = "reference"
    FILETYPES = [
        (SOURCE, 'Src'),
        (REFERENCE, 'Ref'),
        (TRANSLATION_MEMORY, 'TM'),
        (QA_BLOCKEDTEXT, 'qa_BT'),
        (QA_UNTRANSLATABLE, 'qa_UT'),
        (TERMBASE, 'TB'),
    ]
    file_type_name = models.CharField(\
        max_length=100,\
        choices=FILETYPES,)

    file_type_path = models.CharField(max_length=100)

def get_file_upload_path(instance, filename):
    file_path = os.path.join(instance.project.ai_user.uid,instance.project.ai_project_id,\
            instance.usage_type.type_path)
    print("Upload file path ----> ", file_path)
    instance.filename = filename
    return os.path.join(file_path, filename)

use_spaces = os.environ.get("USE_SPACES")

class File(models.Model):

    usage_type = models.ForeignKey(AssetUsageTypes,null=False, blank=False,\
                on_delete=models.CASCADE, related_name="project_usage_type")
    file = FileField(upload_to=get_file_upload_path, null=False,\
                blank=False, max_length=1000, default=settings.MEDIA_ROOT+"/"+"defualt.zip")
    project = models.ForeignKey(Project, null=False, blank=False, on_delete=models.\
                CASCADE, related_name="project_files_set")
    filename = models.CharField(max_length=200,null=True)
    fid = models.TextField(null=True, blank=True)
    deleted_at = models.BooleanField(default=False)
    # content_file = models.ForeignKey(ContentFile, on_delete=models.SET_NULL, null=True,
    #     related_name="contentfile_files_set")

    # def update_file(self, file_content):
    #     if not self.is_upload_from_integeration:
    #         raise ValueError( "This file cannot be update. Since it"
    #         " is not uploaded from integeration!!!" )
    #     upload_file_name = self.file.name.split("/")[-1]
    #     print("file path---->", self.file.name)
    #     SpacesService.delete_object(file_path=self.file.name)
    #     im = DjRestUtils.convert_content_to_inmemoryfile(filecontent=file_content,
    #         file_name=upload_file_name)
    #     self.file = im
    #     self.save()

    class Meta:
        managed = True #False
    #
    # @property
    # def is_upload_from_integeration(self):
    #     return self.content_file!=None

    def save(self, *args, **kwargs):
        ''' try except block created for logging the exception '''
        if not self.fid:
            # self.ai_user shoould be set before save
            self.fid = str(self.project.ai_project_id)+"f"+str(File.objects\
                .filter(project=self.project.id).count()+1)
        super().save()#*args, **kwargs)

    objects = FileManager()

    def __str__(self):
        return self.filename

    def can_delete(self):
        return self.file_document_set.all().__len__() == 0

    @property
    def use_type(self):
        return self.usage_type.use_type

    @property
    def owner(self):
        return self.project.ai_user
    
    @property
    def owner_pk(self):
        return self.project.owner_pk # created by

    @property
    def get_source_file_path(self):
        if settings.USE_SPACES:
            return self.file.url
        return self.file.path

    @property
    def output_file_path(self):
        if settings.USE_SPACES:
            comp = re.compile("media/[^?]*")
            return "_out".join(os.path.splitext(
                os.path.join(settings.BASE_DIR, comp.findall\
                    (self.get_source_file_path)[0])) )
        return '_out'.join( os.path.splitext(self.get_source_file_path))

    def get_aws_file_path(_string):
        comp = re.compile("/media/.*")
        return  comp.findall \
            (_string)[0].replace("/media/", "")

    @property
    def get_file_name(self):
        return self.filename

    @property
    def get_file_extension(self):
        file,ext = os.path.splitext(self.file.path)
        return ext

    @property
    def get_source_tmx_path(self):
        prefix, ext = os.path.splitext(self.filename)
        return os.path.join(self.project.project_penseivetm.source_tmx_dir_path, prefix+".tmx")

    @property
    def source_language(self):
        return self.project.source_language

    @property
    def target_language(self):
        return "ta"
      
    @property
    def proj_obj(self):
        return self.project

class VersionChoices(Enum):# '''need to discuss with senthil sir, what are the choices?'''

    POST_EDITING = "post_editing"

class Version(models.Model):
    # 'n' number versions can be set to a specific project...it cannot be a job specific or file specific
    version_name = models.CharField(max_length=100, choices=[(version.name, version.value)
                        for version in VersionChoices], null=False, blank=False)
    # project = models.ForeignKey(Project, null=False, blank=False, on_delete=models.CASCADE,
    #             related_name="project_versions_set")

    def __str__(self):
        return self.version_name


def id_generator_ws(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

class Task(models.Model):
    def generate_task_id():
        return "TK-{0}".format(id_generator_ws())

    ai_taskid=models.CharField(max_length=50,unique=True,null=True)

    file = models.ForeignKey(File, on_delete=models.CASCADE, null=True, blank=True,
            related_name="file_tasks_set")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=False, blank=False,
            related_name="job_tasks_set")
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True,)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['file', 'job'], name=\
                'file, job combination unique if file not null',condition=Q(file__isnull=False))
        ]

    objects = TaskManager()

    def save(self, *args, **kwargs):
        if not self.ai_taskid:
            self.ai_taskid = create_task_id()
        super().save()#*args, **kwargs)
        # cache_key_1 = f'audio_file_exists_{self.pk}'
        # cache_key_2 = f'pr_tasks_count_{self.job.project.pk}'
        # cache.delete(cache_key_1)
        # cache.delete(cache_key_2)
        # cache.delete_pattern(f'pr_progress_property_{self.job.project.id}_*')

    def generate_cache_keys(self):
        cache_keys = [
            f'audio_file_exists_{self.pk}',
            f'pr_tasks_count_{self.job.project.pk}',
            f'pr_progress_property_{self.job.project.id}_*',
            f'pr_get_assignable_tasks_exists_{self.job.project.pk}',
            f'pr_assigned_{self.job.project.pk}',
            f'pr_get_tasks_{self.job.project.pk}',
            f'pr_clone_available_{self.job.project.pk}',
            f'task_open_in_{self.pk}',
            f'task_audio_source_file_{self.pk}',
            f'task_audio_output_file_{self.pk}',
            f'task_translated_{self.pk}',
            f'task_converted_{self.pk}',
            f'pr_show_analysis_{self.job.project.id}',
            f'pr_proj_analysed_{self.job.project.id}',
        ]
        return cache_keys

    @property
    def converted_audio_file_exists(self):
        cache_key = f'audio_file_exists_{self.pk}'
        cached_value = cache.get(cache_key)
        if cached_value is None:
            if self.document:
                cached_value = self.document.converted_audio_file_exists
            else:
                cached_value = None#'null'#None#'Not exists'
            cache.set(cache_key, cached_value)
        return cached_value


    @property
    def download_audio_output_file(self):
        cache_key = f'task_audio_output_file_{self.pk}'
        cached_value = cache.get(cache_key)
        if cached_value is None:
            if self.document:
                cache_key = f'task_audio_output_file_{self.document.pk}'
                cached_value = self.document.download_audio_output_file
                cache.set(cache_key,cached_value)
            else:
                cached_value = None#'null'
                cache.set(cache_key,cached_value)
        return cached_value

    @property
    def converted(self):
        cache_key = f'task_converted_{self.pk}'
        cached_value = cache.get(cache_key)
        print("Cached Value---------->",cached_value)
        if cached_value is None:
            if self.job.project.project_type_id == 4 :
                if  self.job.project.voice_proj_detail.project_type_sub_category_id == 1:
                    if self.task_transcript_details.filter(~Q(transcripted_text__isnull = True)).exists():
                        cached_value = True
                    else:cached_value = False
                elif  self.job.project.voice_proj_detail.project_type_sub_category_id == 2:
                    if self.job.target_language==None:
                        if self.task_transcript_details.exists():
                            cached_value = True
                        else:cached_value= False
                    else:cached_value = None
                else:cached_value = None
            elif self.job.project.project_type_id == 1 or self.job.project.project_type_id == 2:
                if self.job.target_language==None and os.path.splitext(self.file.file.path)[1] == '.pdf':
                    if self.pdf_task.all().exists() == True:
                        cached_value = True
                    else:cached_value = False
                else:cached_value = None
            else:cached_value = "null"
            cache.set(cache_key,cached_value)
        return cached_value   


    @property
    def file_translate_done(self):
        res = False
        if self.job.project.file_translate == True:
            if self.task_file_detail.exists() == True:
                res = True
        return res
	
    @property
    def is_task_translated(self):
        cache_key = f'task_translated_{self.pk}'
        cached_value = cache.get(cache_key)
        print("Cached Value---------->",cached_value)
        if cached_value is None:
            if self.job.project.project_type_id == 1 or self.job.project.project_type_id == 2:
                if self.job.target_language==None and os.path.splitext(self.file.file.path)[1] == '.pdf':
                    if self.pdf_task.all().exists() == True and self.pdf_task.first().translation_task_created == True:
                        cached_value = True
                    else:cached_value = False
                else:cached_value = None
            else:cached_value = "null"
            cache.set(cache_key,cached_value)
        return cached_value

    @property
    def mt_only_credit_check(self):
        try:return self.document.doc_credit_check_open_alert
        except:return None

    @property
    def transcribed(self):
        cache_key = f'transcribed_{self.pk}'
        cached_value = cache.get(cache_key)
        print("Cached Value---------->",cached_value)
        if cached_value is None:
            if self.job.project.project_type_id == 4 :
                if  self.job.project.voice_proj_detail.project_type_sub_category_id == 1:
                    if self.task_transcript_details.filter(~Q(transcripted_text__isnull = True)).exists():
                        cached_value = True
                    else:cached_value = False
                else:cached_value = None#"null"#"Not exists"
            else:cached_value= None#"null"#"Not exists"
            cache.set(cache_key,cached_value)
        return cached_value


    @property
    def text_to_speech_convert_enable(self):
        cache_key = f'txt_to_spc_convert_{self.pk}'
        cached_value = cache.get(cache_key)
        print("Cached Value---------->",cached_value)
        if cached_value is None:
            if self.job.project.project_type_id == 4 :
                if  self.job.project.voice_proj_detail.project_type_sub_category_id == 2:
                    if self.job.target_language==None:
                        if self.task_transcript_details.exists():
                            cached_value = False
                        else:cached_value =  True
                    else:cached_value = None#"null"# None# "Not exists"
                else:cached_value =  None#"null"#None#"Not exists"
            else:cached_value = None#"null"# None#"Not exists"
            cache.set(cache_key,cached_value)
        return cached_value

    # @property
    # def open_in(self):
    #     try:
    #         if self.job.project.project_type_id == 5:
    #             return "ExpressEditor"
    #         elif self.job.project.project_type_id == 4:
    #             if  self.job.project.voice_proj_detail.project_type_sub_category_id == 1:
    #                 if self.job.target_language==None:
    #                     return "Ailaysa Writer or Text Editor"
    #                 else:
    #                     return "Transeditor"
    #             elif  self.job.project.voice_proj_detail.project_type_sub_category_id == 2:
    #                 if self.job.target_language==None:
    #                     return "Download"
    #                 else:return "Transeditor"
    #         elif self.job.project.project_type_id == 1 or self.job.project.project_type_id == 2:
    #             if self.job.target_language==None and os.path.splitext(self.file.file.path)[1] == '.pdf':
    #                 try:return self.pdf_task.last().pdf_api_use
    #                 except:return None
    #             else:return "Transeditor"	
    #         else:return "Transeditor"
    #     except:
    #         try:
    #             if self.job.project.glossary_project:
    #                 return "GlossaryEditor"
    #         except:
    #             return "Transeditor"

 
    @property
    def open_in(self):
        cache_key = f'task_open_in_{self.pk}'
        cached_value = cache.get(cache_key)
        print("Cached Value---------->",cached_value)
        if cached_value is None:
            try:
                if self.job.project.project_type_id == 5:
                    cached_value = "ExpressEditor"
                elif self.job.project.project_type_id == 6:
                    cached_value = "Designer"
                elif self.job.project.project_type_id == 7:
                    cached_value = "Book"
                elif self.job.project.project_type_id == 4:
                    if  self.job.project.voice_proj_detail.project_type_sub_category_id == 1:
                        if self.job.target_language==None:
                            cached_value = "Ailaysa Writer or Text Editor"
                        else:
                            cached_value = "Transeditor"
                    elif  self.job.project.voice_proj_detail.project_type_sub_category_id == 2:
                        if self.job.target_language==None:
                            cached_value = "Download"
                        else:cached_value = "Transeditor"
                elif self.job.project.project_type_id == 1 or self.job.project.project_type_id == 2:
                    if self.job.project.file_translate == True:
                        cached_value = "Download"
                    elif self.job.target_language==None and os.path.splitext(self.file.file.path)[1] == '.pdf':
                        try:cached_value = self.pdf_task.last().pdf_api_use
                        except:cached_value = None
                    else:cached_value= "Transeditor"	
                else:cached_value = "Transeditor"
                cache.set(cache_key,cached_value)
            except:
                try:
                    if self.job.project.glossary_project:
                        cached_value= "GlossaryEditor"
                except:
                    cached_value = "Transeditor"
                cache.set(cache_key,cached_value)
        return cached_value

    @property
    def get_document_url(self):
        try:
            if self.job.project.voice_proj_detail.project_type_sub_category_id == 1:
                if self.job.target_language == None:
                    return None
                else:return reverse("ws_okapi:document", kwargs={"task_id": self.id})
            else:return reverse("ws_okapi:document", kwargs={"task_id": self.id})
        except:
            try:
                if self.job.project.glossary_project or self.job.project.project_type_id__in == [6,7]: #designer,book proj
                    return None
            except:
                return reverse("ws_okapi:document", kwargs={"task_id": self.id})

    @property
    def extension(self):
        try:ret=get_file_extension(self.file.file.path)
        except:ret=''
        return ret

    @property
    def first_time_open(self):
        if self.document_id:return False
        else:return True

    @property
    def processor_name(self):
        return  get_processor_name(self.file.file.name).get("processor_name", None)

    @property
    def task_word_count(self):
        cache_key = f'task_word_count_{self.pk}'
        if self.document_id:
            cache_key = f'task_word_count_{self.document.pk}'
            cached_value = cache.get(cache_key)
            print("Cached Value in task_word_count---------->",cached_value)
            if cached_value is None:
                document = Document.objects.get(id = self.document_id)
                cached_value =  document.total_word_count
        elif self.task_details.exists():
            cache_key = f'task_word_count_{self.pk}'
            cached_value = cache.get(cache_key)
            print("Cached Value in task_word_count---------->",cached_value)
            if cached_value is None:
                t = TaskDetails.objects.filter(task_id = self.id).first()
                cached_value = t.task_word_count
        else:
            cached_value = None#"null"#None #"Not exists"
        cache.set(cache_key,cached_value)
        return cached_value


    @property
    def task_char_count(self):
        cache_key = f'task_word_count_{self.pk}'
        if self.document_id:
            cache_key = f'task_char_count_{self.document.pk}'
            cached_value = cache.get(cache_key)
            print("Cached Value in task_char_count---------->",cached_value)
            if cached_value is None:
                document = Document.objects.get(id = self.document_id)
                cached_value =  document.total_char_count
        elif self.task_details.first():
            cache_key = f'task_char_count_{self.pk}'
            cached_value = cache.get(cache_key)
            print("Cached Value in task_char_count---------->",cached_value)
            if cached_value is None:
                t = TaskDetails.objects.filter(task_id = self.id).first()
                cached_value = t.task_char_count
        else:
            cached_value =None#"null"#None #"Not exists"
        cache.set(cache_key,cached_value)
        return cached_value

    @property
    def assignable(self):
        if self.job.target_language == None:
            if self.file.get_file_extension == '.mp3':
                return True
            else:return False
        else:return True

    @property
    def download_audio_source_file(self):
        cache_key = f'task_audio_source_file_{self.pk}'
        cached_value = cache.get(cache_key)
        print("Cached Value---------->",cached_value)
        if cached_value is None:
            try:
                if self.job.project.voice_proj_detail.project_type_sub_category_id == 2:##text_to_speech
                    locale_list = MTLanguageLocaleVoiceSupport.objects.filter(language__language = self.job.source_language)
                    cached_value = [{"locale":i.language_locale.locale_code,'gender':i.gender,\
                            "voice_type":i.voice_type,"voice_name":i.voice_name}\
                            for i in locale_list] if locale_list else []
                elif self.job.project.voice_proj_detail.project_type_sub_category_id == 1:##speech_to_text(checking for speech_to_speech)
                    if self.job.target_language!=None:
                        txt_to_spc = MTLanguageSupport.objects.filter(language__language = self.job.source_language).first().text_to_speech
                        if txt_to_spc:
                            locale_list = MTLanguageLocaleVoiceSupport.objects.filter(language__language = self.job.target_language)
                            cached_value =  [{"locale":i.language_locale.locale_code,'gender':i.gender,\
                                    "voice_type":i.voice_type,"voice_name":i.voice_name}\
                                    for i in locale_list] if locale_list else []
                        else: 
                            cached_value = False
                    else:
                        cached_value = False
            except:
                cached_value = 'null'
            cache.set(cache_key,cached_value)
        return cached_value

    @property
    def corrected_segment_count(self):
        cache_key = f'seg_progress_{self.document.pk}' if self.document else None
        cached_value = cache.get(cache_key)
        if cached_value is None:
            confirm_list = [102, 104, 106, 110, 107]
            total_seg_count = 0
            confirm_count = 0
            doc = self.document
            segs = Segment.objects.filter(text_unit__document=doc)
            for seg in segs:

                if (seg.is_merged == True and seg.is_merge_start != True):
                    continue

                elif seg.is_split == True:
                    total_seg_count += 2

                else:
                    total_seg_count += 1

                seg_new = seg.get_active_object()

                if seg_new.is_split == True:
                    for split_seg in SplitSegment.objects.filter(segment_id=seg_new.id):
                        if split_seg.status_id in confirm_list:
                            confirm_count += 1

                elif seg_new.status_id in confirm_list:
                    confirm_count += 1

            cached_value ={"total_segments":total_seg_count,"confirmed_segments": confirm_count}
            cache.set(cache_key,cached_value)
        return cached_value

    @property
    def get_progress(self):
        if self.job.project.project_type_id != 3:
            data = self.corrected_segment_count
            return data
        else:
            cache_key = f'seg_progress_{self.job.pk}'
            cached_value = cache.get(cache_key)
            print("Cached Value in progress---------->",cached_value)
            if cached_value is None:
                target_words = self.job.term_job.filter(Q(tl_term__isnull=False)).exclude(tl_term='').count()
                source_words = self.job.term_job.filter(Q(sl_term__isnull=False)).exclude(sl_term='').count()
                cached_value = {"source_words":source_words,\
                        "target_words":target_words}
                cache.set(cache_key,cached_value)
        return cached_value


    @property
    def owner_pk(self):
        return self.job.project.owner_pk

    @property
    def proj_obj(self):
        return self.job.project


    def __str__(self):
        return "file=> "+ str(self.file) + ", job=> "+ str(self.job)

    @property
    def task_obj(self):
        return self

pre_save.connect(check_job_file_version_has_same_project, sender=Task)
post_save.connect(invalidate_cache_on_save, sender=Task)
pre_delete.connect(invalidate_cache_on_delete, sender=Task)


def target_file_upload_path(instance, filename):
    print("Ins,name--------->",instance,filename)
    file_path = os.path.join(instance.task.job.project.ai_user.uid,instance.task.job.project.ai_project_id,'source',filename)
    return file_path

class TaskTranslatedFile(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE,related_name="task_file_detail")
    target_file = models.FileField(upload_to=target_file_upload_path,blank=True, null=True)
    mt_engine = models.ForeignKey(AilaysaSupportedMtpeEngines,null=True,blank=True,on_delete=models.CASCADE,related_name="task_trans_mt")

def my_doc_image_upload_path(instance, filename):
    file_path = os.path.join(instance.ai_user.uid,"MyDocImages", filename)
    return file_path

class DocumentImages(models.Model):
    ai_user =  models.ForeignKey(AiUser, null=False, blank=False,on_delete=models.CASCADE)
    document = models.ForeignKey(MyDocuments,null=True, blank=True,on_delete=models.CASCADE,related_name = 'related_image')
    task = models.ForeignKey(Task,null=True, blank=True,on_delete=models.CASCADE,related_name = 'related_img')
    pdf = models.ForeignKey("ai_exportpdf.Ai_PdfUpload",null=True, blank=True,on_delete=models.CASCADE,related_name = 'retd_img')
    book = models.ForeignKey("ai_openai.BookCreation",null=True, blank=True,on_delete=models.CASCADE,related_name = 'book_img')
    image = models.FileField(upload_to=my_doc_image_upload_path,blank=True, null=True)


def ref_file_upload_path(instance, filename):
    file_path = os.path.join(instance.task_assign_info.task_assign.task.job.project.ai_user.uid,instance.task_assign_info.task_assign.task.job.project.ai_project_id,\
            "references", filename)
    return file_path

class ExpressProjectDetail(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE,related_name="express_task_detail")
    source_text = models.TextField(null=True,blank=True)
    target_text = models.TextField(null=True,blank=True)
    mt_raw =models.TextField(null=True,blank=True)
    mt_engine = models.ForeignKey(AilaysaSupportedMtpeEngines,null=True,blank=True,on_delete=models.CASCADE,related_name="express_proj_mt_detail")


    @property
    def owner_pk(self):
        return self.task.owner_pk

    @property
    def task_obj(self):
        return self.task

    def generate_cache_keys(self):
        cache_keys = [
            f'pr_progress_property_{self.task.job.project.id}_*',
        ]
        return cache_keys

    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)
    #     cache.delete_pattern(f'pr_progress_property_{self.task.job.project.id}_*')
post_save.connect(invalidate_cache_on_save, sender=ExpressProjectDetail)
pre_delete.connect(invalidate_cache_on_delete, sender=ExpressProjectDetail) 

class ExpressTaskHistory(models.Model):
    task = models.ForeignKey(Task,on_delete=models.CASCADE,related_name="express_task_history")
    source_text = models.TextField(null=True,blank=True)
    target_text = models.TextField(null=True,blank=True)
    action = models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)

class MTonlytaskCeleryStatus(models.Model):
    IN_PROGRESS = 1
    COMPLETED = 2
    STATUS_CHOICES = [
        (IN_PROGRESS, 'In Progress'),
        (COMPLETED, 'Completed'),
    ]
    task = models.ForeignKey(Task,on_delete=models.CASCADE, null=False, blank=False,
            related_name="mt_only_task_status")
    status = models.IntegerField(choices=STATUS_CHOICES,default=1)
    celery_task_id = models.CharField(max_length=255, blank=True, null=True)
    task_name = models.TextField(blank=True, null=True)
    error_type = models.TextField(blank=True, null=True)
    project = models.ForeignKey(Project,on_delete=models.CASCADE, null=True, blank=True,
            related_name="mt_only_project_status")

    @property
    def owner_pk(self):
        return self.task.owner_pk
        
    @property
    def task_obj(self):
        return self.task

class TaskAssign(models.Model):
    YET_TO_START = 1
    IN_PROGRESS = 2
    COMPLETED = 3
    RETURN_REQUEST = 4
    STATUS_CHOICES = [
        (YET_TO_START,'Yet to start'),
        (IN_PROGRESS, 'In Progress'),
        (COMPLETED, 'Completed'),
        (RETURN_REQUEST, 'Return Request')
    ]
    APPROVED = 1
    REWORK = 2
    CLOSE = 3
    RESPONSE_CHOICES = [
        (APPROVED, 'Approved'),
        (REWORK, 'Rework'),
        (CLOSE, 'Close'),
    ]
    task = models.ForeignKey(Task,on_delete=models.CASCADE, null=False, blank=False,
            related_name="task_info")
    step = models.ForeignKey(Steps,on_delete=models.CASCADE, null=False, blank=False,
             related_name="task_step")
    assign_to = models.ForeignKey(AiUser, on_delete=models.SET_NULL, null=True,
            related_name="user_tasks_set")
    mt_engine = models.ForeignKey(AilaysaSupportedMtpeEngines, null=True, blank=True, \
        on_delete=models.CASCADE, related_name="task_mt_engine")
    pre_translate = models.BooleanField(null=True, blank=True)
    mt_enable = models.BooleanField(null=True, blank=True)
    copy_paste_enable = models.BooleanField(null=True, blank=True)
    status = models.IntegerField(choices=STATUS_CHOICES,default=1)
    reassigned = models.BooleanField(default=False)
    client_response = models.IntegerField(choices=RESPONSE_CHOICES, blank=True, null=True)
    client_reason = models.TextField(null=True, blank=True)
    return_request_reason = models.TextField(null=True, blank=True)
    user_who_approved_or_rejected = models.ForeignKey(AiUser, on_delete=models.SET_NULL, null=True, blank=True)

    objects = TaskAssignManager()



    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def generate_cache_keys(self):
        cache_keys = [
            f'task_assign_info_*',
            f'task_reassign_info_*',
            f'task_reassign_computed_*',
            f'task_assign_computed_*',
            f'pr_progress_property_{self.task.job.project.id}_*',
            f'pr_assigned_{self.task.job.project.pk}'
        ]
        return cache_keys
        # cache.delete_pattern('task_assign_info_*')
        # cache.delete_pattern('task_reassign_info_*')
        # cache.delete_pattern(f'pr_progress_property_{self.task.job.project.id}_*')
        # cache_key = f'task_assign_info_{self.task.pk}'
        # cache.delete(cache_key)

    @property
    def owner_pk(self):
        return self.task.owner_pk

    @property
    def task_obj(self):
        return self.task

post_save.connect(invalidate_cache_on_save, sender=TaskAssign)
pre_delete.connect(invalidate_cache_on_delete, sender=TaskAssign) 
    # task_assign_obj = TaskAssign.objects.filter(
    #     Q(task__document__document_text_unit_set__text_unit_segment_set=segment_id) &
    #     Q(step_id=1)
    # ).first()
    # return TaskAssignSerializer(task_assign_obj).data

class TaskAssignInfo(models.Model):
    task_assign = models.OneToOneField(TaskAssign,on_delete=models.CASCADE, null=False, blank=False,
                    related_name="task_assign_info")
    PAYMENT_TYPE =[("outside_ailaysa","outside_ailaysa"),
                    ("stripe","stripe")]
    ACCEPT_STATUS =[("task_accepted","task_accepted"),
                    ("change_request","change_request")]
    instruction = models.TextField(max_length=1000, blank=True, null=True)
    assignment_id = models.CharField(max_length=191, blank=True, null=True)
    deadline = models.DateTimeField(blank=True, null=True)
    total_word_count = models.IntegerField(null=True, blank=True)
    mtpe_rate= models.DecimalField(max_digits=12,decimal_places=4,blank=True, null=True)
    estimated_hours = models.IntegerField(blank=True,null=True)
    mtpe_count_unit=models.ForeignKey(Billingunits,related_name='accepted_unit', on_delete=models.CASCADE,blank=True, null=True)
    currency = models.ForeignKey(Currencies,related_name='accepted_currency', on_delete=models.CASCADE,blank=True, null=True)
    assigned_by = models.ForeignKey(AiUser, on_delete=models.SET_NULL, null=True, blank=True,
            related_name="user_assign_info")
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    task_ven_status = models.CharField(max_length=20,choices=ACCEPT_STATUS,null=True,blank=True)
    payment_type = models.CharField(max_length=20,choices=PAYMENT_TYPE,null=True,blank=True)
    billable_char_count = models.IntegerField(blank=True,null=True)
    billable_word_count = models.IntegerField(blank=True,null=True)
    account_raw_count = models.BooleanField(default=True)
    change_request_reason = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.assignment_id:
            self.assignment_id = self.task_assign.task.job.project.ai_project_id+self.task_assign.step.short_name+str(TaskAssignInfo.objects.filter(task_assign=self.task_assign).count()+1)
        super().save()#*args, **kwargs)

    def generate_cache_keys(self):
        cache_keys = [
            f'task_assign_info_*',
            f'task_reassign_info_*',
            f'task_reassign_computed_*',
            f'task_assign_computed_*',
            f'pr_progress_property_{self.task_assign.task.job.project.id}_*',
            f'pr_assigned_{self.task_assign.task.job.project.pk}'
        ]
        return cache_keys
        # cache.delete_pattern('task_assign_info_*')
        # cache.delete_pattern('task_reassign_info_*')
        # cache.delete_pattern(f'pr_progress_property_{self.task_assign.task.job.project.id}_*')
        # cache_key = f'task_assign_info_{self.task_assign.task.pk}'
        # cache.delete(cache_key)

    @property
    def owner_pk(self):
        return self.task_assign.owner_pk

    @property
    def task_obj(self):
        return self.task_assign.task_obj

post_save.connect(invalidate_cache_on_save, sender=TaskAssignInfo)
pre_delete.connect(invalidate_cache_on_delete, sender=TaskAssignInfo)
# class TaskReassign(models.Model):
#     YET_TO_START = 1
#     IN_PROGRESS = 2
#     COMPLETED = 3
#     STATUS_CHOICES = [
#         (YET_TO_START,'Yet to start'),
#         (IN_PROGRESS, 'In Progress'),
#         (COMPLETED, 'Completed'),
#     ]
#     task = models.ForeignKey(Task,on_delete=models.CASCADE, null=False, blank=False,
#             related_name="task_reassign_info")
#     step = models.ForeignKey(Steps,on_delete=models.CASCADE, null=False, blank=False,
#              related_name="task_reassign_step")
#     re_assign_to = models.ForeignKey(AiUser, on_delete=models.SET_NULL, null=True,
#             related_name="user_reassign_tasks_set")
#     mt_engine = models.ForeignKey(AilaysaSupportedMtpeEngines, null=True, blank=True, \
#         on_delete=models.CASCADE, related_name="reassign_task_mt_engine")
#     pre_translate = models.BooleanField(null=True, blank=True)
#     mt_enable = models.BooleanField(null=True, blank=True)
#     copy_paste_enable = models.BooleanField(null=True, blank=True)
#     status = models.IntegerField(choices=STATUS_CHOICES,default=1)

#     # objects = TaskAssignManager()

#     # @property
#     # def owner_pk(self):
#     #     return self.task.owner_pk

#     # @property
#     # def task_obj(self):
#     #     return self.task


#     # task_assign_obj = TaskAssign.objects.filter(
#     #     Q(task__document__document_text_unit_set__text_unit_segment_set=segment_id) &
#     #     Q(step_id=1)
#     # ).first()
#     # return TaskAssignSerializer(task_assign_obj).data

# class TaskReassignInfo(models.Model):
#     task_reassign = models.OneToOneField(TaskReassign,on_delete=models.CASCADE, null=False, blank=False,
#                     related_name="task_reassign_info")
#     PAYMENT_TYPE =[("outside_ailaysa","outside_ailaysa"),
#                     ("stripe","stripe")]
#     ACCEPT_STATUS =[("task_accepted","task_accepted"),
#                     ("change_request","change_request")]
#     instruction = models.TextField(max_length=1000, blank=True, null=True)
#     assignment_id = models.CharField(max_length=191, blank=True, null=True)
#     deadline = models.DateTimeField(blank=True, null=True)
#     total_word_count = models.IntegerField(null=True, blank=True)
#     mtpe_rate= models.DecimalField(max_digits=12,decimal_places=4,blank=True, null=True)
#     estimated_hours = models.IntegerField(blank=True,null=True)
#     mtpe_count_unit=models.ForeignKey(Billingunits,related_name='accepted_mtpe_unit', on_delete=models.CASCADE,blank=True, null=True)
#     currency = models.ForeignKey(Currencies,related_name='accepted_rate_currency', on_delete=models.CASCADE,blank=True, null=True)
#     assigned_by = models.ForeignKey(AiUser, on_delete=models.SET_NULL, null=True, blank=True,
#             related_name="user_reassign_info")
#     created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
#     task_ven_status = models.CharField(max_length=20,choices=ACCEPT_STATUS,null=True,blank=True)
#     payment_type = models.CharField(max_length=20,choices=PAYMENT_TYPE,null=True,blank=True)
#     billable_char_count = models.IntegerField(blank=True,null=True)
#     billable_word_count = models.IntegerField(blank=True,null=True)
#     account_raw_count = models.BooleanField(default=True)

    # def save(self, *args, **kwargs):
    #     if not self.assignment_id:
    #         self.assignment_id = self.task_assign.task.job.project.ai_project_id+self.task_assign.step.short_name+str(TaskAssignInfo.objects.filter(task_assign=self.task_assign).count()+1)
    #     super().save()

    # @property
    # def owner_pk(self):
    #     return self.task_assign.owner_pk

    # @property
    # def task_obj(self):
    #     return self.task_assign.task_obj



# post_save.connect(assign_object_task, sender=TaskAssignInfo)

# class TaskAssignBillDetail(models.Model):
#     task_assign = models.OneToOneField(TaskAssign,on_delete=models.CASCADE, null=False, blank=False,
#                     related_name="task_assign_word_info")
#     billable_char_count = models.IntegerField(blank=True,null=True)
#     billable_word_count = models.IntegerField(blank=True,null=True)
# class TaskAssignRateInfo(models.Model):
#     task_assign_info = models.OneToOneField(TaskAssignInfo,on_delete=models.CASCADE, null=False, blank=False,
#             related_name="task_assign_rate_info")
#     total_word_count = models.IntegerField(null=True, blank=True)
#     mtpe_rate= models.DecimalField(max_digits=5,decimal_places=2,blank=True, null=True)
#     mtpe_count_unit=models.ForeignKey(ServiceTypeunits,related_name='accepted_unit', on_delete=models.CASCADE,blank=True, null=True)
#     currency = models.ForeignKey(Currencies,related_name='accepted_currency', on_delete=models.CASCADE,blank=True, null=True)
    # @property
    # def filename(self):
    #     try:
    #         return  os.path.basename(self.instruction_file.file.name)
    #     except:
    #         return None


class Instructionfiles(models.Model):
    instruction_file = models.FileField (upload_to=ref_file_upload_path,blank=True, null=True)
    task_assign_info = models.ForeignKey("TaskAssignInfo", null=True, blank=True,\
            on_delete=models.CASCADE,related_name='task_assign_instruction_file')

    @property
    def filename(self):
        try:
            return  os.path.basename(self.instruction_file.file.name)
        except:
            return None

    @property
    def owner_pk(self):
        return self.task_assign_info.owner_pk
    
    @property
    def task_obj(self):
        return self.task_assign_info.task_obj
# post_save.connect(generate_client_po, sender=TaskAssignInfo)

class TaskAssignHistory(models.Model):
    task_assign = models.ForeignKey(TaskAssign, on_delete=models.CASCADE, null=False, blank=False,
            related_name="task_assign_history")
    previous_assign = models.ForeignKey(AiUser,on_delete=models.CASCADE, null=False, blank=False)
    task_segment_confirmed = models.IntegerField(null=True, blank=True)
    unassigned_by = models.ForeignKey(AiUser,on_delete=models.CASCADE, null=True, blank=True, related_name='unassigned_by')
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)

    @property
    def owner_pk(self):
        return self.task_assign.owner_pk

class TaskDetails(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="task_details")
    task_word_count = models.IntegerField(null=True, blank=True)
    task_char_count = models.IntegerField(null=True, blank=True)
    task_seg_count = models.IntegerField(null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="task_project")

    @property
    def owner_pk(self):
        return self.project.owner_pk

    def __str__(self):
        return "file=> "+ str(self.task.file) + ", job=> "+ str(self.task.job)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def generate_cache_keys(self):
        cache_keys=[
            f'task_word_count_{self.task.pk}',
            f'task_char_count_{self.task.pk}',
            f'pr_proj_analysed_{self.task.job.project.id}',
        ]
        return cache_keys
post_save.connect(invalidate_cache_on_save, sender=TaskDetails)
pre_delete.connect(invalidate_cache_on_delete, sender=TaskDetails)
        # cache_key_1 = f'task_word_count_{self.task.pk}'
        # cache.delete(cache_key_1)
        # cache_key_2 = f'task_char_count_{self.task.pk}'
        # cache.delete(cache_key_2)


def audio_file_path(instance, filename):
    file_path = os.path.join(instance.task.job.project.ai_user.uid,instance.task.job.project.ai_project_id,instance.task.file.usage_type.type_path,\
            "Audio", filename)
    return file_path

def edited_file_path(instance, filename):
    file_path = os.path.join(instance.task.job.project.ai_user.uid,instance.task.job.project.ai_project_id,instance.task.file.usage_type.type_path,\
            "Edited", filename)
    return file_path

class TaskTranscriptDetails(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="task_transcript_details")
    transcripted_text = models.TextField(null=True,blank=True)
    #source_lang_locale = models.TextField(null=True,blank=True)#for reference
    source_audio_file = models.FileField(upload_to=audio_file_path,null=True,blank=True)
    translated_audio_file = models.FileField(upload_to=audio_file_path,null=True,blank=True)
    transcripted_file_writer = models.FileField(upload_to=edited_file_path,null=True,blank=True)
    quill_data =  models.TextField(null=True,blank=True)
    html_data = models.TextField(null=True,blank=True)
    audio_file_length = models.IntegerField(null=True,blank=True)
    user = models.ForeignKey(AiUser, on_delete = models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    writer_project_updated_count = models.IntegerField(null=True,blank=True)
    writer_filename = models.CharField(max_length=200, null=True, blank=True)

    @property
    def owner_pk(self):
        return self.task.owner_pk

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def generate_cache_keys(self):
        cache_keys = [
            f'audio_file_exists_{self.task.pk}',
            f'transcribed_{self.task.pk}',
            f'txt_to_spc_convert_{self.task.pk}',
            f'pr_progress_property_{self.task.job.project.id}_*',
            f'task_converted_{self.task.pk}',
        ]
        return cache_keys
        # cache_key_1 = f'audio_file_exists_{self.task.pk}'
        # cache.delete(cache_key_1)
        # cache_key_2 = f'transcribed_{self.task.pk}'
        # cache.delete(cache_key_2)
        # cache_key_3 = f'txt_to_spc_convert_{self.task.pk}'
        # cache.delete(cache_key_3)
        # cache.delete_pattern(f'pr_progress_property_{self.task.job.project.id}_*')
post_save.connect(invalidate_cache_on_save, sender=TaskTranscriptDetails)
pre_delete.connect(invalidate_cache_on_delete, sender=TaskTranscriptDetails) 

    # @property
    # def writer_filename(self):
    #     if self.writer_edited_count == None:
    #         return  os.path.basename(self.transcripted_file_writer.file.name)
    #     else:
    #         name = os.path.basename(self.transcripted_file_writer.file.name)
    #         filename,ext = os.path.splitext(name)
    #         return filename+ '_edited_'+ str(self.writer_edited_count)+ ext
# class FileReferenceVoiceProject(models.Model):
#     source_file = models.OneToOneField(File, on_delete=models.CASCADE,related_name="source")
#     created_file = models.ForeignKey(File, on_delete=models.CASCADE,related_name='created')

# class TaskAudioDetails(models.Model):
#     task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="task_transcript_details")

class TmxFile(models.Model):

    def tmx_file_path(instance, filename):
        return os.path.join(instance.project.ai_user.uid,instance.project.ai_project_id,\
            "tmx", filename)
    tmx_file = models.FileField(upload_to=tmx_file_path,
                    validators=[FileExtensionValidator(allowed_extensions=["tmx"])])
    project = models.ForeignKey(Project, on_delete=models.CASCADE,
                related_name="project_tmx_files")
    is_processed = models.BooleanField(default=False)
    is_failed = models.BooleanField(default=False)

    @property
    def filename(self):
        return  os.path.basename(self.tmx_file.file.name)

    @property
    def owner_pk(self):
        return self.project.owner_pk

def tbx_file_upload_path(instance, filename):
    file_path = os.path.join(instance.project.ai_user.uid,instance.project.ai_project_id,"tbx",filename)
    return file_path


class Tbxfiles(models.Model):
    tbx_files = models.FileField(upload_to="uploaded_tbx_files", null=False,\
            blank=False, max_length=1000)  # Common for a project
    project = models.ForeignKey("Project", null=False, blank=False,\
            on_delete=models.CASCADE)

    @property
    def owner_pk(self):
        return self.project.owner_pk

def reference_file_upload_path(instance, filename):
    file_path = os.path.join(instance.project.ai_user.uid,instance.project.ai_project_id,\
            "references", filename)
    return file_path

class ReferenceFiles(models.Model):
    ref_files = models.FileField(upload_to=reference_file_upload_path, null=False,\
            blank=False,)  # Common for a project
    project = models.ForeignKey("Project", null=False, blank=False,\
            related_name="project_ref_files_set", on_delete=models.CASCADE)

    @property
    def filename(self):
        return  os.path.basename(self.ref_files.file.name)

    @property
    def owner_pk(self):
        return self.project.owner_pk
    
    @property
    def proj_obj(self):
        return self.project

def tbx_file_path(instance, filename):
    return os.path.join(instance.project.ai_user.uid,instance.project.ai_project_id, "tbx", filename)

class TbxFile(models.Model):
    project = models.ForeignKey(Project, null=False, blank=False, related_name="project_tbx_file",
                                on_delete=models.CASCADE)
    # In case when "Apply to all jobs" is selected, then Project ID will be passed
    job = models.ForeignKey(Job, null=True, blank=True, related_name="job_tbx_file", on_delete=models.CASCADE)
    # When TBX assigned to particular job
    tbx_file = models.FileField(upload_to=tbx_file_path,
                            validators=[FileExtensionValidator(allowed_extensions=["tbx"])])

    @property
    def filename(self):
        return  os.path.basename(self.tbx_file.file.name)

    @property
    def owner_pk(self):
        return self.project.owner_pk
    
    @property
    def proj_obj(self):
        return self.project

def tbx_template_file_upload_path(instance, filename):
    return os.path.join(instance.project.ai_user.uid,instance.project.ai_project_id, "tbx_template", filename)

class TbxTemplateFiles(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE ,null=False, blank=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE ,null=False, blank=False)
    tbx_template_file = models.FileField(upload_to=tbx_template_file_upload_path,
                                    validators=[FileExtensionValidator(allowed_extensions=["xlsx"])])
    # upload_date = models.DateTimeField(auto_now_add=True)

    @property
    def filename(self):
        return  os.path.basename(self.tbx_template_file.file.name)

    @property
    def owner_pk(self):
        return self.project.owner_pk

class TemplateTermsModel(models.Model):

    file = models.ForeignKey(TbxTemplateFiles, on_delete=models.CASCADE ,null=False, blank=False)
    job  =  models.ForeignKey(Job, on_delete=models.CASCADE ,null=False, blank=False)
    sl_term = models.CharField(max_length=200, null=True, blank=True)
    tl_term = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.sl_term

    @property
    def owner_pk(self):
        return self.job.owner_pk

class TaskCreditStatus(models.Model):
    task = models.ForeignKey(Task, null=False, blank=False, on_delete=models.CASCADE)
    allocated_credits = models.IntegerField()
    actual_used_credits = models.IntegerField()
    word_char_ratio = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    @property
    def owner_pk(self):
        return self.task.owner_pk

class TempFiles(models.Model):
    temp_proj = models.ForeignKey(TempProject, on_delete=models.CASCADE,
        related_name="temp_proj_file")
    files = models.FileField(upload_to=get_temp_file_upload_path,\
        null=False, blank=False, max_length=1000)

    @property
    def filename(self):
        return  os.path.basename(self.files.file.name)


# class Steps(models.Model):
#     name = models.CharField(max_length=191)
#     short_name = models.CharField(max_length=50, null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
#     updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
#
#     def __str__(self):
#         return self.name


class WorkflowSteps(models.Model):
    workflow = models.ForeignKey(Workflows,on_delete=models.CASCADE,blank=True,null=True,related_name='workflow')
    steps = models.ForeignKey(Steps,on_delete=models.CASCADE,blank=True,null=True,related_name='step')
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)

    def __str__(self):
        return self.workflow.name + "-" + self.steps.name

    @property
    def owner_pk(self):
        return self.workflow.owner_pk

# class TempAudioFiles(models.model):
#     user = models.ForeignKey(AiUser, on_delete=models.CASCADE,related_name="user")
#     audio_file = models.FileField(upload_to=get_temp_file_upload_path,\
#         null=False, blank=False, max_length=1000)
#     text_file = models.FileField(upload_to=get_temp_file_upload_path,\
#         null=False, blank=False, max_length=1000)


class AiRoleandStep(models.Model):
    """maps which role responsible for which task"""
    role = models.ForeignKey(AiRoles,related_name='step_role',
        on_delete=models.CASCADE,blank=True, null=True)
    step = models.ForeignKey(Steps, on_delete=models.CASCADE,
                        related_name="step_role")



# class ExpressProjectSrcTextUnit(models.Model):
#     task = models.ForeignKey(Task, on_delete=models.CASCADE,related_name="express_src_text_unit")
#     seq_id=models.IntegerField()

# class ExpressProjectTarTextUnit(models.Model):
#     task = models.ForeignKey(Task, on_delete=models.CASCADE,related_name="express_tar_text_unit")
#     src_text_unit = models.ForeignKey(ExpressProjectSrcTextUnit,null=True,blank=True,on_delete=models.CASCADE,related_name="exp_tar_text_unit")
#     seq_id=models.IntegerField()


# class ExpressProjectDetail(models.Model):
#     task = models.ForeignKey(Task, on_delete=models.CASCADE,related_name="express_task_detail")
#     source_text = models.TextField(null=True,blank=True)
#     target_text = models.TextField(null=True,blank=True)
#     mt_raw =models.TextField(null=True,blank=True)
#     mt_engine = models.ForeignKey(AilaysaSupportedMtpeEngines,null=True,blank=True,on_delete=models.CASCADE,related_name="express_proj_mt_detail")

class ExpressProjectSrcSegment(models.Model):
    #src_text_unit = models.ForeignKey(ExpressProjectSrcTextUnit, on_delete=models.CASCADE,related_name="exp_src_seg")
    task = models.ForeignKey(Task, on_delete=models.CASCADE,related_name="express_src_text_unit")
    src_text_unit = models.IntegerField()
    src_segment = models.TextField(null=True,blank=True)
    #tar_segment = models.TextField(null=True,blank=True)
    seq_id=models.IntegerField()
    version = models.IntegerField()

class ExpressProjectSrcMTRaw(models.Model):
    src_seg = models.ForeignKey(ExpressProjectSrcSegment,on_delete=models.CASCADE,related_name="express_src_mt")
    mt_raw =models.TextField(null=True,blank=True)
    mt_engine = models.ForeignKey(AilaysaSupportedMtpeEngines,null=True,blank=True,on_delete=models.CASCADE,related_name="express_proj_mt_raw")


class ExpressProjectAIMT(models.Model):
    express = models.ForeignKey(ExpressProjectDetail, on_delete=models.CASCADE,related_name="express_src_text")
    source = models.TextField(null=True,blank=True)
    customize = models.ForeignKey(AiCustomize, on_delete=models.CASCADE, related_name = 'insta_cust')
    mt_engine = models.ForeignKey(AilaysaSupportedMtpeEngines,null=True,blank=True,on_delete=models.CASCADE,related_name="express_proj_mt")
    api_result = models.TextField(null=True,blank=True)
    final_result = models.TextField(null=True,blank=True)
# class ExpressProjectTarSegment(models.Model):
#     src_seg = models.ForeignKey(ExpressProjectSrcSegment,null=True,blank=True,on_delete=models.CASCADE,related_name="exp_src_seg")
#     tar_text_unit = models.IntegerField()
#     tar_text = models.TextField(null=True,blank=True)
#     seq_id=models.IntegerField()



 #@cached_property
    # @property
    # def progress(self):
    #     from ai_workspace.api_views import voice_project_progress
    #     if self.project_type_id == 3:
    #         terms = self.glossary_project.term.all()
    #         if terms.count() == 0:
    #             return "Yet to start"
    #         elif terms.count() == terms.filter(Q(tl_term='') | Q(tl_term__isnull = True)).count():
    #             return "Yet to start"
    #         else:
    #             if terms.count() == terms.filter(tl_term__isnull = False).exclude(tl_term='').count():
    #                 return "Completed"
    #             else:
    #                 return "In Progress"

    #     elif self.project_type_id == 5:
    #         count=0
    #         for i in self.get_tasks:
    #             obj = ExpressProjectDetail.objects.filter(task=i)
    #             if obj.exists():
    #                 if obj.first().target_text!=None:
    #                     count+=1
    #             else:
    #                 return "Yet to start"
    #         if len(self.get_tasks) == count:
    #             return "Completed"
    #         else:
    #             return "In Progress"

    #     elif self.project_type_id == 4:
    #         rr = voice_project_progress(self)
    #         return rr

    #     else:
    #         docs = Document.objects.filter(job__project_id=self.id).all()
    #         tasks = len(self.get_tasks)
    #         total_segments = 0
    #         if not docs:
    #             return "Yet to start"
    #         else:
    #             if docs.count() == tasks:

    #                 total_seg_count = 0
    #                 confirm_count  = 0
    #                 confirm_list = [102, 104, 106, 110, 107]

    #                 segs = Segment.objects.filter(text_unit__document__job__project_id=self.id)

    #                 for seg in segs:

    #                     if (seg.is_merged == True and seg.is_merge_start != True):
    #                         continue

    #                     elif seg.is_split == True:
    #                         total_seg_count += 2

    #                     else:
    #                         total_seg_count += 1

    #                     seg_new = seg.get_active_object()

    #                     if seg_new.is_split == True:
    #                         for split_seg in SplitSegment.objects.filter(segment_id=seg_new.id):
    #                             if split_seg.status_id in confirm_list:
    #                                 confirm_count += 1

    #                     elif seg_new.status_id in confirm_list:
    #                         confirm_count += 1

    #             else:
    #                 return "In Progress"

    #         if total_seg_count == confirm_count:
    #             return "Completed"
    #         else:
    #             return "In Progress"
    # @property
    # def is_proj_analysed(self):
    #     print("RR---------->",self.get_analysis_tasks.count())
    #     print("RT----------->",self.task_project.count())
    #     print("Rs-------------->",self.is_all_doc_opened)
    #     cache_key = f'pr_proj_analysed_{self.id}'
    #     cached_value = cache.get(cache_key)
    #     print("CC---------->",cached_value)
    #     if cached_value is None:
    #         if self.is_all_doc_opened:
    #             cached_value = True
    #         elif (self.get_analysis_tasks.count() != 0) and (self.get_analysis_tasks.count() == self.task_project.count()):
    #             print("ININIJ")
    #             cached_value = True
    #         else:
    #             cached_value = False
    #         cache.set(cache_key,cached_value)
    #     print("ER-------------->",cached_value)
    #     return cached_value

     # if not self.ai_project_id:
            #     self.ai_project_id = create_ai_project_id_if_not_exists(self.ai_user)

            # if not self.project_name:
            #     queryset = Project.objects.select_for_update().filter(ai_user=self.ai_user)
            #     count = queryset.count()
            #     print("Count for pr name-------->",count)
            #     self.project_name = 'Project-'+str(count+1).zfill(3)+'('+str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) +')'
            #     print("Pr Name--------->",self.project_name)
           
            # project_count = self.get_queryset_count_safely()
            # print("Pr Count if exists---------->",project_count)
            # if project_count != 0:
            #     count_num = self.get_count_num_safely()
            #     print("Already Exists Count_num--------->",count_num)
            #     self.project_name = self.project_name + "(" + str(count_num) + ")"
            #     print("Name---------->",self.project_name)
            # cache_key = f'my_cached_property_{self.id}'  # Use a unique cache key for each instance
            # cache.delete(cache_key)
            # return super().save()

    # @transaction.atomic
    # def get_count_for_project_name_safely(self):
    #     query = Project.objects.filter(ai_user=self.ai_user)
    #     queryset = query.select_for_update()
    #     count = queryset.count()
    #     #print("Count------------>",count)
    #     return count

    # @transaction.atomic
    # def get_queryset_count_safely(self):
    #     if self.id:
    #         queryset = Project.objects.filter(project_name=self.project_name, ai_user=self.ai_user).exclude(id=self.id)
    #     else:
    #         queryset = Project.objects.filter(project_name=self.project_name, ai_user=self.ai_user)
    #     queryset = queryset.select_for_update()
    #     count = queryset.count()
    #     #print("Count1---------->",count)
    #     return count

    # @transaction.atomic
    # def get_count_num_safely(self):
    #     if self.id:
    #         queryset = Project.objects.filter(project_name__icontains=self.project_name, \
    #                         ai_user=self.ai_user).exclude(id=self.id)
    #     else:
    #         queryset = Project.objects.filter(project_name__icontains=self.project_name, \
    #                         ai_user=self.ai_user)
    #     queryset = queryset.select_for_update()
    #     count_num = queryset.count()
    #     #print("Count_num------------>",count_num)
    #     return count_num

      # def convert_to_tuple(self, value):
    #     if isinstance(value, list):
    #         return tuple(self.convert_to_tuple(item) for item in value)
    #     return value

    # @property

        # tasks=[]
        # for job in self.project_jobs_set.all():
        #     for task in job.job_tasks_set.all():
        #        if (task.job.target_language == None):
        #                tasks.append(task)
        # return tasks

         #len([task for job in self.project_jobs_set.all() for task \
                            #    in job.job_tasks_set.all()])

                # for job in self.project_jobs_set.all():
            #     for task in job.job_tasks_set.all():
            #         if (task.job.target_language == None):
            #             if (task.file.get_file_extension == '.mp3'):
            #                 tasks.append(task)
            #             else:pass
            #         else:tasks.append(task)

              # if self.get_tasks:
        #     for task in self.get_tasks:
        #         if bool(task.document) == False:
        #             return False
        #     return True
        # else:
        #     return False
            # @property
    # def assigned_date(self):
    #     assigned = TaskAssignInfo.objects.filter(task_assign__task__job__project=self).order_by('-created_at')[0].created_at
    #     if assigned > self.created_at:
    #         return assigned
    #     else:
    #         return self.created_at
      # return [task for job in self.project_jobs_set.filter(~Q(target_language = None)) for task \
        #     in job.job_tasks_set.all()]
        # task_list =  [task for job in self.project_jobs_set.all() for task \
        #     in job.job_tasks_set.all()]
        #return sorted(task_list, key=lambda x: x.id)


