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
            data, files_key, jobs_key, f_klass, j_klass, ai_user):
        files_data = data.pop(files_key)
        jobs_data = data.pop(jobs_key)
        project = self.create(**data, ai_user=ai_user)
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

class TaskManager(models.Manager):
    def create_tasks_of_files_and_jobs(self, files, jobs, klass,\
        assign_to=None,  project = None):

        if hasattr(project, "ai_user"):
            assign_to = project.ai_user

        if not assign_to:
            raise ValueError("You should send parameter either project "
                             "object or assign_to user")
                                                                    # POSTEDIT
        tasks = [self.get_or_create(file=file, job=job, assign_to=assign_to,\
                    version_id=1) for file in files for job in jobs]

        return tasks

    def create_tasks_of_files_and_jobs_by_project(self, project):
        files = project.project_files_set.all()
        jobs = project.project_jobs_set.all()
        return self.create_tasks_of_files_and_jobs(
            files=files, jobs=jobs, klass=None, project=project
        )
