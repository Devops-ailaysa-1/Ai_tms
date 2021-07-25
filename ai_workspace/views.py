from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, JsonResponse
from django import views
from .forms import JobForm, FileForm, ProjectForm, LoginForm, TaskForm
from .models import Job, File
from django.forms import modelform_factory
from django.forms import formset_factory
import requests, json
import requests

# JobForm = modelform_factory(Job, fields=("source_language", "target_language"))
# Create your views here.

class ProjectSetupDjView(views.View):
    def get(self, request):
        formset_job = formset_factory(JobForm, extra=1)
        job_form = formset_job()
        formset_file = formset_factory(FileForm, extra=1)
        file_form = formset_file()
        project_form = ProjectForm()
        return render(request, "project-setup.html", context={
                "form1":job_form, "form2":file_form, "form3":project_form})

    def post(self, request):
        formset_job = formset_factory(JobForm, extra=1)
        job_form = formset_job(request.POST or None)
        formset_file = formset_factory(FileForm, extra=1)
        file_form = formset_file(request.POST, request.FILES)
        project_form = ProjectForm(request.POST or None)
        if job_form.is_valid() and file_form.is_valid() and project_form.is_valid():
            bearer_token = request.session.get("access_token", "")
            headers = {
                'Authorization': f'Bearer {bearer_token}',}
            # res = requests.post("http://localhost:8000/workspace/project_setup/",
            jobs = []
            for job in job_form:
                job.cleaned_data["source_language"] = job.cleaned_data["source_language"].id
                job.cleaned_data["target_language"] = job.cleaned_data["target_language"].id
                jobs.append(job.cleaned_data)
            data = {**project_form.cleaned_data, "jobs":[jobs],}
            files= [ ("files", value["file"]) for  value in file_form.cleaned_data]
            res = requests.request("POST", url="http://localhost:8000/workspace/project_setup/", headers=headers, data = data, files = files)
            if res.status_code in [200, 201]:
                return redirect("/workspace/tasks_dj")
            else:
                return JsonResponse({"message": res.text}, safe=False)
            # return render(request, "project-setup.html", context={"form":job_form})
        else:
            print("errors--->", job_form.errors)
        return render(request, "project-setup.html", context={
                "form1":job_form, "form2":file_form, "form3": project_form})

class LoginView(views.View):
    def get(self, request):
        form = LoginForm()
        return render(request, "login.html", context={"form": form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            res = requests.post("http://localhost:8000/auth/dj-rest-auth/login/", data=form.cleaned_data)
            print("status code---->", res.status_code)
            if res.status_code == 200:
                request.session["access_token"] = res.json().get("access_token", "")
                return redirect("/workspace/project_setup-dj")
        else:
            print("errors---->", form.errors )
        return render(request, "login.html", context={"form": form})

def session_test(request):
    print("session---->", request.session.get("access_token"))
    return HttpResponse(f"<h1>{request.session.get('access_token')}</h1>")

class TasksListViewDj(views.View):
    def get(self, request):
        bearer_token = request.session.get("access_token", "")
        res = requests.get("http://localhost:8000/workspace/tasks", headers = {
            'Authorization': f'Bearer {bearer_token}',}
        )
        if res.status_code in [200, 201]:
            return render(request, "tasks.html", context={"data": res.json()})
        return JsonResponse({"msg": "Something went to wrong!!!"}, safe=False)

class TaskCreateViewDj(views.View):
    def get(self, request):
        form = TaskForm()
        return render(request, "task-create.html", context={"form": form})

