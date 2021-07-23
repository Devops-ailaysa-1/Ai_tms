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
        formset_file = formset_factory(FileForm, extra=1)
        file_form = formset_file()
        project_form = ProjectForm()
        return render(request, "project-setup.html", context={
                "form1":job_form, "form2":file_form, "form3":project_form})

    def post(self, request):
        formset_job = formset_factory(JobForm, extra=2)
        job_form = formset_job(request.POST or None)
        formset_file = formset_factory(FileForm, extra=1)
        file_form = formset_file(request.POST, request.FILES)
        project_form = ProjectForm(request.POST or None)
        if job_form.is_valid() and file_form.is_valid() and project_form.is_valid():
            headers = {
                'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjI3MDUzNzMxLCJqdGkiOiI3MjIzOTQxNDFjYmQ0ZTgyYmY5MDA1ZWJkYWVlMzk4MyIsInVzZXJfaWQiOjh9.xgKd808exSkuTEeqkZGgW7DwrXkH62HxGlpCmo9paoE',}
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
                return JsonResponse(res.json(), safe=False)
            else:
                return JsonResponse({"message": res.text}, safe=False)
            # return render(request, "project-setup.html", context={"form":job_form})
        else:
            print("errors--->", job_form.errors)
        return render(request, "project-setup.html", context={
                "form1":job_form, "form2":file_form, "form3": project_form})
# import requests
#
# url = "http://localhost:8000/workspace/project_setup/"
#
# payload = {'project_name': 'new_project1116',
# 'jobs': [{"source_language":2, "target_language":1}]}
# files = [
#   ('files', open('/home/langscape/Desktop/test-resume.html','rb')),
#   ('files', open('/home/langscape/Desktop/tm_mt.doc.txt','rb'))
# ]
# headers = {
#   'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjI2OTUxNTE5LCJqdGkiOiI2ZGZmYzdlMzVlNWQ0YmUwYWU2MGZjNTI5M2Q4OGQ4ZCIsInVzZXJfaWQiOjJ9.lkEAB2fWkZnLD-rYUad9UWwnsfJoXHXVUkAlXhEPWc8',
#   'Cookie': 'sessionid=hdluuplhix4nrgoej0zy6j1on082f1mn; csrftoken=9Fcy2nh51hI7vQwhRbARcKwP56dZ0MOYadtqMppC83AhSkjrAVhItYFGptkDqWxN'
# }
#
# response = requests.request("POST", url, headers=headers, data = payload, files = files)
#
# print(response.text.encode('utf8'))
