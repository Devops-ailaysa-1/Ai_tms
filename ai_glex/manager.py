from django.db.models import QuerySet
from django.db import models



class GlossaryTasksManager(models.Manager):
    def create_glossary_tasks_of_jobs(self, jobs, glossary, klass,\
          project = None):
        glossary_tasks = [self.get_or_create(glossary=glossary, job=job) for job in jobs]
        return glossary_tasks

    def create_glossary_tasks_of_jobs_by_project(self, project, glossary):
        jobs = project.project_jobs_set.all()
        return self.create_glossary_tasks_of_jobs(
            jobs=jobs, klass=None, glossary=glossary)
