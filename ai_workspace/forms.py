from django import forms
from .models import Project, Job, File

class JobForm(forms.ModelForm):
    # project = forms.CharField(required=False)
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
