from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, JsonResponse
from django import views
from .forms import (JobForm, FileForm, ProjectForm, LoginForm, TaskForm, ProjectFormv2,
                TaskListForm)
from .models import Job, File
from django.forms import modelform_factory
from django.forms import formset_factory
import requests, json
import requests
from .serializers import TaskSerializer, TaskSerializerv2
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from ai_workspace_okapi.api_views import DocumentViewByTask
from ai_workspace_okapi.serializers import DocumentSerializerV2

# JobForm = modelform_factory(Job, fields=("source_language", "target_language"))
# Create your views here.

class LoginRequiredMixin(LoginRequiredMixin):
    login_url = "dj/login"
    redirect_field_name = "redirect_to"

class LoginView(views.View):
    def get(self, request):
        form = LoginForm()
        return render(request, "login.html", context={"form": form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(request, **form.cleaned_data)
            if user is not None:
                login(request, user)
                return redirect(request.GET.get("redirect_to"))
        return render(request, "login.html", context={"form": form})

class LoginOutView(views.View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect(reverse("dj-login"))

# class ProjectSetupDjView(LoginRequiredMixin, views.View):

#     def get(self, request):
#         print("user--->", request.user)
#         project_form = ProjectFormv2()
#         return render(request, "project-setup.html", context={"project_form":project_form})

#     def post(self, request):
#         project_form = ProjectFormv2(request.POST or None, request.FILES)
#         if project_form.is_valid():
#             project_serlzr = ProjectSetupSerializer(data=project_form.cleaned_data,
#                                 context={"request": request})
#             if project_serlzr.is_valid(raise_exception=True):
#                 project_serlzr.save()
#                 return redirect(reverse("task-create-dj", kwargs={"project_id": project_serlzr.instance.id}))
#         else:
#             return render(request, "project-setup.html", context={"project_form":project_form})

class TaskCreateViewDj(LoginRequiredMixin, views.View):

    def get(self, request, project_id):
        form = TaskForm()
        form.fields["file"].queryset = form.fields["file"].queryset.filter(project_id=project_id).all()
        form.fields["job"].queryset = form.fields["job"].queryset.filter(project_id=project_id).all()
        return render(
            request, "task-create.html",
            {"form": form}
        )

    def post(self, request, project_id):
        form = TaskForm(request.POST)
        if form.is_valid():
            print("data--->", form.cleaned_data)
            task_serlzr = TaskSerializerv2(data=form.cleaned_data)
            if task_serlzr.is_valid(raise_exception=True):
                task_serlzr.save()
                return redirect(
                    reverse("task-list-dj")
                )
        else:
            return render(
                request, "task-create.html",
                {"form": form}
            )

class TaskListView(LoginRequiredMixin, views.View):
    # showing all tasks created by user
    def get(self, request):
        form = TaskListForm()
        form.fields["tasks"].queryset =  (
            form.fields["tasks"].queryset.filter(file__project__ai_user=request.user)
        ).all()
        return render(request, "task-list-view.html", context={"form": form})

    # opening the document of a speciific task
    def post(self, request):
        form = TaskListForm(request.POST or None)
        if form.is_valid():
            task = form.cleaned_data.get("tasks") # Single Task returned
            document = DocumentViewByTask.create_document_for_task_if_not_exists(task, request)
            return redirect(reverse("ws_okapi:document-list"))
