from django.contrib.auth.models import BaseUserManager
from django.db.models import QuerySet
from django.db import models
import os,shutil
import zipfile




class SoftDeletionQuerySet(QuerySet):

    def alive(self):
        return self.filter(deleted_at=None)

    def dead(self):
        print("this dead function called!!!")
        return self.exclude(deleted_at=None)

class AilzaManager(BaseUserManager):
    def create_user(self, email, **kwargs):
        if not email:
            raise ValueError("User must have an email ;")
        user_obj = self.models(email = email, username = username)
        user_obj.save()
        return user_obj

    def get_queryset(self):
        return SoftDeletionQuerySet(self.model, using=self._db).alive()

    def all(self):
        return self.get_queryset()

    def dead(self):
        return SoftDeletionQuerySet(self.model, using=self._db).dead()



class ProjectManager(models.Manager):
    
    def create_and_jobs_files_bulk_create(self,\
            data, files_key, jobs_key, f_klass, j_klass,\
            ai_user, team, project_manager, created_by):
        files_data = data.pop(files_key)
        jobs_data = data.pop(jobs_key)
        project = self.create(**data, ai_user=ai_user, project_manager=project_manager,\
                                team=team,created_by=created_by)
        return self.create_and_jobs_files_bulk_create_for_project(
            project, files_data, jobs_data, f_klass, j_klass
        )

    def create_and_jobs_files_bulk_create_for_project(self, project, files_data,\
        jobs_data, f_klass, j_klass):

        files = f_klass.objects.bulk_create_of_project(
            files_data, project, f_klass
        )
        jobs = j_klass.objects.bulk_create_of_project(
            jobs_data, project, j_klass
        )
        return project, files, jobs

    def create_content_and_subject_and_steps_for_project(self,project,contents_data,\
         subjects_data, steps_data, c_klass, s_klass, step_klass):

         contents = c_klass.objects.bulk_create_of_project(
            contents_data, project, c_klass
            )
         subjects = s_klass.objects.bulk_create_of_project(
            subjects_data, project, s_klass
            )
         steps = step_klass.objects.bulk_create_of_project(
            steps_data, project, step_klass
            )
         return project, contents, subjects, steps

    # def add_default_choice_list_for_project(self,project):
    #     if project.project_type_id not in [3,5]:
    #         from ai_workspace_okapi.models import ChoiceLists,ChoiceListSelected
    #         jobs = project.project_jobs_set.all()
    #         target_languages = [i.target_language_id for i in jobs if i.target_language]
    #         print("TL----------->", target_languages)
    #         for i in target_languages:
    #             ch_list,created = ChoiceLists.objects.get_or_create(user=project.ai_user,language_id=i,is_default=True)
    #             exists = ChoiceListSelected.objects.filter(project=project,choice_list__language_id=i)
    #             if not exists:
    #                 ChoiceListSelected.objects.get_or_create(project=project,choice_list=ch_list)
    #         return None


class FileManager(models.Manager):
    def bulk_create_of_project(self, \
            data, project, klass):
        files = [self.create(**item, project=project) for item in data]
        return files

    # def epub_file_create(self,files,project):
    #     files = [self.create(file = file,usage_type_id = 1,project=project) for file in files]

class JobManager(models.Manager):
    def bulk_create_of_project(self, \
            data, project, klass):
        jobs = [self.create(**item, project=project) for item in data]
        return jobs

    def pdf_job_create(self, \
            data, project, klass):
        job,created = self.get_or_create(**data, project=project)
        print("job------>",job)
        print("created--------------->",created)
        return job

    def bulk_create_of_design_project(self, \
            data, project, klass):
        jobs = [self.get_or_create(**item, project=project) for item in data]
        return jobs

class ProjectContentTypeManager(models.Manager):
    def bulk_create_of_project(self, \
            data, project, klass):
        contents = [self.get_or_create(**item, project=project) for item in data]
        return contents

class ProjectStepsManager(models.Manager):
    def bulk_create_of_project(self, \
            data, project, klass):
        steps = [self.get_or_create(**item, project=project) for item in data]
        return steps

class ProjectSubjectFieldManager(models.Manager):
    def bulk_create_of_project(self, \
            data, project, klass):
        subjects = [self.get_or_create(**item, project=project) for item in data]
        return subjects

