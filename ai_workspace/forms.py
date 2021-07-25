from django import forms
from .models import Project, Job, File, Task
from ai_staff.models import Languages
from ai_auth.models import AiUser

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