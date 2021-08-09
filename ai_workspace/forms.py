from django import forms
from .models import Project, Job, File, Task, VersionChoices, Version
from ai_staff.models import Languages
from ai_auth.models import AiUser
from ai_staff.models import Languages
import json

class JobForm(forms.ModelForm):
    # project = forms.CharField(required=False)
	# source_language = forms.ChoiceField(choices=[(lang.id, lang.language) for lang in Languages.objects.all()])
	class Meta:
		model = Job
		fields = ( "source_language", "target_language")

class FileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ( "file", )

class ProjectForm(forms.ModelForm):
    project_name = forms.CharField(required=False)
    class Meta:
        model = Project
        fields = ( "project_name", )

class LoginForm(forms.Form):
    email = forms.EmailField(required=True);
    password = forms.CharField(required=True, widget=forms.PasswordInput())

    class Meta:
        fields = (
            "email", "password"
        )

class TaskForm(forms.ModelForm):
    file = forms.ModelChoiceField(queryset=File.objects.all())
    job = forms.ModelChoiceField(queryset=Job.objects.all())
    version = forms.ModelChoiceField(queryset=Version.objects.all())
    assign_to = forms.ModelChoiceField(queryset=AiUser.objects.filter(
                    userattribute__user_type__type="vendor") .all())
    class Meta:
        model = Task
        fields = (
            "file", "job", "version", "assign_to",
        )

        extra_kwargs = {
            "file": {"write_only": True},
            "job": {"write_only": True},
            "version": {"write_only": True},
            "assign_to": {"write_only": True},
        }

    def is_valid(self):
        valid = super().is_valid()
        if not valid:
            return valid
        # set_ ids
        self.cleaned_data = { k:v.id for k, v in self.cleaned_data.items()}
        return valid

class TaskListForm(forms.Form):
    tasks = forms.ModelChoiceField(queryset=Task.objects.all())

    class Meta:
        fields = (
            "tasks",
        )

class ProjectFormv2(forms.ModelForm):
    source_language = forms.ModelChoiceField(queryset=Languages.objects.all())
    target_languages = forms.ModelMultipleChoiceField(queryset=Languages.objects.all())
    files = forms.FileField(widget=forms.ClearableFileInput(attrs={"multiple": True}))

    class Meta:
        model = Project
        fields = (
            "files", "source_language", "target_languages"
        )

    def is_valid(self):
        valid = super().is_valid()
        if not valid:
            return valid
        self.cleaned_data["source_language"] = json.dumps(self.cleaned_data["source_language"].id)
        self.cleaned_data["target_languages"] = json.dumps([tl.id for tl in self.cleaned_data["target_languages"]])
        self.cleaned_data["files"] = self.files.getlist("files")
        return valid
        # self.cleaned_data