class TaskManager(models.Manager):

    def epub_processing(self,epub_list,project):
       from ai_workspace.models import File
       html_files_list =[]
       for i in epub_list:
           base_file,ext = os.path.splitext(i.file.path)
           basedir = os.path.dirname(i.file.path)
           zipped_file = base_file  + '.zip'
           new_file = os.path.join(basedir,zipped_file)
           shutil.copy(i.file.path,new_file)
           zip = zipfile.ZipFile(new_file)
           zip.extractall('epub_1')
           for root, dirs, files in os.walk('epub_1'):
               for file in files:
                    if str(file).endswith('.xhtml') or str(file).endswith('.html'):
                        existing = os.path.join(root, file)
                        base = os.path.join(basedir,file)
                        file_path = os.path.join(project.ai_user.uid,project.ai_project_id,'source',file)
                        shutil.copy(existing,base)
                        file_obj = File.objects.create(file = file_path,usage_type_id = 1,project = project,filename=file)
                        html_files_list.append(file_obj)
       shutil.rmtree('epub_1', ignore_errors=True)
       return html_files_list

    def create_tasks_of_files_and_jobs(self, files, jobs, klass,\
          project = None):

        if project.file_translate == True:
            tasks = [self.get_or_create(file=file, job=job) for file in files for job in jobs]
            return tasks

        epub_list = [file for file in files if  os.path.splitext(file.file.path)[1] == '.epub']
        pdf_list = [file for file in files if  os.path.splitext(file.file.path)[1] == '.pdf']
        files_list = [file for file in files if  os.path.splitext(file.file.path)[1] != '.epub' and os.path.splitext(file.file.path)[1] != '.pdf']
        jobs_list = [job for job in jobs if job.target_language!=None]

        if hasattr(project, "ai_user"):
            assign_to = project.ai_user

        if not assign_to:
            raise ValueError("You should send parameter either project "
                             "object or assign_to user")

        tasks = [self.get_or_create(file=file, job=job) for file in files_list for job in jobs_list]
        if epub_list:
            html_files_list = self.epub_processing(epub_list,project)
            additional_tasks = [self.get_or_create(file=file, job=job) for file in html_files_list for job in jobs]
        if pdf_list:
            self.create_tasks_of_pdf_files_and_jobs(project,pdf_list,jobs[0].source_language)
        return tasks

    def create_tasks_of_pdf_files_and_jobs(self,project,pdf_list,lang):
        from ai_workspace.models import Job
        j_klass = Job
        jobs_data = {'source_language':lang,'target_language':None}
        job = j_klass.objects.pdf_job_create(
            jobs_data, project, j_klass
        )
        additional_tasks = [self.get_or_create(file=file, job=job) for file in pdf_list]

    def create_tasks_of_files_and_jobs_by_project(self, project):
        files = project.project_files_set.all()
        jobs = project.project_jobs_set.all()
        print(files,jobs,project)
        return self.create_tasks_of_files_and_jobs(
            files=files, jobs=jobs, klass=None, project=project
        )

    def create_glossary_tasks_of_jobs(self, jobs, klass,\
          project = None):
        for job in jobs:
            if job.target_language == None:
                job.target_language = job.source_language
                job.save()
        glossary_tasks = [self.get_or_create(job=job) for job in jobs]
        return glossary_tasks

    def create_design_tasks_of_jobs(self, jobs, klass,\
          project = None):
        design_tasks = [self.get_or_create(job=job) for job in jobs]
        return design_tasks

    def create_glossary_tasks_of_jobs_by_project(self, project):
        jobs = project.project_jobs_set.all()
        print([[job.source_language,job.target_language] for job in jobs ])
        return self.create_glossary_tasks_of_jobs(
            jobs=jobs, klass=None)

    def create_tasks_of_audio_files(self, files,jobs,klass,project = None):
        file_formats = ['.mp3']
        if hasattr(project, "ai_user"):
            assign_to = project.ai_user

        files_list = [file for file in files if  os.path.splitext(file.file.path)[1] not in file_formats]
        audio_files = [file for file in files if  os.path.splitext(file.file.path)[1] in file_formats]
        additional_job = [job for job in jobs if job.target_language == None]
        jobs_list = [job for job in jobs if job.target_language!=None]
        if not assign_to:
            raise ValueError("You should send parameter either project "
                             "object or assign_to user")
        if project.voice_proj_detail.project_type_sub_category_id == 1:
            tasks = [self.get_or_create(file=file, job = job) for file in files_list for job in jobs_list ]#, version_id=1, defaults = {"assign_to": assign_to}
            additional_tasks = [self.get_or_create(file=file, job = job) for file in audio_files for job in additional_job]#version_id=1, defaults = {"assign_to": assign_to})
        else:
            tasks = [self.get_or_create(file=file, job = job) for file in files_list for job in jobs_list ]#, version_id=1, defaults = {"assign_to": assign_to}
            additional_tasks = [self.get_or_create(file=file, job = job) for file in files_list for job in additional_job]#, version_id=1, defaults = {"assign_to": assign_to}
        return tasks

    def create_tasks_of_audio_files_by_project(self, project):
        files = project.project_files_set.all()
        jobs = project.project_jobs_set.all()
        print(files,jobs,project)
        return self.create_tasks_of_audio_files(
            files=files, jobs=jobs, klass=None, project=project
        )

