from django.contrib.auth.models import BaseUserManager
from django.db.models import QuerySet
from django.db import models

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
        project = self.create(**data, ai_user=ai_user,project_manager=project_manager,\
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

class FileManager(models.Manager):
    def bulk_create_of_project(self, \
            data, project, klass):
        files = [self.create(**item, project=project) for item in data]
        return files

class JobManager(models.Manager):
    def bulk_create_of_project(self, \
            data, project, klass):
        jobs = [self.create(**item, project=project) for item in data]
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
    def create_tasks_of_files_and_jobs(self, files, jobs, klass,\
          project = None):

        if hasattr(project, "ai_user"):
            assign_to = project.ai_user

        if not assign_to:
            raise ValueError("You should send parameter either project "
                             "object or assign_to user")
        # tasks = [self.get_or_create(file=file, job=job, version_id=1, defaults = {"assign_to": assign_to}) for file in files for job in jobs]
        tasks = [self.get_or_create(file=file, job=job) for file in files for job in jobs]
        print(tasks)
        return tasks


    def create_tasks_of_files_and_jobs_by_project(self, project):
        files = project.project_files_set.all()
        jobs = project.project_jobs_set.all()
        print(files,jobs,project)
        return self.create_tasks_of_files_and_jobs(
            files=files, jobs=jobs, klass=None, project=project
        )

    def create_glossary_tasks_of_jobs(self, jobs, klass,\
          project = None):
        glossary_tasks = [self.get_or_create(job=job) for job in jobs]
        return glossary_tasks

    def create_glossary_tasks_of_jobs_by_project(self, project):
        jobs = project.project_jobs_set.all()
        return self.create_glossary_tasks_of_jobs(
            jobs=jobs, klass=None)

class TaskAssignManager(models.Manager):

    def task_assign_update(self, pk, mt_engine , mt_enable):
        self.filter(pk__in=pk).update(mt_engine_id = mt_engine, mt_enable = mt_enable)

    def assign_task(self,project):
        # print("PRO---->",project.id)
        if hasattr(project, "ai_user"):
            assign_to = project.created_by
        tasks = project.get_tasks
        mt_engine = project.mt_engine_id
        mt_enable = project.mt_enable
        pre_translate = project.pre_translate
        steps = project.get_steps
        # print("Inside Manager---------->",tasks)
        # print("Inside---->",steps)
        task_assign = [self.get_or_create(task=task,step=step,\
                         defaults = {"assign_to": assign_to,"status":1,"mt_engine_id":mt_engine,\
                         "mt_enable":mt_enable,"pre_translate":pre_translate})\
                        for task in tasks for step in steps]
        data = [i[0].id for i in task_assign if i[1]==False]
        self.task_assign_update(data,mt_engine,mt_enable)
        # print("tASK ASSIGN --> ", task_assign)
        return task_assign
