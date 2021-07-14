from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django import views
from .forms import JobForm, FileForm, ProjectForm
from .models import Job, File
from django.forms import modelform_factory
from django.forms import formset_factory
import requests, json

# JobForm = modelform_factory(Job, fields=("source_language", "target_language"))
# Create your views here.

class ProjectSetupDjView(views.View):
    def get(self, request):
        formset_job = formset_factory(JobForm, extra=2)
        job_form = formset_job()
        formset_file = formset_factory(FileForm, extra=2)
        file_form = formset_file()
        project_form = ProjectForm()
        return render(request, "project-setup.html", context={
                "form1":job_form, "form2":file_form, "form3":project_form})

    def post(self, request):
        formset_job = formset_factory(JobForm, extra=2)
        job_form = formset_job(request.POST or None)
        formset_file = formset_factory(FileForm, extra=2)
        file_form = formset_file(request.POST, request.FILES)
        project_form = ProjectForm(request.POST or None)
        if job_form.is_valid() and file_form.is_valid() and project_form.is_valid():
            res = requests.post("http://localhost:8000/workspace/project_setup/",
                        data = {**project_form.cleaned_data,
                        "jobs": [{"source_language":1, "target_language":2}]
                        }, files= [ value["file"] for  value in file_form.cleaned_data], headers={"Content-Type": "multipart/form-data;"})
            if res.status_code in [200, 201]:
                return JsonResponse(res.json(), safe=False)
            else:
                return JsonResponse({"message": res.text}, safe=False)
            # return render(request, "project-setup.html", context={"form":job_form})
        else:
            print("errors--->", job_form.errors)
        return render(request, "project-setup.html", context={
                "form1":job_form, "form2":file_form, "form3": project_form})