class TaskAssignManager(models.Manager):

    def task_assign_update(self, pk, mt_engine , mt_enable, pre_translate,copy_paste_enable):
        self.filter(pk__in=pk).update(mt_engine_id = mt_engine, mt_enable = mt_enable, pre_translate=pre_translate,copy_paste_enable=copy_paste_enable)

    def assign_task(self,project):
        print("PRO---->",project.id)
        if hasattr(project, "ai_user"):
            assign_to = project.created_by
        tasks = project.get_tasks
        print("Tasks------->",tasks)
        mt_engine = project.mt_engine_id
        mt_enable = project.mt_enable
        pre_translate = project.pre_translate
        steps = project.get_steps
        copy_paste_enable = project.copy_paste_enable
        print("Inside Manager---------->",pre_translate)
        print("Inside---->",steps)
        for task in tasks:
            for step in steps:
                obj,created = self.get_or_create(task=task,step=step,reassigned=False,\
                         defaults = {"assign_to": assign_to,"status":1,"mt_engine_id":mt_engine,\
                         "mt_enable":mt_enable,"pre_translate":pre_translate,'copy_paste_enable':copy_paste_enable})
                if not created:
                    self.filter(pk__in=obj.id).update(mt_engine_id = mt_engine, mt_enable = mt_enable, pre_translate=pre_translate,copy_paste_enable=copy_paste_enable)
        return None       
        # task_assign = [self.get_or_create(task=task,step=step,reassigned=False,\
        #                  defaults = {"assign_to": assign_to,"status":1,"mt_engine_id":mt_engine,\
        #                  "mt_enable":mt_enable,"pre_translate":pre_translate,'copy_paste_enable':copy_paste_enable})\
        #                 for task in tasks for step in steps]
        # print("Insideeee-------->",task_assign)
        # #data = [i[0].id for i in task_assign if i[1]==False]
        # data = list(map(lambda i: i[0].id, filter(lambda i: not i[1], task_assign)))
        # self.task_assign_update(data,mt_engine,mt_enable,pre_translate,copy_paste_enable)
        # print("tASK ASSIGN --> ", task_assign)
        # return task_assign
        #return obj

    # def create_tasks_of_audio_files(self, files,jobs,klass,project = None):
    #     if hasattr(project, "ai_user"):
    #         assign_to = project.ai_user
    #
    #     files_list = [file for file in files if  os.path.splitext(file.file.path)[1] != '.mp3']
    #     audio_files = [file for file in files if  os.path.splitext(file.file.path)[1] == '.mp3']
    #     additional_job = [job for job in jobs if job.target_language == None]
    #     jobs_list = [job for job in jobs if job.target_language!=None]
    #     if not assign_to:
    #         raise ValueError("You should send parameter either project "
    #                          "object or assign_to user")
    #     if project.voice_proj_detail.project_type_sub_category_id == 1:
    #         tasks = [self.get_or_create(file=file, job = job) for file in files_list for job in jobs_list ]#, version_id=1, defaults = {"assign_to": assign_to}
    #         additional_tasks = [self.get_or_create(file=file, job = job) for file in audio_files for job in additional_job]#version_id=1, defaults = {"assign_to": assign_to})
    #     else:
    #         tasks = [self.get_or_create(file=file, job = job) for file in files_list for job in jobs_list ]#, version_id=1, defaults = {"assign_to": assign_to}
    #         additional_tasks = [self.get_or_create(file=file, job = job) for file in files_list for job in additional_job]#, version_id=1, defaults = {"assign_to": assign_to}
    #     return tasks
    #
    # def create_tasks_of_audio_files_by_project(self, project):
    #     files = project.project_files_set.all()
    #     jobs = project.project_jobs_set.all()
    #     print(files,jobs,project)
    #     return self.create_tasks_of_audio_files(
    #         files=files, jobs=jobs, klass=None, project=project
    #     )
            # query = [ChoiceLists.objects.get_or_create(user=project.ai_user,language_id=i,is_default=True) for i in target_languages]
            # #query = ChoiceLists.objects.filter(user = project.ai_user).filter(language_id__in = target_languages).filter(is_default=True)
            # print("Qr------------>",query)
            # objects = [item[0] for item in query]
            # if objects:
            #     ChoiceListSelected.objects.filter(project=project,choice_list__language_id=i) f
            #     ch = [ChoiceListSelected.objects.get_or_create(project=project,choice_list=i) for i in objects]
            #     print("Ch--------->",ch)
            # return None